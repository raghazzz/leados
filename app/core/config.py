from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # App
    APP_NAME: str = "LeadOS"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/leados"

    # Mistral AI
    MISTRAL_API_KEY: str = "tAtvcBo4qbr02xzenE84NxuUZ5rqQSBX"
    MISTRAL_MODEL: str = "mistral-small-latest"

    # Lead scoring
    SCORE_THRESHOLD: float = 60.0

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    # n8n
    N8N_WEBHOOK_URL: str = ""

    class Config:
        env_file = "/Users/raghavmalhotra/Desktop/leados/app/.env"
        env_file_encoding = "utf-8"


settings = Settings()