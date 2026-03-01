"""
Subtasks router — AC20-22.

Endpoints (all scoped to /users/{username}/tasks/{task_id}/subtasks)
---------------------------------------------------------------------
POST  /users/{username}/tasks/{task_id}/subtasks                        — create subtask
GET   /users/{username}/tasks/{task_id}/subtasks                        — list subtasks
PATCH /users/{username}/tasks/{task_id}/subtasks/{subtask_id}/toggle    — toggle done/undone
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, HTTPException, status

from student_app.models import SubtaskCreate, SubtaskOut
from student_app.routers.users import _require_user
from student_app.routers.tasks import _get_user_task
from student_app.storage import storage

router = APIRouter(
    prefix="/users/{username}/tasks/{task_id}/subtasks",
    tags=["subtasks"],
)


def _now_iso() -> str:
    """Return current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _get_user_subtask(username: str, task_id: str, subtask_id: str) -> dict:
    """Return the subtask dict or raise 404.

    Validates that the subtask belongs to the correct task and user.
    """
    subtask = storage.subtasks.get(subtask_id)
    if subtask is None or subtask["task_id"] != task_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subtask '{subtask_id}' not found for task '{task_id}'.",
        )
    return subtask


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("", status_code=status.HTTP_201_CREATED, response_model=SubtaskOut)
def create_subtask(
    username: str, task_id: str, payload: SubtaskCreate
) -> SubtaskOut:
    """Create a subtask under the given task.

    Returns 404 if the user or task does not exist.
    """
    _require_user(username)
    _get_user_task(username, task_id)  # validates task ownership

    subtask_id = str(uuid.uuid4())
    subtask_dict = {
        "id": subtask_id,
        "task_id": task_id,
        "title": payload.title,
        "done": False,
        "created_at": _now_iso(),
    }
    storage.subtasks[subtask_id] = subtask_dict
    return SubtaskOut(**subtask_dict)


@router.get("", response_model=List[SubtaskOut])
def list_subtasks(username: str, task_id: str) -> List[SubtaskOut]:
    """List all subtasks for the given task.

    Returns 404 if the user or task does not exist.
    """
    _require_user(username)
    _get_user_task(username, task_id)

    subtasks = [
        SubtaskOut(**s)
        for s in storage.subtasks.values()
        if s["task_id"] == task_id
    ]
    subtasks.sort(key=lambda s: s.created_at)
    return subtasks


@router.patch("/{subtask_id}/toggle", response_model=SubtaskOut)
def toggle_subtask(
    username: str, task_id: str, subtask_id: str
) -> SubtaskOut:
    """Toggle the done/undone state of a subtask.

    Returns 404 if the user, task, or subtask does not exist.
    """
    _require_user(username)
    _get_user_task(username, task_id)
    subtask = _get_user_subtask(username, task_id, subtask_id)

    subtask["done"] = not subtask["done"]
    return SubtaskOut(**subtask)
