
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

from auth import get_current_user, require_admin, router as auth_router

app = FastAPI()

# Adds /auth/register, /auth/login and /auth/me
app.include_router(auth_router)

# Each task is saved as a dict: {"id", "title", "completed", "owner"}
tasks = []
next_id = 1


class Task(BaseModel):
    title: str
    completed: bool = False


# ---------------------------------------------------------------------------
# Authorization rules for tasks:
#   - You must be logged in for every /tasks endpoint.
#   - A normal user can only see and change THEIR OWN tasks.
#   - An admin can see and change ALL tasks.
#   - Only an admin can delete tasks.
# ---------------------------------------------------------------------------

def can_access(user: dict, task: dict) -> bool:
    return user["role"] == "admin" or task["owner"] == user["username"]


def find_task(task_id: int, user: dict) -> dict:
    """Find a task the user is allowed to see, or raise 404."""
    for task in tasks:
        if task["id"] == task_id and can_access(user, task):
            return task

    # We say "not found" (not "forbidden") so users can't guess other people's IDs
    raise HTTPException(status_code=404, detail="Task not found")


@app.get("/")
def home():
    # Public endpoint - no login needed
    return {"message": "Task Manager API is running"}


# CREATE a task
@app.post("/tasks")
def create_task(task: Task, user: dict = Depends(get_current_user)):
    global next_id

    new_task = {
        "id": next_id,
        "title": task.title,
        "completed": task.completed,
        "owner": user["username"],  # remember who created it
    }
    tasks.append(new_task)
    next_id += 1

    return {
        "message": "Task created successfully",
        "task": new_task
    }


# SEARCH tasks by title
@app.get("/tasks/search")
def search_tasks(title: str, user: dict = Depends(get_current_user)):
    search_results = []

    for task in tasks:
        if can_access(user, task) and title.lower() in task["title"].lower():
            search_results.append(task)

    return {
        "search_query": title,
        "total_results": len(search_results),
        "tasks": search_results
    }


# READ all tasks
@app.get("/tasks")
def get_tasks(user: dict = Depends(get_current_user)):
    return [task for task in tasks if can_access(user, task)]


# READ one task
@app.get("/tasks/{task_id}")
def get_task(task_id: int, user: dict = Depends(get_current_user)):
    return find_task(task_id, user)


# UPDATE a task
@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: Task, user: dict = Depends(get_current_user)):
    existing = find_task(task_id, user)

    existing["title"] = task.title
    existing["completed"] = task.completed

    return {
        "message": "Task updated successfully",
        "task": existing
    }


# DELETE a task (admins only)
@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, user: dict = Depends(require_admin)):
    task = find_task(task_id, user)
    tasks.remove(task)

    return {
        "message": "Task deleted successfully",
        "task": task
    }
