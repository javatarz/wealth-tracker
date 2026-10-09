"""The ledger: who owns what, where, and every Transaction that got them there (ADR 0001)."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import override

from sqlalchemy import Dialect, ForeignKey, String, TypeDecorator, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

PAISE = Decimal("0.01")
ZERO = Decimal(0)


class DecimalText(TypeDecorator[Decimal]):
    """Stores decimals as text so SQLite never rounds them through a float."""

    impl = String(40)
    cache_ok = True

    @override
    def process_bind_param(self, value: Decimal | None, dialect: Dialect) -> str | None:
        return None if value is None else str(value)

    @override
    def process_result_value(self, value: str | None, dialect: Dialect) -> Decimal | None:
        return None if value is None else Decimal(value)


class HouseholdMember(Base):
    __tablename__ = "household_members"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100))


class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (UniqueConstraint("household_member_id", "kind", "institution", "number"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    household_member_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("household_members.id"))
    kind: Mapped[str] = mapped_column(String(32))
    institution: Mapped[str] = mapped_column(String(255))
    number: Mapped[str] = mapped_column(String(64))


class Instrument(Base):
    __tablename__ = "instruments"
    __table_args__ = (UniqueConstraint("kind", "identity"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    kind: Mapped[str] = mapped_column(String(32))
    identity: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(255))
    amfi_code: Mapped[str | None] = mapped_column(String(16))
    isin: Mapped[str | None] = mapped_column(String(12))


class Import(Base):
    __tablename__ = "imports"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    household_member_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("household_members.id"))
    content_hash: Mapped[str] = mapped_column(String(64), unique=True)
    source: Mapped[str] = mapped_column(String(16))
    statement_type: Mapped[str] = mapped_column(String(16))
    period_from: Mapped[date]
    period_to: Mapped[date]
    parser_version: Mapped[str] = mapped_column(String(32))
    imported_at: Mapped[datetime]


class Position(Base):
    __tablename__ = "positions"
    __table_args__ = (UniqueConstraint("account_id", "instrument_id"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounts.id"))
    instrument_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("instruments.id"))

    account: Mapped[Account] = relationship()
    instrument: Mapped[Instrument] = relationship()
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="position")
    lots: Mapped[list["Lot"]] = relationship(order_by="(Lot.acquired_on, Lot.id)")
    income: Mapped[list["Income"]] = relationship(
        back_populates="position", order_by="(Income.date, Income.id)"
    )

    @property
    def ledger_key(self) -> str:
        account = self.account
        return f"{account.institution}|{account.number}|{self.instrument.identity}"

    def units(self) -> Decimal:
        return sum((transaction.units for transaction in self.transactions), ZERO)

    def cost_basis(self) -> Decimal:
        return sum((lot.remaining_cost for lot in self.lots), ZERO)

    def acquire(self, transaction: "Transaction", cost: Decimal) -> None:
        self.lots.append(Lot.acquired_by(transaction, cost))

    def dispose(self, units: Decimal) -> None:
        remaining = units
        for lot in self.lots:
            remaining = lot.consume(remaining)


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    position_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("positions.id"), index=True)
    import_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("imports.id"))
    date: Mapped[date]
    kind: Mapped[str] = mapped_column(String(32))
    description: Mapped[str] = mapped_column(String(255))
    units: Mapped[Decimal] = mapped_column(DecimalText())
    amount: Mapped[Decimal | None] = mapped_column(DecimalText())
    nav: Mapped[Decimal | None] = mapped_column(DecimalText())
    notes: Mapped[str | None] = mapped_column(String(500))
    income_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("incomes.id"))
    synthetic: Mapped[bool] = mapped_column(default=False)
    fingerprint: Mapped[str | None] = mapped_column(String(64), unique=True)

    position: Mapped[Position] = relationship(back_populates="transactions")


class Lot(Base):
    """Units acquired by one Transaction and not yet disposed of, reduced FIFO."""

    __tablename__ = "lots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    position_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("positions.id"), index=True)
    transaction_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("transactions.id"), unique=True)
    acquired_on: Mapped[date]
    units: Mapped[Decimal] = mapped_column(DecimalText())
    cost: Mapped[Decimal] = mapped_column(DecimalText())
    remaining_units: Mapped[Decimal] = mapped_column(DecimalText())
    remaining_cost: Mapped[Decimal] = mapped_column(DecimalText())

    transaction: Mapped[Transaction] = relationship()

    @classmethod
    def acquired_by(cls, transaction: Transaction, cost: Decimal) -> "Lot":
        return cls(
            transaction=transaction,
            acquired_on=transaction.date,
            units=transaction.units,
            cost=cost,
            remaining_units=transaction.units,
            remaining_cost=cost,
        )

    def consume(self, units: Decimal) -> Decimal:
        """Takes up to `units` from this lot and returns how many are still to be taken."""
        taken = min(self.remaining_units, units)
        if taken <= ZERO:
            return units
        released = (self.remaining_cost * taken / self.remaining_units).quantize(PAISE)
        self.remaining_units -= taken
        self.remaining_cost -= released
        return units - taken


class Income(Base):
    """Value a Position generated without changing its quantity (ADR 0003).

    Withdrawn Income crosses the Portfolio boundary and is a Cash Flow; reinvested
    Income produces a Transaction that raises the Position's quantity.
    """

    __tablename__ = "incomes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    position_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("positions.id"), index=True)
    date: Mapped[date]
    kind: Mapped[str] = mapped_column(String(16))
    gross_amount: Mapped[Decimal] = mapped_column(DecimalText())
    tax_deducted: Mapped[Decimal] = mapped_column(DecimalText())
    net_amount: Mapped[Decimal] = mapped_column(DecimalText())
    withdrawn: Mapped[bool] = mapped_column(default=False)
    fingerprint: Mapped[str | None] = mapped_column(String(64), unique=True)

    position: Mapped[Position] = relationship(back_populates="income")
    reinvestment: Mapped["Transaction | None"] = relationship(
        primaryjoin="Income.id == Transaction.income_id",
        foreign_keys="Transaction.income_id",
        uselist=False,
        viewonly=True,
        lazy="selectin",
    )

    def cash_flow(self) -> Decimal:
        """Withdrawn Income is money the household took out; reinvested Income stays in."""
        return self.net_amount if self.withdrawn else ZERO

    def reinvested_units(self) -> Decimal | None:
        """The units the reinvestment Transaction bought, or None when withdrawn."""
        transaction = self.reinvestment
        return None if transaction is None else transaction.units
