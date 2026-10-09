"""Reading a Position line for the Net Worth dashboard (#28)."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from app.ledger.models import PAISE, ZERO, Position
from app.ledger.valuation import net_worth_series, position_value

PERCENT = Decimal(100)


@dataclass(frozen=True)
class ValuedPosition:
    """A Position with the figures the summary table needs, before its share."""

    id: UUID
    scheme: str
    account: str
    asset_class: str
    units: Decimal
    cost_basis: Decimal
    current_value: Decimal

    @classmethod
    def of(cls, position: Position) -> "ValuedPosition":
        return cls(
            id=position.id,
            scheme=position.instrument.name,
            account=_account_label(position),
            asset_class=position.instrument.asset_class,
            units=position.units(),
            cost_basis=position.cost_basis(),
            current_value=position_value(position),
        )


@dataclass(frozen=True)
class Dashboard:
    current_value: Decimal
    invested: Decimal
    absolute_return: Decimal
    positions: list[ValuedPosition]
    percent_by_position: dict[UUID, Decimal]
    series: list[tuple[date, Decimal]]


def build_dashboard(positions: Sequence[Position]) -> Dashboard:
    valued = [ValuedPosition.of(position) for position in positions]
    current_value = sum((entry.current_value for entry in valued), ZERO)
    invested = sum((entry.cost_basis for entry in valued), ZERO)
    return Dashboard(
        current_value=current_value,
        invested=invested,
        absolute_return=current_value - invested,
        positions=valued,
        percent_by_position=_shares(valued, current_value),
        series=net_worth_series(positions),
    )


def _account_label(position: Position) -> str:
    account = position.account
    return f"{account.institution} · {account.number}"


def _shares(valued: Sequence[ValuedPosition], total: Decimal) -> dict[UUID, Decimal]:
    return {entry.id: _percent(entry.current_value, total) for entry in valued}


def _percent(value: Decimal, total: Decimal) -> Decimal:
    if total <= ZERO:
        return ZERO.quantize(PAISE)
    return (value / total * PERCENT).quantize(PAISE)
