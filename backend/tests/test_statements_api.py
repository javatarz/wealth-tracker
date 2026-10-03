import pytest
from fastapi.testclient import TestClient

from app.api import statements, uploads
from app.core.cas_parser import StatementUpload
from app.core.statement_preview import StatementParseError, StatementPreview
from app.main import app
from tests.conftest import MOCK_CAS_PASSWORD

client = TestClient(app)


@pytest.mark.unit
def test_preview_returns_parsed_statement(mock_cas_pdf: bytes) -> None:
    response = client.post(
        "/api/statements/preview",
        files={"file": ("statement.pdf", mock_cas_pdf, "application/pdf")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["parser"]["name"] == "casparser"
    assert body["statement_period"] == {"from": "01-Apr-2024", "to": "31-Mar-2025"}
    assert len(body["folios"]) == 3
    txn = body["folios"][0]["schemes"][0]["transactions"][0]
    assert txn == {
        "date": "2024-04-02",
        "description": "Purchase",
        "type": "PURCHASE",
        "amount": "-76739.54",
        "units": "1136.067",
        "nav": "67.5484",
        "balance": "1136.067",
        "dividend_rate": None,
    }
    assert body["parse_warnings"] == []


@pytest.mark.unit
def test_preview_accepts_password(encrypted_mock_cas_pdf: bytes) -> None:
    response = client.post(
        "/api/statements/preview",
        files={"file": ("statement.pdf", encrypted_mock_cas_pdf, "application/pdf")},
        data={"password": MOCK_CAS_PASSWORD},
    )

    assert response.status_code == 200


@pytest.mark.unit
def test_preview_reports_parse_errors_as_400(encrypted_mock_cas_pdf: bytes) -> None:
    response = client.post(
        "/api/statements/preview",
        files={"file": ("statement.pdf", encrypted_mock_cas_pdf, "application/pdf")},
    )

    assert response.status_code == 400
    assert response.json() == {
        "code": "password_required",
        "message": "This statement is password-protected.",
    }


@pytest.mark.unit
def test_preview_rejects_oversized_files(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(uploads, "MAX_STATEMENT_BYTES", 10)

    response = client.post(
        "/api/statements/preview",
        files={"file": ("statement.pdf", b"%PDF-" + b"0" * 10, "application/pdf")},
    )

    assert response.status_code == 413
    assert response.json()["code"] == "file_too_large"


@pytest.mark.unit
def test_preview_requires_a_file() -> None:
    response = client.post("/api/statements/preview")

    assert response.status_code == 422


@pytest.mark.unit
def test_preview_uses_the_injected_statement_reader() -> None:
    def unreadable(_upload: StatementUpload) -> StatementPreview:
        raise StatementParseError.unrecognised_statement()

    app.dependency_overrides[statements.get_statement_reader] = lambda: unreadable
    try:
        response = client.post(
            "/api/statements/preview",
            files={"file": ("statement.pdf", b"%PDF-", "application/pdf")},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["code"] == "unrecognised_statement"
