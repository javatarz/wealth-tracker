"""Goals and their projection inputs (CONTEXT.md, ADR 0009, 0022)."""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.ledger.models import Account, DecimalText, Position

MAX_GOAL_NAME = 100
MAX_STRATEGY = 16
MAX_FREQUENCY = 16
MAX_DIRECTION = 16
MAX_SCHEDULE_DESCRIPTION = 255

CAGR = "cagr"
TRAILING_WINDOW = "trailing_window"
CONTRIBUTION = "contribution"
REDEMPTION = "redemption"
MONTHLY = "monthly"
YEARLY = "yearly"
ONE_OFF = "one_off"

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
    projection_strategy: Mapped[str | None] = mapped_column(String(MAX_STRATEGY))
    cagr_rate: Mapped[Decimal | None] = mapped_column(DecimalText())
    trailing_window_years: Mapped[int | None]
    accounts: Mapped[list[Account]] = relationship(secondary=goal_accounts)


class ScheduledTransaction(Base):
    """A known future flow against a Position (CONTEXT.md). Feeds Goal Projections (ADR 0022)."""

    __tablename__ = "scheduled_transactions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    position_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("positions.id"), index=True)
    description: Mapped[str] = mapped_column(String(MAX_SCHEDULE_DESCRIPTION))
    direction: Mapped[str] = mapped_column(String(MAX_DIRECTION))
    frequency: Mapped[str] = mapped_column(String(MAX_FREQUENCY))
    amount: Mapped[Decimal] = mapped_column(DecimalText())
    start_date: Mapped[date]
    end_date: Mapped[date | None]
    escalation_rate: Mapped[Decimal] = mapped_column(DecimalText())

    position: Mapped[Position] = relationship()


def account_label(account: Account) -> str:
    return f"{account.institution} · {account.number}"
