"""Read the ledger's Positions for API responses (#26, #28)."""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, selectinload

from app.ledger.asset_classes import ASSET_CLASSES, LABELS
from app.ledger.models import Account, HouseholdMember, Instrument, Position

DEFAULT_MEMBER_NAME = "Me"


def asset_class_options() -> list[tuple[str, str]]:
    """Every Asset Class in dropdown order, as (value, label)."""
    return [(value, LABELS[value]) for value in ASSET_CLASSES]


def list_positions(
    session: Session,
    household_member_id: UUID | None = None,
    asset_class: str | None = None,
) -> Sequence[Position]:
    return session.scalars(_positions_query(household_member_id, asset_class)).all()


def list_memberships(session: Session) -> Sequence[HouseholdMember]:
    """Household Members that own at least one Account, in name order."""
    owned = select(Account.household_member_id)
    query = select(HouseholdMember).where(HouseholdMember.id.in_(owned))
    return session.scalars(query.order_by(HouseholdMember.name)).all()


def ensure_default_member(session: Session) -> HouseholdMember:
    """The single Household Member the import auto-seeds on first run (ADR 0001)."""
    member = session.scalars(select(HouseholdMember).limit(1)).first()
    if member is not None:
        return member
    seeded = HouseholdMember(name=DEFAULT_MEMBER_NAME)
    session.add(seeded)
    session.flush()
    return seeded


def _positions_query(household_member_id: UUID | None, asset_class: str | None) -> Select[Position]:
    query = _base_query()
    return _filter_by_member(_filter_by_class(query, asset_class), household_member_id)


def _base_query() -> Select[Position]:
    return (
        select(Position)
        .join(Position.account)
        .join(Position.instrument)
        .options(selectinload(Position.transactions), selectinload(Position.lots))
        .order_by(Account.institution, Account.number, Instrument.name)
    )


def _filter_by_member(
    query: Select[Position], household_member_id: UUID | None
) -> Select[Position]:
    if household_member_id is None:
        return query
    return query.where(Account.household_member_id == household_member_id)


def _filter_by_class(query: Select[Position], asset_class: str | None) -> Select[Position]:
    if asset_class is None:
        return query
    return query.where(Instrument.asset_class == asset_class)
