import io
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from pypdf import PdfWriter
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core import config, database
from app.main import app

FIXTURES = Path(__file__).resolve().parents[2] / "tests" / "fixtures"
ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"
MOCK_CAS_PASSWORD = "ABCDE1234F"  # noqa: S105  # synthetic PAN printed in the mock PDF


@pytest.fixture
def mock_cas_pdf() -> bytes:
    return (FIXTURES / "mock_cams_cas.pdf").read_bytes()


@pytest.fixture
def encrypted_mock_cas_pdf() -> bytes:
    writer = PdfWriter(clone_from=FIXTURES / "mock_cams_cas.pdf")
    writer.encrypt(MOCK_CAS_PASSWORD, algorithm="RC4-128")
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


@pytest.fixture
def blank_pdf() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


@pytest.fixture
def migrated_engine(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Engine]:
    """A fresh SQLite file brought to head by the real Alembic migrations."""
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    config.get_settings.cache_clear()
    database.get_engine.cache_clear()
    database.get_sessionmaker.cache_clear()
    command.upgrade(Config(ALEMBIC_INI), "head")
    yield database.get_engine()
    database.get_engine().dispose()
    config.get_settings.cache_clear()
    database.get_engine.cache_clear()
    database.get_sessionmaker.cache_clear()


@pytest.fixture
def db(migrated_engine: Engine) -> Iterator[Session]:
    with sessionmaker(bind=migrated_engine)() as session:
        yield session


@pytest.fixture
def client(migrated_engine: Engine) -> TestClient:
    del migrated_engine  # requested only so the app's sessions open the migrated file
    return TestClient(app)
