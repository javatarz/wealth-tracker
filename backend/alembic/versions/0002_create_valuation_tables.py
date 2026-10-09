"""Add Valuation Strategy terms, price history, and appraisals (#34).

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


def upgrade() -> None:
    _add_instrument_terms()
    _create_prices()
    _create_appraisals()


def downgrade() -> None:
    op.drop_table("appraisals")
    op.drop_table("prices")
    for column in _INSTRUMENT_TERMS:
        op.drop_column("instruments", column)


_INSTRUMENT_TERMS = (
    "valuation_strategy",
    "principal",
    "interest_rate",
    "accrual_start",
    "maturity_date",
    "annual_income",
    "cap_rate",
)


def _add_instrument_terms() -> None:
    op.add_column(
        "instruments",
        sa.Column(
            "valuation_strategy",
            sa.String(length=32),
            nullable=False,
            server_default="market_priced",
        ),
    )
    for column in ("principal", "interest_rate", "annual_income", "cap_rate"):
        op.add_column("instruments", sa.Column(column, DECIMAL, nullable=True))
    for column in ("accrual_start", "maturity_date"):
        op.add_column("instruments", sa.Column(column, sa.Date(), nullable=True))


def _create_prices() -> None:
    op.create_table(
        "prices",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "instrument_id",
            sa.Uuid(),
            sa.ForeignKey("instruments.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("price", DECIMAL, nullable=False),
        sa.Column("source", sa.String(length=16), nullable=False),
        sa.UniqueConstraint("instrument_id", "date"),
    )


def _create_appraisals() -> None:
    op.create_table(
        "appraisals",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "instrument_id",
            sa.Uuid(),
            sa.ForeignKey("instruments.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("value", DECIMAL, nullable=False),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("instrument_id", "date"),
    )
