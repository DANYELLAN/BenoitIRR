from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.schemas import InspectionSubmit
from app.services.inspection_service import InspectionService


def _session():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(bind=engine)
    local = sessionmaker(bind=engine)
    return local()


def test_first_pass_moves_to_completed():
    db = _session()
    svc = InspectionService()
    payload = InspectionSubmit(
        adp_number='123',
        inspector_name='Jane',
        operator_name='Op1',
        workstation='QMS-ENNIS-M1',
        work_order='WO100',
        connection='CONN-A',
        pipe_number=1,
        fai_number='FAI-1',
        drawing_number='DRW-1',
        measurements={'od': 1.05},
    )
    rec = svc.submit_inspection(db, payload, {'limits': {'od': {'min': 1.0, 'max': 1.1}}})
    assert rec.status == 'COMPLETED'
    assert rec.inspection_round == 1


def test_failed_without_approval_goes_to_second_inspection():
    db = _session()
    svc = InspectionService()
    payload = InspectionSubmit(
        adp_number='123',
        inspector_name='Jane',
        operator_name='Op1',
        workstation='QMS-ENNIS-M1',
        work_order='WO100',
        connection='CONN-A',
        pipe_number=1,
        fai_number='FAI-1',
        drawing_number='DRW-1',
        measurements={'od': 1.5},
    )
    rec = svc.submit_inspection(db, payload, {'limits': {'od': {'min': 1.0, 'max': 1.1}}})
    assert rec.status == 'SECOND_INSPECTION'


def test_failed_with_tier1_is_scrapped():
    db = _session()
    svc = InspectionService()
    payload = InspectionSubmit(
        adp_number='123',
        inspector_name='Jane',
        operator_name='Op1',
        workstation='QMS-ENNIS-M1',
        work_order='WO100',
        connection='CONN-A',
        pipe_number=2,
        fai_number='FAI-1',
        drawing_number='DRW-1',
        measurements={'od': 1.5},
        tier_code='Tier1',
    )
    rec = svc.submit_inspection(db, payload, {'limits': {'od': {'min': 1.0, 'max': 1.1}}})
    assert rec.status == 'SCRAPPED'
