from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.entities import InspectionRecord, NCRRecord
from app.schemas import InspectionStatus, InspectionSubmit


WORKSTATION_MAP = {
    'QMS-ENNIS-M1': {'area': 'Area A', 'machine_number': 'M1'},
    'QMS-ENNIS-M2': {'area': 'Area B', 'machine_number': 'M2'},
}


class InspectionService:
    def resolve_shift_context(self, workstation: str, now: datetime | None = None) -> dict:
        now = now or datetime.now()
        hour = now.hour
        shift = 'DAY' if 6 <= hour < 18 else 'NIGHT'
        station = WORKSTATION_MAP.get(workstation, {'area': 'Unknown', 'machine_number': workstation})
        return {'shift': shift, **station}

    def next_expected_pipe(self, db: Session, work_order: str, connection: str) -> int:
        stmt = select(func.max(InspectionRecord.pipe_number)).where(
            InspectionRecord.work_order == work_order,
            InspectionRecord.connection == connection,
        )
        current = db.scalar(stmt)
        return (current or 0) + 1

    def _evaluate_measurements(self, recipe: dict, measurements: dict[str, float]) -> bool:
        # expected format in recipe: {'limits': {'od': {'min': 1.0, 'max': 1.1}}}
        limits: dict = recipe.get('limits', {})
        for key, value in measurements.items():
            rule = limits.get(key)
            if not rule:
                continue
            if value < rule['min'] or value > rule['max']:
                return False
        return True

    def submit_inspection(self, db: Session, payload: InspectionSubmit, recipe: dict) -> InspectionRecord:
        expected = self.next_expected_pipe(db, payload.work_order, payload.connection)
        existing = db.scalar(
            select(InspectionRecord)
            .where(
                InspectionRecord.work_order == payload.work_order,
                InspectionRecord.connection == payload.connection,
                InspectionRecord.pipe_number == payload.pipe_number,
                InspectionRecord.status.in_([
                    InspectionStatus.FIRST_INSPECTION.value,
                    InspectionStatus.SECOND_INSPECTION.value,
                    InspectionStatus.THIRD_INSPECTION.value,
                ]),
            )
            .order_by(InspectionRecord.id.desc())
        )

        context = self.resolve_shift_context(payload.workstation)
        passes = self._evaluate_measurements(recipe, payload.measurements)

        if existing:
            inspection_round = existing.inspection_round + 1
        elif payload.pipe_number == expected:
            inspection_round = 1
        else:
            inspection_round = max(payload.pipe_number - expected + 1, 1)

        status = InspectionStatus.COMPLETED.value
        requires_ncr = False

        if not passes:
            requires_ncr = True
            if payload.manager_approved:
                status = InspectionStatus.COMPLETED.value
            else:
                status = {
                    1: InspectionStatus.SECOND_INSPECTION.value,
                    2: InspectionStatus.THIRD_INSPECTION.value,
                }.get(inspection_round, InspectionStatus.SCRAPPED.value)

        if payload.tier_code == 'Tier1':
            status = InspectionStatus.SCRAPPED.value

        record = InspectionRecord(
            work_order=payload.work_order,
            connection=payload.connection,
            pipe_number=payload.pipe_number,
            inspection_round=inspection_round,
            status=status,
            inspector_adp=payload.adp_number,
            inspector_name=payload.inspector_name,
            operator_name=payload.operator_name,
            area=context['area'],
            machine_number=context['machine_number'],
            shift=context['shift'],
            fai_number=payload.fai_number,
            drawing_number=payload.drawing_number,
            measurements=payload.measurements,
        )
        db.add(record)
        db.flush()

        if requires_ncr:
            ncr_status = 'CLOSED' if status in {InspectionStatus.COMPLETED.value, InspectionStatus.SCRAPPED.value} else 'OPEN'
            ncr = NCRRecord(
                inspection_id=record.id,
                tier_code=payload.tier_code or 'Tier2',
                nonconformance=payload.nonconformance or 'Measurement out of tolerance',
                immediate_containment=payload.immediate_containment or 'Hold at station',
                status=ncr_status,
            )
            db.add(ncr)

        db.commit()
        db.refresh(record)
        return record
