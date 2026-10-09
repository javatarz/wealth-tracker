"""Reading and writing Goals and their Scheduled Transactions."""

import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.goals.errors import GoalNotFoundError, ScheduleNotFoundError, UnknownAccountsError
from app.goals.models import Goal, ScheduledTransaction
from app.ledger.members import default_member
from app.ledger.models import Account, Position


def list_goals(session: Session) -> Sequence[Goal]:
    query = select(Goal).options(selectinload(Goal.accounts)).order_by(Goal.target_date, Goal.name)
    return session.scalars(query).all()


def find_goal(session: Session, goal_id: uuid.UUID) -> Goal:
    goal = session.get(Goal, goal_id, options=[selectinload(Goal.accounts)])
    if goal is None:
        raise GoalNotFoundError(goal_id)
    return goal


@dataclass(frozen=True)
class GoalDraft:
    """The fields a browser submits when creating or editing a Goal."""

    name: str
    target_amount: Decimal
    target_date: date
    account_ids: tuple[uuid.UUID, ...] = field(default_factory=tuple)
    projection_strategy: str | None = None
    cagr_rate: Decimal | None = None
    trailing_window_years: int | None = None


def create_goal(session: Session, draft: GoalDraft) -> Goal:
    goal = Goal(
        id=uuid.uuid4(),
        household_member_id=default_member(session).id,
        name=draft.name,
        target_amount=draft.target_amount,
        target_date=draft.target_date,
        projection_strategy=draft.projection_strategy,
        cagr_rate=draft.cagr_rate,
        trailing_window_years=draft.trailing_window_years,
    )
    goal.accounts = _accounts(session, draft.account_ids)
    session.add(goal)
    return goal


def update_goal(session: Session, goal: Goal, draft: GoalDraft) -> Goal:
    goal.name = draft.name
    goal.target_amount = draft.target_amount
    goal.target_date = draft.target_date
    goal.projection_strategy = draft.projection_strategy
    goal.cagr_rate = draft.cagr_rate
    goal.trailing_window_years = draft.trailing_window_years
    goal.accounts = _accounts(session, draft.account_ids)
    return goal


def delete_goal(session: Session, goal: Goal) -> None:
    session.delete(goal)


def list_accounts(session: Session) -> Sequence[Account]:
    return session.scalars(select(Account).order_by(Account.institution, Account.number)).all()


def positions_schedules(
    session: Session, positions: Sequence[Position]
) -> Sequence[ScheduledTransaction]:
    position_ids = [position.id for position in positions]
    if not position_ids:
        return []
    query = select(ScheduledTransaction).where(ScheduledTransaction.position_id.in_(position_ids))
    return session.scalars(query).all()


@dataclass(frozen=True)
class ScheduledTransactionDraft:
    position_id: uuid.UUID
    description: str
    direction: str
    frequency: str
    amount: Decimal
    start_date: date
    end_date: date | None
    escalation_rate: Decimal


def create_scheduled(session: Session, draft: ScheduledTransactionDraft) -> ScheduledTransaction:
    schedule = ScheduledTransaction(
        id=uuid.uuid4(),
        position_id=draft.position_id,
        description=draft.description,
        direction=draft.direction,
        frequency=draft.frequency,
        amount=draft.amount,
        start_date=draft.start_date,
        end_date=draft.end_date,
        escalation_rate=draft.escalation_rate,
    )
    session.add(schedule)
    return schedule


def delete_scheduled(session: Session, schedule_id: uuid.UUID) -> None:
    schedule = session.get(ScheduledTransaction, schedule_id)
    if schedule is None:
        raise ScheduleNotFoundError(schedule_id)
    session.delete(schedule)


def _accounts(session: Session, account_ids: Sequence[uuid.UUID]) -> list[Account]:
    wanted = list(dict.fromkeys(account_ids))
    found = list(session.scalars(select(Account).where(Account.id.in_(wanted))).all())
    if len(found) != len(wanted):
        raise UnknownAccountsError()
    return found
