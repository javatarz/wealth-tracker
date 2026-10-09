"""Compute what a Portfolio is worth over time (#28).

Phase 1 has no market-data feed yet (#31, #34), so a Position is valued at its
last known price (ADR 0016) — the NAV of its most recent priced Transaction.
Once the price table lands, this module is the seam that swaps carry-forward
ledger prices for the shared per-Instrument price history.
"""

from collections.abc import Iterable, Sequence
from datetime import date
from decimal import Decimal
from itertools import chain

from app.ledger.models import PAISE, ZERO, Position


def position_value(position: Position) -> Decimal:
    """A Position's worth today, at its last known price."""
    return _value_at(position, _latest_date(position))


def net_worth_series(positions: Sequence[Position]) -> list[tuple[date, Decimal]]:
    """Portfolio Net Worth on each date any Position changes, in order.

    Positions with no Transactions contribute nothing (ADR 0016: no line before
    a Position's first known point). Valuations carry forward between changes.
    """
    deltas = _deltas_by_date(positions)
    total = ZERO
    series: list[tuple[date, Decimal]] = []
    for on in sorted(deltas):
        total += deltas[on]
        series.append((on, total.quantize(PAISE)))
    return series


def _deltas_by_date(positions: Sequence[Position]) -> dict[date, Decimal]:
    deltas: dict[date, Decimal] = {}
    for on, delta in _all_changes(positions):
        deltas[on] = deltas.get(on, ZERO) + delta
    return deltas


def _all_changes(positions: Iterable[Position]) -> Iterable[tuple[date, Decimal]]:
    return chain.from_iterable(_value_changes(position) for position in positions)


def _value_changes(position: Position) -> list[tuple[date, Decimal]]:
    """The step in a Position's value each time its units or price move."""
    dates = sorted({transaction.date for transaction in position.transactions})
    return [
        (on, _value_at(position, on) - _value_at(position, _previous(dates, on))) for on in dates
    ]


def _previous(dates: Sequence[date], on: date) -> date | None:
    earlier = [candidate for candidate in dates if candidate < on]
    return earlier[-1] if earlier else None


def _latest_date(position: Position) -> date | None:
    return max((transaction.date for transaction in position.transactions), default=None)


def _value_at(position: Position, on: date | None) -> Decimal:
    if on is None:
        return ZERO
    return (_units_at(position, on) * _price_at(position, on)).quantize(PAISE)


def _units_at(position: Position, on: date) -> Decimal:
    return sum(
        (transaction.units for transaction in position.transactions if transaction.date <= on),
        ZERO,
    )


def _price_at(position: Position, on: date) -> Decimal:
    priced = [
        transaction
        for transaction in position.transactions
        if transaction.date <= on and transaction.nav is not None
    ]
    if not priced:
        return ZERO
    latest = max(priced, key=lambda transaction: transaction.date)
    return latest.nav or ZERO
