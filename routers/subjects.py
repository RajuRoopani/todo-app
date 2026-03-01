"""
Subjects router — AC9-12.

Endpoints (all scoped to /users/{username}/subjects)
------------------------------------------------------
POST   /users/{username}/subjects                    — create subject
GET    /users/{username}/subjects                    — list subjects
DELETE /users/{username}/subjects/{subject_id}       — delete subject
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status

from student_app.models import SubjectCreate, SubjectOut
from student_app.routers.users import _require_user
from student_app.storage import storage

router = APIRouter(
    prefix="/users/{username}/subjects",
    tags=["subjects"],
)


def _now_iso() -> str:
    """Return current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("", status_code=status.HTTP_201_CREATED, response_model=SubjectOut)
def create_subject(username: str, payload: SubjectCreate) -> SubjectOut:
    """Create a new subject for the given user.

    Returns 404 if the user does not exist.
    Returns 409 if the user already has a subject with the same name.
    """
    _require_user(username)

    # Duplicate check (case-sensitive, per-user scope)
    for subj in storage.subjects.values():
        if subj["username"] == username and subj["name"] == payload.name:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Subject '{payload.name}' already exists for user '{username}'.",
            )

    subject_id = str(uuid.uuid4())
    subj_dict = {
        "id": subject_id,
        "username": username,
        "name": payload.name,
        "teacher": payload.teacher,
        "color": payload.color,
        "created_at": _now_iso(),
    }
    storage.subjects[subject_id] = subj_dict
    return SubjectOut(**subj_dict)


@router.get("", response_model=list[SubjectOut])
def list_subjects(username: str) -> list[SubjectOut]:
    """List all subjects belonging to the given user.

    Returns 404 if the user does not exist.
    """
    _require_user(username)

    subjects = [
        SubjectOut(**s)
        for s in storage.subjects.values()
        if s["username"] == username
    ]
    # Stable order: oldest first
    subjects.sort(key=lambda s: s.created_at)
    return subjects


@router.delete(
    "/{subject_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
)
def delete_subject(username: str, subject_id: str) -> dict:
    """Delete a subject by ID.

    Returns 404 if the user or subject does not exist.
    """
    _require_user(username)

    subj = storage.subjects.get(subject_id)
    if subj is None or subj["username"] != username:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject '{subject_id}' not found for user '{username}'.",
        )

    del storage.subjects[subject_id]
    return {"detail": f"Subject '{subject_id}' deleted."}
