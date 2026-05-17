from datetime import datetime
from typing import (
    List,
    Optional,
)
from pydantic import (
    BaseModel,
    UUID4,
    Field,
    EmailStr,
)

from src.core.enums import (
    LeadStatus,
    PipelineStatus
)

class LeadCreate(BaseModel):
    name: str
    company: Optional[str] = None
    phone_number: str
    email: Optional[str] = None

    lead_status: LeadStatus
    pipeline_status: PipelineStatus
    class Config:
        from_attributes = True
        from_orm = True

class LeadResponse(BaseModel):
    id: UUID4
    owner_id: UUID4
    name: str
    company: Optional[str] = None
    phone_number: str = Field(max_length=16)
    email: Optional[str] = None
    lead_status: LeadStatus
    pipeline_status: PipelineStatus

    created_at: datetime

    class Config:
        from_orm = True
        from_attributes = True

class LeadUpdate(BaseModel):
    lead_status: Optional[LeadStatus] = None
    pipeline_status: Optional[PipelineStatus] = None

    company: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None

    class Config:
        from_orm = True
        from_attributes = True

class LeadListResponse(BaseModel):
    leads: List[LeadResponse]

    class Config:
        from_orm = True
        from_attributes = True

class CSVUploadResponse(BaseModel):
    total_rows: int
    successful: int
    failed: int
    errors: List[dict]

    class Config:
        from_attributes = True