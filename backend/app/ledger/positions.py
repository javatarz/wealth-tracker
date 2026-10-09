from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.ledger.models import Account, Instrument, Position


def list_positions(session: Session) -> Sequence[Position]:
    query = (
        select(Position)
        .join(Position.account)
        .join(Position.instrument)
        .options(selectinload(Position.transactions), selectinload(Position.lots))
        .order_by(Account.institution, Account.number, Instrument.name)
    )
    return session.scalars(query).all()
