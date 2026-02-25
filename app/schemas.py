from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class InspectionStatus(str, Enum):
    FIRST_INSPECTION = 'FIRST_INSPECTION'
    SECOND_INSPECTION = 'SECOND_INSPECTION'
    THIRD_INSPECTION = 'THIRD_INSPECTION'
    COMPLETED = 'COMPLETED'
    SCRAPPED = 'SCRAPPED'


class LoginContext(BaseModel):
    adp_number: str
    workstation: str


class LoginProfile(BaseModel):
    inspector_name: str
    adp_number: str
    login_time: datetime
    shift: str
    area: str
    machine_number: str


class InspectionSubmit(BaseModel):
    adp_number: str
    inspector_name: str
    operator_name: str
    workstation: str
    work_order: str
    connection: str
    pipe_number: int = Field(gt=0)
    fai_number: str
    drawing_number: str
    measurements: dict[str, float]
    manager_approved: bool = False
    tier_code: str | None = None
    nonconformance: str | None = None
    immediate_containment: str | None = None


class InspectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    work_order: str
    connection: str
    pipe_number: int
    inspection_round: int
    status: InspectionStatus


class NCRResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    inspection_id: int
    tier_code: str
    nonconformance: str
    immediate_containment: str
    status: str
    sharepoint_sync_status: str
    sharepoint_synced_at: datetime | None


class NCRSyncUpdate(BaseModel):
    sharepoint_sync_status: str = Field(pattern='^(PENDING|SYNCED)$')


class HealthResponse(BaseModel):
    status: str = 'ok'
