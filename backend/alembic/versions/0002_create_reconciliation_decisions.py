"""Record how statement mismatches were resolved (#27).

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-03
"""
# mypy: disallow-any-expr=False
# sqlalchemy.Column and alembic.op are typed with Any.

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | None = None
depends_on: str | None = None

DECIMAL = sa.String(length=40)


def upgrade() -> None:
    op.create_table(
        "reconciliation_decisions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("import_id", sa.Uuid(), sa.ForeignKey("imports.id"), nullable=False, index=True),
        sa.Column(
            "position_id", sa.Uuid(), sa.ForeignKey("positions.id"), nullable=True, index=True
        ),
        sa.Column("scheme", sa.String(length=255), nullable=False),
        sa.Column("holding", sa.String(length=255), nullable=False),
        sa.Column("action", sa.String(length=16), nullable=False),
        sa.Column("statement_units", DECIMAL, nullable=False),
        sa.Column("derived_units", DECIMAL, nullable=False),
        sa.Column("delta", DECIMAL, nullable=False),
        sa.Column("cost_basis", DECIMAL, nullable=True),
        sa.Column("parser_version", sa.String(length=32), nullable=False),
        sa.Column("decided_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("reconciliation_decisions")
