from decimal import Decimal
from typing import cast

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ledger.models import Transaction

Json = dict[str, object]


def commit(client: TestClient, pdf: bytes) -> None:
    response = client.post("/api/imports", files={"file": ("cas.pdf", pdf, "application/pdf")})
    assert response.status_code == 201


def first_position(client: TestClient) -> Json:
    return cast("list[Json]", client.get("/api/positions").json())[0]


def add(client: TestClient, position_id: str, **fields: object) -> Json:
    body: Json = {
        "type": "purchase",
        "date": "2026-09-01",
        "units": "100.000",
        "amount": "10000.00",
    }
    body.update(fields)
    response = client.post(f"/api/positions/{position_id}/transactions", json=body)
    return {"status": response.status_code, **cast(Json, response.json())}


def entries_of(detail: Json) -> list[Json]:
    return cast("list[Json]", detail["transactions"])


def fixture_position(client: TestClient, mock_cas_pdf: bytes) -> Json:
    commit(client, mock_cas_pdf)
    return first_position(client)


def test_manual_transaction_updates_units_and_cost_basis(
    client: TestClient, db: Session, mock_cas_pdf: bytes
) -> None:
    position = fixture_position(client, mock_cas_pdf)
    before_units = Decimal(str(position["units"]))
    before_cost = Decimal(str(position["cost_basis"]))

    detail = add(client, str(position["id"]))

    assert detail["status"] == 201
    assert Decimal(str(detail["units"])) == before_units + Decimal("100.000")
    assert Decimal(str(detail["cost_basis"])) == before_cost + Decimal("10000.00")
    manual = db.scalars(
        select(Transaction).where(Transaction.import_id.is_(None), Transaction.synthetic.is_(False))
    ).all()
    assert [entry.kind for entry in manual] == ["PURCHASE"]
    assert [entry.notes for entry in manual] == [None]


def test_manual_transaction_keeps_its_notes(client: TestClient, mock_cas_pdf: bytes) -> None:
    position = fixture_position(client, mock_cas_pdf)

    detail = add(client, str(position["id"]), notes="top-up from savings")

    assert entries_of(detail)[-1]["notes"] == "top-up from savings"


def test_second_manual_transaction_stacks_on_the_first(
    client: TestClient, mock_cas_pdf: bytes
) -> None:
    position = fixture_position(client, mock_cas_pdf)
    add(client, str(position["id"]), units="100.000", amount="10000.00")

    second = add(client, str(position["id"]), units="50.000", amount="6000.00")

    baseline = Decimal(str(position["units"]))
    assert Decimal(str(second["units"])) == baseline + Decimal("150.000")
    assert Decimal(str(second["cost_basis"])) == Decimal(str(position["cost_basis"])) + Decimal(
        "16000.00"
    )


def test_manual_redemption_reduces_units(client: TestClient, mock_cas_pdf: bytes) -> None:
    position = fixture_position(client, mock_cas_pdf)

    detail = add(client, str(position["id"]), type="redemption", units="30.000")

    assert Decimal(str(detail["units"])) == Decimal(str(position["units"])) - Decimal("30.000")


def test_unexpected_type_for_the_instrument_is_rejected(
    client: TestClient, mock_cas_pdf: bytes
) -> None:
    position = fixture_position(client, mock_cas_pdf)

    rejection = add(client, str(position["id"]), type="contribution")

    assert (rejection["status"], rejection["code"]) == (400, "unexpected_type")


def test_future_date_is_rejected(client: TestClient, mock_cas_pdf: bytes) -> None:
    position = fixture_position(client, mock_cas_pdf)

    rejection = add(client, str(position["id"]), date="2999-01-01")

    assert (rejection["status"], rejection["code"]) == (400, "future_date")


def test_non_positive_units_are_rejected(client: TestClient, mock_cas_pdf: bytes) -> None:
    position = fixture_position(client, mock_cas_pdf)

    rejection = add(client, str(position["id"]), units="0")

    assert (rejection["status"], rejection["code"]) == (400, "non_positive_units")


def test_buying_without_a_cost_is_rejected(client: TestClient, mock_cas_pdf: bytes) -> None:
    position = fixture_position(client, mock_cas_pdf)

    rejection = add(client, str(position["id"]), amount=None)

    assert (rejection["status"], rejection["code"]) == (400, "cost_required")


def test_unknown_position_is_not_found(client: TestClient, mock_cas_pdf: bytes) -> None:
    fixture_position(client, mock_cas_pdf)

    rejection = add(client, "00000000-0000-0000-0000-000000000000")

    assert (rejection["status"], rejection["code"]) == (404, "position_not_found")


def test_detail_lists_the_allowed_types_for_the_instrument(
    client: TestClient, mock_cas_pdf: bytes
) -> None:
    position = fixture_position(client, mock_cas_pdf)

    detail = client.get(f"/api/positions/{position['id']}").json()

    assert detail["instrument_kind"] == "mutual_fund"
    assert detail["allowed_types"] == ["purchase", "redemption", "sip"]
