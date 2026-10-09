from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import Engine, inspect

import app.ledger.models  # noqa: F401  # registers the ledger tables
from app.core.database import Base

LEDGER_TABLES = {
    "household_members",
    "accounts",
    "instruments",
    "positions",
    "transactions",
    "lots",
    "imports",
    "incomes",
}


def test_migrations_create_every_ledger_table(migrated_engine: Engine) -> None:
    assert set(inspect(migrated_engine).get_table_names()) >= LEDGER_TABLES


def test_migrations_match_the_models(migrated_engine: Engine) -> None:
    with migrated_engine.connect() as connection:
        context = MigrationContext.configure(connection, opts={"compare_type": True})
        assert compare_metadata(context, Base.metadata) == []
