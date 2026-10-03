import io
from pathlib import Path

import pytest
from pypdf import PdfWriter

FIXTURES = Path(__file__).resolve().parents[2] / "tests" / "fixtures"
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
