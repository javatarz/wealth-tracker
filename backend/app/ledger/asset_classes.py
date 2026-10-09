"""The asset classes a Portfolio is sliced by (#28).

An Instrument carries one asset class, derived when it is created. The class
drives the dashboard's Asset Class filter and (later) benchmark defaults (ADR 0017).
"""

from app.core.statement_preview import Scheme

EQUITY = "equity"
DEBT = "debt"
GOLD = "gold"
REAL_ESTATE = "real_estate"
CASH = "cash"
CRYPTO = "crypto"
OTHER = "other"

ASSET_CLASSES: tuple[str, ...] = (EQUITY, DEBT, GOLD, REAL_ESTATE, CASH, CRYPTO, OTHER)

LABELS: dict[str, str] = {
    EQUITY: "Equity",
    DEBT: "Debt",
    GOLD: "Gold",
    REAL_ESTATE: "Real Estate",
    CASH: "Cash",
    CRYPTO: "Crypto",
    OTHER: "Other",
}

_BY_SCHEME_TYPE: dict[str, str] = {"EQUITY": EQUITY, "DEBT": DEBT}


def asset_class_for(scheme: Scheme) -> str:
    """Mutual funds carry a plan type (EQUITY/DEBT); anything else is `other`."""
    return _BY_SCHEME_TYPE.get((scheme.type or "").upper(), OTHER)
