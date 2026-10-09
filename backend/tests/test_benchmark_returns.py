"""Benchmark assignment, return series and overlay (ADR 0017)."""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.domain import benchmark, benchmark_service, returns
from app.domain.asset_classes import (
    asset_class_of_instrument_kind,
    default_benchmark_key,
    is_known_benchmark,
)
from app.domain.series import DatedValue, rebased_to, summed
from app.ledger.models import Instrument, Price

JAN = date(2024, 1, 1)
JAN_10 = date(2024, 1, 10)


def plain_instrument(session: Session, kind: str = "mutual_fund") -> Instrument:
    row = Instrument(id=uuid.uuid4(), kind=kind, identity=str(uuid.uuid4()), name="Test Fund")
    session.add(row)
    session.flush()
    return row


def priced(session: Session, instrument_id: object, points: list[tuple[date, str]]) -> None:
    for on, price in points:
        session.add(
            Price(instrument_id=instrument_id, date=on, price=Decimal(price), source="test")
        )
    session.flush()


def benchmark_row(session: Session, key: str) -> Instrument:
    row = benchmark.benchmark_instrument(session, key)
    session.flush()
    return row


def test_instrument_kind_maps_to_an_asset_class() -> None:
    assert asset_class_of_instrument_kind("mutual_fund") == "equity"
    assert asset_class_of_instrument_kind("physical_gold") == "gold"
    assert asset_class_of_instrument_kind("unmapped-kind") == "other"


def test_returns_are_rebased_to_a_hundred_at_the_range_start(db: Session) -> None:
    row = plain_instrument(db)
    priced(db, row.id, [(JAN, "100"), (JAN_10, "150")])

    points = returns.rebased_series(db, row.id, (JAN, JAN_10))

    assert points[0] == DatedValue(JAN, Decimal("100.000000"))
    assert points[-1] == DatedValue(JAN_10, Decimal("150.000000"))


def test_returns_carry_the_last_price_across_a_gap(db: Session) -> None:
    row = plain_instrument(db)
    priced(db, row.id, [(date(2024, 1, 5), "100"), (date(2024, 1, 8), "110")])

    points = returns.rebased_series(db, row.id, (date(2024, 1, 5), date(2024, 1, 8)))

    values = {point.date: point.value for point in points}
    assert values[date(2024, 1, 6)] == Decimal("100.000000")
    assert values[date(2024, 1, 7)] == Decimal("100.000000")
    assert values[date(2024, 1, 8)] == Decimal("110.000000")


def test_returns_reach_backwards_for_a_baseline_before_the_range(db: Session) -> None:
    row = plain_instrument(db)
    priced(db, row.id, [(date(2023, 12, 20), "80"), (JAN_10, "160")])

    points = returns.rebased_series(db, row.id, (JAN, JAN_10))

    assert points[0] == DatedValue(JAN, Decimal("100.000000"))


def test_rebasing_onto_a_portfolio_value_keeps_the_start() -> None:
    points = (DatedValue(JAN, Decimal("100")), DatedValue(JAN_10, Decimal("120")))

    scaled = rebased_to(points, Decimal("50000"))

    assert scaled[0].value == Decimal("50000.00")
    assert scaled[1].value == Decimal("60000.00")


def test_defaults_need_no_configuration(db: Session) -> None:
    assert benchmark.assigned_benchmark_key(db, "equity") == "nifty50_tri"
    assert benchmark.assigned_benchmark_key(db, "gold") == "nifty_composite_debt"


def test_an_asset_class_override_replaces_the_default(db: Session) -> None:
    benchmark.assign_benchmark(db, "equity", "nifty_midcap150_tri")
    db.flush()

    assert benchmark.assigned_benchmark_key(db, "equity") == "nifty_midcap150_tri"


def test_an_instrument_override_beats_the_asset_class(db: Session) -> None:
    row = plain_instrument(db)
    benchmark.assign_benchmark(db, "equity", "nifty_midcap150_tri")
    benchmark.set_instrument_override(db, row.id, "nifty_smallcap250_tri")

    assert benchmark.resolve_benchmark_key(db, row) == "nifty_smallcap250_tri"


def test_clearing_an_override_falls_back_to_the_asset_class(db: Session) -> None:
    row = plain_instrument(db)
    benchmark.set_instrument_override(db, row.id, "nifty_midcap150_tri")
    benchmark.set_instrument_override(db, row.id, None)

    assert benchmark.resolve_benchmark_key(db, row) == "nifty50_tri"


def test_return_series_reads_the_benchmark_instrument(db: Session) -> None:
    row = benchmark_row(db, "nifty50_tri")
    priced(db, row.id, [(JAN, "200"), (JAN_10, "220")])

    series = benchmark_service.return_series(db, "nifty50_tri", (JAN, JAN_10))

    assert series is not None
    assert series.name == "NIFTY 50 TRI"
    assert series.points[-1].value == Decimal("110.000000")


def test_an_unpriced_benchmark_has_no_series(db: Session) -> None:
    assert benchmark_service.return_series(db, "nifty50_tri", (JAN, JAN_10)) is None


def test_asset_class_benchmarks_report_assigned_and_default(db: Session) -> None:
    benchmark.assign_benchmark(db, "equity", "nifty_midcap150_tri")
    db.flush()

    by_class = {view.asset_class: view for view in benchmark_service.asset_class_benchmarks(db)}

    assert by_class["equity"].assigned_key == "nifty_midcap150_tri"
    assert by_class["equity"].default_key == "nifty50_tri"
    assert by_class["equity"].overridden is True
    assert by_class["gold"].overridden is False
    assert by_class["gold"].assigned_key == default_benchmark_key("gold")


def test_blended_overlay_sums_independent_series(db: Session) -> None:
    nifty = benchmark_row(db, "nifty50_tri")
    cpi = benchmark_row(db, "cpi")
    priced(db, nifty.id, [(JAN, "100"), (JAN_10, "110")])
    priced(db, cpi.id, [(JAN, "200"), (JAN_10, "210")])
    components = (
        benchmark_service.OverlayComponent("nifty50_tri", Decimal("1000")),
        benchmark_service.OverlayComponent("cpi", Decimal("500")),
    )

    blended = benchmark_service.blended_overlay(db, (JAN, JAN_10), components)

    assert blended[0].value == Decimal("1500.00")
    assert blended[-1].value == Decimal("1100.00") + Decimal("525.00")


def test_blended_overlay_of_one_component_is_that_component(db: Session) -> None:
    nifty = benchmark_row(db, "nifty50_tri")
    priced(db, nifty.id, [(JAN, "100"), (JAN_10, "110")])
    components = (benchmark_service.OverlayComponent("nifty50_tri", Decimal("1000")),)

    blended = benchmark_service.blended_overlay(db, (JAN, JAN_10), components)

    assert blended[0] == DatedValue(JAN, Decimal("1000.00"))
    assert blended[-1] == DatedValue(JAN_10, Decimal("1100.00"))


def test_summing_keeps_only_dates_both_series_cover() -> None:
    left = (DatedValue(JAN, Decimal("100")), DatedValue(JAN_10, Decimal("110")))
    right = (DatedValue(JAN_10, Decimal("200")),)

    assert summed([left, right]) == (DatedValue(JAN_10, Decimal("310.00")),)


def test_known_benchmark_guard() -> None:
    assert is_known_benchmark("nifty50_tri")
    assert not is_known_benchmark("made_up")


def test_unknown_benchmark_is_rejected(db: Session) -> None:
    with pytest.raises(benchmark.UnknownBenchmarkError):
        benchmark.assign_benchmark(db, "equity", "made_up")
