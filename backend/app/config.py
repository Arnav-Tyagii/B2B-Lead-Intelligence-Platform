"""Application configuration.

All config comes from environment variables (or a local `.env`) via
pydantic-settings — there are NO secrets in code. `get_settings()` is cached so
the .env is parsed once and the same Settings object is reused everywhere
(routers, services, the Mongo client), which keeps behavior consistent and cheap.
"""

from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # tolerate unrelated env vars (e.g. Render system vars)
    )

    # ── MongoDB ──
    mongodb_uri: str = Field(
        default="mongodb://localhost:27017",
        description="MongoDB Atlas connection string.",
    )
    mongodb_db_name: str = Field(default="lead_intelligence")

    # ── Gemini ── (optional: blank key => deterministic fallback enricher)
    gemini_api_key: str = Field(default="")
    gemini_model: str = Field(default="gemini-2.5-flash-lite")

    # ── CORS ── locked to the frontend origin(s); comma-separated in env.
    # NoDecode: stop pydantic-settings from JSON-parsing the env value so our
    # validator below can split a plain "a,b,c" string instead.
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:3000"]
    )

    # ── Pagination guardrails (free-tier: never return the whole collection) ──
    page_size_default: int = Field(default=20)
    page_size_max: int = Field(default=100)

    # ── Observability ──
    log_level: str = Field(default="INFO")
    environment: str = Field(default="development")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors(cls, value: object) -> object:
        # Env vars arrive as a single string; allow "a,b,c" → ["a","b","c"].
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def gemini_enabled(self) -> bool:
        """True only when a key is configured. Services consult this before
        attempting a live call so a missing key degrades gracefully."""
        return bool(self.gemini_api_key.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
