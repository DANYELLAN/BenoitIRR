from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
import json

from app.db.session import SessionLocal
from app.integrations import AcumaticaClient, SharePointClient
from app.models import WorkOrder, Connection, Employee, Recipe
from app.schemas.external import AcumaticaWorkOrderDetail, SharePointEmployee, EnrichedWorkOrder

router = APIRouter(prefix="/integrations", tags=["Integrations"])

# Initialize clients with mock mode
acumatica_client = AcumaticaClient(mock_mode=True)
sharepoint_client = SharePointClient(mock_mode=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============ Acumatica Endpoints ============

@router.get("/acumatica/work-orders", response_model=list[AcumaticaWorkOrderDetail])
def list_acumatica_work_orders(
    status: Optional[str] = Query(None, description="Filter by status"),
):
    """
    Fetch work orders from Acumatica.
    
    Mock mode returns sample data; real implementation calls Acumatica API.
    """
    try:
        orders = acumatica_client.list_work_orders(status=status)
        # Fetch full details for each order
        detailed_orders = []
        for order in orders:
            details = acumatica_client.get_work_order(order.order_number)
            if details:
                detailed_orders.append(details)
        return detailed_orders
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Acumatica fetch failed: {str(e)}")


@router.get("/acumatica/work-orders/{order_number}", response_model=AcumaticaWorkOrderDetail)
def get_acumatica_work_order(order_number: str):
    """
    Fetch a specific work order from Acumatica with its connections.
    """
    try:
        order = acumatica_client.get_work_order(order_number)
        if not order:
            raise HTTPException(status_code=404, detail=f"Work order {order_number} not found in Acumatica")
        return order
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Acumatica fetch failed: {str(e)}")


@router.post("/acumatica/work-orders/{order_number}/sync", response_model=dict)
def sync_work_order_to_db(
    order_number: str,
    db: Session = Depends(get_db),
):
    """
    Sync an Acumatica work order into the BenoitIRR database.
    
    Creates:
    - WorkOrder record (if not exists)
    - Connection records for each connection
    - Recipe records (if applicable)
    """
    try:
        # Fetch from Acumatica
        acumatica_order = acumatica_client.get_work_order(order_number)
        if not acumatica_order:
            raise HTTPException(status_code=404, detail=f"Work order {order_number} not found in Acumatica")
        
        # Check if already in DB
        existing_wo = db.query(WorkOrder).filter(WorkOrder.external_id == order_number).first()
        if existing_wo:
            return {"status": "already_exists", "work_order_id": existing_wo.id, "message": f"Work order {order_number} already synced"}
        
        # Create WorkOrder record
        wo = WorkOrder(
            external_id=order_number,
            status="FIRST_INSPECTION",
        )
        db.add(wo)
        db.commit()
        db.refresh(wo)
        
        # Create Connection records
        created_connections = []
        for conn in acumatica_order.connections:
            connection = Connection(
                work_order_id=wo.id,
                connection_code=conn.connection_code,
            )
            db.add(connection)
            
            # Create Recipe record (if not exists)
            existing_recipe = db.query(Recipe).filter(Recipe.connection_code == conn.connection_code).first()
            if not existing_recipe:
                spec_json = json.dumps({
                    "connection_code": conn.connection_code,
                    "description": conn.connection_description,
                    "thread_type": conn.thread_type,
                    "material": conn.material,
                    "measurements": [
                        {"parameter": "OD", "unit": "mm", "min": 10.0, "max": 12.0},
                        {"parameter": "Wall", "unit": "mm", "min": 1.5, "max": 2.5},
                    ],
                })
                recipe = Recipe(
                    connection_code=conn.connection_code,
                    version="1.0",
                    spec_json=spec_json,
                )
                db.add(recipe)
            
            created_connections.append(conn.connection_code)
        
        db.commit()
        
        return {
            "status": "synced",
            "work_order_id": wo.id,
            "external_id": order_number,
            "connections_created": created_connections,
            "message": f"Work order {order_number} synced with {len(created_connections)} connections",
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


# ============ SharePoint Endpoints ============

@router.get("/sharepoint/employees/{adp_number}", response_model=SharePointEmployee)
def get_sharepoint_employee(adp_number: str):
    """
    Fetch employee details from SharePoint by ADP number.
    """
    try:
        employee = sharepoint_client.get_employee(adp_number)
        if not employee:
            raise HTTPException(status_code=404, detail=f"Employee {adp_number} not found in SharePoint")
        return employee
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SharePoint fetch failed: {str(e)}")


@router.get("/sharepoint/employees", response_model=list[SharePointEmployee])
def list_sharepoint_employees(
    department: Optional[str] = Query(None, description="Filter by department"),
):
    """
    List employees from SharePoint.
    """
    try:
        employees = sharepoint_client.list_employees(department=department, active_only=True)
        return employees
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SharePoint fetch failed: {str(e)}")


@router.post("/sharepoint/employees/{adp_number}/sync", response_model=dict)
def sync_employee_to_db(
    adp_number: str,
    db: Session = Depends(get_db),
):
    """
    Sync a SharePoint employee into the BenoitIRR database.
    """
    try:
        # Fetch from SharePoint
        sp_employee = sharepoint_client.get_employee(adp_number)
        if not sp_employee:
            raise HTTPException(status_code=404, detail=f"Employee {adp_number} not found in SharePoint")
        
        # Check if already exists
        existing = db.query(Employee).filter(Employee.adp_number == adp_number).first()
        if existing:
            return {"status": "already_exists", "employee_id": existing.id, "message": f"Employee {adp_number} already in database"}
        
        # Create Employee record
        employee = Employee(
            adp_number=adp_number,
            name=sp_employee.full_name,
            role=sp_employee.role or "inspector",
            active=sp_employee.active,
        )
        db.add(employee)
        db.commit()
        db.refresh(employee)
        
        return {
            "status": "synced",
            "employee_id": employee.id,
            "adp_number": adp_number,
            "name": employee.name,
            "message": f"Employee {adp_number} synced to database",
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/sharepoint/ncr/{work_order_number}/{pipe_number}", response_model=dict)
def get_ncr_for_pipe(
    work_order_number: str,
    pipe_number: int,
):
    """
    Fetch NCR records from SharePoint for a specific pipe.
    """
    try:
        ncrs = sharepoint_client.get_ncr_for_pipe(work_order_number, pipe_number)
        return {
            "work_order_number": work_order_number,
            "pipe_number": pipe_number,
            "ncr_count": len(ncrs),
            "ncrs": ncrs,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SharePoint fetch failed: {str(e)}")


@router.post("/sharepoint/ncr/create", response_model=dict)
def create_ncr_in_sharepoint(
    work_order_number: str,
    pipe_number: int,
    tier_code: str,
    nonconformance: str,
    created_by: str,
):
    """
    Create a new NCR record in SharePoint.
    """
    try:
        ncr_id = sharepoint_client.create_ncr(
            work_order_number=work_order_number,
            pipe_number=pipe_number,
            tier_code=tier_code,
            nonconformance=nonconformance,
            created_by=created_by,
        )
        
        if not ncr_id:
            raise HTTPException(status_code=500, detail="Failed to create NCR in SharePoint")
        
        return {
            "status": "created",
            "ncr_id": ncr_id,
            "work_order_number": work_order_number,
            "pipe_number": pipe_number,
            "message": f"NCR created in SharePoint",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SharePoint create failed: {str(e)}")


# ============ Health checks ============

@router.get("/health", response_model=dict)
def integration_health():
    """Check integration service health."""
    return {
        "status": "healthy",
        "acumatica": "mock" if acumatica_client.mock_mode else "connected",
        "sharepoint": "mock" if sharepoint_client.mock_mode else "connected",
    }