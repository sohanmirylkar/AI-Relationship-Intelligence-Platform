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
    default_llm_provider: str = "local"
    default_extraction_model: str = "claude-haiku-4-5"
    default_synthesis_model: str = "claude-sonnet-4-6"
    dealcloud_base_url: str | None = None
    dealcloud_client_id: str | None = None
    dealcloud_client_secret: str | None = None
    cors_origins: list[str] = ["http://localhost:8501", "http://127.0.0.1:8501"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.export_dir.mkdir(parents=True, exist_ok=True)
    return settings
