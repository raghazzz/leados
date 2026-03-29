from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List

from app.db.session import get_db
from app.services import lead_service
from app.ml.scorer import train_model

router = APIRouter()

# Request body for bulk scoring
class BulkScoreRequest(BaseModel):
    lead_ids: List[str]  # list of lead IDs to score

# Request body for training
class TrainRequest(BaseModel):
    leads_data: List[dict]  # list of leads with converted=True/False labels

# SCORE a single lead
# Example: POST /api/v1/scoring/abc-123
@router.post("/{lead_id}")
async def score_lead(lead_id: str, db: AsyncSession = Depends(get_db)):
    """Score or re-score a single lead."""
    lead = await lead_service.score_single_lead(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {
        "lead_id": lead.id,
        "score": lead.score,
        "is_qualified": lead.is_qualified,
        "breakdown": lead.score_breakdown,
    }

# SCORE multiple leads at once
# Example: POST /api/v1/scoring/bulk
@router.post("/bulk")
async def bulk_score(data: BulkScoreRequest, db: AsyncSession = Depends(get_db)):
    """Score multiple leads in one request."""
    result = await lead_service.bulk_score_leads(db, data.lead_ids)
    return result

# TRAIN the ML model
# Example: POST /api/v1/scoring/train
@router.post("/train")
async def trigger_training(data: TrainRequest, background_tasks: BackgroundTasks):
    """
    Train the Random Forest ML model on your historical data.
    Each lead in leads_data needs a 'converted' field (true or false).
    Training happens in the background so the API stays responsive.
    """
    if len(data.leads_data) < 50:
        raise HTTPException(
            status_code=400,
            detail=f"Need at least 50 labeled leads to train. You sent {len(data.leads_data)}."
        )
    background_tasks.add_task(train_model, data.leads_data)
    return {
        "message": "Model training started in the background.",
        "samples": len(data.leads_data)
    }