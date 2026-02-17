from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.schemas import (
    InspectionStartRequest,
    RecordMeasurementsRequest,
    InspectionResponse,
    ManagerApprovalRequest,
    ApprovalResponse,
    PipeStatusResponse,
)
from app.services.inspection import InspectionService
from app.models import Pipe, Inspection, Approval

router = APIRouter(prefix="/inspections", tags=["Inspections"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/start", response_model=PipeStatusResponse)
def start_inspection(
    request: InspectionStartRequest,
    db: Session = Depends(get_db),
):
    """
    Start a new inspection for a pipe on a work order.
    
    Creates or retrieves a Pipe record and prepares for measurements recording.
    """
    try:
        pipe = InspectionService.start_inspection(
            db=db,
            work_order_id=request.work_order_id,
            connection_code=request.connection_code,
            inspector_id=request.inspector_id,
            pipe_number=request.pipe_number,
            machine_no=request.machine_no,
        )

        # Build response with latest inspection and NCRs
        latest_inspection = None
        if pipe.inspections:
            latest = max(pipe.inspections, key=lambda x: x.created_at)
            latest_inspection = InspectionResponse.from_orm(latest)

        ncrs = [{"id": ncr.id, "pipe_id": ncr.pipe_id, "tier_code": ncr.tier_code,
                 "nonconformance": ncr.nonconformance, "containment": ncr.containment,
                 "status": ncr.status, "created_at": ncr.created_at} for ncr in pipe.ncrs]

        return PipeStatusResponse(
            id=pipe.id,
            work_order_id=pipe.work_order_id,
            pipe_number=pipe.pipe_number,
            current_round=pipe.current_round,
            status=pipe.status,
            created_at=pipe.created_at,
            latest_inspection=latest_inspection,
            ncrs=ncrs,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{pipe_id}/measurements", response_model=PipeStatusResponse)
def record_measurements(
    pipe_id: int,
    request: RecordMeasurementsRequest,
    inspector_id: int,  # In production, this would come from JWT token
    db: Session = Depends(get_db),
):
    """
    Record measurements for a pipe inspection.
    
    Evaluates pass/fail and automatically updates pipe status:
    - All pass → COMPLETED
    - Any fail → AWAITING_MANAGER_APPROVAL + creates NCR
    """
    try:
        inspection, new_status = InspectionService.record_measurements(
            db=db,
            pipe_id=pipe_id,
            inspector_id=inspector_id,
            measurements=[m.dict() for m in request.measurements],
            notes=request.notes,
        )

        # Refresh pipe with new state
        pipe = db.query(Pipe).filter(Pipe.id == pipe_id).first()

        # Build response
        latest_inspection = InspectionResponse.from_orm(inspection)
        ncrs = [{"id": ncr.id, "pipe_id": ncr.pipe_id, "tier_code": ncr.tier_code,
                 "nonconformance": ncr.nonconformance, "containment": ncr.containment,
                 "status": ncr.status, "created_at": ncr.created_at} for ncr in pipe.ncrs]

        return PipeStatusResponse(
            id=pipe.id,
            work_order_id=pipe.work_order_id,
            pipe_number=pipe.pipe_number,
            current_round=pipe.current_round,
            status=pipe.status,
            created_at=pipe.created_at,
            latest_inspection=latest_inspection,
            ncrs=ncrs,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{inspection_id}/manager-decision", response_model=PipeStatusResponse)
def manager_decision(
    inspection_id: int,
    request: ManagerApprovalRequest,
    db: Session = Depends(get_db),
):
    """
    Manager reviews a failed inspection and approves or denies.
    
    - APPROVE → Pipe moves to COMPLETED
    - DENY → Pipe moves to next inspection round (SECOND, THIRD, or SCRAPPED if max rounds exceeded)
    """
    try:
        pipe = InspectionService.manager_decision(
            db=db,
            inspection_id=inspection_id,
            manager_id=request.manager_id,
            decision=request.decision,
            notes=request.notes,
        )

        # Build response
        latest_inspection = None
        if pipe.inspections:
            latest = max(pipe.inspections, key=lambda x: x.created_at)
            latest_inspection = InspectionResponse.from_orm(latest)

        ncrs = [{"id": ncr.id, "pipe_id": ncr.pipe_id, "tier_code": ncr.tier_code,
                 "nonconformance": ncr.nonconformance, "containment": ncr.containment,
                 "status": ncr.status, "created_at": ncr.created_at} for ncr in pipe.ncrs]

        return PipeStatusResponse(
            id=pipe.id,
            work_order_id=pipe.work_order_id,
            pipe_number=pipe.pipe_number,
            current_round=pipe.current_round,
            status=pipe.status,
            created_at=pipe.created_at,
            latest_inspection=latest_inspection,
            ncrs=ncrs,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{pipe_id}", response_model=PipeStatusResponse)
def get_pipe_status(
    pipe_id: int,
    db: Session = Depends(get_db),
):
    """Get current status of a pipe and its inspections/NCRs."""
    pipe = db.query(Pipe).filter(Pipe.id == pipe_id).first()
    if not pipe:
        raise HTTPException(status_code=404, detail=f"Pipe {pipe_id} not found")

    latest_inspection = None
    if pipe.inspections:
        latest = max(pipe.inspections, key=lambda x: x.created_at)
        latest_inspection = InspectionResponse.from_orm(latest)

    ncrs = [{"id": ncr.id, "pipe_id": ncr.pipe_id, "tier_code": ncr.tier_code,
             "nonconformance": ncr.nonconformance, "containment": ncr.containment,
             "status": ncr.status, "created_at": ncr.created_at} for ncr in pipe.ncrs]

    return PipeStatusResponse(
        id=pipe.id,
        work_order_id=pipe.work_order_id,
        pipe_number=pipe.pipe_number,
        current_round=pipe.current_round,
        status=pipe.status,
        created_at=pipe.created_at,
        latest_inspection=latest_inspection,
        ncrs=ncrs,
    )
