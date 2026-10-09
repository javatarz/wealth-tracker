import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.ledger.members import default_member
from app.ledger.models import Account, Instrument, Position, Transaction

NEW_CAR = {
    "name": "New Car",
    "target_amount": "2000.00",
    "target_date": "2027-01-01",
}
ZERO = Decimal(0)


@dataclass(frozen=True)
class Holding:
    units: str
    navs: Sequence[tuple[str, str]]
    institution: str = "HDFC Mutual Fund"


def seed_holding(session: Session, holding: Holding) -> Account:
    """An Account with one mutual-fund Position whose Transactions price it."""
    account, position = _open_account(session, holding.institution)
    transactions = [
        Transaction(
            id=uuid.uuid4(),
            position_id=position.id,
            date=date.fromisoformat(on),
            kind="PURCHASE",
            description="buy",
            units=Decimal(holding.units) if index == 0 else ZERO,
            amount=None,
            nav=Decimal(nav),
        )
        for index, (on, nav) in enumerate(holding.navs)
    ]
    session.add_all(transactions)
    session.commit()
    return account


def _open_account(session: Session, institution: str) -> tuple[Account, Position]:
    member = default_member(session)
    account = Account(
        id=uuid.uuid4(),
        household_member_id=member.id,
        kind="mf_folio",
        institution=institution,
        number="0001",
    )
    instrument = Instrument(
        id=uuid.uuid4(), kind="mutual_fund", identity=f"INF{institution}", name=institution
    )
    position = Position(id=uuid.uuid4(), account_id=account.id, instrument_id=instrument.id)
    session.add_all([account, instrument, position])
    session.flush()
    return account, position


def create(client: TestClient, **overrides: object) -> dict[str, object]:
    response = client.post("/api/goals", json={**NEW_CAR, **overrides})
    return {"status": response.status_code, **response.json()}


def test_a_goal_can_be_created_and_listed(client: TestClient) -> None:
    receipt = create(client)

    assert (receipt["status"], receipt["name"]) == (201, "New Car")
    listed = client.get("/api/goals").json()
    assert [g["name"] for g in listed] == ["New Car"]
    assert listed[0]["target_amount"] == "2000.00"
    assert listed[0]["percent_funded"] == "0.00"


def test_a_goal_can_be_edited(client: TestClient) -> None:
    goal_id = create(client)["id"]

    response = client.put(
        f"/api/goals/{goal_id}",
        json={**NEW_CAR, "name": "Family Car", "target_amount": "2500.00"},
    )

    assert (response.status_code, response.json()["name"]) == (200, "Family Car")
    assert client.get("/api/goals").json()[0]["target_amount"] == "2500.00"


def test_a_goal_can_be_deleted(client: TestClient) -> None:
    goal_id = create(client)["id"]

    assert client.delete(f"/api/goals/{goal_id}").status_code == 204
    assert client.get("/api/goals").json() == []


def test_editing_or_deleting_a_missing_goal_is_a_404(client: TestClient) -> None:
    missing = str(uuid.uuid4())

    assert client.put(f"/api/goals/{missing}", json=NEW_CAR).status_code == 404
    assert client.delete(f"/api/goals/{missing}").status_code == 404


def test_a_goal_shows_the_value_of_its_assigned_accounts(client: TestClient, db: Session) -> None:
    account = seed_holding(db, Holding(units="1500.000", navs=[("2025-03-31", "80.00")]))

    receipt = create(client, target_amount="200000.00", account_ids=[str(account.id)])

    assert (receipt["current_value"], receipt["percent_funded"]) == ("120000.00", "60.00")


def test_the_latest_nav_prices_a_goal(client: TestClient, db: Session) -> None:
    account = seed_holding(
        db, Holding(units="1000.000", navs=[("2024-04-02", "60.00"), ("2025-03-31", "75.00")])
    )

    receipt = create(client, target_amount="100000.00", account_ids=[str(account.id)])

    assert (receipt["current_value"], receipt["percent_funded"]) == ("75000.00", "75.00")


def test_a_goal_with_unknown_accounts_is_rejected(client: TestClient) -> None:
    response = client.post("/api/goals", json={**NEW_CAR, "account_ids": [str(uuid.uuid4())]})

    assert response.status_code == 422
    assert response.json()["code"] == "unknown_accounts"


def test_accounts_are_listed_for_the_picker(client: TestClient, db: Session) -> None:
    seed_holding(db, Holding(units="1.000", navs=[("2025-03-31", "10.00")]))

    listed = client.get("/api/accounts").json()

    assert listed[0]["institution"] == "HDFC Mutual Fund"
    assert listed[0]["name"].startswith("HDFC Mutual Fund")


def test_a_goal_rejects_an_empty_name_and_non_positive_target(client: TestClient) -> None:
    assert client.post("/api/goals", json={**NEW_CAR, "name": ""}).status_code == 422
    assert client.post("/api/goals", json={**NEW_CAR, "target_amount": "0"}).status_code == 422
