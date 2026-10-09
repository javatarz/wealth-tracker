"""Create Benchmark assignment and price-history tables (#36, #31).

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-09
"""
# mypy: disallow-any-expr=False
# sqlalchemy.Column is typed with Any.

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | None = None
depends_on: str | None = None

DECIMAL = sa.String(length=40)
NEW_TABLES = ("prices", "instrument_benchmarks", "benchmark_assignments")


def upgrade() -> None:
    _create_benchmark_assignments()
    _create_instrument_benchmarks()
    _create_prices()


def downgrade() -> None:
    for table in NEW_TABLES:
        op.drop_table(table)


def _create_benchmark_assignments() -> None:
    op.create_table(
        "benchmark_assignments",
        sa.Column("asset_class", sa.String(length=32), primary_key=True),
        sa.Column(
            "benchmark_instrument_id",
            sa.Uuid(),
            sa.ForeignKey("instruments.id"),
            nullable=False,
        ),
    )


def _create_instrument_benchmarks() -> None:
    op.create_table(
        "instrument_benchmarks",
        sa.Column("instrument_id", sa.Uuid(), sa.ForeignKey("instruments.id"), primary_key=True),
        sa.Column(
            "benchmark_instrument_id",
            sa.Uuid(),
            sa.ForeignKey("instruments.id"),
            nullable=False,
        ),
    )


def _create_prices() -> None:
    op.create_table(
        "prices",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "instrument_id", sa.Uuid(), sa.ForeignKey("instruments.id"), nullable=False, index=True
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("price", DECIMAL, nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.UniqueConstraint("instrument_id", "date"),
    )
