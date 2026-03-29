from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Text, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.db.session import Base

# Simple function to generate a unique ID for each lead
def gen_uuid():
    return str(uuid.uuid4())

# These are the possible stages a lead can be in
class LeadStatus(str, enum.Enum):
    ingested = "ingested"       # just came in
    scoring = "scoring"         # being scored right now
    qualified = "qualified"     # score is high enough
    disqualified = "disqualified" # score too low
    email_sent = "email_sent"   # outreach email sent
    follow_up_1 = "follow_up_1" # first follow up sent
    follow_up_2 = "follow_up_2" # second follow up sent
    converted = "converted"     # became a customer!
    lost = "lost"               # never converted

# This defines the "leads" table in PostgreSQL
class Lead(Base):
    __tablename__ = "leads"

    id = Column(String, primary_key=True, default=gen_uuid)  # unique ID
    name = Column(String(255), nullable=False)               # required
    email = Column(String(255), nullable=False, index=True)  # required, indexed for fast search
    company = Column(String(255))
    title = Column(String(255))        # job title e.g. "VP Sales"
    industry = Column(String(100))     # e.g. "SaaS"
    company_size = Column(String(50))  # e.g. "50-200"
    website = Column(String(255))
    phone = Column(String(50))
    linkedin_url = Column(String(500))
    source = Column(String(100))       # where did this lead come from? csv, api, etc.

    # ML scoring results
    score = Column(Float, default=0.0)         # 0 to 100
    score_breakdown = Column(JSON)             # detailed breakdown of why they got that score
    score_version = Column(String(20))         # which version of the model scored them

    # Pipeline tracking
    status = Column(Enum(LeadStatus), default=LeadStatus.ingested)
    is_qualified = Column(Boolean, default=False)

    # Outcome tracking
    responded = Column(Boolean, default=False)
    converted = Column(Boolean, default=False)
    deal_value = Column(Float)

    # Timestamps — set automatically
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    raw_data = Column(JSON)  # stores the original CSV row exactly as it came in

    # This connects Lead to EmailActivity (one lead can have many emails)
    emails = relationship("EmailActivity", back_populates="lead", cascade="all, delete")


# This defines the "email_activity" table
class EmailActivity(Base):
    __tablename__ = "email_activity"

    id = Column(String, primary_key=True, default=gen_uuid)
    lead_id = Column(String, ForeignKey("leads.id"), nullable=False, index=True)

    subject = Column(String(500))
    body = Column(Text)
    email_type = Column(String(50))      # outreach / follow_up_1 / follow_up_2
    sequence_number = Column(Integer, default=1)

    # Tracking
    sent = Column(Boolean, default=False)
    sent_at = Column(DateTime(timezone=True))
    opened = Column(Boolean, default=False)
    opened_at = Column(DateTime(timezone=True))
    clicked = Column(Boolean, default=False)
    replied = Column(Boolean, default=False)

    generated_by = Column(String(50))    # which AI model wrote this email
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # This connects back to the Lead
    lead = relationship("Lead", back_populates="emails")