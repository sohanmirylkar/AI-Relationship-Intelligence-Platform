from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Indago AI Relationship Intelligence Platform"
    environment: str = "local"
    api_prefix: str = "/api/v1"
    data_dir: Path = Path("data")
    upload_dir: Path = Path("data/uploads")
    export_dir: Path = Path("data/exports")
    jwt_secret_key: str = "change-me-for-production"
    access_token_expire_minutes: int = 8 * 60
    default_llm_provider: str = "anthropic"
    default_extraction_model: str = "claude-haiku-4-5"
    default_synthesis_model: str = "claude-sonnet-4-6"
    openai_api_key: str | None = None
    openai_model: str = "gpt-5.5"
    openai_base_url: str = "https://api.openai.com/v1"
    anthropic_api_key: str | None = None
    anthropic_version: str = "2023-06-01"
    anthropic_base_url: str = "https://api.anthropic.com/v1"
    supabase_url: str | None = None
    supabase_service_role_key: str | None = None
    supabase_crm_table: str = "crm_exports"
    cors_origins: list[str] = ["http://localhost:8501", "http://127.0.0.1:8501"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.export_dir.mkdir(parents=True, exist_ok=True)
    return settings
