"""Shared vocabulary for dated decimal series."""

from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from typing import NamedTuple

PAISE = Decimal("0.01")
PERCENT = Decimal(100)


class DatedValue(NamedTuple):
    date: date
    value: Decimal


def rebased_to(points: Sequence[DatedValue], start_value: Decimal) -> tuple[DatedValue, ...]:
    """Scales a percentage series (100 at the start) so it starts at ``start_value``.

    A Benchmark line rebased this way starts at the Portfolio's starting value, so
    the gap between the two lines reads directly as currency outperformance (ADR 0017).
    """
    return tuple(
        DatedValue(point.date, (point.value / PERCENT * start_value).quantize(PAISE))
        for point in points
    )


def summed(series: Sequence[Sequence[DatedValue]]) -> tuple[DatedValue, ...]:
    """Adds independent series point by point, aligning them by date.

    A blended Benchmark for a mixed Portfolio is the sum of each component's own
    series (ADR 0017), so this keeps only the dates every series covers.
    """
    if not series:
        return ()
    common = _common_dates(series)
    return tuple(DatedValue(on, _total(series, on).quantize(PAISE)) for on in common)


def _total(series: Sequence[Sequence[DatedValue]], on: date) -> Decimal:
    return sum((_values_on(component, on) for component in series), Decimal(0))


def _common_dates(series: Sequence[Sequence[DatedValue]]) -> tuple[date, ...]:
    dated = [{point.date: point.value for point in component} for component in series]
    return tuple(sorted(set.intersection(*(set(component) for component in dated))))


def _values_on(component: Sequence[DatedValue], on: date) -> Decimal:
    return next(point.value for point in component if point.date == on)
