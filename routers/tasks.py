"""
Tasks router — AC13-19, AC23-26.

# ROUTE ORDERING NOTE (do not re-arrange without care):
# Static sub-paths (e.g. GET /tasks) must appear before dynamic ones
# (e.g. GET /tasks/{task_id}).  FastAPI matches routes top-to-bottom;
# a dynamic segment would capture 'summary', 'search', etc. if listed first.

Endpoints (all scoped to /users/{username}/tasks)
--------------------------------------------------
POST   /users/{username}/tasks                           — create task
GET    /users/{username}/tasks                           — list tasks (filter + search)
GET    /users/{username}/tasks/{task_id}                 — get task
PUT    /users/{username}/tasks/{task_id}                 — update task
DELETE /users/{username}/tasks/{task_id}                 — delete task
PATCH  /users/{username}/tasks/{task_id}/status          — change status
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status

from student_app.models import (
    VALID_TRANSITIONS,
    Category,
    Priority,
    TaskCreate,
    TaskOut,
    TaskStatus,
    TaskStatusUpdate,
    TaskUpdate,
)
from student_app.routers.users import _require_user
from student_app.storage import storage

router = APIRouter(
    prefix="/users/{username}/tasks",
    tags=["tasks"],
)


def _now_iso() -> str:
    """Return current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _task_to_out(t: dict) -> TaskOut:
    """Convert a raw storage dict to a TaskOut model."""
    return TaskOut(**t)


# ---------------------------------------------------------------------------
# Endpoints — ordered: static paths BEFORE /{task_id}
# ---------------------------------------------------------------------------


@router.post("", status_code=status.HTTP_201_CREATED, response_model=TaskOut)
def create_task(username: str, payload: TaskCreate) -> TaskOut:
    """Create a new task for the given user.

    Returns 404 if the user does not exist.
    """
    _require_user(username)

    now = _now_iso()
    task_id = str(uuid.uuid4())
    task_dict = {
        "id": task_id,
        "username": username,
        "title": payload.title,
        "description": payload.description,
        "due_date": payload.due_date,
        "priority": payload.priority,
        "category": payload.category,
        "subject_id": payload.subject_id,
        "tags": payload.tags,
        "status": TaskStatus.todo.value,
        "created_at": now,
        "updated_at": now,
        "completed_at": None,
    }
    storage.tasks[task_id] = task_dict
    return _task_to_out(task_dict)


@router.get("", response_model=List[TaskOut])
def list_tasks(
    username: str,
    # NOTE: use alias to avoid shadowing `from fastapi import status`
    status_filter: Optional[str] = Query(default=None, alias="status"),
    priority: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    search: Optional[str] = Query(
        default=None,
        description="Case-insensitive substring search across title and description"
    ),
) -> List[TaskOut]:
    """List tasks for the given user, newest first.

    Supports optional filtering by status, priority, category, and free-text
    search (matched case-insensitively against title and description).

    Returns 404 if the user does not exist.
    """
    _require_user(username)

    tasks = [t for t in storage.tasks.values() if t["username"] == username]

    # Apply filters
    if status_filter is not None:
        tasks = [t for t in tasks if t["status"] == status_filter]
    if priority is not None:
        tasks = [t for t in tasks if t["priority"] == priority]
    if category is not None:
        tasks = [t for t in tasks if t["category"] == category]
    if search is not None:
        q = search.lower()
        tasks = [
            t for t in tasks
            if q in t["title"].lower()
            or (t["description"] and q in t["description"].lower())
        ]

    # Newest first
    tasks.sort(key=lambda t: t["created_at"], reverse=True)
    return [_task_to_out(t) for t in tasks]


# ---- dynamic path endpoints below ----------------------------------------


@router.get("/{task_id}", response_model=TaskOut)
def get_task(username: str, task_id: str) -> TaskOut:
    """Retrieve a single task by ID.

    Returns 404 if the user or task does not exist.
    """
    _require_user(username)
    task = _get_user_task(username, task_id)
    return _task_to_out(task)


@router.put("/{task_id}", response_model=TaskOut)
def update_task(username: str, task_id: str, payload: TaskUpdate) -> TaskOut:
    """Update task fields.  Only provided fields are changed.

    Refreshes ``updated_at`` on every successful update.
    Returns 404 if the user or task does not exist.
    """
    _require_user(username)
    task = _get_user_task(username, task_id)

    if payload.title is not None:
        task["title"] = payload.title
    if payload.description is not None:
        task["description"] = payload.description
    if payload.due_date is not None:
        task["due_date"] = payload.due_date
    if payload.priority is not None:
        task["priority"] = payload.priority
    if payload.category is not None:
        task["category"] = payload.category
    if payload.subject_id is not None:
        task["subject_id"] = payload.subject_id
    if payload.tags is not None:
        task["tags"] = payload.tags

    task["updated_at"] = _now_iso()
    return _task_to_out(task)


@router.delete("/{task_id}", response_model=dict)
def delete_task(username: str, task_id: str) -> dict:
    """Delete a task and all its subtasks.

    Returns 404 if the user or task does not exist.
    """
    _require_user(username)
    _get_user_task(username, task_id)  # validates ownership

    # Cascade: remove subtasks
    orphan_ids = [
        sid for sid, s in storage.subtasks.items() if s["task_id"] == task_id
    ]
    for sid in orphan_ids:
        del storage.subtasks[sid]

    del storage.tasks[task_id]
    return {"detail": f"Task '{task_id}' deleted."}


@router.patch("/{task_id}/status", response_model=TaskOut)
def change_task_status(
    username: str, task_id: str, payload: TaskStatusUpdate
) -> TaskOut:
    """Advance a task's status following the allowed transition chain.

    Allowed transitions:
        todo → in_progress → done

    No backwards movement and no skipping steps.
    Returns 400 for invalid transitions.
    Returns 404 if the user or task does not exist.
    """
    _require_user(username)
    task = _get_user_task(username, task_id)

    current = task["status"]
    new_status = payload.status.value

    allowed = VALID_TRANSITIONS.get(current, set())
    if new_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Cannot transition task from '{current}' to '{new_status}'. "
                f"Allowed next states: {sorted(allowed) or 'none (terminal state)'}."
            ),
        )

    task["status"] = new_status
    task["updated_at"] = _now_iso()
    if new_status == TaskStatus.done:
        task["completed_at"] = _now_iso()

    return _task_to_out(task)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_user_task(username: str, task_id: str) -> dict:
    """Return the task dict or raise 404 if not found / wrong user."""
    task = storage.tasks.get(task_id)
    if task is None or task["username"] != username:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task '{task_id}' not found for user '{username}'.",
        )
    return task
