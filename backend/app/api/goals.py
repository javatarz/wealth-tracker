import uuid
from datetime import date
from decimal import Decimal
from typing import Self

from fastapi import APIRouter, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field

from app.core.database import SessionDependency
from app.goals.errors import GoalRejectedError, GoalRejectionCode
from app.goals.models import MAX_GOAL_NAME, Goal, account_label
from app.goals.progress import GoalProgress, progress
from app.goals.store import (
    GoalDraft,
    create_goal,
    delete_goal,
    find_goal,
    list_accounts,
    list_goals,
    update_goal,
)
from app.ledger.models import Account

router = APIRouter()

_STATUS_BY_CODE: dict[GoalRejectionCode, int] = {
    "goal_not_found": status.HTTP_404_NOT_FOUND,
    "unknown_accounts": status.HTTP_422_UNPROCESSABLE_CONTENT,
}


class GoalError(BaseModel):
    model_config = ConfigDict(strict=True)

    code: GoalRejectionCode
    message: str


def rejection_responses(*status_codes: int) -> dict[int | str, dict[str, type[GoalError]]]:
    return {status_code: {"model": GoalError} for status_code in status_codes}


def handle_rejection(_request: Request, exc: Exception) -> Response:
    if not isinstance(exc, GoalRejectedError):
        raise exc
    error = GoalError(code=exc.code, message=exc.message)
    return Response(
        content=error.model_dump_json(),
        status_code=_STATUS_BY_CODE[exc.code],
        media_type="application/json",
    )


_REPLIES = rejection_responses(status.HTTP_404_NOT_FOUND, status.HTTP_422_UNPROCESSABLE_CONTENT)


class GoalWrite(BaseModel):
    """What the browser sends to create or edit a Goal."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=MAX_GOAL_NAME)
    target_amount: Decimal = Field(gt=0)
    target_date: date
    account_ids: list[uuid.UUID] = Field(default_factory=list)

    def draft(self) -> GoalDraft:
        return GoalDraft(self.name, self.target_amount, self.target_date, tuple(self.account_ids))


class GoalSummary(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)

    id: uuid.UUID
    name: str
    target_amount: Decimal
    target_date: date
    account_ids: list[uuid.UUID]
    current_value: Decimal
    percent_funded: Decimal

    @classmethod
    def of(cls, goal: Goal, funded: GoalProgress) -> Self:
        return cls(
            id=goal.id,
            name=goal.name,
            target_amount=funded.target_amount,
            target_date=goal.target_date,
            account_ids=[account.id for account in goal.accounts],
            current_value=funded.current_value,
            percent_funded=funded.percent_funded,
        )


class AccountSummary(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)

    id: uuid.UUID
    name: str
    institution: str

    @classmethod
    def of(cls, account: Account) -> Self:
        return cls(id=account.id, name=account_label(account), institution=account.institution)


@router.get("/goals", operation_id="listGoals")  # type: ignore[misc]  # FastAPI decorators are typed with Any
def get_goals(session: SessionDependency) -> list[GoalSummary]:
    return [GoalSummary.of(goal, progress(session, goal)) for goal in list_goals(session)]


@router.post(  # type: ignore[misc]  # FastAPI decorators are typed with Any
    "/goals",
    operation_id="createGoal",
    status_code=status.HTTP_201_CREATED,
    response_model=None,
    responses=_REPLIES,
)
def post_goal(body: GoalWrite, session: SessionDependency) -> GoalSummary:
    goal = create_goal(session, body.draft())
    session.commit()
    return GoalSummary.of(goal, progress(session, goal))


@router.put(  # type: ignore[misc]  # FastAPI decorators are typed with Any
    "/goals/{goal_id}",
    operation_id="updateGoal",
    response_model=None,
    responses=_REPLIES,
)
def put_goal(goal_id: uuid.UUID, body: GoalWrite, session: SessionDependency) -> GoalSummary:
    goal = update_goal(session, find_goal(session, goal_id), body.draft())
    session.commit()
    return GoalSummary.of(goal, progress(session, goal))


@router.delete(  # type: ignore[misc]  # FastAPI decorators are typed with Any
    "/goals/{goal_id}",
    operation_id="deleteGoal",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=_REPLIES,
)
def delete_goal_route(goal_id: uuid.UUID, session: SessionDependency) -> Response:
    delete_goal(session, find_goal(session, goal_id))
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/accounts", operation_id="listAccounts")  # type: ignore[misc]  # FastAPI decorators are typed with Any
def get_accounts(session: SessionDependency) -> list[AccountSummary]:
    return [AccountSummary.of(account) for account in list_accounts(session)]
