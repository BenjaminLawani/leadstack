from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Request,
    Path,
    Query,
)

from .models import Note
from .schemas import (
    NoteCreate,
    NoteUpdate,
    NoteResponse,
    NoteListResponse,
)

from src.auth.models import User
from src.leads.models import Lead


from src.core.config import settings, templates
from src.core.db import get_db
from src.core.enums import NoteTag

from src.core.security import get_current_user

notes_router = APIRouter(
    prefix="/notes", 
    tags=["notes"]
)

@notes_router.post("/{lead_id}/", response_model=NoteResponse)
def create_note(
    request: Request,
    lead_id: UUID,
    note: NoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )
    try:
        db_note = Note(
            lead_id=lead_id,
            owner_id=current_user.id,
            content=note.content,
            tags=note.tags,
        )
        db.add(db_note)
        db.commit()
        db.refresh(db_note)
        return db_note
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create note: {str(e)}",
        )

@notes_router.get("/{lead_id}/{note_id}", response_model=NoteResponse)
def get_note(
    request: Request,
    lead_id: UUID,
    note_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )
    note = db.query(Note).filter(Note.id == note_id, Note.lead_id == lead_id).first()
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        )
    return note

@notes_router.get("/{lead_id}/", response_model=NoteListResponse)
def get_all_notes_for_lead(
    request: Request,
    lead_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),

):
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.owner_id == current_user.id).first()
    return lead.notes

@notes_router.put("/{lead_id}/{note_id}", response_model=NoteResponse)
def update_note(
    request: Request,
    lead_id: UUID,
    note_id: UUID,
    note_update: NoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )
    note = db.query(Note).filter(Note.id == note_id, Note.lead_id == lead_id).first()
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        )
    for key, value in note_update.dict(exclude_unset=True).items():
        setattr(note, key, value)
    db.commit()
    db.refresh(note)
    return NoteResponse.model_validate(note)
