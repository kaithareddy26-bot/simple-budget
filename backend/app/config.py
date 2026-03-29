from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration settings."""

    # Application
    APP_NAME: str = "Budgeting Application"
    APP_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql://postgres:budget_pass@db:5432/budget_db"

    # Set to True to initialize DB tables on startup (DEV ONLY)
    RUN_DB_INIT: bool = True

    # Security
    # Development fallback exists; override in .env for all non-local deployments
    # Generate with: python -c "import secrets; print(secrets.token_hex(32))"
    SECRET_KEY: str = "dev-only-secret-change-before-any-deployment"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Rate limiting (all configurable via .env)
    LOGIN_RATE_LIMIT: str = "5/minute"
    REGISTER_RATE_LIMIT: str = "3/minute"
    GLOBAL_RATE_LIMIT: str = "60/minute"
    REPORT_RATE_LIMIT: str = "10/minute"
    LOGIN_LOCKOUT_MAX_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_WINDOW_MINUTES: int = 15

    # CORS
    ALLOWED_ORIGINS: list = [
        "http://localhost:3000",
        "http://frontend:3000",
        "http://localhost:8081",
    ]

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()