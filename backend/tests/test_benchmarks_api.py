"""The Benchmark configuration and returns API (ADR 0017)."""

import uuid
from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain import benchmark
from app.ledger.models import Instrument, Price

JAN = date(2024, 1, 1)
JAN_10 = date(2024, 1, 10)


def plain_instrument(db: Session, name: str = "HDFC Top 200") -> Instrument:
    row = Instrument(id=uuid.uuid4(), kind="mutual_fund", identity=str(uuid.uuid4()), name=name)
    db.add(row)
    db.commit()
    return row


def priced(db: Session, instrument_id: object, points: list[tuple[date, str]]) -> None:
    for on, price in points:
        db.add(Price(instrument_id=instrument_id, date=on, price=Decimal(price), source="test"))
    db.commit()


def config_by_class(client: TestClient) -> dict[str, dict[str, object]]:
    response = client.get("/api/benchmarks/config").json()
    return {view["asset_class"]: view for view in response["asset_classes"]}


def test_catalog_lists_the_benchmarks_a_user_can_pick(client: TestClient) -> None:
    keys = [item["key"] for item in client.get("/api/benchmarks/catalog").json()]

    assert "nifty50_tri" in keys
    assert "cpi" in keys


def test_config_shows_the_shipped_defaults(client: TestClient) -> None:
    by_class = config_by_class(client)

    assert by_class["equity"]["assigned_key"] == "nifty50_tri"
    assert by_class["equity"]["default_key"] == "nifty50_tri"
    assert by_class["equity"]["overridden"] is False


def test_setting_an_asset_class_benchmark_is_persisted(client: TestClient) -> None:
    response = client.put(
        "/api/benchmarks/config/equity", json={"benchmark": "nifty_midcap150_tri"}
    )

    assert response.status_code == 200
    assert response.json()["assigned_key"] == "nifty_midcap150_tri"
    assert config_by_class(client)["equity"]["overridden"] is True


def test_an_unknown_asset_class_benchmark_is_rejected(client: TestClient) -> None:
    response = client.put("/api/benchmarks/config/equity", json={"benchmark": "made_up"})

    assert response.status_code == 422


def test_an_unknown_asset_class_is_rejected(client: TestClient) -> None:
    response = client.put("/api/benchmarks/config/stamps", json={"benchmark": "cpi"})

    assert response.status_code == 422


def test_instruments_report_their_resolved_benchmark(client: TestClient, db: Session) -> None:
    plain_instrument(db)
    client.put("/api/benchmarks/config/equity", json={"benchmark": "nifty_midcap150_tri"})

    listed = client.get("/api/benchmarks/instruments").json()

    assert listed[0]["asset_class"] == "equity"
    assert listed[0]["resolved_key"] == "nifty_midcap150_tri"
    assert listed[0]["override_key"] is None


def test_an_instrument_override_wins_over_the_asset_class(client: TestClient, db: Session) -> None:
    row = plain_instrument(db)
    client.put("/api/benchmarks/config/equity", json={"benchmark": "nifty_midcap150_tri"})

    response = client.put(
        f"/api/benchmarks/instruments/{row.id}", json={"benchmark": "nifty_smallcap250_tri"}
    )

    assert response.status_code == 200
    assert response.json()["resolved_key"] == "nifty_smallcap250_tri"
    assert response.json()["override_key"] == "nifty_smallcap250_tri"


def test_clearing_an_instrument_override_restores_the_class(
    client: TestClient, db: Session
) -> None:
    row = plain_instrument(db)
    client.put(f"/api/benchmarks/instruments/{row.id}", json={"benchmark": "nifty_smallcap250_tri"})

    response = client.put(f"/api/benchmarks/instruments/{row.id}", json={"benchmark": None})

    assert response.status_code == 200
    assert response.json()["resolved_key"] == "nifty50_tri"


def test_overriding_an_unknown_instrument_is_a_404(client: TestClient) -> None:
    response = client.put(f"/api/benchmarks/instruments/{uuid.uuid4()}", json={"benchmark": "cpi"})

    assert response.status_code == 404


def test_returns_come_from_the_benchmark_price_history(client: TestClient, db: Session) -> None:
    row = benchmark.benchmark_instrument(db, "nifty50_tri")
    db.commit()
    priced(db, row.id, [(JAN, "200"), (JAN_10, "220")])

    response = client.get(
        "/api/benchmarks/returns",
        params={"benchmark": "nifty50_tri", "from": JAN.isoformat(), "to": JAN_10.isoformat()},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "NIFTY 50 TRI"
    assert body["points"][0]["value"] == "100.000000"
    assert body["points"][-1]["value"] == "110.000000"


def test_returns_for_an_unpriced_benchmark_are_a_404(client: TestClient) -> None:
    response = client.get(
        "/api/benchmarks/returns",
        params={"benchmark": "nifty50_tri", "from": JAN.isoformat(), "to": JAN_10.isoformat()},
    )

    assert response.status_code == 404


def test_overlay_rebases_returns_onto_a_portfolio_value(client: TestClient, db: Session) -> None:
    row = benchmark.benchmark_instrument(db, "nifty50_tri")
    db.commit()
    priced(db, row.id, [(JAN, "200"), (JAN_10, "220")])

    response = client.get(
        "/api/benchmarks/overlay",
        params={
            "benchmark": "nifty50_tri",
            "start_value": "50000",
            "from": JAN.isoformat(),
            "to": JAN_10.isoformat(),
        },
    )

    assert response.status_code == 200
    points = response.json()["points"]
    assert points[0]["value"] == "50000.00"
    assert points[-1]["value"] == "55000.00"
