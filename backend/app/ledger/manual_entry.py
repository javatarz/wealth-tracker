"""Manually recording a Transaction against a Position (ADR 0001, 0002, 0021).

Each Instrument kind accepts only the Transaction types that make sense for it,
so an FD cannot receive an SIP and a mutual fund cannot receive a contribution.
The accepted types drive both the form's choices and validation, so the two
cannot drift apart. A manual Transaction joins the same immutable ledger an
import writes to, and the Position's units and cost basis are derived from it
immediately.
"""

import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.statement_rejection import StatementRejectedError
from app.ledger.models import Position, Transaction

PURCHASE = "purchase"
REDEMPTION = "redemption"
SIP = "sip"
CONTRIBUTION = "contribution"
MATURITY = "maturity"

ZERO = Decimal(0)

# Which Transaction types each Instrument kind accepts (ADR 0002, 0021).
ALLOWED_TYPES: dict[str, frozenset[str]] = {
    "mutual_fund": frozenset({PURCHASE, REDEMPTION, SIP}),
    "equity": frozenset({PURCHASE, REDEMPTION}),
    "gold_etf": frozenset({PURCHASE, REDEMPTION}),
    "physical_gold": frozenset({PURCHASE, REDEMPTION}),
    "crypto": frozenset({PURCHASE, REDEMPTION}),
    "fd": frozenset({PURCHASE, MATURITY}),
    "ppf": frozenset({CONTRIBUTION, MATURITY}),
    "epf": frozenset({CONTRIBUTION, MATURITY}),
    "nps": frozenset({CONTRIBUTION, REDEMPTION}),
    "property": frozenset({PURCHASE, REDEMPTION}),
}

BUYING_TYPES: frozenset[str] = frozenset({PURCHASE, SIP, CONTRIBUTION})
SELLING_TYPES: frozenset[str] = frozenset({REDEMPTION, MATURITY})


@dataclass(frozen=True)
class ManualTransaction:
    """A Transaction as the browser submitted it, before any validation."""

    position_id: uuid.UUID
    type: str
    date: date
    units: Decimal
    amount: Decimal | None
    notes: str


def allowed_types_for(kind: str) -> list[str]:
    return sorted(ALLOWED_TYPES.get(kind, frozenset()))


def record(session: Session, draft: ManualTransaction, today: date) -> Decimal:
    """Validates the draft, writes the Transaction, and returns the Position's new units."""
    position = _position_for(session, draft.position_id)
    validate(draft, position.instrument.kind, today)
    _write(session, position, draft)
    return position.units()


def validate(draft: ManualTransaction, kind: str, today: date) -> None:
    _ensure_accepted(draft.type, kind)
    _ensure_not_future(draft.date, today)
    _ensure_positive_units(draft.units)
    _ensure_cost(draft)


def _position_for(session: Session, position_id: uuid.UUID) -> Position:
    position = session.scalars(select(Position).where(Position.id == position_id)).first()
    if position is None:
        raise StatementRejectedError("position_not_found", "That Position no longer exists.")
    return position


def _ensure_accepted(entry_type: str, kind: str) -> None:
    if entry_type in ALLOWED_TYPES.get(kind, frozenset()):
        return
    allowed = ", ".join(allowed_types_for(kind)) or "none"
    raise StatementRejectedError(
        "unexpected_type",
        f"A {kind} Position doesn't accept a {entry_type} Transaction. Accepted: {allowed}.",
    )


def _ensure_not_future(entry_date: date, today: date) -> None:
    if entry_date > today:
        raise StatementRejectedError("future_date", "A Transaction can't be dated in the future.")


def _ensure_positive_units(units: Decimal) -> None:
    if units <= ZERO:
        raise StatementRejectedError("non_positive_units", "Units must be greater than zero.")


def _ensure_not_negative(amount: Decimal | None) -> None:
    if amount is not None and amount < ZERO:
        raise StatementRejectedError("negative_cost", "Cost can't be negative.")


def _ensure_buying_cost(draft: ManualTransaction) -> None:
    if draft.type in BUYING_TYPES and draft.amount is None:
        raise StatementRejectedError(
            "cost_required", "This Transaction needs the cost it was made at."
        )


def _ensure_cost(draft: ManualTransaction) -> None:
    _ensure_not_negative(draft.amount)
    _ensure_buying_cost(draft)


def _write(session: Session, position: Position, draft: ManualTransaction) -> None:
    transaction = Transaction(
        id=uuid.uuid4(),
        position=position,
        import_id=None,
        date=draft.date,
        kind=draft.type.upper(),
        description=f"Manual {draft.type}",
        units=_signed_units(draft),
        amount=draft.amount,
        nav=None,
        notes=draft.notes or None,
        synthetic=False,
        fingerprint=None,
    )
    session.add(transaction)
    _apply_to_position(position, transaction, draft)
    session.flush()


def _signed_units(draft: ManualTransaction) -> Decimal:
    return -draft.units if draft.type in SELLING_TYPES else draft.units


def _apply_to_position(
    position: Position, transaction: Transaction, draft: ManualTransaction
) -> None:
    if draft.type in SELLING_TYPES:
        position.dispose(draft.units)
        return
    position.acquire(transaction, draft.amount or ZERO)
