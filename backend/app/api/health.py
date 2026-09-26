"""Health-check endpoint."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from app import __version__

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):  # type: ignore[explicit-any]  # pydantic BaseModel internals
    """Response shape for GET /health."""

    model_config = ConfigDict(strict=True)

    status: Literal["ok"]
    version: str
    schema_revision: str | None = None


@router.get("/health", response_model=HealthResponse)  # type: ignore[misc]
def health() -> HealthResponse:
    """Return a health-check response.

    ``schema_revision`` is ``None`` here — reading ``alembic_version``
    is ADR 0025's health work, not the scaffold's.
    """
    return HealthResponse(status="ok", version=__version__)
