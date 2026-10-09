"""Turning Scheduled Transactions into dated future flows (ADR 0022).

A periodic schedule compounds its escalation rate yearly: the occurrence in
month *m* of year *y* is `amount * (1 + escalation_rate) ** y`.
"""

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from itertools import count, takewhile

from app.goals.dates import MONTHS_PER_YEAR, add_months
from app.goals.growth import grow
from app.goals.models import MONTHLY, YEARLY, ScheduledTransaction

MONTHS_PER_STEP = {MONTHLY: 1, YEARLY: MONTHS_PER_YEAR}
ZERO = Decimal(0)


@dataclass(frozen=True)
class Occurrence:
    on: date
    amount: Decimal


@dataclass(frozen=True)
class Cadence:
    """One schedule's rhythm: how often it recurs and until when."""

    schedule: ScheduledTransaction
    months: int
    horizon: date

    def at(self, index: int) -> date:
        return add_months(self.schedule.start_date, index * self.months)

    def occurrence(self, index: int) -> Occurrence:
        return Occurrence(on=self.at(index), amount=_escalated(self.schedule, index, self.months))

    def continues(self, index: int) -> bool:
        on = self.at(index)
        return on <= self.horizon and not _ended(self.schedule, on)


def occurrences(schedule: ScheduledTransaction, horizon: date) -> list[Occurrence]:
    months = MONTHS_PER_STEP.get(schedule.frequency)
    if months is None:
        return _one_off(schedule, horizon)
    return list(_periodic(schedule, horizon, months))


def _one_off(schedule: ScheduledTransaction, horizon: date) -> list[Occurrence]:
    if schedule.start_date > horizon:
        return []
    return [Occurrence(on=schedule.start_date, amount=schedule.amount)]


def _periodic(schedule: ScheduledTransaction, horizon: date, months: int) -> Iterator[Occurrence]:
    cadence = Cadence(schedule, months, horizon)
    return (cadence.occurrence(index) for index in takewhile(cadence.continues, count()))


def _ended(schedule: ScheduledTransaction, on: date) -> bool:
    return schedule.end_date is not None and on > schedule.end_date


def _escalated(schedule: ScheduledTransaction, index: int, months: int) -> Decimal:
    whole_years = (index * months) // MONTHS_PER_YEAR
    return grow(schedule.amount, schedule.escalation_rate, Decimal(whole_years))


class FlowStream:
    """All future flows of a Goal's Scheduled Transactions, queryable by month window."""

    def __init__(self, schedules: list[ScheduledTransaction], horizon: date) -> None:
        self._occurrences = [
            occurrence for schedule in schedules for occurrence in occurrences(schedule, horizon)
        ]

    def in_window(self, start: date, end: date) -> Decimal:
        return sum(
            (occurrence.amount for occurrence in self._occurrences if start < occurrence.on <= end),
            ZERO,
        )
