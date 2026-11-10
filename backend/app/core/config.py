from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration for the Personal Health Assistant.
    Stateless, zero-retention in-memory architecture.
    """

    APP_NAME: str = "Personal Health Assistant"
    APP_ENV: str = "development"
    DEBUG: bool = True

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Google Gemini API
    GEMINI_API_KEY: str = ""

    # Resource Caps & Quotas
    MAX_ACTIVE_SESSIONS: int = 100
    SESSION_TTL_MINUTES: int = 30
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB
    MAX_PAGES_PER_DOCUMENT: int = 10
    MAX_DOCUMENTS_PER_SESSION: int = 3

    # Security & Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 30
    COOKIE_NAME: str = "session_token"
    COOKIE_SECURE: bool = False  # Set to True in HTTPS production

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()