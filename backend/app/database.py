# backend/app/database.py

"""
Database configuration.

The calculator currently performs calculations without
requiring persistent database storage.
"""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    sessionmaker,
)


# ---------------------------------------------------------------------------
# Database location
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"

DATABASE_FILE = (
    DATA_DIR / "zp3_calculator.db"
)

DATABASE_URL = (
    f"sqlite:///{DATABASE_FILE}"
)


# ---------------------------------------------------------------------------
# SQLAlchemy engine
# ---------------------------------------------------------------------------

engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
    },
)


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


# ---------------------------------------------------------------------------
# Base model
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Database initialisation
# ---------------------------------------------------------------------------

def init_database() -> None:
    """
    Initialise database tables.

    Database models should be imported here when they exist.
    """

    try:

        from .database_models import (
            ProjectDB,
            LoopDB,
            DeviceDB,
            CalculationDB,
        )

    except ImportError:
        # Database models are not currently installed.
        return

    Base.metadata.create_all(
        bind=engine
    )


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------

def get_db():

    db = SessionLocal()

    try:

        yield db

    finally:

        db.close()
