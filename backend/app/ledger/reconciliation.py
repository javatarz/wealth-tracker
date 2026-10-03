"""Compare a statement's printed closing units with what the ledger would derive (ADR 0027)."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy.orm import Session

from app.core.statement_preview import Folio, Scheme, StatementPreview
from app.ledger.holdings import Fingerprinted, Holding, unseen_rows
from app.ledger.models import ZERO

_PERIOD_FORMAT = "%d-%b-%Y"


class Action(StrEnum):
    TRUST_LEDGER = "trust_ledger"
    TRUST_STATEMENT = "trust_statement"
    LEAVE_OUT = "leave_out"


Decisions = Mapping[str, Action]
"""The user's chosen Action for each mismatched holding, keyed by `Holding.key`."""


@dataclass(frozen=True)
class SchemePlan:
    """What committing one Scheme would add to the ledger, and whether it then reconciles."""

    folio: Folio
    scheme: Scheme
    holding: Holding
    history: list[Decimal]
    rows: list[Fingerprinted]

    @property
    def seeds_opening(self) -> bool:
        """Opening balances anchor a Position with no history up to this statement (ADR 0001)."""
        return not self.history and self.scheme.open != ZERO

    @property
    def derived_units(self) -> Decimal:
        opening = self.scheme.open if self.seeds_opening else ZERO
        added = sum((row.units or ZERO for row, _ in self.rows), ZERO)
        return sum(self.history, ZERO) + opening + added

    @property
    def delta(self) -> Decimal:
        """Printed minus derived: the units a Trust-the-statement adjustment would add."""
        return self.scheme.close - self.derived_units

    @property
    def mismatched(self) -> bool:
        return self.delta != ZERO


def plan_statement(session: Session, statement: StatementPreview) -> list[SchemePlan]:
    planner = _Planner(session, period_date(statement.statement_period.to))
    return [planner.plan(folio, scheme) for folio in statement.folios for scheme in folio.schemes]


def period_date(printed: str) -> date:
    return datetime.strptime(printed, _PERIOD_FORMAT).replace(tzinfo=UTC).date()


class _Planner:
    def __init__(self, session: Session, closing: date) -> None:
        self._session = session
        self._closing = closing

    def plan(self, folio: Folio, scheme: Scheme) -> SchemePlan:
        holding = Holding.of(folio, scheme)
        return SchemePlan(
            folio=folio,
            scheme=scheme,
            holding=holding,
            history=holding.units_until(self._session, self._closing),
            rows=unseen_rows(self._session, holding, scheme.transactions),
        )
