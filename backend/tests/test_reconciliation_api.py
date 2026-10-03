import json
from collections.abc import Iterator
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.statements import get_statement_reader
from app.core.cas_parser import StatementUpload, parse_cas_pdf
from app.core.statement_preview import Folio, Scheme, StatementPreview
from app.ledger.models import (
    Account,
    Import,
    Position,
    ReconciliationDecision,
    Transaction,
)
from app.main import app

HDFC = "HDFC Mutual Fund|1234567890|"
SBI = "SBI Mutual Fund|9876543210|"
PDF = b"%PDF- a statement whose closing units disagree with its rows"


def commit(client: TestClient, decisions: dict[str, str] | None = None) -> dict[str, object]:
    form = {"decisions": json.dumps(decisions)} if decisions else {}
    response = client.post(
        "/api/imports", files={"file": ("cas.pdf", PDF, "application/pdf")}, data=form
    )
    return {"status": response.status_code, **response.json()}


def holding(prefix: str, statement: StatementPreview) -> str:
    """Holdings are keyed by folio plus instrument identity; the test only knows the folio."""
    scheme = next(s for f in statement.folios for s in f.schemes if f.amc in prefix)
    return prefix + (scheme.amfi or scheme.isin or f"{scheme.rta}:{scheme.rta_code}")


def shifted(folio: Folio, units: Decimal) -> Folio:
    """Prints a closing balance `units` away from what the folio's rows add up to."""
    scheme: Scheme = folio.schemes[0]
    valuation = scheme.valuation.model_copy(update={"cost": None})
    moved = scheme.model_copy(update={"close": scheme.close + units, "valuation": valuation})
    return folio.model_copy(update={"schemes": [moved]})


@pytest.fixture
def statement(mock_cas_pdf: bytes) -> Iterator[StatementPreview]:
    """HDFC prints 10 more units than its rows explain; SBI prints 5 fewer."""
    parsed = parse_cas_pdf(StatementUpload(mock_cas_pdf, ""))
    hdfc, icici, sbi = parsed.folios
    mismatched = parsed.model_copy(
        update={"folios": [shifted(hdfc, Decimal(10)), icici, shifted(sbi, Decimal(-5))]}
    )
    app.dependency_overrides[get_statement_reader] = lambda: lambda _upload: mismatched
    yield mismatched
    app.dependency_overrides.clear()


def decisions_for(statement: StatementPreview, hdfc: str, sbi: str) -> dict[str, str]:
    return {holding(HDFC, statement): hdfc, holding(SBI, statement): sbi}


def units_by_institution(client: TestClient) -> dict[str, str]:
    return {p["institution"]: p["units"] for p in client.get("/api/positions").json()}


def decision_rows(db: Session) -> list[ReconciliationDecision]:
    return list(db.scalars(select(ReconciliationDecision).order_by(ReconciliationDecision.scheme)))


def test_mismatches_come_back_for_decisions_and_nothing_is_saved(
    client: TestClient, db: Session, statement: StatementPreview
) -> None:
    outcome = commit(client)

    assert (outcome["status"], outcome["outcome"]) == (200, "needs_decisions")
    assert [
        (m["holding"], m["printed_units"], m["derived_units"], m["delta"])
        for m in outcome["mismatches"]  # type: ignore[attr-defined]
    ] == [
        (holding(HDFC, statement), "1840.270", "1830.270", "10.000"),
        (holding(SBI, statement), "559.781", "564.781", "-5.000"),
    ]
    assert db.scalars(select(Import)).all() == []


def test_commit_stays_blocked_until_every_mismatch_has_a_decision(
    client: TestClient, db: Session, statement: StatementPreview
) -> None:
    outcome = commit(client, {holding(HDFC, statement): "trust_ledger"})

    assert outcome["outcome"] == "needs_decisions"
    assert db.scalars(select(Transaction)).all() == []


def test_trusting_the_ledger_keeps_derived_units_and_records_the_decision(
    client: TestClient, db: Session, statement: StatementPreview
) -> None:
    outcome = commit(client, decisions_for(statement, "trust_ledger", "trust_ledger"))

    assert (outcome["outcome"], outcome["positions"], outcome["transactions"]) == (
        "committed",
        3,
        21,
    )
    assert units_by_institution(client)["HDFC Mutual Fund"] == "1830.270"
    hdfc = decision_rows(db)[0]
    assert (hdfc.action, hdfc.statement_units, hdfc.derived_units, hdfc.delta) == (
        "trust_ledger",
        Decimal("1840.270"),
        Decimal("1830.270"),
        Decimal("10.000"),
    )
    assert (hdfc.cost_basis, hdfc.parser_version, hdfc.position_id is not None) == (
        None,
        statement.parser.version,
        True,
    )


def test_trusting_the_statement_books_a_synthetic_adjustment_at_the_closing_nav(
    client: TestClient, db: Session, statement: StatementPreview
) -> None:
    hdfc_nav = statement.folios[0].schemes[0].valuation.nav

    commit(client, decisions_for(statement, "trust_statement", "trust_statement"))

    assert units_by_institution(client) == {
        "HDFC Mutual Fund": "1840.270",
        "ICICI Prudential Mutual Fund": "3260.204",
        "SBI Mutual Fund": "559.781",
    }
    adjustments = db.scalars(
        select(Transaction).where(Transaction.kind == "RECONCILIATION_ADJUSTMENT")
    ).all()
    assert sorted((a.units, str(a.date), a.synthetic) for a in adjustments) == [
        (Decimal("-5.000"), "2025-03-31", True),
        (Decimal("10.000"), "2025-03-31", True),
    ]
    hdfc, sbi = decision_rows(db)
    assert (hdfc.cost_basis, sbi.cost_basis) == ((10 * hdfc_nav).quantize(Decimal("0.01")), None)


def test_leaving_a_scheme_out_skips_its_rows_and_its_sole_account(
    client: TestClient, db: Session, statement: StatementPreview
) -> None:
    outcome = commit(client, decisions_for(statement, "trust_ledger", "leave_out"))

    assert (outcome["positions"], outcome["transactions"]) == (2, 14)
    assert "SBI Mutual Fund" not in units_by_institution(client)
    assert [a.institution for a in db.scalars(select(Account))] == [
        "HDFC Mutual Fund",
        "ICICI Prudential Mutual Fund",
    ]
    sbi = decision_rows(db)[1]
    assert (sbi.action, sbi.position_id) == ("leave_out", None)


def test_reimporting_the_same_pdf_revisits_mismatches_it_left_unresolved(
    client: TestClient, db: Session, statement: StatementPreview
) -> None:
    commit(client, decisions_for(statement, "trust_ledger", "leave_out"))

    revisit = commit(client)
    settled = commit(client, decisions_for(statement, "trust_statement", "trust_ledger"))

    assert [m["holding"] for m in revisit["mismatches"]] == [  # type: ignore[attr-defined]
        holding(HDFC, statement),
        holding(SBI, statement),
    ]
    assert (settled["outcome"], settled["positions"]) == ("committed", 3)
    assert len(db.scalars(select(Import)).all()) == 1
    assert len(decision_rows(db)) == 4
    assert units_by_institution(client)["HDFC Mutual Fund"] == "1840.270"
    assert len(db.scalars(select(Position)).all()) == 3


def test_a_fully_reconciled_reimport_is_still_rejected(
    client: TestClient, statement: StatementPreview
) -> None:
    commit(client, decisions_for(statement, "trust_statement", "trust_statement"))

    again = commit(client)

    assert (again["status"], again["code"]) == (409, "already_imported")


@pytest.mark.usefixtures("statement")
def test_an_unknown_action_is_refused(client: TestClient) -> None:
    assert commit(client, {"anything": "split_the_difference"})["status"] == 422
