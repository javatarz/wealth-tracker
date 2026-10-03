"""Write a parsed statement into the ledger (ADR 0001, 0006, 0015, 0027)."""

import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import Base
from app.core.statement_preview import Folio, Scheme, StatementPreview
from app.core.statement_preview import Transaction as StatementTransaction
from app.core.statement_rejection import StatementRejectedError
from app.ledger.holdings import instrument_identity
from app.ledger.models import (
    PAISE,
    ZERO,
    Account,
    HouseholdMember,
    Import,
    Instrument,
    Position,
    ReconciliationDecision,
    Transaction,
)
from app.ledger.reconciliation import Action, Decisions, SchemePlan, period_date, plan_statement

logger = logging.getLogger(__name__)

DEFAULT_MEMBER_NAME = "Me"
FOLIO_ACCOUNT = "mf_folio"
MUTUAL_FUND = "mutual_fund"
OPENING_BALANCE = "OPENING_BALANCE"
RECONCILIATION_ADJUSTMENT = "RECONCILIATION_ADJUSTMENT"


@dataclass(frozen=True)
class StatementCommit:
    statement: StatementPreview
    content_hash: str
    decisions: Decisions


@dataclass(frozen=True)
class CommittedImport:
    import_id: uuid.UUID
    positions: int
    transactions: int


@dataclass(frozen=True)
class DecisionsNeeded:
    """Nothing was written: every mismatch needs an Action first (ADR 0027)."""

    mismatches: list[SchemePlan]


CommitOutcome = CommittedImport | DecisionsNeeded


def commit_atomically(session: Session, request: StatementCommit) -> CommitOutcome:
    """Commits the whole statement or, if anything fails, none of it."""
    try:
        return _commit_in_transaction(session, request)
    except SQLAlchemyError as exc:
        logger.exception("Committing an import failed; it was rolled back")
        raise StatementRejectedError(
            "commit_failed", "The import couldn't be saved, so nothing was imported."
        ) from exc


def _commit_in_transaction(session: Session, request: StatementCommit) -> CommitOutcome:
    with session.begin():
        return commit_statement(session, request)


def commit_statement(session: Session, request: StatementCommit) -> CommitOutcome:
    """Adds the statement to the session. The caller owns the database transaction."""
    plans = plan_statement(session, request.statement)
    mismatches = [plan for plan in plans if plan.mismatched]
    previous = _revisitable_import(session, request.content_hash, mismatches)
    if any(plan.holding.key not in request.decisions for plan in mismatches):
        return DecisionsNeeded(mismatches)
    batch = previous or _added(session, _new_import(session, request))
    return StatementWriter(session, batch, request.decisions).write(plans)


def _revisitable_import(
    session: Session, content_hash: str, mismatches: list[SchemePlan]
) -> Import | None:
    """Re-importing a statement is only useful to revisit its mismatches (ADR 0027)."""
    previous = session.scalars(select(Import).where(Import.content_hash == content_hash)).first()
    if previous and not mismatches:
        raise StatementRejectedError(
            "already_imported", "This statement has already been imported."
        )
    return previous


def _default_member(session: Session) -> HouseholdMember:
    member = session.scalars(select(HouseholdMember).limit(1)).first()
    return member or _added(session, HouseholdMember(id=uuid.uuid4(), name=DEFAULT_MEMBER_NAME))


def _new_import(session: Session, request: StatementCommit) -> Import:
    statement = request.statement
    period = statement.statement_period
    return Import(
        id=uuid.uuid4(),
        household_member_id=_default_member(session).id,
        content_hash=request.content_hash,
        source=statement.file_type,
        statement_type=statement.cas_type,
        period_from=period_date(period.from_),
        period_to=period_date(period.to),
        parser_version=statement.parser.version,
        imported_at=datetime.now(UTC),
    )


def _added[E: Base](session: Session, entity: E) -> E:
    session.add(entity)
    return entity


class StatementWriter:
    def __init__(self, session: Session, batch: Import, decisions: Decisions) -> None:
        self._session = session
        self._batch = batch
        self._decisions = decisions
        self._positions = 0
        self._transactions = 0

    def write(self, plans: list[SchemePlan]) -> CommittedImport:
        for plan in plans:
            _WRITERS[self._action(plan)](self, plan)
        return CommittedImport(self._batch.id, self._positions, self._transactions)

    def write_holding(self, plan: SchemePlan) -> Position:
        position = self._position(plan.folio, plan.scheme)
        self._seed_opening_balance(position, plan)
        for row, fingerprint in plan.rows:
            self._write_row(position, row, fingerprint)
        self._positions += 1
        return position

    def trust_ledger(self, plan: SchemePlan) -> None:
        position = self.write_holding(plan)
        self._decide(plan, position.id, None)

    def trust_statement(self, plan: SchemePlan) -> None:
        position = self.write_holding(plan)
        cost = _adjustment_cost(position, plan)
        self._book(self._adjustment(position, plan), cost)
        self._decide(plan, position.id, cost if plan.delta > ZERO else None)

    def leave_out(self, plan: SchemePlan) -> None:
        self._decide(plan, plan.holding.position_id(self._session), None)

    def _action(self, plan: SchemePlan) -> Action | None:
        return self._decisions[plan.holding.key] if plan.mismatched else None

    def _seed_opening_balance(self, position: Position, plan: SchemePlan) -> None:
        if not plan.seeds_opening:
            return
        opening = self._synthetic(position, OPENING_BALANCE, plan.scheme.open)
        opening.nav = _opening_nav(plan.scheme)
        self._record(opening)

    def _adjustment(self, position: Position, plan: SchemePlan) -> Transaction:
        adjustment = self._synthetic(position, RECONCILIATION_ADJUSTMENT, plan.delta)
        adjustment.date = self._batch.period_to
        adjustment.nav = plan.scheme.valuation.nav
        return adjustment

    def _synthetic(self, position: Position, kind: str, units: Decimal) -> Transaction:
        return Transaction(
            id=uuid.uuid4(),
            position=position,
            import_id=self._batch.id,
            date=self._batch.period_from,
            kind=kind,
            description=kind.replace("_", " ").capitalize(),
            units=units,
            amount=None,
            nav=None,
            synthetic=True,
            fingerprint=None,
        )

    def _write_row(self, position: Position, row: StatementTransaction, fingerprint: str) -> None:
        self._record(
            Transaction(
                id=uuid.uuid4(),
                position=position,
                import_id=self._batch.id,
                date=row.date,
                kind=row.type,
                description=row.description,
                units=row.units or ZERO,
                amount=row.amount,
                nav=row.nav,
                synthetic=False,
                fingerprint=fingerprint,
            )
        )

    def _decide(
        self, plan: SchemePlan, position_id: uuid.UUID | None, cost: Decimal | None
    ) -> None:
        self._session.add(
            ReconciliationDecision(
                id=uuid.uuid4(),
                import_id=self._batch.id,
                position_id=position_id,
                scheme=plan.scheme.scheme,
                holding=plan.holding.key,
                action=self._decisions[plan.holding.key],
                statement_units=plan.scheme.close,
                derived_units=plan.derived_units,
                delta=plan.delta,
                cost_basis=cost,
                parser_version=self._batch.parser_version,
                decided_at=datetime.now(UTC),
            )
        )

    def _record(self, transaction: Transaction) -> None:
        self._book(transaction, _acquisition_cost(transaction))

    def _book(self, transaction: Transaction, cost: Decimal) -> None:
        self._session.add(transaction)
        self._transactions += 1
        _LOT_EFFECTS[int(transaction.units.compare(ZERO))](transaction, cost)

    def _account(self, folio: Folio) -> Account:
        member_id = self._batch.household_member_id
        query = select(Account).where(
            Account.household_member_id == member_id,
            Account.kind == FOLIO_ACCOUNT,
            Account.institution == folio.amc,
            Account.number == folio.folio,
        )
        account = Account(
            id=uuid.uuid4(),
            household_member_id=member_id,
            kind=FOLIO_ACCOUNT,
            institution=folio.amc,
            number=folio.folio,
        )
        return self._session.scalars(query).first() or _added(self._session, account)

    def _instrument(self, scheme: Scheme) -> Instrument:
        identity = instrument_identity(scheme)
        query = select(Instrument).where(
            Instrument.kind == MUTUAL_FUND, Instrument.identity == identity
        )
        instrument = Instrument(
            id=uuid.uuid4(),
            kind=MUTUAL_FUND,
            identity=identity,
            name=scheme.scheme,
            amfi_code=scheme.amfi,
            isin=scheme.isin,
        )
        return self._session.scalars(query).first() or _added(self._session, instrument)

    def _position(self, folio: Folio, scheme: Scheme) -> Position:
        account = self._account(folio)
        instrument = self._instrument(scheme)
        query = select(Position).where(
            Position.account_id == account.id, Position.instrument_id == instrument.id
        )
        position = Position(id=uuid.uuid4(), account=account, instrument=instrument)
        return self._session.scalars(query).first() or _added(self._session, position)


_WRITERS: dict[Action | None, Callable[[StatementWriter, SchemePlan], object]] = {
    None: StatementWriter.write_holding,
    Action.TRUST_LEDGER: StatementWriter.trust_ledger,
    Action.TRUST_STATEMENT: StatementWriter.trust_statement,
    Action.LEAVE_OUT: StatementWriter.leave_out,
}


def _opening_nav(scheme: Scheme) -> Decimal:
    navs = (row.nav for row in sorted(scheme.transactions, key=_row_date) if row.nav is not None)
    return next(navs, scheme.valuation.nav)


def _adjustment_cost(position: Position, plan: SchemePlan) -> Decimal:
    """The printed cost not yet in the ledger, else Δ at the closing NAV (ADR 0027)."""
    valuation = plan.scheme.valuation
    by_nav = (plan.delta * valuation.nav).quantize(PAISE)
    gap = by_nav if valuation.cost is None else valuation.cost - position.cost_basis()
    return gap if gap > ZERO else by_nav


def _row_date(row: StatementTransaction) -> date:
    return row.date


def _acquire(transaction: Transaction, cost: Decimal) -> None:
    transaction.position.acquire(transaction, cost)


def _dispose(transaction: Transaction, _cost: Decimal) -> None:
    transaction.position.dispose(-transaction.units)


def _no_lot_effect(_transaction: Transaction, _cost: Decimal) -> None:
    return


def _acquisition_cost(transaction: Transaction) -> Decimal:
    priced = (transaction.units * (transaction.nav or ZERO)).quantize(PAISE)
    return priced if transaction.amount is None else abs(transaction.amount)


_LOT_EFFECTS: dict[int, Callable[[Transaction, Decimal], None]] = {
    1: _acquire,
    -1: _dispose,
    0: _no_lot_effect,
}
