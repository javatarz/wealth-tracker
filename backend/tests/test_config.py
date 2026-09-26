"""Tests for application Settings."""

from __future__ import annotations

import os

from app.core.config import Settings


def test_defaults() -> None:
    s = Settings()
    assert s.port == 8000
    assert s.log_level == "info"
    assert s.cors_origins == ["http://localhost:5173"]
    assert s.db_password is None


def test_db_password_override() -> None:
    os.environ["WEALTH_TRACKER__DB_PASSWORD"] = "secret"
    try:
        s = Settings()
        assert s.db_password == "secret"
    finally:
        del os.environ["WEALTH_TRACKER__DB_PASSWORD"]


def test_db_password_empty_string_is_none() -> None:
    os.environ["WEALTH_TRACKER__DB_PASSWORD"] = ""
    try:
        s = Settings()
        assert s.db_password is None
    finally:
        del os.environ["WEALTH_TRACKER__DB_PASSWORD"]


def test_database_url_shape(tmp_path) -> None:  # type: ignore[no-untyped-def]
    s = Settings(data_dir=tmp_path)
    url = s.database_url
    assert url.startswith("sqlite:///")
    assert str(tmp_path.resolve()) in url
    assert url.endswith("/wealth.db")
