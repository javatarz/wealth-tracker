import uuid
from decimal import Decimal
from typing import Self

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from app.core.database import SessionDependency
from app.ledger.models import Position
from app.ledger.positions import list_positions

router = APIRouter()


class PositionSummary(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)

    id: uuid.UUID
    scheme: str
    institution: str
    folio: str
    asset_class: str
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
            asset_class=position.instrument.asset_class,
            units=position.units(),
            cost_basis=position.cost_basis(),
        )


@router.get("/positions", operation_id="listPositions")  # type: ignore[misc]  # FastAPI decorators are typed with Any
def get_positions(session: SessionDependency) -> list[PositionSummary]:
    return [PositionSummary.of(position) for position in list_positions(session)]
