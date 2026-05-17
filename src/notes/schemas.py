from datetime import datetime
from typing import (
    Optional,
    List,
)
from pydantic import (
    BaseModel,
    Field,
    UUID4,
)

class NoteCreate(BaseModel):
    content: str = Field(..., max_length=1024)
    tags: Optional[List[str]] = None

    class Config:
        from_attributes = True
        from_orm = True

class NoteUpdate(BaseModel):
    content: Optional[str] = Field(None, max_length=1024)
    tags: Optional[List[str]] = None
    
    class Config:
        from_attributes = True
        from_orm = True

class NoteResponse(BaseModel):
    id: UUID4
    lead_id: UUID4
    content: str
    tags: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        from_orm = True

class NoteListResponse(BaseModel):
    notes: List[NoteResponse]