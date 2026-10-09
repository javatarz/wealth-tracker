"""The Net Worth dashboard and its filter options (#28)."""

import uuid
from datetime import date
from decimal import Decimal
from typing import Annotated, Literal, Self

from fastapi import APIRouter, Query
from pydantic import BaseModel, ConfigDict

from app.core.database import SessionDependency
from app.ledger.dashboard import Dashboard, ValuedPosition, build_dashboard
from app.ledger.positions import (
    asset_class_options,
    list_memberships,
    list_positions,
)

router = APIRouter()

AssetClass = Literal["equity", "debt", "gold", "real_estate", "cash", "crypto", "other"]

MemberFilter = Annotated[uuid.UUID | None, Query(description="Household Member")]
AssetClassFilter = Annotated[AssetClass | None, Query(description="Asset Class")]


class NetWorthPoint(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)

    date: date
    value: Decimal


class DashboardPosition(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)

    id: uuid.UUID
    scheme: str
    account: str
    asset_class: str
    units: Decimal
    cost_basis: Decimal
    current_value: Decimal
    percent: Decimal

    @classmethod
    def of(cls, entry: ValuedPosition, percent: Decimal) -> Self:
        return cls(
            id=entry.id,
            scheme=entry.scheme,
            account=entry.account,
            asset_class=entry.asset_class,
            units=entry.units,
            cost_basis=entry.cost_basis,
            current_value=entry.current_value,
            percent=percent,
        )


class DashboardSummary(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)

    current_value: Decimal
    invested: Decimal
    absolute_return: Decimal
    series: list[NetWorthPoint]
    positions: list[DashboardPosition]

    @classmethod
    def of(cls, dashboard: Dashboard) -> "DashboardSummary":
        return cls(
            current_value=dashboard.current_value,
            invested=dashboard.invested,
            absolute_return=dashboard.absolute_return,
            series=[NetWorthPoint(date=on, value=value) for on, value in dashboard.series],
            positions=[
                DashboardPosition.of(entry, dashboard.percent_by_position[entry.id])
                for entry in dashboard.positions
            ],
        )


class MemberOption(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)

    id: uuid.UUID
    name: str


class AssetClassOption(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)

    value: str
    label: str


class FilterOptions(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)

    members: list[MemberOption]
    asset_classes: list[AssetClassOption]


@router.get(  # type: ignore[misc]  # FastAPI decorators are typed with Any
    "/dashboard", operation_id="getDashboard", response_model=DashboardSummary
)
def get_dashboard(
    session: SessionDependency,
    member: MemberFilter = None,
    asset_class: AssetClassFilter = None,
) -> DashboardSummary:
    """Net Worth over time and today's Positions, scoped by the filter bar."""
    positions = list_positions(session, member, asset_class)
    return DashboardSummary.of(build_dashboard(positions))


@router.get(  # type: ignore[misc]  # FastAPI decorators are typed with Any
    "/filters", operation_id="getFilterOptions", response_model=FilterOptions
)
def get_filters(session: SessionDependency) -> FilterOptions:
    """The Member and Asset Class dropdown options for the filter bar."""
    return FilterOptions(
        members=[
            MemberOption(id=member.id, name=member.name) for member in list_memberships(session)
        ],
        asset_classes=[
            AssetClassOption(value=value, label=label) for value, label in asset_class_options()
        ],
    )
