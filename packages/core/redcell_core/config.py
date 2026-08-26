from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# repo-root .env (three levels up), loaded whatever dir a process starts in
_ROOT_ENV = Path(__file__).resolve().parents[3] / ".env"

_DEV_ADMIN_PASSWORD = "admin"
_DEV_SECRETS_DIR = _ROOT_ENV.parent / ".redcell-dev-secrets"


def _read_file(path: str | None) -> str:
    if not path:
        return ""
    try:
        return Path(path).read_text().strip()
    except OSError:
        return ""


def _gen_fernet() -> str:
    from cryptography.fernet import Fernet
    return Fernet.generate_key().decode()


def _gen_token() -> str:
    import secrets
    return secrets.token_urlsafe(48)


def _dev_secret(name: str, generator) -> str:
    try:
        _DEV_SECRETS_DIR.mkdir(parents=True, exist_ok=True)
        f = _DEV_SECRETS_DIR / name
        existing = f.read_text().strip() if f.exists() else ""
        if existing:
            return existing
        value = generator()
        f.write_text(value)
        return value
    except OSError:
        return generator()


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
    llm_num_retries: int = 2
    llm_timeout_seconds: float = 120.0
    rate_limit_enabled: bool = True
    worker_max_jobs: int = 10

    admin_username: str = "admin"
    admin_password: str = ""
    admin_password_file: str | None = None
    jwt_secret: str = ""
    jwt_secret_file: str | None = None
    jwt_ttl_hours: int = 168
    # Fernet key (urlsafe base64, 32 bytes). Override in production.
    secret_key: str = ""
    secret_key_file: str | None = None
    cookie_secure: bool | None = None

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
    def secure_cookies(self) -> bool:
        return self.cookie_secure if self.cookie_secure is not None else self.env != "dev"

    @model_validator(mode="after")
    def _resolve_secrets(self) -> "Settings":
        self.secret_key = self.secret_key.strip()
        self.jwt_secret = self.jwt_secret.strip()
        self.admin_password = self.admin_password.strip()
        if not self.secret_key:
            self.secret_key = _read_file(self.secret_key_file) or (
                _dev_secret("secret_key", _gen_fernet) if self.env == "dev" else "")
        if not self.jwt_secret:
            self.jwt_secret = _read_file(self.jwt_secret_file) or (
                _dev_secret("jwt_secret", _gen_token) if self.env == "dev" else "")
        if not self.admin_password:
            self.admin_password = _read_file(self.admin_password_file) or (
                _DEV_ADMIN_PASSWORD if self.env == "dev" else "")
        if self.env != "dev":
            insecure = [name for name, ok in (
                ("REDCELL_SECRET_KEY", bool(self.secret_key)),
                ("REDCELL_JWT_SECRET", bool(self.jwt_secret)),
                ("REDCELL_ADMIN_PASSWORD", self.admin_password not in ("", _DEV_ADMIN_PASSWORD)),
            ) if not ok]
            if insecure:
                raise ValueError(
                    f"env={self.env!r} requires real values (not the dev defaults) for: "
                    f"{', '.join(insecure)}")
        return self

    @property
    def origins(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def public_base_url(self) -> str:
        return self.s3_public_base_url or f"{self.s3_endpoint}/{self.bucket_public}"


settings = Settings()
