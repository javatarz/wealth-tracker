from alembic import context

from app.core.database import Base, get_engine

target_metadata = Base.metadata  # type: ignore[misc]  # DeclarativeBase.__init__ takes **kw: Any


def run_migrations_offline() -> None:
    context.configure(
        url=str(get_engine().url),
        target_metadata=target_metadata,
        literal_binds=True,
        render_as_batch=True,
    )
    _run_in_transaction()


def run_migrations_online() -> None:
    with get_engine().connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )
        _run_in_transaction()


def _run_in_transaction() -> None:
    with context.begin_transaction():
        context.run_migrations()


run_migrations = run_migrations_offline if context.is_offline_mode() else run_migrations_online
run_migrations()
