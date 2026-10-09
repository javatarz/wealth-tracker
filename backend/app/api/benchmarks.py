"""Benchmark configuration and return endpoints (ADR 0017).

- ``GET  /benchmarks/catalog``       — the Benchmarks a user can choose.
- ``GET  /benchmarks/config``        — each asset class's assigned and default Benchmark.
- ``PUT  /benchmarks/config/{asset_class}`` — change an asset class's Benchmark.
- ``GET  /benchmarks/instruments``   — Instruments with their resolved Benchmark.
- ``PUT  /benchmarks/instruments/{instrument_id}`` — set or clear a per-Instrument override.
- ``GET  /benchmarks/returns``       — a Benchmark's rebased return series over a range.
- ``GET  /benchmarks/overlay``       — a Benchmark line rebased onto a Portfolio value.
"""

import uuid
from datetime import date
from decimal import Decimal
from typing import Annotated, Self

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select

from app.core.database import SessionDependency
from app.domain import benchmark as assignment
from app.domain import benchmark_service
from app.domain.asset_classes import (
    BENCHMARK_INSTRUMENT_KIND,
    AssetClass,
    BenchmarkDefinition,
    benchmark_definition,
    is_known_benchmark,
)
from app.domain.series import DatedValue
from app.ledger.models import Instrument

router = APIRouter()

_OUT = ConfigDict(strict=True, frozen=True)


class BenchmarkDefinitionOut(BaseModel):
    model_config = _OUT

    key: str
    name: str
    kind: str

    @classmethod
    def of(cls, definition: BenchmarkDefinition) -> Self:
        return cls(key=definition.key, name=definition.name, kind=definition.kind)


class AssetClassBenchmarkOut(BaseModel):
    model_config = _OUT

    asset_class: str
    assigned_key: str
    default_key: str
    overridden: bool

    @classmethod
    def of(cls, view: benchmark_service.AssetClassBenchmark) -> Self:
        return cls(
            asset_class=view.asset_class,
            assigned_key=view.assigned_key,
            default_key=view.default_key,
            overridden=view.overridden,
        )


class BenchmarkConfigOut(BaseModel):
    model_config = _OUT

    available: list[BenchmarkDefinitionOut]
    asset_classes: list[AssetClassBenchmarkOut]


class InstrumentBenchmarkOut(BaseModel):
    model_config = _OUT

    instrument_id: uuid.UUID
    name: str
    asset_class: str
    resolved_key: str
    resolved_name: str
    override_key: str | None


class BenchmarkPointOut(BaseModel):
    model_config = _OUT

    date: date
    value: Decimal


class BenchmarkReturnOut(BaseModel):
    model_config = _OUT

    key: str
    name: str
    start: date
    end: date
    points: list[BenchmarkPointOut]


class OverlayOut(BaseModel):
    model_config = _OUT

    key: str
    start_value: Decimal
    points: list[BenchmarkPointOut]


class BenchmarkChoice(BaseModel):
    model_config = ConfigDict(strict=True)

    benchmark: str


class InstrumentBenchmarkChoice(BaseModel):
    model_config = ConfigDict(strict=True)

    benchmark: str | None


@router.get("/benchmarks/catalog", operation_id="listBenchmarks")
def get_catalog() -> list[BenchmarkDefinitionOut]:
    return [
        BenchmarkDefinitionOut.of(definition)
        for definition in benchmark_service.available_benchmarks()
    ]


@router.get("/benchmarks/config", operation_id="getBenchmarkConfig")
def get_config(session: SessionDependency) -> BenchmarkConfigOut:
    return BenchmarkConfigOut(
        available=[
            BenchmarkDefinitionOut.of(definition)
            for definition in benchmark_service.available_benchmarks()
        ],
        asset_classes=[
            AssetClassBenchmarkOut.of(view)
            for view in benchmark_service.asset_class_benchmarks(session)
        ],
    )


@router.put("/benchmarks/config/{asset_class}", operation_id="setBenchmark")
def set_benchmark(
    asset_class: AssetClass, choice: BenchmarkChoice, session: SessionDependency
) -> AssetClassBenchmarkOut:
    _assign(session, asset_class, choice.benchmark)
    session.commit()
    return AssetClassBenchmarkOut.of(_asset_class_view(session, asset_class))


@router.get("/benchmarks/instruments", operation_id="listInstrumentBenchmarks")
def list_instrument_benchmarks(session: SessionDependency) -> list[InstrumentBenchmarkOut]:
    query = (
        select(Instrument)
        .where(Instrument.kind != BENCHMARK_INSTRUMENT_KIND)
        .order_by(Instrument.name)
    )
    return [_instrument_out(session, instrument) for instrument in session.scalars(query).all()]


@router.put(
    "/benchmarks/instruments/{instrument_id}",
    operation_id="setInstrumentBenchmark",
)
def set_instrument_benchmark(
    instrument_id: uuid.UUID, choice: InstrumentBenchmarkChoice, session: SessionDependency
) -> InstrumentBenchmarkOut:
    instrument = session.get(Instrument, instrument_id)
    if instrument is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Instrument not found")
    _override(session, instrument_id, choice.benchmark)
    session.commit()
    return _instrument_out(session, instrument)


@router.get("/benchmarks/returns", operation_id="getBenchmarkReturns")
def get_returns(  # noqa: PLR0913, PLR0917  # one query parameter per field is clearer than a bag
    session: SessionDependency,
    benchmark: Annotated[str, Query()],
    from_: Annotated[date, Query(alias="from")],
    to: Annotated[date, Query(alias="to")],
) -> BenchmarkReturnOut:
    series = benchmark_service.return_series(session, benchmark, (from_, to))
    if series is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="No prices for that Benchmark")
    return BenchmarkReturnOut(
        key=series.key,
        name=series.name,
        start=series.start,
        end=series.end,
        points=[_point(point) for point in series.points],
    )


@router.get("/benchmarks/overlay", operation_id="getBenchmarkOverlay")
def get_overlay(  # noqa: PLR0913, PLR0917  # one query parameter per field is clearer than a bag
    session: SessionDependency,
    benchmark: Annotated[str, Query()],
    start_value: Annotated[Decimal, Query()],
    from_: Annotated[date, Query(alias="from")],
    to: Annotated[date, Query(alias="to")],
) -> OverlayOut:
    points = benchmark_service.overlay_series(session, benchmark, (from_, to), start_value)
    if not points:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="No prices for that Benchmark")
    return OverlayOut(
        key=benchmark, start_value=start_value, points=[_point(point) for point in points]
    )


def _assign(session: SessionDependency, asset_class: AssetClass, key: str) -> None:
    _reject_unknown(key)
    assignment.assign_benchmark(session, asset_class, key)


def _override(session: SessionDependency, instrument_id: uuid.UUID, key: str | None) -> None:
    if key is not None:
        _reject_unknown(key)
    assignment.set_instrument_override(session, instrument_id, key)


def _reject_unknown(key: str) -> None:
    if not is_known_benchmark(key):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail=_unknown(key))


def _asset_class_view(
    session: SessionDependency, asset_class: AssetClass
) -> benchmark_service.AssetClassBenchmark:
    return next(
        view
        for view in benchmark_service.asset_class_benchmarks(session)
        if view.asset_class == asset_class
    )


def _instrument_out(session: SessionDependency, instrument: Instrument) -> InstrumentBenchmarkOut:
    view = benchmark_service.instrument_benchmark(session, instrument)
    return InstrumentBenchmarkOut(
        instrument_id=view.instrument_id,
        name=instrument.name,
        asset_class=view.asset_class,
        resolved_key=view.resolved_key,
        resolved_name=benchmark_definition(view.resolved_key).name,
        override_key=view.override_key,
    )


def _point(point: DatedValue) -> BenchmarkPointOut:
    return BenchmarkPointOut(date=point.date, value=point.value)


def _unknown(key: str) -> str:
    return f"Unknown benchmark: {key}"
