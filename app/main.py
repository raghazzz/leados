from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.routes import leads, scoring, emails, health
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="LeadOS API",
    description="AI Sales Lead Qualification System",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "http://10.174.4.165:5173",
    "http://10.174.4.165:8001",  
],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(leads.router, prefix="/api/v1/leads", tags=["leads"])
app.include_router(scoring.router, prefix="/api/v1/scoring", tags=["scoring"])
app.include_router(emails.router, prefix="/api/v1/emails", tags=["emails"])