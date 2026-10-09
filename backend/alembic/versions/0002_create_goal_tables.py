"""Create the Goal tables (#32).

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-09
"""
# mypy: disallow-any-expr=False
# sqlalchemy.Column and alembic.op are typed with Any.

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | None = None
depends_on: str | None = None

# Decimals are stored as text so SQLite never rounds them through a float.
DECIMAL = sa.String(length=40)
GOAL_TABLES = ("goal_accounts", "goals")


def upgrade() -> None:
    _create_goals()
    _create_goal_accounts()


def downgrade() -> None:
    for table in GOAL_TABLES:
        op.drop_table(table)


def _create_goals() -> None:
    op.create_table(
        "goals",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "household_member_id", sa.Uuid(), sa.ForeignKey("household_members.id"), nullable=False
        ),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("target_amount", DECIMAL, nullable=False),
        sa.Column("target_date", sa.Date(), nullable=False),
    )


def _create_goal_accounts() -> None:
    op.create_table(
        "goal_accounts",
        sa.Column(
            "goal_id", sa.Uuid(), sa.ForeignKey("goals.id", ondelete="CASCADE"), primary_key=True
        ),
        sa.Column("account_id", sa.Uuid(), sa.ForeignKey("accounts.id"), primary_key=True),
    )
