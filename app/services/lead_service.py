import csv
import io
import logging
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import Lead, LeadStatus
from app.schemas.lead import LeadCreate, LeadUpdate
from app.ml.scorer import score_lead, LeadFeatures
from app.core.config import settings

logger = logging.getLogger(__name__)


async def create_lead(db: AsyncSession, data: LeadCreate) -> Lead:
    """Save a new lead to the database."""
    lead = Lead(**data.model_dump())
    db.add(lead)
    await db.flush()  # writes to DB but doesn't commit yet
    return lead


async def get_lead(db: AsyncSession, lead_id: str) -> Optional[Lead]:
    """Find one lead by their ID."""
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    return result.scalar_one_or_none()  # returns None if not found


async def list_leads(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 50,
    status: Optional[str] = None,
    min_score: Optional[float] = None,
) -> tuple[list[Lead], int]:
    """Get a paginated list of leads with optional filters."""
    q = select(Lead)

    # Apply filters if provided
    if status:
        q = q.where(Lead.status == status)
    if min_score is not None:
        q = q.where(Lead.score >= min_score)

    # Count total matching leads
    total_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = total_result.scalar()

    # Apply pagination and sort by score (highest first)
    q = q.order_by(Lead.score.desc())
    q = q.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(q)
    return result.scalars().all(), total


async def update_lead(db: AsyncSession, lead_id: str, data: LeadUpdate) -> Optional[Lead]:
    """Update specific fields on a lead."""
    lead = await get_lead(db, lead_id)
    if not lead:
        return None
    # Only update fields that were actually sent
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(lead, field, value)
    return lead


async def score_single_lead(db: AsyncSession, lead_id: str) -> Optional[Lead]:
    """Run the ML scorer on one lead and save the results."""
    lead = await get_lead(db, lead_id)
    if not lead:
        return None

    # Mark as currently being scored
    lead.status = LeadStatus.scoring

    # Build the features object for the scorer
    features = LeadFeatures(
        name=lead.name,
        email=lead.email,
        company=lead.company,
        title=lead.title,
        industry=lead.industry,
        company_size=lead.company_size,
        website=lead.website,
        phone=lead.phone,
        linkedin_url=lead.linkedin_url,
    )

    # Run the scorer
    result = score_lead(features, threshold=settings.SCORE_THRESHOLD)

    # Save results back to the lead
    lead.score = result.score
    lead.score_breakdown = result.breakdown
    lead.score_version = result.model_used
    lead.is_qualified = result.is_qualified
    lead.status = LeadStatus.qualified if result.is_qualified else LeadStatus.disqualified
    
    if lead.is_qualified:
        await notify_n8n(lead)

    return lead


async def bulk_score_leads(db: AsyncSession, lead_ids: list[str]) -> dict:
    """Score a list of leads all at once."""
    qualified = 0
    disqualified = 0
    results = []

    for lead_id in lead_ids:
        lead = await score_single_lead(db, lead_id)
        if lead:
            if lead.is_qualified:
                qualified += 1
            else:
                disqualified += 1
            results.append({
                "lead_id": lead.id,
                "score": lead.score,
                "is_qualified": lead.is_qualified,
                "breakdown": lead.score_breakdown,
            })

    return {
        "processed": len(results),
        "qualified": qualified,
        "disqualified": disqualified,
        "results": results,
    }


async def ingest_csv(db: AsyncSession, csv_content: str, source: str = "csv") -> dict:
    """
    Parse a CSV file and bulk create + score all leads inside it.
    Handles messy column names automatically.
    """
    reader = csv.DictReader(io.StringIO(csv_content))
    created_ids = []
    errors = []

    # Maps common CSV column variations to our field names
    # So "Email Address" and "email" and "EMAIL" all work
    field_map = {
        "first name": "name",
        "full name": "name",
        "email address": "email",
        "company name": "company",
        "organization": "company",
        "job title": "title",
        "position": "title",
        "phone number": "phone",
        "mobile": "phone",
        "linkedin": "linkedin_url",
        "employees": "company_size",
        "headcount": "company_size",
    }

    for i, row in enumerate(reader):
        try:
            # Normalize the column names
            normalized = {}
            for k, v in row.items():
                key = field_map.get(
                    k.lower().strip(),
                    k.lower().strip().replace(" ", "_")
                )
                normalized[key] = v.strip() if v else None

            # Name and email are required
            if not normalized.get("name") or not normalized.get("email"):
                errors.append({"row": i + 2, "reason": "Missing name or email"})
                continue

            # Only pass fields that LeadCreate actually accepts
            valid_fields = {
                k: v for k, v in normalized.items()
                if k in LeadCreate.model_fields
            }

            lead_data = LeadCreate(source=source, raw_data=row, **valid_fields)
            lead = await create_lead(db, lead_data)
            created_ids.append(lead.id)

        except Exception as e:
            errors.append({"row": i + 2, "reason": str(e)})

    await db.flush()

    # Score every lead that was just created
    score_summary = await bulk_score_leads(db, created_ids)

    return {
        "ingested": len(created_ids),
        "errors": errors,
        **score_summary,
    }
async def notify_n8n(lead: Lead):
    """Ping n8n webhook when a lead is qualified."""
    if not settings.N8N_WEBHOOK_URL:
        return

    try:
        import httpx
        payload = {
            "lead_id": lead.id,
            "name": lead.name,
            "email": lead.email,
            "company": lead.company or "",
            "title": lead.title or "",
            "industry": lead.industry or "",
            "company_size": lead.company_size or "",
            "score": lead.score,
            "status": lead.status.value,
        }
        async with httpx.AsyncClient() as client:
            await client.post(
                settings.N8N_WEBHOOK_URL,
                json=payload,
                timeout=10.0,
            )
        logger.info(f"Notified n8n for lead {lead.id}")
    except Exception as e:
        logger.warning(f"Could not notify n8n: {e}")