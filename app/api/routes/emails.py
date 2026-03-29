from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from app.db.session import get_db
from app.models.lead import EmailActivity
from app.schemas.lead import EmailActivityResponse

router = APIRouter()

# Request body for generating an email
class GenerateEmailRequest(BaseModel):
    lead_id: str
    email_type: str = "outreach"         # outreach, follow_up_1, follow_up_2
    custom_context: Optional[str] = None # any extra info to personalise further

# GENERATE an AI email for a lead
# Example: POST /api/v1/emails/generate
@router.post("/generate", response_model=EmailActivityResponse)
async def generate_email(data: GenerateEmailRequest, db: AsyncSession = Depends(get_db)):
    """Generate a personalised AI email for a lead using Mistral."""
    from app.services.email_service import generate_lead_email
    result = await generate_lead_email(
        db,
        data.lead_id,
        data.email_type,
        data.custom_context
    )
    if not result:
        raise HTTPException(
            status_code=404,
            detail="Lead not found or email generation failed"
        )
    return result

# GET all emails for a specific lead
# Example: GET /api/v1/emails/lead/abc-123
@router.get("/lead/{lead_id}", response_model=list[EmailActivityResponse])
async def get_lead_emails(lead_id: str, db: AsyncSession = Depends(get_db)):
    """Get every email that was generated for a specific lead."""
    result = await db.execute(
        select(EmailActivity)
        .where(EmailActivity.lead_id == lead_id)
        .order_by(EmailActivity.created_at.desc())
    )
    return result.scalars().all()

# MARK an email as opened
# Example: PATCH /api/v1/emails/abc-123/opened
@router.patch("/{email_id}/opened")
async def mark_opened(email_id: str, db: AsyncSession = Depends(get_db)):
    """Mark an email as opened (called by email tracking pixel)."""
    result = await db.execute(
        select(EmailActivity).where(EmailActivity.id == email_id)
    )
    email = result.scalar_one_or_none()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    email.opened = True
    return {"status": "marked as opened"}