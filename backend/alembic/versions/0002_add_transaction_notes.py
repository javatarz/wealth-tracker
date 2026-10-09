"""Add a notes field to Transactions (#30).

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-09
"""
# mypy: disallow-any-expr=False
# alembic.op is typed with Any.

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    with op.batch_alter_table("transactions") as batch:
        batch.add_column(sa.Column("notes", sa.String(length=500), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("transactions") as batch:
        batch.drop_column("notes")
