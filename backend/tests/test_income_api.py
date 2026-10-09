import uuid
from decimal import Decimal
from typing import cast

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ledger.models import Account, HouseholdMember, Income, Instrument, Position, Transaction

Json = dict[str, object]


def commit(client: TestClient, pdf: bytes) -> None:
    response = client.post("/api/imports", files={"file": ("cas.pdf", pdf, "application/pdf")})
    assert response.status_code == 201


def first_position(client: TestClient) -> Json:
    return cast("list[Json]", client.get("/api/positions").json())[0]


def add_income(client: TestClient, position_id: str, **fields: object) -> Json:
    body: Json = {"type": "dividend", "date": "2026-09-01", "amount": "1000.00"}
    body.update(fields)
    response = client.post(f"/api/positions/{position_id}/income", json=body)
    return {"status": response.status_code, **cast(Json, response.json())}


def fixture_position(client: TestClient, mock_cas_pdf: bytes) -> Json:
    commit(client, mock_cas_pdf)
    return first_position(client)


def manual_transactions(db: Session) -> list[Transaction]:
    return list(
        db.scalars(
            select(Transaction).where(
                Transaction.import_id.is_(None), Transaction.synthetic.is_(False)
            )
        ).all()
    )


def make_position(db: Session, kind: str) -> uuid.UUID:
    """An empty Position of a chosen Instrument kind, for kind-specific rules."""
    member = HouseholdMember(id=uuid.uuid4(), name="Me")
    account = Account(
        id=uuid.uuid4(),
        household_member_id=member.id,
        kind=kind,
        institution="Bank",
        number="0001",
    )
    instrument = Instrument(id=uuid.uuid4(), kind=kind, identity=f"{kind}-1", name="Deposit")
    position = Position(id=uuid.uuid4(), account_id=account.id, instrument_id=instrument.id)
    db.add_all([member, account, instrument, position])
    db.commit()
    return position.id


def test_reinvested_dividend_creates_a_purchase_transaction(
    client: TestClient, db: Session, mock_cas_pdf: bytes
) -> None:
    position = fixture_position(client, mock_cas_pdf)
    before_units = Decimal(str(position["units"]))
    before_cost = Decimal(str(position["cost_basis"]))

    detail = add_income(
        client,
        str(position["id"]),
        type="dividend",
        amount="1000.00",
        tax="100.00",
        reinvested=True,
        nav="30.00",
    )

    assert detail["status"] == 201
    transactions = manual_transactions(db)
    assert [entry.kind for entry in transactions] == ["PURCHASE"]
    assert (transactions[0].units, transactions[0].amount) == (
        Decimal("30.000"),
        Decimal("900.00"),
    )
    assert transactions[0].nav == Decimal("30.00")
    assert Decimal(str(detail["units"])) == before_units + Decimal("30.000")
    assert Decimal(str(detail["cost_basis"])) == before_cost + Decimal("900.00")


def test_reinvested_dividend_appears_on_the_position(
    client: TestClient, mock_cas_pdf: bytes
) -> None:
    position = fixture_position(client, mock_cas_pdf)

    detail = add_income(
        client,
        str(position["id"]),
        amount="1000.00",
        tax="100.00",
        reinvested=True,
        nav="30.00",
    )

    events = cast("list[Json]", detail["income"])
    assert [(e["kind"], e["net_amount"], e["withdrawn"], e["units"]) for e in events] == [
        ("dividend", "900.00", False, "30.000")
    ]
    assert detail["income_total"] == "900.00"
    assert detail["cash_flow_total"] == "0"


def test_withdrawn_interest_creates_no_transaction(
    client: TestClient, db: Session, mock_cas_pdf: bytes
) -> None:
    position = fixture_position(client, mock_cas_pdf)

    detail = add_income(
        client,
        str(position["id"]),
        type="interest",
        amount="500.00",
        reinvested=False,
    )

    assert detail["status"] == 201
    assert manual_transactions(db) == []
    assert detail["cash_flow_total"] == "500.00"
    events = cast("list[Json]", detail["income"])
    assert [(e["withdrawn"], e["units"]) for e in events] == [(True, None)]


def test_income_totals_stay_apart_from_the_ledger(
    client: TestClient, db: Session, mock_cas_pdf: bytes
) -> None:
    position = fixture_position(client, mock_cas_pdf)
    before_units = Decimal(str(position["units"]))

    add_income(client, str(position["id"]), type="idcw", amount="250.00")

    assert len(db.scalars(select(Income)).all()) == 1
    assert Decimal(str(first_position(client)["units"])) == before_units


def test_unknown_income_type_is_rejected(client: TestClient, mock_cas_pdf: bytes) -> None:
    position = fixture_position(client, mock_cas_pdf)

    rejection = add_income(client, str(position["id"]), type="royalty")

    assert (rejection["status"], rejection["code"]) == (400, "unexpected_income_type")


def test_income_in_the_future_is_rejected(client: TestClient, mock_cas_pdf: bytes) -> None:
    position = fixture_position(client, mock_cas_pdf)

    rejection = add_income(client, str(position["id"]), date="2999-01-01")

    assert (rejection["status"], rejection["code"]) == (400, "future_date")


def test_non_positive_income_is_rejected(client: TestClient, mock_cas_pdf: bytes) -> None:
    position = fixture_position(client, mock_cas_pdf)

    rejection = add_income(client, str(position["id"]), amount="0")

    assert (rejection["status"], rejection["code"]) == (400, "non_positive_amount")


def test_tax_larger_than_gross_is_rejected(client: TestClient, mock_cas_pdf: bytes) -> None:
    position = fixture_position(client, mock_cas_pdf)

    rejection = add_income(client, str(position["id"]), amount="100.00", tax="150.00")

    assert (rejection["status"], rejection["code"]) == (400, "invalid_tax")


def test_reinvestment_without_nav_is_rejected(client: TestClient, mock_cas_pdf: bytes) -> None:
    position = fixture_position(client, mock_cas_pdf)

    rejection = add_income(client, str(position["id"]), reinvested=True)

    assert (rejection["status"], rejection["code"]) == (400, "nav_required")


def test_reinvestment_with_a_non_positive_nav_is_rejected(
    client: TestClient, mock_cas_pdf: bytes
) -> None:
    position = fixture_position(client, mock_cas_pdf)

    rejection = add_income(client, str(position["id"]), reinvested=True, nav="0")

    assert (rejection["status"], rejection["code"]) == (400, "nav_required")


def test_reinvestment_is_refused_for_a_position_that_cannot_hold_units(
    client: TestClient, db: Session
) -> None:
    position_id = make_position(db, "fd")

    rejection = add_income(client, str(position_id), type="interest", reinvested=True, nav="10.00")

    assert (rejection["status"], rejection["code"]) == (400, "reinvestment_not_supported")


def test_withdrawn_income_is_allowed_for_a_position_that_cannot_hold_units(
    client: TestClient, db: Session
) -> None:
    position_id = make_position(db, "fd")

    detail = add_income(client, str(position_id), type="interest", amount="750.00")

    assert detail["status"] == 201
    assert detail["cash_flow_total"] == "750.00"


def test_income_on_an_unknown_position_is_not_found(client: TestClient) -> None:
    rejection = add_income(client, "00000000-0000-0000-0000-000000000000")

    assert (rejection["status"], rejection["code"]) == (404, "position_not_found")


def test_income_list_returns_every_event_oldest_first(
    client: TestClient, mock_cas_pdf: bytes
) -> None:
    position = fixture_position(client, mock_cas_pdf)
    add_income(client, str(position["id"]), date="2026-08-01", amount="200.00")
    add_income(
        client,
        str(position["id"]),
        date="2026-07-01",
        type="interest",
        amount="100.00",
    )

    response = client.get(f"/api/positions/{position['id']}/income")

    assert response.status_code == 200
    events = cast("list[Json]", response.json())
    assert [event["date"] for event in events] == ["2026-07-01", "2026-08-01"]


def test_income_list_of_an_unknown_position_is_not_found(client: TestClient) -> None:
    response = client.get("/api/positions/00000000-0000-0000-0000-000000000000/income")

    assert (response.status_code, response.json()["code"]) == (
        404,
        "position_not_found",
    )
