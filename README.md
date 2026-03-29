# LeadOS — AI Sales Lead Qualification System

An AI-powered platform that automatically scores leads,
generates personalised outreach emails, and sends them
via automated workflows.

## What it does
- Ingests leads via CSV upload or manual entry
- Scores each lead 0-100 using ML (heuristic + Random Forest)
- Generates personalised sales emails using Mistral AI
- Automatically sends emails via n8n + Gmail automation
- Tracks responses and conversion outcomes

## Tech Stack
- **Frontend:** React + Vite
- **Backend:** FastAPI (Python)
- **Database:** PostgreSQL
- **ML Scoring:** Scikit-learn (Random Forest)
- **AI Emails:** Mistral AI
- **Automation:** n8n
- **Infrastructure:** Docker

## Project Structure
```
leados/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── core/config.py       # Settings
│   ├── db/session.py        # Database connection
│   ├── models/lead.py       # Database tables
│   ├── schemas/lead.py      # Data validation
│   ├── services/
│   │   ├── lead_service.py  # Business logic
│   │   └── email_service.py # AI email generation
│   ├── ml/scorer.py         # ML scoring engine
│   └── api/routes/          # API endpoints
└── frontend/
    └── src/
        ├── App.jsx           # Main dashboard
        └── api/client.js     # Backend connector
```

## Local Setup

### Requirements
- Python 3.10+
- Node.js 18+
- Docker Desktop

### Backend
```bash
# Start database
docker start leados-db

# Start backend
cd leados
PYTHONPATH=$(pwd) MISTRAL_API_KEY=your-key uvicorn app.main:app --reload --port 8001
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Automation
```bash
docker start n8n
# Open http://localhost:5678
```

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/leads/` | Create + score a lead |
| GET | `/api/v1/leads/` | List all leads |
| POST | `/api/v1/leads/upload/csv` | Bulk CSV upload |
| POST | `/api/v1/scoring/{id}` | Re-score a lead |
| POST | `/api/v1/emails/generate` | Generate AI email |
| GET | `/api/v1/health` | Health check |

## Environment Variables
```
DATABASE_URL=postgresql+asyncpg://...
MISTRAL_API_KEY=your-key
SCORE_THRESHOLD=60.0
DEBUG=true
N8N_WEBHOOK_URL=http://localhost:5678/webhook/leados-qualify
```