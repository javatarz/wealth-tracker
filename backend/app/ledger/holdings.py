"""Where a statement's Scheme lives in the ledger, and what the ledger already holds there."""

import uuid
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Self

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.core.statement_preview import Folio, Scheme
from app.core.statement_preview import Transaction as StatementTransaction
from app.ledger.fingerprint import transaction_fingerprint
from app.ledger.models import Account, Instrument, Position, Transaction

Fingerprinted = tuple[StatementTransaction, str]


@dataclass(frozen=True)
class Holding:
    """One Scheme in one folio: the natural key of a Position."""

    institution: str
    folio: str
    identity: str

    @classmethod
    def of(cls, folio: Folio, scheme: Scheme) -> Self:
        return cls(folio.amc, folio.folio, instrument_identity(scheme))

    @property
    def key(self) -> str:
        """Matches `Position.ledger_key`, so fingerprints agree before and after writing."""
        return f"{self.institution}|{self.folio}|{self.identity}"

    def units_until(self, session: Session, day: date) -> list[Decimal]:
        query = self._narrow(select(Transaction.units).join(Transaction.position))
        return list(session.scalars(query.where(Transaction.date <= day)))

    def position_id(self, session: Session) -> uuid.UUID | None:
        return session.scalar(self._narrow(select(Position.id)))

    def _narrow[R](self, query: Select[R]) -> Select[R]:
        return (
            query.join(Position.account)
            .join(Position.instrument)
            .where(
                Account.institution == self.institution,
                Account.number == self.folio,
                Instrument.identity == self.identity,
            )
        )


def instrument_identity(scheme: Scheme) -> str:
    """AMFI code identifies a scheme (ADR 0015); statements that omit it fall back."""
    return scheme.amfi or scheme.isin or f"{scheme.rta}:{scheme.rta_code}"


def unseen_rows(
    session: Session, holding: Holding, rows: Iterable[StatementTransaction]
) -> list[Fingerprinted]:
    """The statement's rows, oldest first, minus those already in the ledger (ADR 0006)."""
    occurrences: Counter[str] = Counter()
    fingerprinted = [
        _fingerprinted(holding.key, row, occurrences) for row in sorted(rows, key=_row_date)
    ]
    return [pair for pair in fingerprinted if not _known(session, pair[1])]


def _fingerprinted(key: str, row: StatementTransaction, seen: Counter[str]) -> Fingerprinted:
    identical = transaction_fingerprint(key, row, 0)
    seen[identical] += 1
    return row, transaction_fingerprint(key, row, seen[identical])


def _known(session: Session, fingerprint: str) -> bool:
    query = select(Transaction.id).where(Transaction.fingerprint == fingerprint)
    return session.scalar(query) is not None


def _row_date(row: StatementTransaction) -> date:
    return row.date
