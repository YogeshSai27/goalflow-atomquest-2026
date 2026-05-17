"""
database.py — SQLite connection, session factory, and declarative Base.
All models import Base from here. All routes import get_db from here.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# ---------------------------------------------------------------------------
# Database file location
# ---------------------------------------------------------------------------
# On Render the /data directory is the persistent disk mount point.
# Locally it just lives next to the project root.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./goalflow.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Required for SQLite + FastAPI
    echo=False,                                   # Set True to debug SQL
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# ---------------------------------------------------------------------------
# Dependency — yields a DB session and guarantees cleanup
# ---------------------------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Helper — create all tables (called once at startup)
# ---------------------------------------------------------------------------
def init_db():
    # Import models so SQLAlchemy registers them before create_all
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    _migrate()


def _migrate():
    """
    Safe column additions for databases created before a model change.
    SQLite does not support DROP/ALTER beyond ADD COLUMN.
    Each statement is wrapped so it no-ops if the column already exists.
    """
    migrations = [
        "ALTER TABLE goal_sheets ADD COLUMN manager_comments TEXT",
        "ALTER TABLE goal_sheets ADD COLUMN return_reason TEXT",
    ]
    with engine.connect() as conn:
        for sql in migrations:
            try:
                conn.execute(__import__("sqlalchemy").text(sql))
                conn.commit()
            except Exception:
                pass  # column already exists — safe to ignore
