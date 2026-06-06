"""
Database configuration — reads settings from .env via pydantic-settings.
Supports SQLite for dev, PostgreSQL/MySQL for production.
"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str = "boutiquely-ai-super-secret-key-change-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    # SQLite default for easy local dev; set DATABASE_URL in .env for PostgreSQL
    DATABASE_URL: str = "sqlite:///./boutiquely_ai.db"

    model_config = {
        "env_file": os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
