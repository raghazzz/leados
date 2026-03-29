from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class LeadStatus(str, Enum):
    ingested = "ingested"
    scoring = "scoring"
    qualified = "qualified"
    disqualified = "disqualified"
    email_sent = "email_sent"
    follow_up_1 = "follow_up_1"
    follow_up_2 = "follow_up_2"
    converted = "converted"
    lost = "lost"

# ── What data is needed TO CREATE a lead ──
class LeadCreate(BaseModel):
    name: str                              # required
    email: EmailStr                        # required, must be valid email format
    company: Optional[str] = None         # optional
    title: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    source: Optional[str] = "api"
    deal_value: Optional[float] = None
    raw_data: Optional[Dict[str, Any]] = None

# ── What data is needed TO UPDATE a lead ──
class LeadUpdate(BaseModel):
    status: Optional[LeadStatus] = None
    responded: Optional[bool] = None
    converted: Optional[bool] = None
    deal_value: Optional[float] = None

# ── What the scoring breakdown looks like ──
class ScoreBreakdown(BaseModel):
    industry_score: float
    title_score: float
    company_size_score: float
    data_completeness: float
    overall: float

# ── What a lead looks like when RETURNED from the API ──
class LeadResponse(BaseModel):
    id: str
    name: str
    email: str
    company: Optional[str]
    title: Optional[str]
    industry: Optional[str]
    company_size: Optional[str]
    score: float
    score_breakdown: Optional[Dict[str, Any]]
    status: LeadStatus
    is_qualified: bool
    responded: bool
    converted: bool
    deal_value: Optional[float]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True  # allows reading from SQLAlchemy model objects

# ── What a list of leads looks like ──
class LeadListResponse(BaseModel):
    leads: List[LeadResponse]
    total: int
    page: int
    page_size: int

# ── Score response ──
class ScoreResponse(BaseModel):
    lead_id: str
    score: float
    is_qualified: bool
    breakdown: Dict[str, Any]
    recommendation: str

# ── Email response ──
class EmailActivityResponse(BaseModel):
    id: str
    lead_id: str
    subject: str
    body: str
    email_type: str
    sent: bool
    opened: bool
    replied: bool
    created_at: datetime

    class Config:
        from_attributes = True