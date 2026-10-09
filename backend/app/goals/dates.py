"""Calendar arithmetic shared by projection and scheduled flows."""

import calendar
from collections.abc import Iterator
from datetime import date, timedelta
from decimal import Decimal

DAYS_PER_YEAR = Decimal("365.25")
MONTHS_PER_YEAR = 12
SIX_PLACES = Decimal("0.000001")


def add_months(when: date, months: int) -> date:
    total = when.month - 1 + months
    year = when.year + total // MONTHS_PER_YEAR
    month = total % MONTHS_PER_YEAR + 1
    return date(year, month, min(when.day, days_in_month(year, month)))


def days_in_month(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]


def elapsed_years(start: date, end: date) -> Decimal:
    return (Decimal((end - start).days) / DAYS_PER_YEAR).quantize(SIX_PLACES)


def years_before(day: date, years: int) -> date:
    return day - timedelta(days=round(years * DAYS_PER_YEAR))


def month_steps(start: date, end: date) -> Iterator[tuple[date, date]]:
    """Successive (previous, boundary) pairs from start to end, one calendar month apart."""
    previous = start
    index = 1
    while previous < end:
        boundary = min(add_months(start, index), end)
        yield previous, boundary
        previous = boundary
        index += 1
