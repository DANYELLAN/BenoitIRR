from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.entities import InspectionRecord
from app.schemas import HealthResponse, InspectionResponse, InspectionSubmit, LoginContext, LoginProfile
from app.services.inspection_service import InspectionService
from app.services.sharepoint_service import SharePointService

router = APIRouter()
sharepoint = SharePointService()
inspections = InspectionService()


@router.get('/health', response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@router.post('/login', response_model=LoginProfile)
async def login(context: LoginContext) -> LoginProfile:
    employees = await sharepoint.get_eligible_employees()
    employee = next((e for e in employees if e.adp_number == context.adp_number), None)
    if not employee:
        raise HTTPException(status_code=404, detail='Active Ennis Quality/Tubular employee not found')

    shift_ctx = inspections.resolve_shift_context(context.workstation)
    return LoginProfile(
        inspector_name=employee.full_name,
        adp_number=employee.adp_number,
        login_time=datetime.utcnow(),
        shift=shift_ctx['shift'],
        area=shift_ctx['area'],
        machine_number=shift_ctx['machine_number'],
    )


@router.get('/work-orders')
async def work_orders() -> list[dict]:
    rows = await sharepoint.get_work_orders()
    return [row.get('fields', {}) for row in rows]


@router.get('/recipes/{connection_name}')
async def recipe(connection_name: str) -> dict:
    return await sharepoint.get_inspection_recipe(connection_name)


@router.post('/inspections', response_model=InspectionResponse)
async def submit_inspection(payload: InspectionSubmit, db: Session = Depends(get_db)) -> InspectionResponse:
    try:
        recipe_row = await sharepoint.get_inspection_recipe(payload.connection)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    record = inspections.submit_inspection(db, payload, {'limits': recipe_row.get('limits', {})})
    return InspectionResponse.model_validate(record)


@router.get('/inspections', response_model=list[InspectionResponse])
def list_inspections(db: Session = Depends(get_db)) -> list[InspectionResponse]:
    rows = db.scalars(select(InspectionRecord).order_by(InspectionRecord.created_at.desc())).all()
    return [InspectionResponse.model_validate(row) for row in rows]
