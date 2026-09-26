"""Shared test fixtures and configuration."""

from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest


@pytest.fixture(autouse=True)
def _clean_env() -> None:
    """Ensure no settings leak between tests."""
    from app.core.config import get_settings

    get_settings.cache_clear()
    for key in ("WEALTH_TRACKER__DB_PASSWORD", "WEALTH_TRACKER__DATA_DIR"):
        os.environ.pop(key, None)
    yield
    get_settings.cache_clear()
    for key in ("WEALTH_TRACKER__DB_PASSWORD", "WEALTH_TRACKER__DATA_DIR"):
        os.environ.pop(key, None)


@pytest.fixture
def tmp_data_dir() -> Path:
    """Create a unique temporary DATA_DIR and return its Path."""
    with TemporaryDirectory() as td:
        yield Path(td)
