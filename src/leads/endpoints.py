from uuid import UUID
from typing import List
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Query,
    Path,
    Request,
    BackgroundTasks
)

from .models import Lead
from .schemas import (
    LeadCreate,
    LeadResponse,
    LeadUpdate,
)

from src.auth.models import User

from src.core.config import settings, templates
from src.core.db import get_db

from src.core.security import get_current_user
from src.core.utils import fm


lead_router = APIRouter(
    prefix="/leads", 
    tags=["Leads"]
)

@lead_router.post("/", response_model=LeadResponse)
def create_lead(
    request: Request,
    lead: LeadCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new lead"""
    existing_lead = (
        db.query(Lead).
        filter((Lead.email == lead.email),
        (Lead.owner_id == current_user.id)).
        first())

    if existing_lead:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lead with this email already exists"
        )
    try:
        db_lead = Lead(**lead.model_dump(), owner_id=current_user.id)
        db.add(db_lead)
        db.commit()
        db.refresh(db_lead)
        return LeadResponse.model_validate(db_lead)

    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists for this user"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the lead"
        )

@lead_router.get("/", response_model=List[LeadResponse])
def get_leads(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all leads for the current user"""
    leads = db.query(Lead).filter(Lead.owner_id == current_user.id).all()
    return [LeadResponse.model_validate(lead) for lead in leads]

@lead_router.get("/{lead_id}", response_model=LeadResponse)
def get_lead(
    request: Request,
    lead_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific lead by ID"""
    lead = db.query(Lead).filter(
        (Lead.id == lead_id),
        (Lead.owner_id == current_user.id)
    ).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    return LeadResponse.model_validate(lead)

@lead_router.put("/{lead_id}", response_model=LeadResponse)
def update_lead(
    request: Request,
    lead_id: UUID,
    lead_update: LeadUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a lead"""
    db_lead = db.query(Lead).filter(
        (Lead.id == lead_id),
        (Lead.owner_id == current_user.id)
    ).first()
    if not db_lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    for key, value in lead_update.model_dump(exclude_unset=True).items():
        setattr(db_lead, key, value)
    
    db.commit()
    db.refresh(db_lead)
    return LeadResponse.model_validate(db_lead)