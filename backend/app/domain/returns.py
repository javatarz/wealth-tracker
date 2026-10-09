"""Benchmark return series from the shared price history (ADR 0016, ADR 0017).

A Benchmark's return at a date is its price at that date rebased to the first
available price at or before the requested range: 100 at the start of the window,
more or less afterwards. Prices are carried forward across weekends, holidays and
gaps — the same rule the valuation engine uses for price gaps.
"""

import bisect
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.series import DatedValue
from app.ledger.models import Price

RATIO_QUANTUM = Decimal("0.000001")
HUNDRED = Decimal(100)
DateRange = tuple[date, date]


@dataclass(frozen=True)
class BenchmarkSeries:
    key: str
    name: str
    start: date
    end: date
    points: tuple[DatedValue, ...]


def price_on_or_before(session: Session, instrument_id: object, on: date) -> DatedValue | None:
    """The closest price at or before a date, reaching back before a range start."""
    query = (
        select(Price.date, Price.price)
        .where(Price.instrument_id == instrument_id, Price.date <= on)
        .order_by(Price.date.desc())
        .limit(1)
    )
    row = session.execute(query).first()
    return None if row is None else DatedValue(row.date, row.price)


def rebased_series(
    session: Session, instrument_id: object, date_range: DateRange
) -> tuple[DatedValue, ...]:
    """Daily return points over the range, rebased to 100 at the range start."""
    prices = _prices_in_range(session, instrument_id, date_range)
    baseline = price_on_or_before(session, instrument_id, date_range[0])
    return _rebase(_carry_forward(prices, baseline, date_range))


def _prices_in_range(
    session: Session, instrument_id: object, date_range: DateRange
) -> tuple[DatedValue, ...]:
    start, end = date_range
    query = (
        select(Price.date, Price.price)
        .where(Price.instrument_id == instrument_id, Price.date >= start, Price.date <= end)
        .order_by(Price.date)
    )
    return tuple(DatedValue(row.date, row.price) for row in session.execute(query))


def _carry_forward(
    history: Sequence[DatedValue], baseline: DatedValue | None, date_range: DateRange
) -> tuple[DatedValue, ...]:
    seeded = _seeded(history, baseline, date_range[0])
    if not seeded:
        return ()
    dates = [point.date for point in seeded]
    values = [point.value for point in seeded]
    return tuple(_carried_points(date_range, dates, values))


def _seeded(
    history: Sequence[DatedValue], baseline: DatedValue | None, start: date
) -> tuple[DatedValue, ...]:
    if baseline is None or baseline.date >= start:
        return tuple(history)
    return (baseline, *history)


def _carried_points(
    date_range: DateRange, dates: Sequence[date], values: Sequence[Decimal]
) -> Iterator[DatedValue]:
    carried = (_from_history(day, dates, values) for day in _each_day(*date_range))
    return (point for point in carried if point is not None)


def _each_day(start: date, end: date) -> Iterator[date]:
    return (date.fromordinal(day) for day in range(start.toordinal(), end.toordinal() + 1))


def _from_history(on: date, dates: Sequence[date], values: Sequence[Decimal]) -> DatedValue | None:
    index = bisect.bisect_right(dates, on) - 1
    return None if index < 0 else DatedValue(on, values[index])


def _rebase(points: Sequence[DatedValue]) -> tuple[DatedValue, ...]:
    if not points or points[0].value == 0:
        return ()
    return _scaled_to(points, points[0].value)


def _scaled_to(points: Sequence[DatedValue], baseline: Decimal) -> tuple[DatedValue, ...]:
    return tuple(
        DatedValue(point.date, (point.value / baseline * HUNDRED).quantize(RATIO_QUANTUM))
        for point in points
    )
