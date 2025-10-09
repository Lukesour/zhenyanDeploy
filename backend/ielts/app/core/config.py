from pathlib import Path

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings

IELTS_PACKAGE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_DATABASE_URL = f"sqlite:///{(IELTS_PACKAGE_DIR / 'ielts_grading.db').resolve()}"


class Settings(BaseSettings):
    # Database
    database_url: str = Field(
        default=DEFAULT_DATABASE_URL,
        validation_alias=AliasChoices("IELTS_DATABASE_URL", "DATABASE_URL", "database_url"),
    )

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Google AI API
    google_api_key: str = "AIzaSyDozL4HoGVCuuu_J9VU5BPAVKJj6FVw82A"

    # AI Models
    # Updated to prioritize gemma-3-27b-it over gemini-1.5-flash
    # gemma-3-27b-it has no quota limits while gemini-1.5-flash has quota limits
    # Note: If a model name is unavailable in current provider, AI client will auto-fallback.
    primary_model: str = "gemma-3-27b-it"
    fallback_models: str = "gemini-1.5-flash,gemini-1.5-pro"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # Application
    debug: bool = True
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # API Configuration
    api_v1_str: str = "/api/v1"
    project_name: str = "IELTS Essay Grading System"

    # Base directory for data files
    @property
    def base_dir(self) -> str:
        """获取项目根目录"""
        # 从当前文件位置向上找到项目根目录
        current_file = Path(__file__)
        # backend/app/core/config.py -> backend -> 项目根目录
        return str(current_file.parent.parent.parent.parent)

    @model_validator(mode="after")
    def _normalize_database_url(self):
        """Ensure the database URL points to the local SQLite file when using the placeholder."""
        if self.database_url.startswith("postgresql://username"):
            object.__setattr__(self, "database_url", DEFAULT_DATABASE_URL)
        return self

    class Config:
        env_file = ".env"


settings = Settings()
