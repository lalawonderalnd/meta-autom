"""Application configuration via pydantic-settings."""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/accfarm"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Auth
    ORCHESTRATOR_API_KEY: str = "dev-api-key-change-in-prod"
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""

    # Telegram alerts
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_OPS_CHAT_ID: str = ""

    # Service URLs
    DEVICE_LAYER_URL: str = "http://localhost:8001"
    IG_BOT_URL: str = "http://localhost:8002"

    # App settings
    APP_NAME: str = "AccFarm Orchestrator"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
