"""Goal Projections and the Scheduled Transactions that feed them (#38, ADR 0009, 0022)."""

import uuid
from datetime import date
from decimal import Decimal
from typing import Self

from fastapi import APIRouter, Response, status
from pydantic import BaseModel, ConfigDict, Field

from app.api.goals import rejection_responses
from app.core.database import SessionDependency
from app.goals.errors import InvalidScheduleError, UnknownPositionsError
from app.goals.history import HistoryInputs, HistorySnapshot, snapshots
from app.goals.models import MAX_SCHEDULE_DESCRIPTION, Goal, ScheduledTransaction
from app.goals.progress import positions_of
from app.goals.projection import GoalProjection, ProjectionInputs, TrajectoryPoint, project
from app.goals.store import (
    ScheduledTransactionDraft,
    create_scheduled,
    delete_scheduled,
    find_goal,
    positions_schedules,
)
from app.ledger.models import Position

router = APIRouter()

_REPLIES = rejection_responses(status.HTTP_404_NOT_FOUND, status.HTTP_422_UNPROCESSABLE_CONTENT)


class TrajectoryPointView(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)

    on: date
    value: Decimal

    @classmethod
    def of(cls, point: TrajectoryPoint) -> Self:
        return cls(on=point.on, value=point.value)


class ProjectionView(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)

    goal_id: uuid.UUID
    strategy: str | None
    rate: Decimal | None
    current_value: Decimal
    target_amount: Decimal
    target_date: date
    projected_value: Decimal
    gap: Decimal
    status: str
    as_of: date
    trajectory: list[TrajectoryPointView]

    @classmethod
    def of(cls, projection: GoalProjection, as_of: date) -> Self:
        goal = projection.goal
        return cls(
            goal_id=goal.id,
            strategy=goal.projection_strategy,
            rate=projection.rate,
            current_value=projection.current_value,
            target_amount=goal.target_amount,
            target_date=goal.target_date,
            projected_value=projection.projected_value,
            gap=(goal.target_amount - projection.projected_value),
            status=projection.status,
            as_of=as_of,
            trajectory=[TrajectoryPointView.of(point) for point in projection.trajectory],
        )


class HistoryPointView(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)

    on: date
    projected_value: Decimal

    @classmethod
    def of(cls, snapshot: HistorySnapshot) -> Self:
        return cls(on=snapshot.on, projected_value=snapshot.projected_value)


class ProjectionHistoryView(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)

    goal_id: uuid.UUID
    points: list[HistoryPointView]


class ScheduleWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    position_id: uuid.UUID
    description: str = Field(min_length=1, max_length=MAX_SCHEDULE_DESCRIPTION)
    direction: str
    frequency: str
    amount: Decimal = Field(gt=0)
    start_date: date
    end_date: date | None = None
    escalation_rate: Decimal = Field(default=Decimal(0), ge=-1)

    def draft(self) -> ScheduledTransactionDraft:
        if self.end_date is not None and self.end_date < self.start_date:
            raise InvalidScheduleError()
        return ScheduledTransactionDraft(
            position_id=self.position_id,
            description=self.description,
            direction=self.direction,
            frequency=self.frequency,
            amount=self.amount,
            start_date=self.start_date,
            end_date=self.end_date,
            escalation_rate=self.escalation_rate,
        )


class PositionOption(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)

    id: uuid.UUID
    name: str

    @classmethod
    def of(cls, position: Position) -> Self:
        return cls(
            id=position.id, name=f"{position.account.institution} · {position.instrument.name}"
        )


class ScheduleView(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)

    id: uuid.UUID
    position_id: uuid.UUID
    position_name: str
    description: str
    direction: str
    frequency: str
    amount: Decimal
    start_date: date
    end_date: date | None
    escalation_rate: Decimal

    @classmethod
    def of(cls, schedule: ScheduledTransaction, position_name: str) -> Self:
        return cls(
            id=schedule.id,
            position_id=schedule.position_id,
            position_name=position_name,
            description=schedule.description,
            direction=schedule.direction,
            frequency=schedule.frequency,
            amount=schedule.amount,
            start_date=schedule.start_date,
            end_date=schedule.end_date,
            escalation_rate=schedule.escalation_rate,
        )


class ScheduleBoard(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)

    schedules: list[ScheduleView]
    positions: list[PositionOption]


def _goal_inputs(session: SessionDependency, goal: Goal, as_of: date) -> ProjectionInputs:
    positions = positions_of(session, goal)
    return ProjectionInputs(
        goal=goal,
        positions=positions,
        schedules=positions_schedules(session, positions),
        as_of=as_of,
    )


def _position_names(session: SessionDependency, goal: Goal) -> dict[uuid.UUID, str]:
    return {
        position.id: PositionOption.of(position).name for position in positions_of(session, goal)
    }


def _board(session: SessionDependency, goal: Goal) -> ScheduleBoard:
    names = _position_names(session, goal)
    schedules = positions_schedules(session, positions_of(session, goal))
    return ScheduleBoard(
        schedules=[
            ScheduleView.of(schedule, names[schedule.position_id]) for schedule in schedules
        ],
        positions=[PositionOption(id=key, name=value) for key, value in names.items()],
    )


@router.get(  # type: ignore[misc]  # FastAPI decorators are typed with Any
    "/goals/{goal_id}/projection",
    operation_id="getGoalProjection",
    responses=_REPLIES,
)
def get_projection(
    goal_id: uuid.UUID, session: SessionDependency, as_of: date | None = None
) -> ProjectionView:
    at = as_of or date.today()
    goal = find_goal(session, goal_id)
    return ProjectionView.of(project(_goal_inputs(session, goal, at)), at)


@router.get(  # type: ignore[misc]  # FastAPI decorators are typed with Any
    "/goals/{goal_id}/projection/history",
    operation_id="getGoalProjectionHistory",
    responses=_REPLIES,
)
def get_projection_history(
    goal_id: uuid.UUID, session: SessionDependency, as_of: date | None = None
) -> ProjectionHistoryView:
    at = as_of or date.today()
    goal = find_goal(session, goal_id)
    inputs = _goal_inputs(session, goal, at)
    points = snapshots(
        HistoryInputs(goal=goal, positions=inputs.positions, schedules=inputs.schedules, as_of=at)
    )
    return ProjectionHistoryView(goal_id=goal.id, points=[HistoryPointView.of(p) for p in points])


@router.get(  # type: ignore[misc]  # FastAPI decorators are typed with Any
    "/goals/{goal_id}/scheduled-transactions",
    operation_id="listScheduledTransactions",
    responses=_REPLIES,
)
def get_schedules(goal_id: uuid.UUID, session: SessionDependency) -> ScheduleBoard:
    return _board(session, find_goal(session, goal_id))


@router.post(  # type: ignore[misc]  # FastAPI decorators are typed with Any
    "/goals/{goal_id}/scheduled-transactions",
    operation_id="createScheduledTransaction",
    status_code=status.HTTP_201_CREATED,
    responses=_REPLIES,
)
def post_schedule(
    goal_id: uuid.UUID, body: ScheduleWrite, session: SessionDependency
) -> ScheduleView:
    names = _position_names(session, find_goal(session, goal_id))
    if body.position_id not in names:
        raise UnknownPositionsError()
    schedule = create_scheduled(session, body.draft())
    session.commit()
    return ScheduleView.of(schedule, names[body.position_id])


@router.delete(  # type: ignore[misc]  # FastAPI decorators are typed with Any
    "/scheduled-transactions/{schedule_id}",
    operation_id="deleteScheduledTransaction",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=_REPLIES,
)
def delete_schedule_route(schedule_id: uuid.UUID, session: SessionDependency) -> Response:
    delete_scheduled(session, schedule_id)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
