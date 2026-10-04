import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


def _env_required(name: str) -> str:
    value = os.getenv(name)
    if value is None:
        raise RuntimeError(f"Missing required environment variable '{name}'")
    return value


def _env_required_int(name: str) -> int:
    raw_value = _env_required(name)
    try:
        return int(raw_value)
    except ValueError as exc:
        raise RuntimeError(f"Environment variable '{name}' must be an integer") from exc


def _env_optional(name: str) -> str | None:
    value = os.getenv(name)
    return value if value not in (None, "") else None


def _env_optional_int(name: str, default: int) -> int:
    raw_value = _env_optional(name)
    if raw_value is None:
        return default
    try:
        return int(raw_value)
    except ValueError as exc:
        raise RuntimeError(f"Environment variable '{name}' must be an integer") from exc


@dataclass(frozen=True)
class Settings:
    app_name: str = field(default_factory=lambda: _env_required("APP_NAME"))
    environment: str = field(default_factory=lambda: _env_required("ENVIRONMENT"))
    api_v1_prefix: str = field(default_factory=lambda: _env_required("API_V1_PREFIX"))
    database_url: str = field(default_factory=lambda: _env_required("DATABASE_URL"))
    postgres_server: str = field(
        default_factory=lambda: _env_required("POSTGRES_SERVER")
    )
    postgres_port: int = field(
        default_factory=lambda: _env_required_int("POSTGRES_PORT")
    )
    postgres_db: str = field(default_factory=lambda: _env_required("POSTGRES_DB"))
    postgres_user: str = field(default_factory=lambda: _env_required("POSTGRES_USER"))
    postgres_password: str = field(
        default_factory=lambda: _env_required("POSTGRES_PASSWORD")
    )
    redis_url: str = field(default_factory=lambda: _env_required("REDIS_URL"))
    secret_key: str = field(default_factory=lambda: _env_required("SECRET_KEY"))
    access_token_expire_minutes: int = field(
        default_factory=lambda: _env_required_int("ACCESS_TOKEN_EXPIRE_MINUTES")
    )
    jwt_algorithm: str = field(default_factory=lambda: _env_required("JWT_ALGORITHM"))
    email_from: str = field(default_factory=lambda: _env_required("EMAIL_FROM"))
    smtp_host: str = field(default_factory=lambda: _env_required("SMTP_HOST"))
    smtp_port: int = field(default_factory=lambda: _env_required_int("SMTP_PORT"))
    smtp_user: str | None = field(default_factory=lambda: _env_optional("SMTP_USER"))
    smtp_password: str | None = field(
        default_factory=lambda: _env_optional("SMTP_PASSWORD")
    )
    log_level: str = field(default_factory=lambda: _env_optional("LOG_LEVEL") or "INFO")

    # AI/LLM Settings (OpenAI)
    openai_api_key: str = field(default_factory=lambda: _env_required("OPENAI_API_KEY"))
    openai_text_model: str = field(
        default_factory=lambda: _env_optional("OPENAI_TEXT_MODEL") or "gpt-6-luna"
    )
    openai_reasoning_effort: str | None = field(
        default_factory=lambda: _env_optional("OPENAI_REASONING_EFFORT")
    )
    openai_image_model: str = field(
        default_factory=lambda: _env_optional("OPENAI_IMAGE_MODEL") or "gpt-image-2.5-flare"
    )
    openai_image_quality: str = field(
        default_factory=lambda: _env_optional("OPENAI_IMAGE_QUALITY") or "medium"
    )
    openai_image_concurrency: int = field(
        default_factory=lambda: _env_optional_int("OPENAI_IMAGE_CONCURRENCY", 4)
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_async_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql+psycopg2"):
        return database_url.replace("psycopg2", "asyncpg", 1)
    return database_url
