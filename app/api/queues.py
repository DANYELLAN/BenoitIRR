from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.session import SessionLocal
from app.models import Pipe, Inspection, NCR, WorkOrder
from app.schemas.inspection import PipeStatusResponse, InspectionResponse

router = APIRouter(prefix="/queues", tags=["Queues"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============ Queue/Status Endpoints ============

@router.get("/first-inspection", response_model=list[PipeStatusResponse])
def get_first_inspection_queue(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Get all pipes waiting for first inspection.
    """
    pipes = (
        db.query(Pipe)
        .filter(Pipe.status == "FIRST_INSPECTION")
        .order_by(desc(Pipe.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    results = []
    for pipe in pipes:
        ncrs = [{"id": ncr.id, "pipe_id": ncr.pipe_id, "tier_code": ncr.tier_code,
                 "nonconformance": ncr.nonconformance, "containment": ncr.containment,
                 "status": ncr.status, "created_at": ncr.created_at} for ncr in pipe.ncrs]
        # Derive a connection_code by selecting the Nth connection for the work order
        conn = (
            db.query(WorkOrder)
            .filter(WorkOrder.id == pipe.work_order_id)
            .first()
        )
        connection_code = None
        if conn and conn.connections:
            idx = max(0, pipe.pipe_number - 1)
            try:
                connection_code = conn.connections[idx].connection_code
            except Exception:
                connection_code = None

        results.append(PipeStatusResponse(
            id=pipe.id,
            work_order_id=pipe.work_order_id,
            pipe_number=pipe.pipe_number,
            current_round=pipe.current_round,
            status=pipe.status,
            created_at=pipe.created_at,
            ncrs=ncrs,
            connection_code=connection_code,
            inspection_status=pipe.status,
        ))
    
    return results


@router.get("/second-inspection", response_model=list[PipeStatusResponse])
def get_second_inspection_queue(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Get all pipes in second inspection round.
    """
    pipes = (
        db.query(Pipe)
        .filter(Pipe.status == "SECOND_INSPECTION")
        .order_by(desc(Pipe.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )

    results = []
    for pipe in pipes:
        ncrs = [{"id": ncr.id, "pipe_id": ncr.pipe_id, "tier_code": ncr.tier_code,
                 "nonconformance": ncr.nonconformance, "containment": ncr.containment,
                 "status": ncr.status, "created_at": ncr.created_at} for ncr in pipe.ncrs]

        conn = (
            db.query(WorkOrder)
            .filter(WorkOrder.id == pipe.work_order_id)
            .first()
        )
        connection_code = None
        if conn and conn.connections:
            idx = max(0, pipe.pipe_number - 1)
            try:
                connection_code = conn.connections[idx].connection_code
            except Exception:
                connection_code = None

        results.append(PipeStatusResponse(
            id=pipe.id,
            work_order_id=pipe.work_order_id,
            pipe_number=pipe.pipe_number,
            current_round=pipe.current_round,
            status=pipe.status,
            created_at=pipe.created_at,
            ncrs=ncrs,
            connection_code=connection_code,
            inspection_status=pipe.status,
        ))

    return results


@router.get("/third-inspection", response_model=list[PipeStatusResponse])
def get_third_inspection_queue(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Get all pipes in third inspection round.
    """
    pipes = (
        db.query(Pipe)
        .filter(Pipe.status == "THIRD_INSPECTION")
        .order_by(desc(Pipe.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )

    results = []
    for pipe in pipes:
        ncrs = [{"id": ncr.id, "pipe_id": ncr.pipe_id, "tier_code": ncr.tier_code,
                 "nonconformance": ncr.nonconformance, "containment": ncr.containment,
                 "status": ncr.status, "created_at": ncr.created_at} for ncr in pipe.ncrs]

        conn = (
            db.query(WorkOrder)
            .filter(WorkOrder.id == pipe.work_order_id)
            .first()
        )
        connection_code = None
        if conn and conn.connections:
            idx = max(0, pipe.pipe_number - 1)
            try:
                connection_code = conn.connections[idx].connection_code
            except Exception:
                connection_code = None

        results.append(PipeStatusResponse(
            id=pipe.id,
            work_order_id=pipe.work_order_id,
            pipe_number=pipe.pipe_number,
            current_round=pipe.current_round,
            status=pipe.status,
            created_at=pipe.created_at,
            ncrs=ncrs,
            connection_code=connection_code,
            inspection_status=pipe.status,
        ))

    return results


@router.get("/awaiting-approval", response_model=list[PipeStatusResponse])
def get_awaiting_approval_queue(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Get all pipes awaiting manager approval/decision.
    """
    pipes = (
        db.query(Pipe)
        .filter(Pipe.status == "AWAITING_MANAGER_APPROVAL")
        .order_by(desc(Pipe.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )

    results = []
    for pipe in pipes:
        ncrs = [{"id": ncr.id, "pipe_id": ncr.pipe_id, "tier_code": ncr.tier_code,
                 "nonconformance": ncr.nonconformance, "containment": ncr.containment,
                 "status": ncr.status, "created_at": ncr.created_at} for ncr in pipe.ncrs]

        results.append(PipeStatusResponse(
            id=pipe.id,
            work_order_id=pipe.work_order_id,
            pipe_number=pipe.pipe_number,
            current_round=pipe.current_round,
            status=pipe.status,
            created_at=pipe.created_at,
            ncrs=ncrs,
        ))

    return results


@router.get("/completed", response_model=list[PipeStatusResponse])
def get_completed_queue(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Get all completed pipes (passed all inspections).
    """
    pipes = (
        db.query(Pipe)
        .filter(Pipe.status == "COMPLETED")
        .order_by(desc(Pipe.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )

    results = []
    for pipe in pipes:
        ncrs = [{"id": ncr.id, "pipe_id": ncr.pipe_id, "tier_code": ncr.tier_code,
                 "nonconformance": ncr.nonconformance, "containment": ncr.containment,
                 "status": ncr.status, "created_at": ncr.created_at} for ncr in pipe.ncrs]

        results.append(PipeStatusResponse(
            id=pipe.id,
            work_order_id=pipe.work_order_id,
            pipe_number=pipe.pipe_number,
            current_round=pipe.current_round,
            status=pipe.status,
            created_at=pipe.created_at,
            ncrs=ncrs,
        ))

    return results


@router.get("/scrapped", response_model=list[PipeStatusResponse])
def get_scrapped_queue(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Get all scrapped pipes (failed inspection).
    """
    pipes = (
        db.query(Pipe)
        .filter(Pipe.status == "SCRAPPED")
        .order_by(desc(Pipe.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )

    results = []
    for pipe in pipes:
        ncrs = [{"id": ncr.id, "pipe_id": ncr.pipe_id, "tier_code": ncr.tier_code,
                 "nonconformance": ncr.nonconformance, "containment": ncr.containment,
                 "status": ncr.status, "created_at": ncr.created_at} for ncr in pipe.ncrs]

        results.append(PipeStatusResponse(
            id=pipe.id,
            work_order_id=pipe.work_order_id,
            pipe_number=pipe.pipe_number,
            current_round=pipe.current_round,
            status=pipe.status,
            created_at=pipe.created_at,
            ncrs=ncrs,
        ))

    return results


# ============ Summary endpoints ============

@router.get("/summary", response_model=dict)
def get_queue_summary(db: Session = Depends(get_db)):
    """
    Get summary counts of all queue statuses.
    """
    first = db.query(Pipe).filter(Pipe.status == "FIRST_INSPECTION").count()
    second = db.query(Pipe).filter(Pipe.status == "SECOND_INSPECTION").count()
    third = db.query(Pipe).filter(Pipe.status == "THIRD_INSPECTION").count()
    awaiting = db.query(Pipe).filter(Pipe.status == "AWAITING_MANAGER_APPROVAL").count()
    completed = db.query(Pipe).filter(Pipe.status == "COMPLETED").count()
    scrapped = db.query(Pipe).filter(Pipe.status == "SCRAPPED").count()
    
    return {
        "first_inspection": first,
        "second_inspection": second,
        "third_inspection": third,
        "awaiting_manager_approval": awaiting,
        "completed": completed,
        "scrapped": scrapped,
        "total": first + second + third + awaiting + completed + scrapped,
    }


@router.get("/work-order/{work_order_id}", response_model=list[PipeStatusResponse])
def get_pipes_for_work_order(
    work_order_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Get all pipes for a specific work order.
    """
    pipes = (
        db.query(Pipe)
        .filter(Pipe.work_order_id == work_order_id)
        .order_by(Pipe.pipe_number)
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    if not pipes:
        return []
    
    results = []
    for pipe in pipes:
        wo = db.query(WorkOrder).filter(WorkOrder.id == pipe.work_order_id).first()
        ncrs = db.query(NCR).filter(NCR.pipe_id == pipe.id).all()

        # Derive connection_code by pipe number (order of connections on the work order)
        connection_code = None
        if wo and wo.connections:
            idx = max(0, pipe.pipe_number - 1)
            try:
                connection_code = wo.connections[idx].connection_code
            except Exception:
                connection_code = None

        results.append(PipeStatusResponse(
            id=pipe.id,
            work_order_id=pipe.work_order_id,
            work_order_external_id=wo.external_id if wo else None,
            pipe_number=pipe.pipe_number,
            connection_code=connection_code,
            current_round=pipe.current_round,
            inspection_status=pipe.status,
            ncrs=[{"id": n.id, "pipe_id": n.pipe_id, "tier_code": n.tier_code,
                   "nonconformance": n.nonconformance, "containment": n.containment,
                   "status": n.status, "created_at": n.created_at} for n in ncrs],
            ncr_count=len(ncrs),
            tier_1_count=len([n for n in ncrs if n.tier_code == "TIER_1"]),
            tier_2_count=len([n for n in ncrs if n.tier_code == "TIER_2"]),
            tier_3_count=len([n for n in ncrs if n.tier_code == "TIER_3"]),
        ))
    
    return results
