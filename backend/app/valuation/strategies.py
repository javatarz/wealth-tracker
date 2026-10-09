"""How a Position's current worth is determined (ADR 0002, 0016)."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.ledger.models import PAISE, ZERO, Appraisal, Instrument, Price

MARKET_PRICED = "market_priced"
ACCRUAL = "accrual"
APPRAISED = "appraised"
YIELD_DERIVED = "yield_derived"

STALE_AFTER_DAYS = 7
DAYS_IN_YEAR = Decimal(365)
PERCENT = Decimal(100)

NO_PRICE = "No price has been cached for this Instrument yet."
NO_TERMS = "This Instrument is missing the principal or rate its accrual needs."
NO_APPRAISAL = "No appraised value has been recorded for this Instrument yet."
NO_YIELD_TERMS = "This Instrument is missing the income or cap rate its yield needs."


@dataclass(frozen=True)
class Valuation:
    """What a Position is worth, and how fresh and trustworthy that number is."""

    amount: Decimal | None
    strategy: str
    priced_on: date | None = None
    stale: bool = False
    warning: str | None = None


@dataclass(frozen=True)
class ValuationInputs:
    """Everything any strategy needs: the ledger, the Instrument's terms, and its marks."""

    units: Decimal
    instrument: Instrument
    on: date
    opened_on: date
    price: Price | None = None
    appraisal: Appraisal | None = None


Strategy = Callable[[ValuationInputs], Valuation]


def market_priced(inputs: ValuationInputs) -> Valuation:
    mark = inputs.price
    if mark is None:
        return Valuation(None, MARKET_PRICED, warning=NO_PRICE)
    amount = (inputs.units * mark.price).quantize(PAISE)
    age = (inputs.on - mark.date).days
    return Valuation(
        amount,
        MARKET_PRICED,
        priced_on=mark.date,
        stale=age > STALE_AFTER_DAYS,
        warning=_aging(age),
    )


def accrual(inputs: ValuationInputs) -> Valuation:
    terms = inputs.instrument
    if terms.principal is None or terms.interest_rate is None:
        return Valuation(None, ACCRUAL, warning=NO_TERMS)
    elapsed = _elapsed_days(inputs)
    interest = terms.principal * terms.interest_rate * elapsed / (PERCENT * DAYS_IN_YEAR)
    return Valuation((terms.principal + interest).quantize(PAISE), ACCRUAL, priced_on=inputs.on)


def appraised(inputs: ValuationInputs) -> Valuation:
    mark = inputs.appraisal
    if mark is None:
        return Valuation(None, APPRAISED, warning=NO_APPRAISAL)
    return Valuation(mark.value, APPRAISED, priced_on=mark.date)


def yield_derived(inputs: ValuationInputs) -> Valuation:
    terms = inputs.instrument
    if terms.annual_income is None or terms.cap_rate in (None, ZERO):
        return Valuation(None, YIELD_DERIVED, warning=NO_YIELD_TERMS)
    amount = (terms.annual_income * PERCENT / terms.cap_rate).quantize(PAISE)
    return Valuation(amount, YIELD_DERIVED, priced_on=inputs.on)


def _aging(age: int) -> str | None:
    if age <= STALE_AFTER_DAYS:
        return None
    return f"The last price is {age} days old."


def _elapsed_days(inputs: ValuationInputs) -> Decimal:
    start = inputs.instrument.accrual_start or inputs.opened_on
    end = _no_later_than(inputs.on, inputs.instrument.maturity_date)
    return Decimal(max((end - start).days, 0))


def _no_later_than(day: date, limit: date | None) -> date:
    if limit is None or day <= limit:
        return day
    return limit


_REGISTRY: dict[str, Strategy] = {
    MARKET_PRICED: market_priced,
    ACCRUAL: accrual,
    APPRAISED: appraised,
    YIELD_DERIVED: yield_derived,
}

LABELS: dict[str, str] = {
    MARKET_PRICED: "Market-priced",
    ACCRUAL: "Accrual",
    APPRAISED: "Appraised",
    YIELD_DERIVED: "Yield-derived",
}


def strategy_for(instrument: Instrument) -> Strategy:
    return _REGISTRY.get(instrument.valuation_strategy, market_priced)


def value_with(inputs: ValuationInputs) -> Valuation:
    return strategy_for(inputs.instrument)(inputs)


def label_for(strategy: str) -> str:
    return LABELS.get(strategy, strategy)
