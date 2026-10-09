"""Create the Income table (#35).

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-09
"""
# mypy: disallow-any-expr=False
# alembic.op is typed with Any.

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | None = None
depends_on: str | None = None

# Decimals are stored as text so SQLite never rounds them through a float.
DECIMAL = sa.String(length=40)


def upgrade() -> None:
    op.create_table(
        "incomes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "position_id", sa.Uuid(), sa.ForeignKey("positions.id"), nullable=False, index=True
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("gross_amount", DECIMAL, nullable=False),
        sa.Column("tax_deducted", DECIMAL, nullable=False),
        sa.Column("net_amount", DECIMAL, nullable=False),
        sa.Column("withdrawn", sa.Boolean(), nullable=False),
        sa.Column("fingerprint", sa.String(length=64), nullable=True, unique=True),
    )
    with op.batch_alter_table("transactions") as batch:
        batch.add_column(
            sa.Column(
                "income_id",
                sa.Uuid(),
                sa.ForeignKey("incomes.id", name="fk_transactions_income_id"),
                nullable=True,
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("transactions") as batch:
        batch.drop_column("income_id")
    op.drop_table("incomes")
