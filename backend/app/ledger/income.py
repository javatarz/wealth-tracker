"""Recording Income against a Position (ADR 0003).

Income is value a Position generates without changing its quantity. Every event
carries a disposition: **withdrawn** Income crosses the Portfolio boundary and is
a Cash Flow, while **reinvested** Income stays inside and produces a Transaction
that raises the Position's quantity. The two dispositions are the same record
with a flag, so the reporting engine can consume them uniformly.
"""

import hashlib
import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.statement_rejection import StatementRejectedError
from app.ledger.models import PAISE, ZERO, Income, Position, Transaction

DIVIDEND = "dividend"
IDCW = "idcw"
INTEREST = "interest"
RENT = "rent"

INCOME_TYPES: frozenset[str] = frozenset({DIVIDEND, IDCW, INTEREST, RENT})

# Only quantity-bearing Positions can turn Income into units (ADR 0003).
REINVESTABLE_KINDS: frozenset[str] = frozenset({"mutual_fund", "equity"})

REINVESTMENT = "PURCHASE"
INCOME_FINGERPRINT_VERSION = "v1"

# Units are quantities, reported to three decimals like a fund statement.
UNITS_PLACES = Decimal("0.001")


@dataclass(frozen=True)
class IncomeDraft:
    """An Income event as the browser submitted it, before any validation."""

    position_id: uuid.UUID
    kind: str
    date: date
    gross_amount: Decimal
    tax_deducted: Decimal | None
    reinvested: bool
    nav: Decimal | None


def allowed_income_types() -> list[str]:
    return sorted(INCOME_TYPES)


def reinvestment_allowed(instrument_kind: str) -> bool:
    return instrument_kind in REINVESTABLE_KINDS


def record(session: Session, draft: IncomeDraft, today: date) -> Income:
    """Validates the draft, writes the Income event, and returns it."""
    position = _position_for(session, draft.position_id)
    validate(draft, position.instrument.kind, today)
    income = _write(session, position, draft)
    session.flush()
    return income


def validate(draft: IncomeDraft, instrument_kind: str, today: date) -> None:
    _ensure_known_kind(draft.kind)
    _ensure_not_future(draft.date, today)
    _ensure_positive_gross(draft.gross_amount)
    _ensure_tax(draft.gross_amount, draft.tax_deducted)
    _ensure_reinvestment(draft, instrument_kind)


def _position_for(session: Session, position_id: uuid.UUID) -> Position:
    position = session.scalars(select(Position).where(Position.id == position_id)).first()
    if position is None:
        raise StatementRejectedError("position_not_found", "That Position no longer exists.")
    return position


def _ensure_known_kind(kind: str) -> None:
    if kind in INCOME_TYPES:
        return
    accepted = ", ".join(allowed_income_types())
    raise StatementRejectedError(
        "unexpected_income_type", f"Unknown Income type. Accepted: {accepted}."
    )


def _ensure_not_future(entry_date: date, today: date) -> None:
    if entry_date > today:
        raise StatementRejectedError("future_date", "Income can't be dated in the future.")


def _ensure_positive_gross(gross: Decimal) -> None:
    if gross <= ZERO:
        raise StatementRejectedError(
            "non_positive_amount", "Gross amount must be greater than zero."
        )


def _ensure_tax(gross: Decimal, tax: Decimal | None) -> None:
    if tax is None or ZERO <= tax < gross:
        return
    raise StatementRejectedError(
        "invalid_tax", "Tax deducted can't be negative or more than the gross amount."
    )


def _ensure_reinvestment(draft: IncomeDraft, instrument_kind: str) -> None:
    if not draft.reinvested:
        return
    _ensure_reinvestable(instrument_kind)
    _ensure_nav(draft.nav)


def _ensure_reinvestable(instrument_kind: str) -> None:
    if reinvestment_allowed(instrument_kind):
        return
    raise StatementRejectedError(
        "reinvestment_not_supported",
        f"A {instrument_kind} Position can't reinvest Income; record it as withdrawn.",
    )


def _ensure_nav(nav: Decimal | None) -> None:
    if nav is not None and nav > ZERO:
        return
    raise StatementRejectedError("nav_required", "Reinvested Income needs a positive NAV.")


def _write(session: Session, position: Position, draft: IncomeDraft) -> Income:
    tax = draft.tax_deducted or ZERO
    income = Income(
        id=uuid.uuid4(),
        position=position,
        date=draft.date,
        kind=draft.kind,
        gross_amount=draft.gross_amount,
        tax_deducted=tax,
        net_amount=(draft.gross_amount - tax).quantize(PAISE),
        withdrawn=not draft.reinvested,
        fingerprint=_fingerprint(position, draft),
    )
    session.add(income)
    _reinvest(session, income, draft)
    return income


def _reinvest(session: Session, income: Income, draft: IncomeDraft) -> None:
    """Reinvested Income buys units: a Purchase Transaction priced at NAV (ADR 0003)."""
    if not draft.reinvested:
        return
    nav = _required_nav(draft.nav)
    units = _units_for(income.net_amount, nav)
    transaction = Transaction(
        id=uuid.uuid4(),
        position=income.position,
        import_id=None,
        date=income.date,
        kind=REINVESTMENT,
        description=f"Reinvestment of {income.kind} Income",
        units=units,
        amount=income.net_amount,
        nav=nav,
        notes=None,
        income_id=income.id,
        synthetic=False,
        fingerprint=None,
    )
    session.add(transaction)
    income.position.acquire(transaction, income.net_amount)


def _required_nav(nav: Decimal | None) -> Decimal:
    if nav is None:  # validated before we get here
        raise StatementRejectedError("nav_required", "Reinvested Income needs a positive NAV.")
    return nav


def _units_for(net_amount: Decimal, nav: Decimal) -> Decimal:
    """Units = net amount ÷ NAV, the quantity the reinvestment bought (issue #35)."""
    return (net_amount / nav).quantize(UNITS_PLACES)


def _fingerprint(position: Position, draft: IncomeDraft) -> str:
    parts = (
        INCOME_FINGERPRINT_VERSION,
        position.ledger_key,
        draft.date.isoformat(),
        draft.kind,
        draft.gross_amount,
        draft.tax_deducted,
        draft.reinvested,
    )
    return hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()
