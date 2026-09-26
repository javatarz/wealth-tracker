"""Application settings loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Wealth Tracker configuration loaded from env / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="WEALTH_TRACKER__",
    )

    data_dir: Path = Field(default=Path("./data"))
    port: int = Field(default=8000)
    log_level: str = Field(default="info")
    cors_origins: list[str] = Field(default=["http://localhost:5173"])
    db_password: str | None = Field(default=None)

    @field_validator("db_password", mode="before")
    @classmethod
    def _coerce_empty_to_none(cls, v: object) -> str | None:
        if isinstance(v, str) and v == "":
            return None
        if v is None:
            return None
        return str(v)

    @property
    def database_url(self) -> str:
        """SQLite database URL pointing into data_dir."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{self.data_dir.resolve()}/wealth.db"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance so tests can override via env.

    Use ``dependency_overrides`` or monkeypatch env vars in tests rather
    than constructing multiple instances.
    """
    return Settings()