from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Repo-root .env (local dev) and backend/.env (optional override).
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Industrial Engineering Copilot"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = False

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    database_url: str = "postgresql+asyncpg://iec:iec@localhost:5432/iec"
    database_url_sync: str = "postgresql+psycopg://iec:iec@localhost:5432/iec"

    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"]
    )

    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    redis_url: str = "redis://localhost:6379/0"

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "iec-documents"
    minio_secure: bool = False

    groq_api_key: str | None = None
    groq_model: str = "openai/gpt-oss-120b"
    groq_base_url: str = "https://api.groq.com/openai/v1"

    run_groq_integration_tests: bool = False

    embedding_provider: str = "deterministic"
    embedding_dimensions: int = 384


@lru_cache
def get_settings() -> Settings:
    return Settings()
