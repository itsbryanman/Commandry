"""Commandry database setup — SQLite via synchronous SQLAlchemy."""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DB_PATH = os.environ.get("COMMANDRY_DB", "/data/commandry/commandry.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

# FastAPI may serve requests in worker threads, so disable SQLite's same-thread check.
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    """Create all tables if they don't exist."""
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    from models import Base as _  # noqa: F401 - ensure model metadata is registered

    Base.metadata.create_all(bind=engine)


def get_db():
    db: Session = session_factory()
    try:
        yield db
    finally:
        db.close()
