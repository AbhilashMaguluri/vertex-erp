import json
import sys
from pathlib import Path
from typing import List, Optional, Union

from pydantic import Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Always resolve to apps/backend/.env regardless of the process's working
# directory — a relative "./.env" would silently miss the file (and fall
# back to defaults) if the app is launched from anywhere else.
ENV_FILE_PATH = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    PROJECT_NAME: str = "Student Counselling Management System"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    API_V1_STR: str = "/api/v1"

    # Database — no default. A missing/blank value must fail startup loudly
    # rather than silently connecting to some placeholder local database.
    DATABASE_URL: str = Field(...)

    # JWT — no default. A missing secret must fail startup loudly rather
    # than silently signing tokens with a well-known placeholder value.
    JWT_SECRET_KEY: str = Field(...)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    # Default session length (no "remember me")
    REFRESH_TOKEN_EXPIRE_DAYS: int = 1
    # Session length when the user checks "Remember me"
    REMEMBER_ME_REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30

    # Cookies (refresh token transport)
    COOKIE_SECURE: bool = False  # overridden to True automatically outside development
    COOKIE_SAMESITE: str = "lax"
    COOKIE_DOMAIN: Union[str, None] = None

    @field_validator("COOKIE_SECURE", mode="after")
    @classmethod
    def force_secure_outside_dev(cls, v: bool, info) -> bool:
        env = info.data.get("ENVIRONMENT", "development")
        if env != "development":
            return True
        return v

    # Bootstrap Admin (used only by `python -m app.scripts.seed`, never by the app at runtime)
    INITIAL_ADMIN_EMAIL: str = "admin@scms.local"
    INITIAL_ADMIN_PASSWORD: str = "ChangeMe123!"
    INITIAL_ADMIN_FIRST_NAME: str = "System"
    INITIAL_ADMIN_LAST_NAME: str = "Administrator"

    # CORS — kept as a raw string, not List[str]: pydantic-settings treats
    # list-typed fields as JSON and tries to json.loads() the env value
    # *before* any field_validator runs, which breaks on a plain
    # comma-separated value like "http://a,http://b". Parsed on access below.
    BACKEND_CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"

    @property
    def cors_origins(self) -> List[str]:
        raw = self.BACKEND_CORS_ORIGINS.strip()
        if raw.startswith("["):
            return json.loads(raw)
        return [origin.strip() for origin in raw.split(",") if origin.strip()]

    # Storage — Cloudinary (no local file storage)
    MAX_FILE_SIZE_MB: int = 10
    CLOUDINARY_CLOUD_NAME: str = Field(...)
    CLOUDINARY_API_KEY: str = Field(...)
    CLOUDINARY_API_SECRET: str = Field(...)

    # Email — Resend
    RESEND_API_KEY: str = Field(...)
    EMAIL_FROM: str = Field(...)

    # Vertex AI
    GROQ_API_KEY: str = ""
    LLM_PROVIDER: str = "groq"
    LLM_MODEL: str = "llama-3.1-8b-instant"


def _load_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as exc:
        missing = [str(err["loc"][0]) for err in exc.errors() if err["type"] == "missing"]
        lines = [
            "",
            "=" * 70,
            "SCMS backend configuration is incomplete.",
            f"Expected an .env file at: {ENV_FILE_PATH}",
        ]
        if missing:
            lines.append(f"Missing required variable(s): {', '.join(missing)}")
        lines += [
            "Copy apps/backend/.env.example to apps/backend/.env and fill in",
            "the required values (DATABASE_URL, JWT_SECRET_KEY, CLOUDINARY_*,",
            "RESEND_API_KEY, EMAIL_FROM) before starting the backend.",
            "=" * 70,
            "",
        ]
        sys.stderr.write("\n".join(lines))
        raise SystemExit(1) from exc


settings = _load_settings()
