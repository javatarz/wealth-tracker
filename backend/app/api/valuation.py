"""Valuation history and user-supplied appraisals (#34)."""

import datetime
import uuid
from decimal import Decimal
from typing import Self

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict

from app.core.database import SessionDependency
from app.ledger.models import Appraisal
from app.valuation import engine
from app.valuation.engine import RequestedAppraisal
from app.valuation.strategies import Valuation

router = APIRouter()

_NOT_FOUND: dict[int | str, dict[str, str]] = {
    status.HTTP_404_NOT_FOUND: {"description": "Position not found"}
}


class ValuationPoint(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)

    date: datetime.date
    value: Decimal | None
    strategy: str
    priced_on: datetime.date | None
    stale: bool
    warning: str | None

    @classmethod
    def of(cls, day: datetime.date, valuation: Valuation) -> Self:
        return cls(
            date=day,
            value=valuation.amount,
            strategy=valuation.strategy,
            priced_on=valuation.priced_on,
            stale=valuation.stale,
            warning=valuation.warning,
        )


class AppraisalMark(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)

    instrument_id: uuid.UUID
    date: datetime.date
    value: Decimal
    recorded_at: datetime.datetime

    @classmethod
    def of(cls, appraisal: Appraisal) -> Self:
        return cls(
            instrument_id=appraisal.instrument_id,
            date=appraisal.date,
            value=appraisal.value,
            recorded_at=appraisal.recorded_at,
        )


class AppraisalRequest(BaseModel):
    """A user-supplied revaluation. Lax, because JSON carries dates and decimals as text."""

    date: datetime.date
    value: Decimal


@router.get(  # type: ignore[misc]  # FastAPI decorators are typed with Any
    "/positions/{position_id}/valuation-history",
    operation_id="getValuationHistory",
    responses=_NOT_FOUND,
)
def get_valuation_history(
    position_id: uuid.UUID, session: SessionDependency, on: datetime.date | None = None
) -> list[ValuationPoint]:
    """The Position's value at each of its Transaction dates, using its strategy."""
    position = engine.position_of(session, position_id)
    if position is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "That Position doesn't exist.")
    points = engine.history_of(session, position, on or _today())
    return [ValuationPoint.of(day, valuation) for day, valuation in points]


@router.post(  # type: ignore[misc]  # FastAPI decorators are typed with Any
    "/positions/{position_id}/appraisal",
    operation_id="recordAppraisal",
    status_code=status.HTTP_201_CREATED,
    responses=_NOT_FOUND,
)
def post_appraisal(
    position_id: uuid.UUID, request: AppraisalRequest, session: SessionDependency
) -> AppraisalMark:
    """Record a user-supplied revaluation for an appraised Instrument."""
    position = engine.position_of(session, position_id)
    if position is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "That Position doesn't exist.")
    requested = RequestedAppraisal(
        instrument_id=position.instrument_id,
        date=request.date,
        value=request.value,
        recorded_at=datetime.datetime.now(datetime.UTC),
    )
    appraisal = engine.record_appraisal(session, requested)
    session.commit()
    return AppraisalMark.of(appraisal)


def _today() -> datetime.date:
    return datetime.datetime.now(datetime.UTC).date()
