"""Reading Benchmark configuration and series for the API (ADR 0017)."""

import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.domain import benchmark as assignment
from app.domain import returns
from app.domain.asset_classes import (
    ASSET_CLASSES,
    BENCHMARK_CATALOG,
    AssetClass,
    BenchmarkDefinition,
    asset_class_of_instrument_kind,
    benchmark_definition,
    default_benchmark_key,
)
from app.domain.series import DatedValue, rebased_to, summed
from app.ledger.models import BenchmarkAssignment, Instrument


@dataclass(frozen=True)
class AssetClassBenchmark:
    asset_class: AssetClass
    assigned_key: str
    default_key: str
    overridden: bool


@dataclass(frozen=True)
class InstrumentBenchmark:
    instrument_id: uuid.UUID
    asset_class: AssetClass
    resolved_key: str
    override_key: str | None


@dataclass(frozen=True)
class OverlayComponent:
    """One slice of a Portfolio measured against one Benchmark (ADR 0017)."""

    key: str
    start_value: Decimal


def available_benchmarks() -> tuple[BenchmarkDefinition, ...]:
    return tuple(BENCHMARK_CATALOG.values())


def asset_class_benchmarks(session: Session) -> tuple[AssetClassBenchmark, ...]:
    return tuple(_asset_class_benchmark(session, asset_class) for asset_class in ASSET_CLASSES)


def instrument_benchmark(session: Session, instrument: Instrument) -> InstrumentBenchmark:
    return InstrumentBenchmark(
        instrument_id=instrument.id,
        asset_class=asset_class_of_instrument_kind(instrument.kind),
        resolved_key=assignment.resolve_benchmark_key(session, instrument),
        override_key=assignment.instrument_benchmark_key(session, instrument.id),
    )


def return_series(
    session: Session, key: str, date_range: tuple[date, date]
) -> returns.BenchmarkSeries | None:
    instrument = assignment.find_benchmark_instrument(session, key)
    if instrument is None:
        return None
    points = returns.rebased_series(session, instrument.id, date_range)
    if not points:
        return None
    return returns.BenchmarkSeries(
        key=key,
        name=benchmark_definition(key).name,
        start=date_range[0],
        end=date_range[1],
        points=points,
    )


def overlay_series(  # noqa: PLR0913, PLR0917  # a session, a key, a range and a baseline
    session: Session, key: str, date_range: tuple[date, date], start_value: Decimal
) -> tuple[DatedValue, ...]:
    series = return_series(session, key, date_range)
    return () if series is None else rebased_to(series.points, start_value)


def blended_overlay(
    session: Session, date_range: tuple[date, date], components: tuple[OverlayComponent, ...]
) -> tuple[DatedValue, ...]:
    """The single blended line for a Portfolio of several Benchmarks (ADR 0017).

    Each component's own series is rebased to that component's starting investment,
    and the series are summed. A Portfolio measured against one Benchmark therefore
    comes back unchanged, and a mixed one blends by construction.
    """
    series = [
        overlay_series(session, component.key, date_range, component.start_value)
        for component in components
    ]
    return summed([component for component in series if component])


def _asset_class_benchmark(session: Session, asset_class: AssetClass) -> AssetClassBenchmark:
    row = session.get(BenchmarkAssignment, asset_class)
    return AssetClassBenchmark(
        asset_class=asset_class,
        assigned_key=assignment.assigned_benchmark_key(session, asset_class),
        default_key=default_benchmark_key(asset_class),
        overridden=row is not None,
    )
