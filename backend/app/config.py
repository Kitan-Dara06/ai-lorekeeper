from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "AI Lorekeeper"
    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/lorekeeper"
    )
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@localhost:5432/lorekeeper"

    # Supabase Auth
    SUPABASE_URL: str = ""
    SUPABASE_JWT_SECRET: str = ""

    # OpenRouter (Gemma 4 inference)
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "google/gemma-4-31b-it:free"
    OPENROUTER_API_URL: str = "https://openrouter.ai/api/v1/chat/completions"

    # Files
    UPLOAD_DIR: str = "uploaded_files"
    MAX_UPLOAD_SIZE_MB: int = 50
    MAX_TEXT_CHARS_PER_BATCH: int = 100_000

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
