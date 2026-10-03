from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

router = APIRouter()


class HealthResponse(BaseModel):
    model_config = ConfigDict(strict=True)

    status: Literal["ok"]


@router.get("/health", operation_id="getHealth")  # type: ignore[misc]  # FastAPI decorators are typed with Any
def get_health() -> HealthResponse:
    return HealthResponse(status="ok")
