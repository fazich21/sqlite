"""
check_db.py - Look inside tasks.db without starting the server.

Run it with:   python check_db.py

It shows:
    1. Which database file is used (full path)
    2. Which tables exist
    3. Which tasks are saved

It only READS. It never creates or changes anything.
"""

from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from database import DATABASE_PATH, engine
from models import Task

print("=" * 60)
print("Database file :", DATABASE_PATH)

# Connecting to a missing SQLite file would silently create an empty one,
# so we check first.
if not DATABASE_PATH.exists():
    print("File exists   : NO")
    print()
    print("tasks.db has not been created yet.")
    print("Start the server once:  python -m uvicorn sqlite_api:app --reload")
    print("=" * 60)
    raise SystemExit

print("File exists   : YES")
print("File size     :", DATABASE_PATH.stat().st_size, "bytes")

# --- Tables ---------------------------------------------------------------
tables = inspect(engine).get_table_names()
print("Tables        :", tables if tables else "(none)")

if "tasks" not in tables:
    print()
    print("The 'tasks' table does not exist yet. Start the server once to create it.")
    print("=" * 60)
    raise SystemExit

# --- Tasks ----------------------------------------------------------------
with Session(engine) as session:
    tasks = session.scalars(select(Task).order_by(Task.id)).all()

    print("Saved tasks   :", len(tasks))
    print("-" * 60)

    if not tasks:
        print("(no tasks saved yet)")

    for task in tasks:
        status = "[x]" if task.completed else "[ ]"
        print(f"{task.id:>3}  {status}  {task.title}   (owner: {task.owner})")

print("=" * 60)
