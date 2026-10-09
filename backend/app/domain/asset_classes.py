"""Asset classes, the Benchmark catalogue, and each class's shipped default (ADR 0017).

The Benchmark catalogue is deliberately small: a Benchmark is an index, an inflation
series, or a rate. Anything the user can pick from is defined here, and a Benchmark is
persisted as an Instrument of kind ``benchmark`` whose identity is the catalogue key.
"""

from dataclasses import dataclass
from typing import Literal

type AssetClass = Literal["equity", "debt", "gold", "real_estate", "crypto", "cash", "other"]
type BenchmarkKind = Literal["index", "inflation", "rate"]

BENCHMARK_INSTRUMENT_KIND = "benchmark"
DEFAULT_ASSET_CLASS: AssetClass = "other"

ASSET_CLASSES: tuple[AssetClass, ...] = (
    "equity",
    "debt",
    "gold",
    "real_estate",
    "crypto",
    "cash",
    "other",
)


@dataclass(frozen=True)
class BenchmarkDefinition:
    key: str
    name: str
    kind: BenchmarkKind


BENCHMARK_CATALOG: dict[str, BenchmarkDefinition] = {
    definition.key: definition
    for definition in (
        BenchmarkDefinition("nifty50_tri", "NIFTY 50 TRI", "index"),
        BenchmarkDefinition("nifty_midcap150_tri", "NIFTY Midcap 150 TRI", "index"),
        BenchmarkDefinition("nifty_smallcap250_tri", "NIFTY Smallcap 250 TRI", "index"),
        BenchmarkDefinition("nifty_composite_debt", "NIFTY Composite Debt Index", "index"),
        BenchmarkDefinition("cpi", "CPI (Inflation)", "inflation"),
        BenchmarkDefinition("fd_rate", "Fixed Deposit rate", "rate"),
    )
}

# ADR 0017's shipped defaults. The user overrides per asset class, or per Instrument.
DEFAULT_BENCHMARK_BY_ASSET_CLASS: dict[AssetClass, str] = {
    "equity": "nifty50_tri",
    "debt": "cpi",
    "gold": "nifty_composite_debt",
    "real_estate": "cpi",
    "crypto": "nifty_smallcap250_tri",
    "cash": "cpi",
    "other": "nifty50_tri",
}

_ASSET_CLASS_BY_INSTRUMENT_KIND: dict[str, AssetClass] = {
    "mutual_fund": "equity",
    "equity": "equity",
    "gold_etf": "gold",
    "physical_gold": "gold",
    "crypto": "crypto",
    "fd": "debt",
    "ppf": "debt",
    "property": "real_estate",
}


def asset_class_of_instrument_kind(kind: str) -> AssetClass:
    """Instruments carry an ADR 0015 kind; its asset class follows from that."""
    return _ASSET_CLASS_BY_INSTRUMENT_KIND.get(kind, DEFAULT_ASSET_CLASS)


def is_known_benchmark(key: str) -> bool:
    return key in BENCHMARK_CATALOG


def benchmark_definition(key: str) -> BenchmarkDefinition:
    missing = f"Unknown benchmark: {key}"
    if not is_known_benchmark(key):
        raise KeyError(missing)
    return BENCHMARK_CATALOG[key]


def default_benchmark_key(asset_class: AssetClass) -> str:
    return DEFAULT_BENCHMARK_BY_ASSET_CLASS[asset_class]
