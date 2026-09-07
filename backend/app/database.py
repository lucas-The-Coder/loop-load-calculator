from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


# ---------------------------------------------------------------------------
# Database location
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

DATABASE_FILE = DATA_DIR / "zp3_calculator.db"

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
    Create database tables if they do not already exist.
    """

    from database_models import (
        ProjectDB,
        LoopDB,
        DeviceDB,
        CalculationDB,
    )

    Base.metadata.create_all(
        bind=engine
    )


def get_db():
    """
    Provide a database session.

    Intended for use with FastAPI dependency injection.
    """

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()
