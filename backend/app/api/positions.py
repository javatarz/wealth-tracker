import datetime
import uuid
from decimal import Decimal
from typing import Self

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict

from app.core.database import SessionDependency
from app.ledger.models import Position
from app.valuation import engine
from app.valuation.strategies import Valuation, label_for

router = APIRouter()

_NOT_FOUND: dict[int | str, dict[str, str]] = {
    status.HTTP_404_NOT_FOUND: {"description": "Position not found"}
}


class PositionSummary(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)

    id: uuid.UUID
    scheme: str
    institution: str
    folio: str
    units: Decimal
    cost_basis: Decimal
    value: Decimal | None
    valuation_strategy: str
    valuation_label: str
    stale: bool
    warning: str | None

    @classmethod
    def of(cls, position: Position, valuation: Valuation) -> Self:
        account = position.account
        instrument = position.instrument
        return cls(
            id=position.id,
            scheme=instrument.name,
            institution=account.institution,
            folio=account.number,
            units=position.units(),
            cost_basis=position.cost_basis(),
            value=valuation.amount,
            valuation_strategy=instrument.valuation_strategy,
            valuation_label=label_for(instrument.valuation_strategy),
            stale=valuation.stale,
            warning=valuation.warning,
        )


@router.get("/positions", operation_id="listPositions")  # type: ignore[misc]  # FastAPI decorators are typed with Any
def get_positions(session: SessionDependency) -> list[PositionSummary]:
    return [
        PositionSummary.of(position, valuation)
        for position, valuation in engine.valued_positions(session, _today())
    ]


@router.get(  # type: ignore[misc]  # FastAPI decorators are typed with Any
    "/positions/{position_id}",
    operation_id="getPosition",
    responses=_NOT_FOUND,
)
def get_position(position_id: uuid.UUID, session: SessionDependency) -> PositionSummary:
    found = engine.valued_position(session, position_id, _today())
    if found is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "That Position doesn't exist.")
    position, valuation = found
    return PositionSummary.of(position, valuation)


def _today() -> datetime.date:
    return datetime.datetime.now(datetime.UTC).date()
