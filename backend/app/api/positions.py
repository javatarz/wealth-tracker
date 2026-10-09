import datetime
import uuid
from decimal import Decimal
from typing import Self

from fastapi import APIRouter, status
from pydantic import BaseModel, ConfigDict, Field

from app.api.rejections import rejection_responses
from app.core.database import SessionDependency
from app.core.statement_rejection import StatementRejectedError
from app.ledger import income as income_ledger
from app.ledger.manual_entry import ManualTransaction, allowed_types_for, record
from app.ledger.models import ZERO, Income, Position, Transaction
from app.ledger.positions import find_position, list_positions

router = APIRouter()

_NOT_FOUND = "That Position no longer exists."


class PositionSummary(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)

    id: uuid.UUID
    scheme: str
    institution: str
    folio: str
    units: Decimal
    cost_basis: Decimal

    @classmethod
    def of(cls, position: Position) -> Self:
        account = position.account
        return cls(
            id=position.id,
            scheme=position.instrument.name,
            institution=account.institution,
            folio=account.number,
            units=position.units(),
            cost_basis=position.cost_basis(),
        )


class LedgerEntry(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)

    date: datetime.date
    kind: str
    description: str
    units: Decimal
    amount: Decimal | None
    notes: str | None
    synthetic: bool

    @classmethod
    def of(cls, transaction: Transaction) -> Self:
        return cls(
            date=transaction.date,
            kind=transaction.kind,
            description=transaction.description,
            units=transaction.units,
            amount=transaction.amount,
            notes=transaction.notes,
            synthetic=transaction.synthetic,
        )


class IncomeEntry(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)

    date: datetime.date
    kind: str
    gross_amount: Decimal
    tax_deducted: Decimal
    net_amount: Decimal
    withdrawn: bool
    units: Decimal | None

    @classmethod
    def of(cls, income: Income) -> Self:
        return cls(
            date=income.date,
            kind=income.kind,
            gross_amount=income.gross_amount,
            tax_deducted=income.tax_deducted,
            net_amount=income.net_amount,
            withdrawn=income.withdrawn,
            units=income.reinvested_units(),
        )


class PositionDetail(PositionSummary):
    """A Position with its full ledger and the Transaction types it accepts."""

    instrument_kind: str
    allowed_types: list[str]
    allowed_income_types: list[str]
    reinvestable: bool
    transactions: list[LedgerEntry]
    income: list[IncomeEntry]
    income_total: Decimal
    cash_flow_total: Decimal

    @classmethod
    def with_ledger(
        cls, position: Position, entries: list[LedgerEntry], income: list[IncomeEntry]
    ) -> Self:
        summary = PositionSummary.of(position)
        kind = position.instrument.kind
        return cls(
            **summary.model_dump(),
            instrument_kind=kind,
            allowed_types=allowed_types_for(kind),
            allowed_income_types=income_ledger.allowed_income_types(),
            reinvestable=income_ledger.reinvestment_allowed(kind),
            transactions=entries,
            income=income,
            income_total=sum((event.net_amount for event in position.income), ZERO),
            cash_flow_total=sum((event.cash_flow() for event in position.income), ZERO),
        )


class IncomeRequest(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    type: str
    date: datetime.date = Field(strict=False)
    amount: Decimal = Field(strict=False)
    tax: Decimal | None = Field(default=None, strict=False)
    reinvested: bool = False
    nav: Decimal | None = Field(default=None, strict=False)

    def as_draft(self, position_id: uuid.UUID) -> income_ledger.IncomeDraft:
        return income_ledger.IncomeDraft(
            position_id=position_id,
            kind=self.type,
            date=self.date,
            gross_amount=self.amount,
            tax_deducted=self.tax,
            reinvested=self.reinvested,
            nav=self.nav,
        )


class ManualTransactionRequest(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    type: str
    date: datetime.date = Field(strict=False)
    units: Decimal = Field(strict=False)
    amount: Decimal | None = Field(default=None, strict=False)
    notes: str = Field(default="", max_length=500)

    def as_draft(self, position_id: uuid.UUID) -> ManualTransaction:
        return ManualTransaction(
            position_id=position_id,
            type=self.type,
            date=self.date,
            units=self.units,
            amount=self.amount,
            notes=self.notes,
        )


@router.get(
    "/positions",
    operation_id="listPositions",
)
def get_positions(session: SessionDependency) -> list[PositionSummary]:
    return [PositionSummary.of(position) for position in list_positions(session)]


@router.get(
    "/positions/{position_id}",
    operation_id="getPosition",
    responses=rejection_responses(status.HTTP_404_NOT_FOUND),
)
def get_position(position_id: uuid.UUID, session: SessionDependency) -> PositionDetail:
    return _detail(_found(session, position_id))


@router.post(
    "/positions/{position_id}/transactions",
    operation_id="createTransaction",
    status_code=status.HTTP_201_CREATED,
    responses=rejection_responses(status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND),
)
def create_transaction(
    position_id: uuid.UUID, request: ManualTransactionRequest, session: SessionDependency
) -> PositionDetail:
    """Add a Transaction the user entered by hand. Units and cost basis update at once."""
    record(session, request.as_draft(position_id), datetime.date.today())
    session.commit()
    return get_position(position_id, session)


def _detail(position: Position) -> PositionDetail:
    entries = [LedgerEntry.of(row) for row in position.transactions]
    events = [IncomeEntry.of(event) for event in position.income]
    return PositionDetail.with_ledger(position, entries, events)


def _found(session: SessionDependency, position_id: uuid.UUID) -> Position:
    position = find_position(session, position_id)
    if position is None:
        raise StatementRejectedError("position_not_found", _NOT_FOUND)
    return position


@router.get(
    "/positions/{position_id}/income",
    operation_id="listIncome",
    responses=rejection_responses(status.HTTP_404_NOT_FOUND),
)
def list_income(position_id: uuid.UUID, session: SessionDependency) -> list[IncomeEntry]:
    """Every Income event recorded against the Position, oldest first."""
    return [IncomeEntry.of(event) for event in _found(session, position_id).income]


@router.post(
    "/positions/{position_id}/income",
    operation_id="createIncome",
    status_code=status.HTTP_201_CREATED,
    responses=rejection_responses(status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND),
)
def create_income(
    position_id: uuid.UUID, request: IncomeRequest, session: SessionDependency
) -> PositionDetail:
    """Record an Income event. Reinvested Income also buys units at once."""
    income_ledger.record(session, request.as_draft(position_id), datetime.date.today())
    session.commit()
    return get_position(position_id, session)
