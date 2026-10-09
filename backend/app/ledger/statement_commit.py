"""Write a parsed statement into the ledger (ADR 0001, 0006, 0015)."""

import logging
import uuid
from collections import Counter
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
from app.ledger.fingerprint import transaction_fingerprint
from app.ledger.models import (
    PAISE,
    ZERO,
    Account,
    HouseholdMember,
    Import,
    Instrument,
    Position,
    Transaction,
)

logger = logging.getLogger(__name__)

DEFAULT_MEMBER_NAME = "Me"
FOLIO_ACCOUNT = "mf_folio"
MUTUAL_FUND = "mutual_fund"
OPENING_BALANCE = "OPENING_BALANCE"
_PERIOD_FORMAT = "%d-%b-%Y"


@dataclass(frozen=True)
class CommittedImport:
    import_id: uuid.UUID
    positions: int
    transactions: int


def commit_atomically(
    session: Session, statement: StatementPreview, content_hash: str
) -> CommittedImport:
    """Commits the whole statement or, if anything fails, none of it."""
    try:
        return _commit_in_transaction(session, statement, content_hash)
    except SQLAlchemyError as exc:
        logger.exception("Committing an import failed; it was rolled back")
        raise StatementRejectedError(
            "commit_failed", "The import couldn't be saved, so nothing was imported."
        ) from exc


def _commit_in_transaction(
    session: Session, statement: StatementPreview, content_hash: str
) -> CommittedImport:
    with session.begin():
        return commit_statement(session, statement, content_hash)


def commit_statement(
    session: Session, statement: StatementPreview, content_hash: str
) -> CommittedImport:
    """Adds the statement to the session. The caller owns the database transaction."""
    _ensure_not_imported(session, content_hash)
    batch = _new_import(statement, content_hash, _default_member(session))
    session.add(batch)
    writer = StatementWriter(session, batch)
    for folio in statement.folios:
        writer.write_folio(folio)
    written = session.scalars(select(Transaction.id).where(Transaction.import_id == batch.id))
    return CommittedImport(
        import_id=batch.id,
        positions=sum(len(folio.schemes) for folio in statement.folios),
        transactions=len(written.all()),
    )


def _ensure_not_imported(session: Session, content_hash: str) -> None:
    if session.scalars(select(Import).where(Import.content_hash == content_hash)).first():
        raise StatementRejectedError(
            "already_imported", "This statement has already been imported."
        )


def _default_member(session: Session) -> HouseholdMember:
    member = session.scalars(select(HouseholdMember).limit(1)).first()
    return member or _added(session, HouseholdMember(id=uuid.uuid4(), name=DEFAULT_MEMBER_NAME))


def _new_import(statement: StatementPreview, content_hash: str, member: HouseholdMember) -> Import:
    period = statement.statement_period
    return Import(
        id=uuid.uuid4(),
        household_member_id=member.id,
        content_hash=content_hash,
        source=statement.file_type,
        statement_type=statement.cas_type,
        period_from=_period_date(period.from_),
        period_to=_period_date(period.to),
        parser_version=statement.parser.version,
        imported_at=datetime.now(UTC),
    )


def _period_date(printed: str) -> date:
    return datetime.strptime(printed, _PERIOD_FORMAT).replace(tzinfo=UTC).date()


def _added[E: Base](session: Session, entity: E) -> E:
    session.add(entity)
    return entity


class StatementWriter:
    def __init__(self, session: Session, batch: Import) -> None:
        self._session = session
        self._batch = batch

    def write_folio(self, folio: Folio) -> None:
        account = self._account(folio)
        for scheme in folio.schemes:
            self._write_scheme(account, scheme)

    def _write_scheme(self, account: Account, scheme: Scheme) -> None:
        position = self._position(account, self._instrument(scheme))
        rows = sorted(scheme.transactions, key=_row_date)
        self._seed_opening_balance(position, scheme)
        occurrences: Counter[str] = Counter()
        for row in rows:
            self._write_row(position, row, occurrences)

    def _seed_opening_balance(self, position: Position, scheme: Scheme) -> None:
        if position.transactions or scheme.open == ZERO:
            return
        self._record(
            Transaction(
                id=uuid.uuid4(),
                position=position,
                import_id=self._batch.id,
                date=self._batch.period_from,
                kind=OPENING_BALANCE,
                description="Opening balance",
                units=scheme.open,
                amount=None,
                nav=_opening_nav(scheme),
                synthetic=True,
                fingerprint=None,
            )
        )

    def _write_row(self, position: Position, row: StatementTransaction, seen: Counter[str]) -> None:
        identical = transaction_fingerprint(position.ledger_key, row, 0)
        seen[identical] += 1
        fingerprint = transaction_fingerprint(position.ledger_key, row, seen[identical])
        if self._known(fingerprint):
            return
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

    def _record(self, transaction: Transaction) -> None:
        self._session.add(transaction)
        _LOT_EFFECTS[int(transaction.units.compare(ZERO))](transaction)

    def _known(self, fingerprint: str) -> bool:
        query = select(Transaction.id).where(Transaction.fingerprint == fingerprint)
        return self._session.scalar(query) is not None

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
        identity = _instrument_identity(scheme)
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

    def _position(self, account: Account, instrument: Instrument) -> Position:
        query = select(Position).where(
            Position.account_id == account.id, Position.instrument_id == instrument.id
        )
        position = Position(id=uuid.uuid4(), account=account, instrument=instrument)
        return self._session.scalars(query).first() or _added(self._session, position)


def _instrument_identity(scheme: Scheme) -> str:
    """AMFI code identifies a scheme (ADR 0015); statements that omit it fall back."""
    return scheme.amfi or scheme.isin or f"{scheme.rta}:{scheme.rta_code}"


def _opening_nav(scheme: Scheme) -> Decimal:
    navs = (row.nav for row in sorted(scheme.transactions, key=_row_date) if row.nav is not None)
    return next(navs, scheme.valuation.nav)


def _row_date(row: StatementTransaction) -> date:
    return row.date


def _acquire(transaction: Transaction) -> None:
    transaction.position.acquire(transaction, _acquisition_cost(transaction))


def _dispose(transaction: Transaction) -> None:
    transaction.position.dispose(-transaction.units)


def _no_lot_effect(_transaction: Transaction) -> None:
    return


def _acquisition_cost(transaction: Transaction) -> Decimal:
    priced = (transaction.units * (transaction.nav or ZERO)).quantize(PAISE)
    return priced if transaction.amount is None else abs(transaction.amount)


_LOT_EFFECTS: dict[int, Callable[[Transaction], None]] = {
    1: _acquire,
    -1: _dispose,
    0: _no_lot_effect,
}
