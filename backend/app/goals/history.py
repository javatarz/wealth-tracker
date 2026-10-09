"""A Goal's Projection as it stood at earlier points, so the graph can show how it drifted.

Projections are computed on the fly (ADR 0022), so an earlier trajectory is reconstructed
from the current inputs: a past `as_of` understates value and omits the flows already
scheduled before then, which shows what the Goal looked like without the Settlement of
later events.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from app.goals.models import Goal, ScheduledTransaction
from app.goals.projection import GoalProjection, ProjectionInputs, project
from app.ledger.models import Position

INTERVAL = timedelta(days=30)
MAX_SNAPSHOTS = 12


@dataclass(frozen=True)
class HistoryInputs:
    goal: Goal
    positions: Sequence[Position]
    schedules: Sequence[ScheduledTransaction]
    as_of: date


@dataclass(frozen=True)
class HistorySnapshot:
    on: date
    projected_value: Decimal


def snapshots(inputs: HistoryInputs) -> list[HistorySnapshot]:
    return [_snapshot(inputs, at) for at in _review_dates(inputs.as_of)]


def _review_dates(as_of: date) -> list[date]:
    return list(reversed([as_of - INTERVAL * index for index in range(MAX_SNAPSHOTS)]))


def _snapshot(inputs: HistoryInputs, at: date) -> HistorySnapshot:
    projection: GoalProjection = project(
        ProjectionInputs(
            goal=inputs.goal,
            positions=inputs.positions,
            schedules=inputs.schedules,
            as_of=at,
        )
    )
    return HistorySnapshot(on=at, projected_value=projection.projected_value)
