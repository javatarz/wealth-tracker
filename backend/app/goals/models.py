"""Goals: a future financial need funded from a designated set of Accounts (CONTEXT.md)."""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.ledger.models import Account, DecimalText

MAX_GOAL_NAME = 100

goal_accounts = Table(
    "goal_accounts",
    Base.metadata,
    Column("goal_id", ForeignKey("goals.id", ondelete="CASCADE"), primary_key=True),
    Column("account_id", ForeignKey("accounts.id"), primary_key=True),
)


class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    household_member_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("household_members.id"))
    name: Mapped[str] = mapped_column(String(MAX_GOAL_NAME))
    target_amount: Mapped[Decimal] = mapped_column(DecimalText())
    target_date: Mapped[date]
    accounts: Mapped[list[Account]] = relationship(secondary=goal_accounts)


def account_label(account: Account) -> str:
    return f"{account.institution} · {account.number}"
