"""Value Positions today, or at any past date, using the right Valuation Strategy (ADR 0016).

Value is always derived, never materialised: a Position's worth on a date is its
units-on-that-date put through its Instrument's strategy. Price and appraisal marks
are read through a request-scoped cache so a list of Positions doesn't refetch them.
"""

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.ledger.models import ZERO, Appraisal, Position, Price, Transaction
from app.ledger.positions import list_positions
from app.valuation.strategies import Valuation, ValuationInputs, value_with


class Dated(Protocol):
    """A mark that applies to every date at or after its own (ADR 0016 carry-forward)."""

    date: date


@dataclass(frozen=True)
class RequestedAppraisal:
    """A user-supplied revaluation to record against an Instrument."""

    instrument_id: uuid.UUID
    date: date
    value: Decimal
    recorded_at: datetime


class Marks:
    """Price and appraisal marks, loaded once per Instrument per request."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._prices: dict[uuid.UUID, Sequence[Price]] = {}
        self._appraisals: dict[uuid.UUID, Sequence[Appraisal]] = {}

    def price(self, instrument_id: uuid.UUID, on: date) -> Price | None:
        return _closest(self._prices_of(instrument_id), on)

    def appraisal(self, instrument_id: uuid.UUID, on: date) -> Appraisal | None:
        return _closest(self._appraisals_of(instrument_id), on)

    def _prices_of(self, instrument_id: uuid.UUID) -> Sequence[Price]:
        if instrument_id not in self._prices:
            query = select(Price).where(Price.instrument_id == instrument_id)
            self._prices[instrument_id] = self._session.scalars(query).all()
        return self._prices[instrument_id]

    def _appraisals_of(self, instrument_id: uuid.UUID) -> Sequence[Appraisal]:
        if instrument_id not in self._appraisals:
            query = select(Appraisal).where(Appraisal.instrument_id == instrument_id)
            self._appraisals[instrument_id] = self._session.scalars(query).all()
        return self._appraisals[instrument_id]


def value_of(position: Position, on: date, marks: Marks) -> Valuation:
    """The Position's value on `on`, using its Instrument's Valuation Strategy."""
    return value_with(
        ValuationInputs(
            units=_units_on(position, on),
            instrument=position.instrument,
            on=on,
            opened_on=_opened_on(position),
            price=marks.price(position.instrument_id, on),
            appraisal=marks.appraisal(position.instrument_id, on),
        )
    )


def valued_positions(session: Session, on: date) -> list[tuple[Position, Valuation]]:
    """Every Position in the ledger, valued on `on`, in ledger order."""
    marks = Marks(session)
    return [(position, value_of(position, on, marks)) for position in list_positions(session)]


def position_of(session: Session, position_id: uuid.UUID) -> Position | None:
    """The Position with its Instrument and ledger loaded, or None if it isn't there."""
    return _one_position(session, position_id)


def valued_position(
    session: Session, position_id: uuid.UUID, on: date
) -> tuple[Position, Valuation] | None:
    """One Position and its value on `on`, or None if the Position doesn't exist."""
    position = _one_position(session, position_id)
    if position is None:
        return None
    return position, value_of(position, on, Marks(session))


def history_of(session: Session, position: Position, on: date) -> list[tuple[date, Valuation]]:
    """The Position's value at each of its real Transaction dates up to `on`."""
    marks = Marks(session)
    return [(day, value_of(position, day, marks)) for day in _transaction_dates(position, on)]


def record_appraisal(session: Session, requested: "RequestedAppraisal") -> Appraisal:
    """Record or replace a user-supplied revaluation mark for an Instrument (ADR 0016)."""
    existing = session.scalars(
        select(Appraisal).where(
            Appraisal.instrument_id == requested.instrument_id, Appraisal.date == requested.date
        )
    ).first()
    if existing is not None:
        existing.value = requested.value
        return existing
    appraisal = Appraisal(
        id=uuid.uuid4(),
        instrument_id=requested.instrument_id,
        date=requested.date,
        value=requested.value,
        recorded_at=requested.recorded_at,
    )
    session.add(appraisal)
    return appraisal


def _one_position(session: Session, position_id: uuid.UUID) -> Position | None:
    query = (
        select(Position)
        .where(Position.id == position_id)
        .options(selectinload(Position.transactions), selectinload(Position.instrument))
    )
    return session.scalars(query).first()


def _transaction_dates(position: Position, on: date) -> list[date]:
    return sorted({row.date for row in _real_transactions(position) if row.date <= on})


def _units_on(position: Position, on: date) -> Decimal:
    return sum((row.units for row in _real_transactions(position) if row.date <= on), ZERO)


def _real_transactions(position: Position) -> list[Transaction]:
    return [row for row in position.transactions if not row.synthetic]


def _opened_on(position: Position) -> date:
    return min((row.date for row in position.transactions), default=date.today())


def _closest[Mark: Dated](marks: Sequence[Mark], on: date) -> Mark | None:
    at_or_before = [mark for mark in marks if mark.date <= on]
    return max(at_or_before, key=lambda mark: mark.date, default=None)
