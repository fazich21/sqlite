"""
models.py - Database TABLES, written as Python classes (this is the "ORM").

One class = one table.  One object of the class = one row in that table.
So a `Task` object is one row in the `tasks` table.

Your old in-memory task was a dict:   {"id", "title", "completed", "owner"}
The table below has exactly the same four columns.
"""

from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Task(Base):
    __tablename__ = "tasks"  # the real table name inside tasks.db

    # sqlite_autoincrement=True: SQLite never re-uses the ID of a deleted task.
    # Without it, deleting the newest task could make the next new task get
    # the same ID again, which is confusing.
    __table_args__ = {"sqlite_autoincrement": True}

    # Unique number for each task. The database fills it in automatically.
    id: Mapped[int] = mapped_column(primary_key=True)

    # The task text. (Not optional: a task must have a title.)
    title: Mapped[str]

    # True = done, False = not done yet.
    completed: Mapped[bool] = mapped_column(default=False)

    # Username of the person who created the task (taken from the login
    # token). Users still live in users.json, so we store just the name.
    # index=True makes "find all tasks of this user" faster.
    owner: Mapped[str] = mapped_column(index=True)
