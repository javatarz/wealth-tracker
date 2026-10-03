from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

LogLevel = Literal["critical", "error", "warning", "info", "debug"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(strict=True, env_file=".env", extra="ignore")

    data_dir: Path = Path("./data")
    port: int = 8000
    log_level: LogLevel = "info"
    cors_origins: list[str] = ["http://localhost:5173"]
    static_dir: Path | None = None


@lru_cache  # type: ignore[misc]  # functools.lru_cache is typed with Any
def get_settings() -> Settings:
    return Settings()
