from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import Settings, get_settings


class Base(DeclarativeBase):
    pass


def database_url(settings: Settings) -> str:
    return f"sqlite:///{settings.data_dir / 'wealth.db'}"


@lru_cache  # type: ignore[misc]  # functools.lru_cache is typed with Any
def get_engine() -> Engine:
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    return create_engine(database_url(settings))


@lru_cache  # type: ignore[misc]  # functools.lru_cache is typed with Any
def get_sessionmaker() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine())
