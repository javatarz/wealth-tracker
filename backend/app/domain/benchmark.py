"""Assigning Benchmarks and resolving them for an Instrument (ADR 0017).

Resolution is a chain: a per-Instrument override wins, then the asset class's
configured Benchmark, then the shipped default. The defaults are read from the
catalogue rather than copied into the database, so an empty database already
answers correctly and a user override is the only thing worth persisting.
"""

import uuid

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.domain.asset_classes import (
    BENCHMARK_INSTRUMENT_KIND,
    AssetClass,
    asset_class_of_instrument_kind,
    benchmark_definition,
    default_benchmark_key,
    is_known_benchmark,
)
from app.ledger.models import BenchmarkAssignment, Instrument, InstrumentBenchmark


class UnknownBenchmarkError(ValueError):
    """Raised when a caller names a Benchmark that isn't in the catalogue."""

    def __init__(self, key: str) -> None:
        self.key = key
        super().__init__(f"Unknown benchmark: {key}")


def assigned_benchmark_key(session: Session, asset_class: AssetClass) -> str:
    assignment = session.get(BenchmarkAssignment, asset_class)
    if assignment is None:
        return default_benchmark_key(asset_class)
    return assignment.benchmark.identity


def assign_benchmark(session: Session, asset_class: AssetClass, key: str) -> Instrument:
    """Persists an asset class's Benchmark choice and returns its benchmark Instrument."""
    _reject_unknown(key)
    instrument = benchmark_instrument(session, key)
    assignment = session.get(BenchmarkAssignment, asset_class)
    if assignment is None:
        session.add(
            BenchmarkAssignment(asset_class=asset_class, benchmark_instrument_id=instrument.id)
        )
        return instrument
    assignment.benchmark_instrument_id = instrument.id
    return instrument


def find_benchmark_instrument(session: Session, key: str) -> Instrument | None:
    return session.scalars(
        select(Instrument).where(
            Instrument.kind == BENCHMARK_INSTRUMENT_KIND, Instrument.identity == key
        )
    ).first()


def benchmark_instrument(session: Session, key: str) -> Instrument:
    """The Instrument standing in for a catalogue Benchmark, created on first use."""
    existing = find_benchmark_instrument(session, key)
    if existing is not None:
        return existing
    definition = benchmark_definition(key)
    instrument = Instrument(
        id=uuid.uuid4(),
        kind=BENCHMARK_INSTRUMENT_KIND,
        identity=key,
        name=definition.name,
    )
    session.add(instrument)
    return instrument


def instrument_benchmark_key(session: Session, instrument_id: uuid.UUID) -> str | None:
    override = session.get(InstrumentBenchmark, instrument_id)
    return None if override is None else override.benchmark.identity


def set_instrument_override(session: Session, instrument_id: uuid.UUID, key: str | None) -> None:
    """Sets or clears an Instrument's Benchmark override (``None`` restores the default)."""
    session.execute(
        delete(InstrumentBenchmark).where(InstrumentBenchmark.instrument_id == instrument_id)
    )
    benchmark = _benchmark_for_key(session, key)
    if benchmark is None:
        return
    session.add(
        InstrumentBenchmark(instrument_id=instrument_id, benchmark_instrument_id=benchmark.id)
    )


def _benchmark_for_key(session: Session, key: str | None) -> Instrument | None:
    if key is None:
        return None
    _reject_unknown(key)
    return benchmark_instrument(session, key)


def _reject_unknown(key: str) -> None:
    if not is_known_benchmark(key):
        raise UnknownBenchmarkError(key)


def resolve_benchmark_key(session: Session, instrument: Instrument) -> str:
    """The Benchmark an Instrument is measured against: override, class, then default."""
    override = instrument_benchmark_key(session, instrument.id)
    if override is not None:
        return override
    return assigned_benchmark_key(session, asset_class_of_instrument_kind(instrument.kind))
