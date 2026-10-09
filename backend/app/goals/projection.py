"""Whether a Goal will be met: its trajectory to the target date (ADR 0009, 0022).

Starting from the value of the Goal's Accounts, the balance steps forward one calendar
month at a time — growing at the Projection Strategy's rate and absorbing each Scheduled
Transaction that falls in the month. The projected value is the balance at the target date.
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.goals.dates import month_steps
from app.goals.growth import ONE, monthly_factor
from app.goals.models import Goal, ScheduledTransaction
from app.goals.plans import FlowStream
from app.goals.progress import value_asof
from app.goals.strategies import rate_for, status_for
from app.ledger.models import PAISE, ZERO, Position


@dataclass(frozen=True)
class ProjectionInputs:
    goal: Goal
    positions: Sequence[Position]
    schedules: Sequence[ScheduledTransaction]
    as_of: date


@dataclass(frozen=True)
class TrajectoryPoint:
    on: date
    value: Decimal


@dataclass(frozen=True)
class GoalProjection:
    goal: Goal
    rate: Decimal | None
    current_value: Decimal
    projected_value: Decimal
    status: str
    trajectory: list[TrajectoryPoint]


class Run:
    """The state of one projection run as it steps month by month."""

    def __init__(self, factor: Decimal, flows: FlowStream, value: Decimal) -> None:
        self.factor = factor
        self.flows = flows
        self.value = value

    def step(self, window: tuple[date, date]) -> Decimal:
        previous, boundary = window
        self.value = self.value * self.factor + self.flows.in_window(previous, boundary)
        return self.value

    def grow_into(self, steps: Iterable[tuple[date, date]]) -> list[TrajectoryPoint]:
        return [
            TrajectoryPoint(on=boundary, value=self.step((previous, boundary)).quantize(PAISE))
            for previous, boundary in steps
        ]


def project(inputs: ProjectionInputs) -> GoalProjection:
    rate = rate_for(inputs.goal, inputs.positions, inputs.as_of)
    points = _trajectory(inputs, rate)
    projected = points[-1].value
    return GoalProjection(
        goal=inputs.goal,
        rate=rate,
        current_value=_current_value(inputs).quantize(PAISE),
        projected_value=projected,
        status=_status(rate, projected, inputs.goal),
        trajectory=points,
    )


def _current_value(inputs: ProjectionInputs) -> Decimal:
    return sum((value_asof(position, inputs.as_of) for position in inputs.positions), ZERO)


def _status(rate: Decimal | None, projected: Decimal, goal: Goal) -> str:
    return "insufficient_data" if rate is None else status_for(projected, goal.target_amount)


def _trajectory(inputs: ProjectionInputs, rate: Decimal | None) -> list[TrajectoryPoint]:
    current = _current_value(inputs)
    steps = month_steps(inputs.as_of, inputs.goal.target_date)
    run = Run(
        factor=ONE if rate is None else monthly_factor(rate),
        flows=FlowStream(list(inputs.schedules), inputs.goal.target_date),
        value=current,
    )
    start = TrajectoryPoint(on=inputs.as_of, value=current.quantize(PAISE))
    return [start, *run.grow_into(steps)]
