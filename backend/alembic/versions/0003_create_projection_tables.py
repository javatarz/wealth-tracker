"""Create the projection tables and Goal Projection Strategy columns (#38).

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-09
"""
# mypy: disallow-any-expr=False
# sqlalchemy.Column and alembic.op are typed with Any.

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | None = None
depends_on: str | None = None

# Decimals are stored as text so SQLite never rounds them through a float.
DECIMAL = sa.String(length=40)
NEW_GOAL_COLUMNS = ("projection_strategy", "cagr_rate", "trailing_window_years")


def upgrade() -> None:
    _add_goal_columns()
    _create_scheduled_transactions()


def downgrade() -> None:
    op.drop_table("scheduled_transactions")
    for column in NEW_GOAL_COLUMNS:
        op.drop_column("goals", column)


def _add_goal_columns() -> None:
    op.add_column("goals", sa.Column("projection_strategy", sa.String(length=16), nullable=True))
    op.add_column("goals", sa.Column("cagr_rate", DECIMAL, nullable=True))
    op.add_column("goals", sa.Column("trailing_window_years", sa.Integer(), nullable=True))


def _create_scheduled_transactions() -> None:
    op.create_table(
        "scheduled_transactions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "position_id", sa.Uuid(), sa.ForeignKey("positions.id"), nullable=False, index=True
        ),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("direction", sa.String(length=16), nullable=False),
        sa.Column("frequency", sa.String(length=16), nullable=False),
        sa.Column("amount", DECIMAL, nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("escalation_rate", DECIMAL, nullable=False),
    )
