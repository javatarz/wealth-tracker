"""Tests for the database engine factory."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.core.database import create_engine_from_settings


def test_engine_without_password(tmp_path: Path) -> None:
    from app.core.config import Settings

    s = Settings(data_dir=tmp_path, db_password=None)
    engine = create_engine_from_settings(s)
    # Smoke: connect and execute a trivial query.
    with engine.connect() as conn:
        result = conn.exec_driver_sql("SELECT 1 AS x").scalar()
        assert result == 1
    engine.dispose()


def test_engine_with_password_raises(tmp_path: Path) -> None:
    from app.core.config import Settings

    s = Settings(data_dir=tmp_path, db_password="secret")
    with pytest.raises(RuntimeError, match="Encrypted SQLite"):
        create_engine_from_settings(s)
