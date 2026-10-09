"""Valuation Strategies (ADR 0002, 0016). One test per formula the issue names."""

import uuid
from datetime import date
from decimal import Decimal

from app.ledger.models import Appraisal, Instrument, Price
from app.valuation.strategies import (
    ACCRUAL,
    APPRAISED,
    MARKET_PRICED,
    NO_APPRAISAL,
    NO_PRICE,
    YIELD_DERIVED,
    ValuationInputs,
    value_with,
)

ON = date(2025, 3, 31)


def instrument(strategy: str, **terms: object) -> Instrument:
    return Instrument(
        id=uuid.uuid4(),
        kind="fd",
        identity="ACME-1",
        name="ACME",
        valuation_strategy=strategy,
        **terms,
    )


def price_mark(instrument_id: uuid.UUID, on: date, price: str) -> Price:
    return Price(
        id=uuid.uuid4(), instrument_id=instrument_id, date=on, price=Decimal(price), source="amfi"
    )


def appraisal_mark(instrument_id: uuid.UUID, on: date, value: str) -> Appraisal:
    return Appraisal(
        id=uuid.uuid4(),
        instrument_id=instrument_id,
        date=on,
        value=Decimal(value),
        recorded_at=date(2025, 1, 1),
    )


def inputs(terms: Instrument, units: str, **mark: object) -> ValuationInputs:
    return ValuationInputs(
        units=Decimal(units),
        instrument=terms,
        on=ON,
        opened_on=ON,
        **mark,  # type: ignore[arg-type]
    )


def test_market_priced_value_is_units_times_nav() -> None:
    terms = instrument(MARKET_PRICED)

    valuation = value_with(inputs(terms, "12.500", price=price_mark(terms.id, ON, "80.00")))

    assert valuation.amount == Decimal("1000.00")
    assert (valuation.strategy, valuation.priced_on, valuation.stale) == (MARKET_PRICED, ON, False)


def test_market_priced_without_a_price_warns_rather_than_zeroing() -> None:
    valuation = value_with(inputs(instrument(MARKET_PRICED), "12.500"))

    assert valuation.amount is None
    assert valuation.warning == NO_PRICE


def test_market_priced_flags_carried_forward_nav_as_stale() -> None:
    terms = instrument(MARKET_PRICED)

    valuation = value_with(
        inputs(terms, "1.000", price=price_mark(terms.id, date(2025, 3, 1), "10.00"))
    )

    assert valuation.amount == Decimal("10.00")
    assert valuation.stale is True
    assert valuation.warning is not None


def test_accrual_is_principal_plus_interest_for_elapsed_days() -> None:
    terms = instrument(
        ACCRUAL,
        principal=Decimal("100000.00"),
        interest_rate=Decimal("7.10"),
        accrual_start=date(2025, 1, 1),
    )

    valuation = value_with(inputs(terms, "0.000"))

    # 100000 + 100000 x 7.10% x 89/365 = 101731.23 (89 days from 1 Jan to 31 Mar)
    assert valuation.amount == Decimal("101731.23")


def test_accrual_stops_at_the_maturity_date() -> None:
    terms = instrument(
        ACCRUAL,
        principal=Decimal("100000.00"),
        interest_rate=Decimal("7.10"),
        accrual_start=date(2025, 1, 1),
        maturity_date=date(2025, 1, 31),
    )

    valuation = value_with(inputs(terms, "0.000"))

    assert valuation.amount == Decimal("100583.56")  # 30 days, not 89


def test_accrual_without_terms_warns() -> None:
    valuation = value_with(inputs(instrument(ACCRUAL), "0.000"))

    assert valuation.amount is None
    assert valuation.warning is not None


def test_appraised_returns_the_user_supplied_value() -> None:
    terms = instrument(APPRAISED)

    valuation = value_with(
        inputs(terms, "5.000", appraisal=appraisal_mark(terms.id, ON, "750000.00"))
    )

    assert valuation.amount == Decimal("750000.00")
    assert valuation.strategy == APPRAISED


def test_appraised_without_a_mark_warns() -> None:
    valuation = value_with(inputs(instrument(APPRAISED), "5.000"))

    assert valuation.amount is None
    assert valuation.warning == NO_APPRAISAL


def test_yield_derived_is_annual_income_over_cap_rate() -> None:
    terms = instrument(YIELD_DERIVED, annual_income=Decimal("300000.00"), cap_rate=Decimal("3.00"))

    valuation = value_with(inputs(terms, "0.000"))

    assert valuation.amount == Decimal("10000000.00")
    assert valuation.strategy == YIELD_DERIVED


def test_yield_derived_without_terms_warns() -> None:
    valuation = value_with(inputs(instrument(YIELD_DERIVED), "0.000"))

    assert valuation.amount is None
    assert valuation.warning is not None
