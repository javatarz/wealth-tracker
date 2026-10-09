"""The single default Household Member, seeded on first use (no member picker in v1)."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ledger.models import HouseholdMember

DEFAULT_MEMBER_NAME = "Me"


def default_member(session: Session) -> HouseholdMember:
    member = session.scalars(select(HouseholdMember).limit(1)).first()
    if member is not None:
        return member
    seeded = HouseholdMember(id=uuid.uuid4(), name=DEFAULT_MEMBER_NAME)
    session.add(seeded)
    return seeded
