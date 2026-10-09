"""Reading and writing Goals, and resolving the Accounts they are funded from."""

import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.goals.errors import GoalNotFoundError, UnknownAccountsError
from app.goals.models import Goal
from app.ledger.members import default_member
from app.ledger.models import Account


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


def create_goal(session: Session, draft: GoalDraft) -> Goal:
    goal = Goal(
        id=uuid.uuid4(),
        household_member_id=default_member(session).id,
        name=draft.name,
        target_amount=draft.target_amount,
        target_date=draft.target_date,
    )
    goal.accounts = _accounts(session, draft.account_ids)
    session.add(goal)
    return goal


def update_goal(session: Session, goal: Goal, draft: GoalDraft) -> Goal:
    goal.name = draft.name
    goal.target_amount = draft.target_amount
    goal.target_date = draft.target_date
    goal.accounts = _accounts(session, draft.account_ids)
    return goal


def delete_goal(session: Session, goal: Goal) -> None:
    session.delete(goal)


def list_accounts(session: Session) -> Sequence[Account]:
    return session.scalars(select(Account).order_by(Account.institution, Account.number)).all()


def _accounts(session: Session, account_ids: Sequence[uuid.UUID]) -> list[Account]:
    wanted = list(dict.fromkeys(account_ids))
    found = list(session.scalars(select(Account).where(Account.id.in_(wanted))).all())
    if len(found) != len(wanted):
        raise UnknownAccountsError()
    return found
