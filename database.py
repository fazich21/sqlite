"""
database.py - Everything about CONNECTING to the SQLite database.

Big picture:
    ENGINE   = the connection to the database file (tasks.db).
    SESSION  = one "conversation" with the database. You add / change / delete
               things inside a session, then call commit() to save them.
    BASE     = the parent class of all our table classes (see models.py).
    get_db() = a FastAPI dependency that gives each request its own session
               and closes it when the request is finished.
"""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# ---------------------------------------------------------------------------
# 1. WHERE IS THE DATABASE FILE?
#    __file__ is the location of THIS file (database.py).
#    We build the path from it, so tasks.db is ALWAYS created next to
#    database.py - it does not matter which folder you run Uvicorn from.
#    (A path like "./tasks.db" would depend on the current folder, and could
#    silently create a second, empty database somewhere else.)
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "tasks.db"

# URL.create builds the "sqlite:///C:/.../tasks.db" connection string for us.
# It also works correctly on Windows paths that contain spaces.
DATABASE_URL = URL.create(drivername="sqlite", database=str(DATABASE_PATH))

# ---------------------------------------------------------------------------
# 2. THE ENGINE
#    check_same_thread=False is needed for SQLite + FastAPI, because FastAPI
#    can handle one request in a different thread than the one that opened
#    the connection. Each request still gets its own session (see get_db).
# ---------------------------------------------------------------------------

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# ---------------------------------------------------------------------------
# 3. THE SESSION FACTORY
#    SessionLocal() creates a new session every time you call it.
# ---------------------------------------------------------------------------

SessionLocal = sessionmaker(bind=engine)

# ---------------------------------------------------------------------------
# 4. THE BASE CLASS
#    Every table class in models.py inherits from this.
# ---------------------------------------------------------------------------


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# 5. THE DATABASE DEPENDENCY
#    Use it in an endpoint like:   db: Session = Depends(get_db)
#    FastAPI will:
#       1. create a session before your endpoint runs,
#       2. pass it to your endpoint as `db`,
#       3. close it afterwards (the "finally" part), even if an error happens.
# ---------------------------------------------------------------------------


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
