"""Task Management API — FastAPI implementation.

Endpoints:
  GET    /tasks              List tasks (filter by ?status=todo|done|all)
  GET    /tasks/{id}         Get a single task by ID
  POST   /tasks              Create a new task
  PUT    /tasks/{id}         Update task fields
  PATCH  /tasks/{id}/status  Toggle task status (todo ↔ done)
  DELETE /tasks/{id}         Delete a task
"""

from datetime import date, datetime
from enum import Enum
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, model_validator
from pydantic.functional_validators import AfterValidator
from typing_extensions import Annotated

app = FastAPI(title="Task Manager API", version="1.0.0")


# ── Status Enum ──────────────────────────────────────────────────────

class TaskStatus(str, Enum):
    """Valid task statuses."""
    todo = "todo"
    done = "done"


class StatusFilter(str, Enum):
    """Allowed values for the ?status filter parameter."""
    todo = "todo"
    done = "done"
    all = "all"


# ── Validation Helpers ──────────────────────────────────────────────

def validate_date_not_past(v: date) -> date:
    """Ensure due_date is not in the past (allows today)."""
    if v < date.today():
        raise ValueError("due_date cannot be in the past")
    return v


# ── Pydantic Models ─────────────────────────────────────────────────

class TaskBase(BaseModel):
    """Shared fields for Task models."""
    title: str = Field(..., min_length=1, description="Task title (required)")
    description: Optional[str] = Field(None, description="Optional task description")
    due_date: Optional[Annotated[date, AfterValidator(validate_date_not_past)]] = Field(
        None, description="Due date (YYYY-MM-DD, must not be in the past)"
    )
    status: TaskStatus = Field(default=TaskStatus.todo, description="Task status")


class TaskCreate(BaseModel):
    """Schema for creating a new task."""
    title: str = Field(..., min_length=1, description="Task title (required)")
    description: Optional[str] = Field(None, description="Optional task description")
    due_date: Optional[Annotated[date, AfterValidator(validate_date_not_past)]] = Field(
        None, description="Due date (YYYY-MM-DD, must not be in the past)"
    )


class TaskUpdate(BaseModel):
    """Schema for updating an existing task. All fields are optional."""
    title: Optional[str] = Field(None, min_length=1, description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    due_date: Optional[Annotated[date, AfterValidator(validate_date_not_past)]] = Field(
        None, description="Due date (YYYY-MM-DD, must not be in the past)"
    )
    status: Optional[TaskStatus] = Field(None, description="Task status")


class Task(TaskBase):
    """Complete task model returned by the API."""
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ── In-Memory Store ─────────────────────────────────────────────────

_tasks: list[dict] = []
_next_id: int = 1


def _get_task_or_404(task_id: int) -> dict:
    """Retrieve a task by ID or raise 404."""
    for task in _tasks:
        if task["id"] == task_id:
            return task
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


def _sort_tasks(tasks: list[dict]) -> list[dict]:
    """Sort tasks by due_date ascending (None dates after dated ones)."""
    return sorted(tasks, key=lambda t: (t["due_date"] is None, t["due_date"] or date.min))


# ── API Endpoints ───────────────────────────────────────────────────

@app.get("/tasks", response_model=list[Task])
def list_tasks(status: StatusFilter = Query(StatusFilter.all, alias="status")) -> list[dict]:
    """List tasks, optionally filtered by status.

    Results are sorted by due_date ascending.
    """
    if status == StatusFilter.all:
        filtered = _tasks[:]
    else:
        filtered = [t for t in _tasks if t["status"] == status.value]
    return _sort_tasks(filtered)


@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int) -> dict:
    """Get a single task by its ID."""
    return _get_task_or_404(task_id)


@app.post("/tasks", response_model=Task, status_code=201)
def create_task(payload: TaskCreate) -> dict:
    """Create a new task."""
    global _next_id
    now = datetime.now()
    task = {
        "id": _next_id,
        "title": payload.title,
        "description": payload.description,
        "due_date": payload.due_date,
        "status": TaskStatus.todo,
        "created_at": now,
    }
    _tasks.append(task)
    _next_id += 1
    return task


@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, payload: TaskUpdate) -> dict:
    """Update an existing task. Only provided fields are changed."""
    task = _get_task_or_404(task_id)

    if payload.title is not None:
        task["title"] = payload.title
    if payload.description is not None:
        task["description"] = payload.description
    if payload.due_date is not None:
        task["due_date"] = payload.due_date
    if payload.status is not None:
        task["status"] = payload.status

    return task


@app.patch("/tasks/{task_id}/status", response_model=Task)
def toggle_task_status(task_id: int) -> dict:
    """Toggle task status between todo and done."""
    task = _get_task_or_404(task_id)
    task["status"] = TaskStatus.done if task["status"] == TaskStatus.todo else TaskStatus.todo
    return task


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int) -> None:
    """Delete a task by its ID."""
    task = _get_task_or_404(task_id)
    _tasks.remove(task)
    return None
