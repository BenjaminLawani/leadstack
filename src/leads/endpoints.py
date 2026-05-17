from uuid import UUID
from typing import List
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
import csv
import io

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Query,
    Path,
    Request,
    BackgroundTasks,
    UploadFile,
    File
)

from .models import Lead
from .schemas import (
    LeadCreate,
    LeadResponse,
    LeadUpdate,
    CSVUploadResponse,
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

@lead_router.post("/upload-csv", response_model=CSVUploadResponse)
async def upload_leads_csv(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload leads from a CSV file
    
    Expected CSV format:
    name,company,phone_number,email,lead_status,pipeline_status
    
    lead_status must be one of: HOT, WARM, COLD
    pipeline_status must be one of: NEW, IN_PROGRESS, CLOSED, WON, LOST, ACTIVE, INACTIVE
    """
    if not file.filename or not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV"
        )
    
    # Read file content
    contents = await file.read()
    csv_data = contents.decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(csv_data))
    
    total_rows = 0
    successful = 0
    failed = 0
    errors = []
    
    # Validate required columns
    required_columns = {'name', 'phone_number', 'lead_status', 'pipeline_status'}
    if not required_columns.issubset(set(csv_reader.fieldnames or [])):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CSV must contain columns: {', '.join(required_columns)}"
        )
    
    for row_num, row in enumerate(csv_reader, start=2):  # start=2 because row 1 is header
        total_rows += 1
        
        try:
            # Validate lead_status
            lead_status_value = row.get('lead_status', '').strip().upper()
            if lead_status_value not in ['HOT', 'WARM', 'COLD']:
                errors.append({
                    'row': row_num,
                    'error': f"Invalid lead_status '{row.get('lead_status')}'. Must be HOT, WARM, or COLD"
                })
                failed += 1
                continue
            
            # Validate pipeline_status
            pipeline_status_value = row.get('pipeline_status', '').strip().upper()
            if pipeline_status_value not in ['NEW', 'IN_PROGRESS', 'CLOSED', 'WON', 'LOST', 'ACTIVE', 'INACTIVE']:
                errors.append({
                    'row': row_num,
                    'error': f"Invalid pipeline_status '{row.get('pipeline_status')}'. Must be NEW, IN_PROGRESS, CLOSED, WON, LOST, ACTIVE, or INACTIVE"
                })
                failed += 1
                continue
            
            # Prepare lead data
            lead_data = {
                'name': row.get('name', '').strip(),
                'company': row.get('company', '').strip() or None,
                'phone_number': row.get('phone_number', '').strip(),
                'email': row.get('email', '').strip() or None,
                'lead_status': lead_status_value,
                'pipeline_status': pipeline_status_value
            }
            
            # Validate required fields
            if not lead_data['name']:
                errors.append({
                    'row': row_num,
                    'error': 'Name is required'
                })
                failed += 1
                continue
            
            if not lead_data['phone_number']:
                errors.append({
                    'row': row_num,
                    'error': 'Phone number is required'
                })
                failed += 1
                continue
            
            # Check for duplicate email for this user
            if lead_data['email']:
                existing_lead = (
                    db.query(Lead)
                    .filter(
                        Lead.email == lead_data['email'],
                        Lead.owner_id == current_user.id
                    )
                    .first()
                )
                
                if existing_lead:
                    errors.append({
                        'row': row_num,
                        'error': f"Lead with email '{lead_data['email']}' already exists"
                    })
                    failed += 1
                    continue
            
            # Create lead
            db_lead = Lead(**lead_data, owner_id=current_user.id)
            db.add(db_lead)
            db.commit()
            db.refresh(db_lead)
            successful += 1
            
        except Exception as e:
            db.rollback()
            errors.append({
                'row': row_num,
                'error': str(e)
            })
            failed += 1
    
    return CSVUploadResponse(
        total_rows=total_rows,
        successful=successful,
        failed=failed,
        errors=errors
    )