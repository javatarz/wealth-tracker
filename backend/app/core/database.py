from collections.abc import Iterator
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
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


def get_session() -> Iterator[Session]:
    with get_sessionmaker()() as session:
        yield session


SessionDependency = Annotated[Session, Depends(get_session)]  # type: ignore[misc]  # sqlalchemy.orm.Session is typed with Any
