"""The valuation endpoints: per-strategy values, history, and appraisals (#34)."""

import uuid
from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.ledger.models import Account, HouseholdMember, Instrument, Position, Price, Transaction
from app.valuation.strategies import APPRAISED, MARKET_PRICED, NO_PRICE

TODAY = date.today()


def instrument(strategy: str, **terms: object) -> Instrument:
    return Instrument(
        id=uuid.uuid4(),
        kind="mutual_fund",
        identity="ACME-1",
        name="ACME Fund",
        valuation_strategy=strategy,
        **terms,
    )


def seeded_position(
    db: Session, strategy: str, units: str, **terms: object
) -> tuple[Position, Instrument]:
    member = HouseholdMember(id=uuid.uuid4(), name="Me")
    db.add(member)
    db.flush()
    account = Account(
        id=uuid.uuid4(),
        household_member_id=member.id,
        kind="fd",
        institution="ACME",
        number="1",
    )
    holding = instrument(strategy, **terms)
    position = Position(id=uuid.uuid4(), account=account, instrument=holding)
    db.add(position)
    db.add(
        Transaction(
            id=uuid.uuid4(),
            position=position,
            date=TODAY,
            kind="PURCHASE",
            description="Opening",
            units=Decimal(units),
            synthetic=False,
            fingerprint=str(uuid.uuid4()),
        )
    )
    db.commit()
    return position, holding


def cache_price(db: Session, holding: Instrument, price: str) -> None:
    db.add(
        Price(
            id=uuid.uuid4(),
            instrument_id=holding.id,
            date=TODAY,
            price=Decimal(price),
            source="amfi",
        )
    )
    db.commit()


def test_positions_api_values_units_times_cached_nav(client: TestClient, db: Session) -> None:
    position, holding = seeded_position(db, MARKET_PRICED, "12.500")
    cache_price(db, holding, "80.00")

    [row] = client.get("/api/positions").json()

    assert row["value"] == "1000.00"
    assert row["valuation_strategy"] == MARKET_PRICED
    assert row["valuation_label"] == "Market-priced"
    assert row["stale"] is False
    assert row["id"] == str(position.id)


def test_positions_api_warns_when_no_market_data_is_cached(client: TestClient, db: Session) -> None:
    seeded_position(db, MARKET_PRICED, "12.500")

    [row] = client.get("/api/positions").json()

    assert row["value"] is None
    assert row["warning"] == NO_PRICE


def test_single_position_endpoint_returns_the_same_summary(client: TestClient, db: Session) -> None:
    position, holding = seeded_position(db, MARKET_PRICED, "12.500")
    cache_price(db, holding, "80.00")

    assert (
        client.get(f"/api/positions/{position.id}").json() == client.get("/api/positions").json()[0]
    )


def test_single_position_endpoint_is_not_found_for_an_unknown_id(client: TestClient) -> None:
    assert client.get(f"/api/positions/{uuid.uuid4()}").status_code == 404


def test_recording_an_appraisal_sets_the_position_value(client: TestClient, db: Session) -> None:
    position, _holding = seeded_position(db, APPRAISED, "5.000")

    response = client.post(
        f"/api/positions/{position.id}/appraisal",
        json={"date": TODAY.isoformat(), "value": "750000.00"},
    )

    assert response.status_code == 201
    assert response.json()["value"] == "750000.00"
    assert client.get("/api/positions").json()[0]["value"] == "750000.00"


def test_appraisal_for_an_unknown_position_is_not_found(client: TestClient) -> None:
    response = client.post(
        f"/api/positions/{uuid.uuid4()}/appraisal",
        json={"date": TODAY.isoformat(), "value": "1.00"},
    )

    assert response.status_code == 404


def test_valuation_history_values_each_transaction_date(client: TestClient, db: Session) -> None:
    position, holding = seeded_position(db, MARKET_PRICED, "10.000")
    cache_price(db, holding, "12.00")

    response = client.get(f"/api/positions/{position.id}/valuation-history")

    assert response.status_code == 200
    assert [(point["date"], point["value"]) for point in response.json()] == [
        (TODAY.isoformat(), "120.00")
    ]


def test_valuation_history_for_an_unknown_position_is_not_found(client: TestClient) -> None:
    assert client.get(f"/api/positions/{uuid.uuid4()}/valuation-history").status_code == 404
