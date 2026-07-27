"""
Database engine and session management.

One place creates the SQLAlchemy engine (from `settings.database_url`) and
hands out sessions; nothing else in the codebase should call
`create_engine` directly. Swapping SQLite for Postgres later is a one-line
change to `DATABASE_URL` - nothing in `analytics/`, `forecasting/`, or
`streamlit_app.py` references SQLite specifically.
"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from utils.config import settings
from utils.logger import get_logger

logger = get_logger(__name__)

_SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    """Return the process-wide SQLAlchemy engine, creating it on first call."""
    global _engine, _SessionLocal
    if _engine is None:
        connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
        _engine = create_engine(settings.database_url, connect_args=connect_args)
        _SessionLocal = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False)
        logger.info("Created database engine for %s", settings.database_url)
    return _engine


@contextmanager
def get_session() -> Iterator[Session]:
    """Yield a `Session`, committing on success and rolling back on error.

    Usage:
        with get_session() as session:
            session.execute(...)
    """
    get_engine()  # ensures _SessionLocal is initialized
    assert _SessionLocal is not None
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """Create all tables and indexes by executing `schema.sql`.

    Uses raw DDL (rather than `Base.metadata.create_all`) so the schema is
    identical whether it's applied through SQLAlchemy or through
    `sqlite3` directly (see `etl/load.py`).
    """
    engine = get_engine()
    ddl = _SCHEMA_PATH.read_text()
    with engine.begin() as conn:
        for statement in ddl.split(";"):
            statement = statement.strip()
            if statement:
                conn.execute(text(statement))
    logger.info("Database schema ready")
