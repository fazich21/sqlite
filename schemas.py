"""
schemas.py - Pydantic models that describe the JSON going IN and OUT of the API.

Do not confuse the two kinds of "models":
    models.py   (SQLAlchemy) = what the DATABASE TABLE looks like.
    schemas.py  (Pydantic)   = what the JSON in requests / responses looks like.

Why keep them separate?  The client must NOT be able to send "id" or "owner".
The server decides those (the database creates the id, the login token gives
the owner). So the input schemas below only contain title and completed.
"""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# INPUT schemas (what the client sends)
# ---------------------------------------------------------------------------

class TaskCreate(BaseModel):
    """Body of POST /tasks."""

    # Spaces around the title are removed, so "   " counts as empty (rejected).
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=200)
    completed: bool = False


class TaskUpdate(TaskCreate):
    """
    Body of PUT /tasks/{id}.
    PUT replaces the whole task, so it has the same fields as TaskCreate.
    (If you leave out "completed", it is set back to false.)
    """


class TaskPatch(BaseModel):
    """
    Body of PATCH /tasks/{id}.
    PATCH changes ONLY the fields you send, so both fields are optional.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    completed: Optional[bool] = None

    @field_validator("title", "completed")
    @classmethod
    def must_not_be_null(cls, value):
        # Leaving a field OUT is fine ("don't change it").
        # Sending it as null is not: the table does not allow empty values.
        if value is None:
            raise ValueError("cannot be null - leave the field out to keep it unchanged")
        return value


# ---------------------------------------------------------------------------
# OUTPUT schemas (what the API sends back)
# ---------------------------------------------------------------------------

class TaskOut(BaseModel):
    """One task as the client sees it."""

    # from_attributes=True lets Pydantic read a database object (task.title)
    # and not only a dict (task["title"]).
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    completed: bool
    owner: str


class TaskMessage(BaseModel):
    """Same shape your old main.py used: a message plus the task."""

    message: str
    task: TaskOut


class TaskSearchResult(BaseModel):
    """Response of GET /tasks/search (same shape as your old main.py)."""

    search_query: str
    total_results: int
    tasks: List[TaskOut]
