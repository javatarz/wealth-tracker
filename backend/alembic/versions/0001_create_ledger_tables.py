"""Create the ledger tables (#26).

Revision ID: 0001
Revises:
Create Date: 2026-10-03
"""
# mypy: disallow-any-expr=False
# sqlalchemy.Column and alembic.op are typed with Any.

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None

# Decimals are stored as text so SQLite never rounds them through a float.
DECIMAL = sa.String(length=40)
LEDGER_TABLES = (
    "lots",
    "transactions",
    "positions",
    "imports",
    "accounts",
    "instruments",
    "household_members",
)


def upgrade() -> None:
    _create_household_members()
    _create_instruments()
    _create_accounts()
    _create_imports()
    _create_positions()
    _create_transactions()
    _create_lots()


def downgrade() -> None:
    for table in LEDGER_TABLES:
        op.drop_table(table)


def _create_household_members() -> None:
    op.create_table(
        "household_members",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
    )


def _create_instruments() -> None:
    op.create_table(
        "instruments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("identity", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("amfi_code", sa.String(length=16), nullable=True),
        sa.Column("isin", sa.String(length=12), nullable=True),
        sa.UniqueConstraint("kind", "identity"),
    )


def _create_accounts() -> None:
    op.create_table(
        "accounts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "household_member_id",
            sa.Uuid(),
            sa.ForeignKey("household_members.id"),
            nullable=False,
        ),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("institution", sa.String(length=255), nullable=False),
        sa.Column("number", sa.String(length=64), nullable=False),
        sa.UniqueConstraint("household_member_id", "kind", "institution", "number"),
    )


def _create_imports() -> None:
    op.create_table(
        "imports",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "household_member_id",
            sa.Uuid(),
            sa.ForeignKey("household_members.id"),
            nullable=False,
        ),
        sa.Column("content_hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column("source", sa.String(length=16), nullable=False),
        sa.Column("statement_type", sa.String(length=16), nullable=False),
        sa.Column("period_from", sa.Date(), nullable=False),
        sa.Column("period_to", sa.Date(), nullable=False),
        sa.Column("parser_version", sa.String(length=32), nullable=False),
        sa.Column("imported_at", sa.DateTime(), nullable=False),
    )


def _create_positions() -> None:
    op.create_table(
        "positions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("account_id", sa.Uuid(), sa.ForeignKey("accounts.id"), nullable=False),
        sa.Column("instrument_id", sa.Uuid(), sa.ForeignKey("instruments.id"), nullable=False),
        sa.UniqueConstraint("account_id", "instrument_id"),
    )


def _create_transactions() -> None:
    op.create_table(
        "transactions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "position_id", sa.Uuid(), sa.ForeignKey("positions.id"), nullable=False, index=True
        ),
        sa.Column("import_id", sa.Uuid(), sa.ForeignKey("imports.id"), nullable=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("units", DECIMAL, nullable=False),
        sa.Column("amount", DECIMAL, nullable=True),
        sa.Column("nav", DECIMAL, nullable=True),
        sa.Column("synthetic", sa.Boolean(), nullable=False),
        sa.Column("fingerprint", sa.String(length=64), nullable=True, unique=True),
    )


def _create_lots() -> None:
    op.create_table(
        "lots",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "position_id", sa.Uuid(), sa.ForeignKey("positions.id"), nullable=False, index=True
        ),
        sa.Column(
            "transaction_id",
            sa.Uuid(),
            sa.ForeignKey("transactions.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("acquired_on", sa.Date(), nullable=False),
        sa.Column("units", DECIMAL, nullable=False),
        sa.Column("cost", DECIMAL, nullable=False),
        sa.Column("remaining_units", DECIMAL, nullable=False),
        sa.Column("remaining_cost", DECIMAL, nullable=False),
    )
