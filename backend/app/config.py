from typing import Optional

from pydantic_settings import BaseSettings


def fix_database_url(url: str, async_suffix: str = "+asyncpg") -> str:
    """Heroku gives postgres:// but asyncpg needs postgresql+asyncpg://"""
    if url.startswith("postgres://"):
        url = url.replace("postgres://", f"postgresql{async_suffix}://", 1)
    elif url.startswith("postgresql://") and async_suffix:
        url = url.replace("postgresql://", f"postgresql{async_suffix}://", 1)
    return url


class Settings(BaseSettings):
    APP_NAME: str = "AI Lorekeeper"
    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/lorekeeper"
    )
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@localhost:5432/lorekeeper"

    # Supabase Auth
    SUPABASE_URL: str = ""
    SUPABASE_JWT_SECRET: str = ""

    # Google AI / Gemini API (Gemma 4 inference)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemma-4-31b-it"
    GEMINI_API_URL: str = "https://generativelanguage.googleapis.com/v1beta/models"

    # Files
    UPLOAD_DIR: str = "uploaded_files"
    MAX_UPLOAD_SIZE_MB: int = 50
    MAX_TEXT_CHARS_PER_BATCH: int = 100_000

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,https://lorekeeper.vercel.app"

    class Config:
        env_file = ".env"


settings = Settings()

# Auto-fix DATABASE_URL for Heroku's postgres:// format
settings.DATABASE_URL = fix_database_url(settings.DATABASE_URL)
settings.DATABASE_URL_SYNC = fix_database_url(
    settings.DATABASE_URL_SYNC, async_suffix=""
)
