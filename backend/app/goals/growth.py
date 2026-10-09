"""Growing a value and discounting flows by a rate (ADR 0009)."""

from decimal import Decimal

from app.goals.dates import MONTHS_PER_YEAR

ONE = Decimal(1)


def grow(value: Decimal, rate: Decimal, years: Decimal) -> Decimal:
    return value * (ONE + rate) ** years


def monthly_factor(rate: Decimal) -> Decimal:
    return (ONE + rate) ** (ONE / MONTHS_PER_YEAR)
