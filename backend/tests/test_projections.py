"""Per-Goal projections: CAGR, trailing window, and Scheduled Transaction flows (#38)."""

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
    "target_amount": "112000.00",
    "target_date": "2027-01-01",
    "projection_strategy": "cagr",
    "cagr_rate": "0.12",
}
AS_OF = "2026-01-01"
ZERO = Decimal(0)


@dataclass(frozen=True)
class Holding:
    units: str
    navs: Sequence[tuple[str, str]]
    institution: str = "HDFC Mutual Fund"


def seed_holding(session: Session, holding: Holding) -> tuple[Account, Position]:
    """An Account with one mutual-fund Position whose Transactions price it."""
    member = default_member(session)
    account = Account(
        id=uuid.uuid4(),
        household_member_id=member.id,
        kind="mf_folio",
        institution=holding.institution,
        number="0001",
    )
    instrument = Instrument(
        id=uuid.uuid4(),
        kind="mutual_fund",
        identity=f"INF{holding.institution}",
        name=holding.institution,
    )
    position = Position(id=uuid.uuid4(), account_id=account.id, instrument_id=instrument.id)
    session.add_all([account, instrument, position])
    session.flush()
    session.add_all(_transactions(position, holding))
    session.commit()
    return account, position


def _transactions(position: Position, holding: Holding) -> list[Transaction]:
    return [
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


def create(client: TestClient, **overrides: object) -> dict[str, object]:
    response = client.post("/api/goals", json={**NEW_CAR, **overrides})
    body = response.json()
    return {**body, "status": response.status_code}


def projection_of(client: TestClient, goal_id: object, **params: str) -> dict[str, object]:
    response = client.get(f"/api/goals/{goal_id}/projection", params={"as_of": AS_OF, **params})
    return {**response.json(), "http_status": response.status_code}


def add_schedule(
    client: TestClient,
    goal_id: object,
    position_id: object,
    **overrides: object,
) -> dict[str, object]:
    body = {
        "position_id": str(position_id),
        "description": "Monthly SIP",
        "direction": "contribution",
        "frequency": "monthly",
        "amount": "1000.00",
        "start_date": "2026-01-01",
        "escalation_rate": "0",
        **overrides,
    }
    response = client.post(f"/api/goals/{goal_id}/scheduled-transactions", json=body)
    return {**response.json(), "status": response.status_code}


def test_cagr_projection_grows_at_the_users_rate(client: TestClient, db: Session) -> None:
    account, _ = seed_holding(db, Holding(units="1000.000", navs=[("2025-03-31", "100.00")]))

    receipt = create(client, account_ids=[str(account.id)])
    forecast = projection_of(client, receipt["id"])

    assert receipt["projection_strategy"] == "cagr"
    assert forecast["current_value"] == "100000.00"
    assert forecast["projected_value"] == "112000.00"  # 100000 x 1.12 over one year
    assert forecast["rate"] == "0.12"


def test_a_projection_that_beats_its_target_is_exceeded(client: TestClient, db: Session) -> None:
    account, _ = seed_holding(db, Holding(units="1000.000", navs=[("2025-03-31", "100.00")]))

    receipt = create(client, account_ids=[str(account.id)], target_amount="105000.00")

    assert projection_of(client, receipt["id"])["status"] == "exceeded"


def test_a_projection_on_track_when_it_lands_exactly_on_the_target(
    client: TestClient, db: Session
) -> None:
    account, _ = seed_holding(db, Holding(units="1000.000", navs=[("2025-03-31", "100.00")]))

    receipt = create(client, account_ids=[str(account.id)], target_amount="112000.00")

    assert projection_of(client, receipt["id"])["status"] == "on_track"


def test_a_projection_at_risk_when_it_falls_short_by_a_tenth(
    client: TestClient, db: Session
) -> None:
    account, _ = seed_holding(db, Holding(units="1000.000", navs=[("2025-03-31", "100.00")]))

    receipt = create(client, account_ids=[str(account.id)], target_amount="120000.00")

    assert projection_of(client, receipt["id"])["status"] == "at_risk"


def test_a_projection_off_track_when_it_falls_short_by_more_than_a_tenth(
    client: TestClient, db: Session
) -> None:
    account, _ = seed_holding(db, Holding(units="1000.000", navs=[("2025-03-31", "100.00")]))

    receipt = create(client, account_ids=[str(account.id)], target_amount="200000.00")

    assert projection_of(client, receipt["id"])["status"] == "off_track"


def test_a_projection_without_a_strategy_has_insufficient_data(client: TestClient) -> None:
    receipt = create(client, projection_strategy=None, cagr_rate=None)

    forecast = projection_of(client, receipt["id"])

    assert (forecast["rate"], forecast["status"]) == (None, "insufficient_data")


def test_a_trailing_window_projection_uses_the_historical_window(
    client: TestClient, db: Session
) -> None:
    account, _ = seed_holding(
        db,
        Holding(
            units="1000.000",
            navs=[("2024-01-01", "100.00"), ("2025-01-01", "121.00")],
        ),
    )

    receipt = create(
        client,
        account_ids=[str(account.id)],
        projection_strategy="trailing_window",
        cagr_rate=None,
        trailing_window_years=2,
    )
    forecast = projection_of(client, receipt["id"])

    assert forecast["rate"] == "0.10"  # sqrt(1.21) - 1 over the trailing two years
    assert forecast["current_value"] == "121000.00"
    assert forecast["projected_value"] == "133100.00"


def test_a_trailing_window_without_enough_history_has_insufficient_data(
    client: TestClient, db: Session
) -> None:
    account, _ = seed_holding(db, Holding(units="1000.000", navs=[("2025-01-01", "100.00")]))

    receipt = create(
        client,
        account_ids=[str(account.id)],
        projection_strategy="trailing_window",
        cagr_rate=None,
        trailing_window_years=2,
    )

    assert projection_of(client, receipt["id"])["status"] == "insufficient_data"


def test_a_scheduled_contribution_feeds_the_projection(client: TestClient, db: Session) -> None:
    account, position = seed_holding(db, Holding(units="1000.000", navs=[("2025-03-31", "100.00")]))
    receipt = create(client, account_ids=[str(account.id)], cagr_rate="0")

    add_schedule(client, receipt["id"], position.id, amount="1000.00")

    forecast = projection_of(client, receipt["id"])
    assert forecast["current_value"] == "100000.00"
    assert forecast["projected_value"] == "112000.00"  # 100000 + 12 x 1000


def test_escalation_raises_the_later_scheduled_contributions(
    client: TestClient, db: Session
) -> None:
    account, position = seed_holding(db, Holding(units="1000.000", navs=[("2025-03-31", "100.00")]))
    receipt = create(client, account_ids=[str(account.id)], cagr_rate="0", target_date="2028-01-01")
    add_schedule(client, receipt["id"], position.id, amount="1000.00", escalation_rate="0.10")

    forecast = projection_of(client, receipt["id"])

    # 100000 + 11 payments at 1000 + 12 at 1100 + the target-date one at 1210.
    assert forecast["projected_value"] == "125410.00"


def test_scheduled_transactions_are_listed_and_deletable(client: TestClient, db: Session) -> None:
    account, position = seed_holding(db, Holding(units="1000.000", navs=[("2025-03-31", "100.00")]))
    receipt = create(client, account_ids=[str(account.id)])
    schedule = add_schedule(client, receipt["id"], position.id)

    board = client.get(f"/api/goals/{receipt['id']}/scheduled-transactions").json()
    assert board["schedules"][0]["description"] == "Monthly SIP"
    assert board["positions"][0]["id"] == str(position.id)

    assert client.delete(f"/api/scheduled-transactions/{schedule['id']}").status_code == 204
    assert (
        client.get(f"/api/goals/{receipt['id']}/scheduled-transactions").json()["schedules"] == []
    )


def test_a_scheduled_transaction_for_a_foreign_position_is_rejected(
    client: TestClient, db: Session
) -> None:
    account, _ = seed_holding(db, Holding(units="1000.000", navs=[("2025-03-31", "100.00")]))
    receipt = create(client, account_ids=[str(account.id)])

    response = add_schedule(client, receipt["id"], uuid.uuid4())

    assert response["status"] == 422
    assert response["code"] == "unknown_position"


def test_a_schedule_ending_before_it_starts_is_rejected(client: TestClient, db: Session) -> None:
    account, position = seed_holding(db, Holding(units="1000.000", navs=[("2025-03-31", "100.00")]))
    receipt = create(client, account_ids=[str(account.id)])

    response = add_schedule(
        client, receipt["id"], position.id, start_date="2026-06-01", end_date="2026-01-01"
    )

    assert response["status"] == 422
    assert response["code"] == "invalid_schedule"


def test_projection_history_snapshots_the_trajectory(client: TestClient, db: Session) -> None:
    account, _ = seed_holding(db, Holding(units="1000.000", navs=[("2025-03-31", "100.00")]))
    receipt = create(client, account_ids=[str(account.id)])

    history = client.get(
        f"/api/goals/{receipt['id']}/projection/history", params={"as_of": AS_OF}
    ).json()

    assert len(history["points"]) == 12
    assert history["points"][-1]["on"] == AS_OF


def test_projecting_a_missing_goal_is_a_404(client: TestClient) -> None:
    missing = str(uuid.uuid4())

    assert client.get(f"/api/goals/{missing}/projection").status_code == 404
    assert client.get(f"/api/goals/{missing}/scheduled-transactions").status_code == 404
