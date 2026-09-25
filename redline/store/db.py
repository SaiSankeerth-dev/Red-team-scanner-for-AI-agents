"""SQLite/Postgres engine + session helpers."""
from __future__ import annotations

import os
from contextlib import contextmanager

from sqlalchemy import create_engine

from .models import Base


def get_db_url() -> str:
    return os.environ.get("DATABASE_URL", "sqlite:///./redline.db")


_engines: dict[str, object] = {}


def init_db(db_url: str | None = None):
    """Return the engine for this URL, creating it (and tables) once.

    :memory: databases are never cached — each caller gets a fresh one,
    which keeps tests isolated.
    """
    url = get_db_url() if db_url is None else db_url
    if url == "sqlite:///:memory:":
        engine = create_engine(url)
        Base.metadata.create_all(engine)
        return engine
    if url not in _engines:
        engine = create_engine(url)
        Base.metadata.create_all(engine)
        _engines[url] = engine
    return _engines[url]


@contextmanager
def session_scope(db_url: str | None = None):
    """Yield a DB session; commits on success, rolls back on error."""
    engine = init_db(db_url)
    from sqlalchemy.orm import sessionmaker

    session = sessionmaker(bind=engine)()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
