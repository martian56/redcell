from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# repo-root .env (three levels up), loaded whatever dir a process starts in
_ROOT_ENV = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="REDCELL_", env_file=str(_ROOT_ENV), extra="ignore")

    env: str = "dev"
    api_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:5183"

    database_url: str = "postgresql+asyncpg://redcell:redcell@localhost:5432/redcell"
    redis_url: str = "redis://localhost:6379/0"
    run_mode: str = "live"  # live | sim (sim replays canned output, runs no tools)
    # reverse-shell callback address. listener runs on the worker host; a Docker
    # target reaches it via host.docker.internal.
    callback_host: str = "host.docker.internal"

    admin_username: str = "admin"
    admin_password: str = "admin"
    jwt_secret: str = "dev-insecure-change-me-in-production-0123456789"
    jwt_ttl_hours: int = 168
    # Fernet key (urlsafe base64, 32 bytes). Override in production.
    secret_key: str = "bRaPZZwSP-Bt9ziZ-iGjxLnQM5mlE-iOW2bMCoyUUp4="

    s3_endpoint: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_region: str = "us-east-1"
    s3_public_base_url: str | None = None
    s3_presign_endpoint: str | None = None

    # durable checkpoint store for the agent loop, survives restarts. SQLite so it
    # runs on any OS/event loop; business data stays in Postgres.
    checkpoint_db: str = str(_ROOT_ENV.parent / "redcell-checkpoints.sqlite")

    bucket_uploads: str = "uploads"
    bucket_loot: str = "loot"
    bucket_reports: str = "reports"
    bucket_public: str = "public"
    presign_ttl_seconds: int = 600

    @property
    def origins(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def public_base_url(self) -> str:
        return self.s3_public_base_url or f"{self.s3_endpoint}/{self.bucket_public}"


settings = Settings()
