from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db.session import get_db
from app.schemas.lead import LeadCreate, LeadUpdate, LeadResponse, LeadListResponse
from app.services import lead_service

router = APIRouter()

# CREATE a single lead
# Example: POST /api/v1/leads/
@router.post("/", response_model=LeadResponse, status_code=201)
async def create_lead(data: LeadCreate, db: AsyncSession = Depends(get_db)):
    """Create a single lead and immediately score it."""
    lead = await lead_service.create_lead(db, data)
    await lead_service.score_single_lead(db, lead.id)
    return lead

# GET all leads (with optional filters)
# Example: GET /api/v1/leads/?status=qualified&min_score=70
@router.get("/", response_model=LeadListResponse)
async def list_leads(
    page: int = Query(1, ge=1),                        # which page (default 1)
    page_size: int = Query(50, ge=1, le=200),          # how many per page (default 50)
    status: Optional[str] = None,                      # filter by status
    min_score: Optional[float] = Query(None, ge=0, le=100), # filter by minimum score
    db: AsyncSession = Depends(get_db),
):
    """Get all leads. Can filter by status and minimum score."""
    leads, total = await lead_service.list_leads(db, page, page_size, status, min_score)
    return LeadListResponse(leads=leads, total=total, page=page, page_size=page_size)

# GET a single lead by ID
# Example: GET /api/v1/leads/abc-123
@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(lead_id: str, db: AsyncSession = Depends(get_db)):
    """Get one specific lead by their ID."""
    lead = await lead_service.get_lead(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead

# UPDATE a lead
# Example: PATCH /api/v1/leads/abc-123
@router.patch("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: str,
    data: LeadUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a lead's status, responded, converted, or deal value."""
    lead = await lead_service.update_lead(db, lead_id, data)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead

# UPLOAD a CSV file of leads
# Example: POST /api/v1/leads/upload/csv
@router.post("/upload/csv")
async def upload_csv(
    file: UploadFile = File(...),   # the uploaded file
    db: AsyncSession = Depends(get_db),
):
    """Upload a CSV file. All leads get ingested and scored automatically."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a .csv")

    content = await file.read()

    # Try reading as UTF-8 first, fall back to latin-1
    try:
        csv_text = content.decode("utf-8")
    except UnicodeDecodeError:
        csv_text = content.decode("latin-1")

    result = await lead_service.ingest_csv(db, csv_text, source="csv_upload")
    return result