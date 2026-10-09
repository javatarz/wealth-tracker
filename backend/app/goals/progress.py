"""How far a Goal has come: the value of its assigned Accounts against its target.

Value is units times the latest known NAV per Instrument (ADR 0016 carries a price forward).
Until the valuation engine (#34) lands, the latest NAV is the most recent Transaction NAV
the ledger knows; an Account with no priced Transaction values at zero.
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.goals.models import Goal
from app.ledger.models import PAISE, ZERO, Position

HUNDRED = Decimal(100)


@dataclass(frozen=True)
class GoalProgress:
    current_value: Decimal
    target_amount: Decimal
    percent_funded: Decimal


def progress(session: Session, goal: Goal) -> GoalProgress:
    current = portfolio_value(positions_of(session, goal))
    return GoalProgress(
        current_value=current,
        target_amount=goal.target_amount,
        percent_funded=_percent(current, goal.target_amount),
    )


def positions_of(session: Session, goal: Goal) -> Sequence[Position]:
    return _positions(session, [account.id for account in goal.accounts])


def _positions(session: Session, account_ids: Sequence[object]) -> Sequence[Position]:
    if not account_ids:
        return []
    query = (
        select(Position)
        .where(Position.account_id.in_(account_ids))
        .options(selectinload(Position.transactions))
    )
    return session.scalars(query).all()


def portfolio_value(positions: Iterable[Position]) -> Decimal:
    return sum((value(position) for position in positions), ZERO)


def value(position: Position) -> Decimal:
    return (position.units() * _latest_nav(position)).quantize(PAISE)


def value_asof(position: Position, as_of: date) -> Decimal:
    """The Position's worth on a past date: units held then times the latest NAV known then."""
    return (units_asof(position, as_of) * _nav_asof(position, as_of)).quantize(PAISE)


def units_asof(position: Position, as_of: date) -> Decimal:
    return sum((row.units for row in position.transactions if row.date <= as_of), ZERO)


def _latest_nav(position: Position) -> Decimal:
    return _nav_asof(position, None)


def _nav_asof(position: Position, as_of: date | None) -> Decimal:
    priced = [
        (row.date, row.nav)
        for row in position.transactions
        if row.nav is not None and (as_of is None or row.date <= as_of)
    ]
    return max(priced, default=(None, ZERO))[1]


def _percent(current: Decimal, target: Decimal) -> Decimal:
    if target <= ZERO:
        return ZERO
    return (current * HUNDRED / target).quantize(PAISE)
