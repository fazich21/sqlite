"""
sqlite_api.py - The Task Manager API, but tasks are saved in SQLite (tasks.db).

Run it with:   python -m uvicorn sqlite_api:app --reload

It follows the SAME rules as your old main.py:
    - You must be logged in for every /tasks endpoint.
    - A normal user can only see and change THEIR OWN tasks.
    - An admin can see and change ALL tasks.
    - Only an admin can delete tasks.
The only difference: tasks now live in the database, so they survive restarts.
"""

from contextlib import asynccontextmanager
from typing import List

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

import models  # importing this file tells SQLAlchemy that the `tasks` table exists
import schemas
from auth import get_current_user, require_admin, router as auth_router
from database import Base, engine, get_db


# ---------------------------------------------------------------------------
# 1. START-UP: create the tables automatically
#    This code runs ONCE when the server starts. create_all() creates tasks.db
#    and the `tasks` table if they do not exist yet. If they already exist,
#    it does nothing, so your saved tasks are never touched.
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Task Manager API (SQLite)", lifespan=lifespan)

# Adds /auth/register, /auth/login and /auth/me (unchanged, from auth.py)
app.include_router(auth_router)


# ---------------------------------------------------------------------------
# 2. HELPERS
# ---------------------------------------------------------------------------

def tasks_visible_to(user: dict):
    """
    Build a database query for the tasks this user may see.
    Admin  -> all tasks.
    User   -> only tasks where owner == their username.
    """
    query = select(models.Task)
    if user["role"] != "admin":
        query = query.where(models.Task.owner == user["username"])
    return query


def get_task_or_404(db: Session, task_id: int, user: dict) -> models.Task:
    """Find one task the user is allowed to see, or raise 404."""
    task = db.get(models.Task, task_id)

    can_access = task is not None and (
        user["role"] == "admin" or task.owner == user["username"]
    )

    if not can_access:
        # We say "not found" (not "forbidden") so users can't guess other
        # people's IDs. Same behaviour as your old main.py.
        raise HTTPException(status_code=404, detail="Task not found")

    return task


# ---------------------------------------------------------------------------
# 3. ENDPOINTS
# ---------------------------------------------------------------------------

@app.get("/")
def home():
    # Public endpoint - no login needed
    return {"message": "Task Manager API (SQLite version) is running"}


# CREATE a task
@app.post(
    "/tasks",
    response_model=schemas.TaskMessage,
    status_code=status.HTTP_201_CREATED,  # 201 = "Created"
)
def create_task(
    task_data: schemas.TaskCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    new_task = models.Task(
        title=task_data.title,
        completed=task_data.completed,
        owner=user["username"],  # remember who created it
    )

    db.add(new_task)  # 1. put it in the session (not saved yet)
    db.commit()  # 2. save it permanently in tasks.db
    db.refresh(new_task)  # 3. reload it so we get the new id the database made

    return {"message": "Task created successfully", "task": new_task}


# SEARCH tasks by title
# (This must stay ABOVE /tasks/{task_id}, otherwise FastAPI would think the
#  word "search" is a task_id.)
@app.get("/tasks/search", response_model=schemas.TaskSearchResult)
def search_tasks(  
    title: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    # icontains = "contains this text, ignoring upper/lower case"
    query = tasks_visible_to(user).where(
        models.Task.title.icontains(title, autoescape=True)
    )
    tasks = db.scalars(query.order_by(models.Task.id)).all()

    return {
        "search_query": title,
        "total_results": len(tasks),
        "tasks": tasks,
    }


# READ all tasks
@app.get("/tasks", response_model=List[schemas.TaskOut])
def get_tasks(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    return db.scalars(tasks_visible_to(user).order_by(models.Task.id)).all()


# READ one task
@app.get("/tasks/{task_id}", response_model=schemas.TaskOut)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    return get_task_or_404(db, task_id, user)


# UPDATE a task completely (PUT = replace all editable fields)
@app.put("/tasks/{task_id}", response_model=schemas.TaskMessage)
def update_task(
    task_id: int,
    task_data: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    task = get_task_or_404(db, task_id, user)

    task.title = task_data.title
    task.completed = task_data.completed

    db.commit()
    db.refresh(task)

    return {"message": "Task updated successfully", "task": task}


# UPDATE a task partially (PATCH = change only the fields that were sent)
@app.patch("/tasks/{task_id}", response_model=schemas.TaskMessage)
def patch_task(
    task_id: int,
    task_data: schemas.TaskPatch,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    task = get_task_or_404(db, task_id, user)

    # exclude_unset=True -> only the fields the client really sent.
    changes = task_data.model_dump(exclude_unset=True)

    if not changes:
        raise HTTPException(
            status_code=400,
            detail="Send at least one field to update: title or completed",
        )

    for field_name, new_value in changes.items():
        setattr(task, field_name, new_value)  # same as: task.title = new_value

    db.commit()
    db.refresh(task)

    return {"message": "Task updated successfully", "task": task}


# DELETE a task (admins only)
@app.delete("/tasks/{task_id}", response_model=schemas.TaskMessage)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(require_admin),
):
    task = get_task_or_404(db, task_id, user)

    # Make a copy of the task BEFORE deleting, so we can show it in the answer.
    deleted_task = schemas.TaskOut.model_validate(task)

    db.delete(task)
    db.commit()

    return {"message": "Task deleted successfully", "task": deleted_task}
