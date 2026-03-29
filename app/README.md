# LeadOS Backend

FastAPI + ML lead scoring engine for the LeadOS AI Sales system.

## Stack
- **FastAPI** — async REST API
- **SQLAlchemy 2.0** — async ORM
- **PostgreSQL** — primary database
- **Scikit-learn** — Random Forest lead scoring (heuristic fallback for MVP)
- **OpenAI** — personalized email generation

## Project Structure

```
app/
├── main.py                  # FastAPI app + middleware
├── core/
│   └── config.py            # Settings from .env
├── db/
│   └── session.py           # Async DB engine + get_db dep
├── models/
│   └── lead.py              # SQLAlchemy ORM models
├── schemas/
│   └── lead.py              # Pydantic request/response schemas
├── services/
│   ├── lead_service.py      # Lead CRUD + CSV ingestion
│   └── email_service.py     # OpenAI email generation
├── ml/
│   ├── scorer.py            # Heuristic + ML scoring engine
│   └── models/              # Trained .pkl model files
└── api/routes/
    ├── leads.py             # /leads endpoints
    ├── scoring.py           # /scoring endpoints
    ├── emails.py            # /emails endpoints
    └── health.py            # /health
```

## Setup

```bash
# 1. Clone and install
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Fill in DATABASE_URL and OPENAI_API_KEY

# 3. Start PostgreSQL (Docker)
docker run -d --name leados-db \
  -e POSTGRES_DB=leados \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 postgres:16

# 4. Run the API
uvicorn app.main:app --reload
```

API docs available at: http://localhost:8000/docs

## Key Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/leads/` | Create + score a single lead |
| GET | `/api/v1/leads/` | List leads (filter by status/score) |
| POST | `/api/v1/leads/upload/csv` | Bulk upload CSV |
| POST | `/api/v1/scoring/{lead_id}` | Re-score a lead |
| POST | `/api/v1/scoring/bulk` | Score multiple leads |
| POST | `/api/v1/scoring/train` | Train ML model on labeled data |
| POST | `/api/v1/emails/generate` | Generate AI email for a lead |
| GET | `/api/v1/emails/lead/{lead_id}` | Get all emails for a lead |

## Lead Scoring

**Phase 1 (MVP):** Rule-based heuristic scorer runs immediately with no training data.
Weights: Industry (30%) + Title (30%) + Company Size (20%) + Data Completeness (12%) + Email Quality (8%)

**Phase 2:** Once you have 200+ labeled leads (converted=True/False), call `POST /api/v1/scoring/train`
to train a Random Forest model. The system automatically switches to ML scoring.

## Running Tests

```bash
pytest tests/test_scorer.py -v
```
