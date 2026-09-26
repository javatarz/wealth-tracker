"""Database engine factory and session dependency."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import Settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models. No mapped classes yet."""


def create_engine_from_settings(settings: Settings) -> Engine:
    """Return a SQLAlchemy Engine for *settings*.

    Raises RuntimeError if a db_password is set — encrypted SQLite
    (ADR 0019) is not implemented yet.
    """
    if settings.db_password:
        raise RuntimeError("Encrypted SQLite (ADR 0019) is not implemented yet")
    return create_engine(settings.database_url, future=True)


_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def _init_db() -> None:
    """Lazily initialise the module-level engine and session factory."""
    global _engine, _SessionLocal  # noqa: PLW0603
    if _engine is None:
        settings = get_settings()
        _engine = create_engine_from_settings(settings)
        _SessionLocal = sessionmaker(bind=_engine)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a per-request SQLAlchemy Session."""
    _init_db()
    assert _SessionLocal is not None
    session = _SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_settings() -> Settings:
    """Re-export so dependants only import from database."""
    from app.core.config import get_settings as _get_settings

    return _get_settings()