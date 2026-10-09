from collections.abc import Iterator
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.statements import get_statement_reader
from app.core.cas_parser import StatementUpload, parse_cas_pdf
from app.core.statement_preview import StatementPreview
from app.ledger import statement_commit
from app.ledger.models import (
    Account,
    HouseholdMember,
    Import,
    Instrument,
    Lot,
    Position,
    Transaction,
)
from app.main import app

LEDGER_MODELS = (HouseholdMember, Account, Instrument, Import, Position, Transaction, Lot)

# Units are the statement's printed closing balances; cost basis is FIFO over the
# fixture's purchases and redemptions, worked out independently of the code.
EXPECTED_POSITIONS = [
    ("HDFC Mutual Fund", "1234567890", "1830.270", "129871.58"),
    ("ICICI Prudential Mutual Fund", "1234567890", "3260.204", "156266.13"),
    ("SBI Mutual Fund", "9876543210", "564.781", "45135.00"),
]


def commit(client: TestClient, pdf: bytes) -> dict[str, object]:
    response = client.post("/api/imports", files={"file": ("cas.pdf", pdf, "application/pdf")})
    return {"status": response.status_code, **response.json()}


def count(db: Session, model: type[object]) -> int:
    return len(db.scalars(select(model)).all())


def reading_every_upload_as(preview: StatementPreview) -> Iterator[StatementPreview]:
    app.dependency_overrides[get_statement_reader] = lambda: lambda _upload: preview
    yield preview
    app.dependency_overrides.clear()


@pytest.fixture
def mock_statement(mock_cas_pdf: bytes) -> StatementPreview:
    return parse_cas_pdf(StatementUpload(mock_cas_pdf, ""))


@pytest.fixture
def reads_as_mock_statement(mock_statement: StatementPreview) -> Iterator[StatementPreview]:
    yield from reading_every_upload_as(mock_statement)


@pytest.fixture
def reads_with_opening_balance(mock_statement: StatementPreview) -> Iterator[StatementPreview]:
    folio = mock_statement.folios[0]
    scheme = folio.schemes[0].model_copy(update={"open": Decimal("100.000")})
    held_before = folio.model_copy(update={"schemes": [scheme]})
    yield from reading_every_upload_as(mock_statement.model_copy(update={"folios": [held_before]}))


@pytest.fixture
def failing_writer(monkeypatch: pytest.MonkeyPatch) -> None:
    def explode(*_args: object) -> None:
        raise SQLAlchemyError("disk full")

    monkeypatch.setattr(statement_commit.StatementWriter, "_write_row", explode)


def test_commit_records_the_statement_in_the_ledger(
    client: TestClient, db: Session, mock_cas_pdf: bytes
) -> None:
    receipt = commit(client, mock_cas_pdf)

    assert receipt["status"] == 201
    assert (receipt["positions"], receipt["transactions"]) == (3, 21)
    assert [count(db, model) for model in (HouseholdMember, Account, Instrument, Position)] == [
        1,
        3,
        3,
        3,
    ]
    assert count(db, Import) == 1


def test_positions_show_units_and_fifo_cost_basis(client: TestClient, mock_cas_pdf: bytes) -> None:
    commit(client, mock_cas_pdf)

    positions = client.get("/api/positions").json()

    assert [
        (p["institution"], p["folio"], p["units"], p["cost_basis"]) for p in positions
    ] == EXPECTED_POSITIONS
    assert positions[0]["scheme"] == "HDFC Top 200 Fund - Direct Plan - Growth"


def test_positions_are_empty_before_any_import(client: TestClient) -> None:
    assert client.get("/api/positions").json() == []


def test_reimporting_the_same_pdf_is_rejected(
    client: TestClient, db: Session, mock_cas_pdf: bytes
) -> None:
    commit(client, mock_cas_pdf)

    second = commit(client, mock_cas_pdf)

    assert second["status"] == 409
    assert second["code"] == "already_imported"
    assert (count(db, Import), count(db, Transaction)) == (1, 21)


@pytest.mark.usefixtures("reads_as_mock_statement")
def test_overlapping_statement_skips_transactions_already_in_the_ledger(
    client: TestClient, db: Session, mock_cas_pdf: bytes
) -> None:
    commit(client, mock_cas_pdf)

    overlapping = commit(client, mock_cas_pdf + b"\n% a different file, the same rows")

    assert (overlapping["status"], overlapping["transactions"]) == (201, 0)
    assert (count(db, Import), count(db, Transaction), count(db, Lot)) == (2, 21, 12)


@pytest.mark.usefixtures("failing_writer")
def test_failed_commit_leaves_nothing_behind(
    client: TestClient, db: Session, mock_cas_pdf: bytes
) -> None:
    receipt = commit(client, mock_cas_pdf)

    assert (receipt["status"], receipt["code"]) == (500, "commit_failed")
    assert [count(db, model) for model in LEDGER_MODELS] == [0] * len(LEDGER_MODELS)


@pytest.mark.usefixtures("reads_with_opening_balance")
def test_first_import_seeds_an_opening_balance(client: TestClient, db: Session) -> None:
    commit(client, b"%PDF- any statement")

    opening = db.scalars(select(Transaction).where(Transaction.synthetic)).one()
    assert (opening.kind, opening.units, str(opening.date)) == (
        "OPENING_BALANCE",
        Decimal("100.000"),
        "2024-04-01",
    )
    assert opening.fingerprint is None
