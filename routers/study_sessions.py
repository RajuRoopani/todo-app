"""
Study Sessions router — AC27-30.

# ROUTE ORDERING NOTE:
# GET /study-sessions/summary MUST be declared BEFORE
# GET /study-sessions/{session_id} (if we ever add it) to avoid
# 'summary' being captured as a dynamic segment.

Endpoints (all scoped to /users/{username}/study-sessions)
----------------------------------------------------------
POST /users/{username}/study-sessions            — log a study session
GET  /users/{username}/study-sessions            — list all sessions (newest first)
GET  /users/{username}/study-sessions/summary    — aggregated stats
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, HTTPException, status

from student_app.models import (
    StudySessionCreate,
    StudySessionOut,
    StudySummaryOut,
    StudySummarySubjectEntry,
)
from student_app.routers.users import _require_user
from student_app.storage import storage

router = APIRouter(
    prefix="/users/{username}/study-sessions",
    tags=["study_sessions"],
)


def _now_iso() -> str:
    """Return current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Endpoints — static paths BEFORE dynamic ones
# ---------------------------------------------------------------------------


@router.post("", status_code=status.HTTP_201_CREATED, response_model=StudySessionOut)
def create_study_session(
    username: str, payload: StudySessionCreate
) -> StudySessionOut:
    """Log a new study session.

    duration_minutes must be a positive integer (≥1); Pydantic enforces this
    via the ``ge=1`` constraint on the model.  Returns 400 if validation fails.
    Returns 404 if the user or subject does not exist.
    """
    _require_user(username)

    # Validate subject exists for this user
    subj = storage.subjects.get(payload.subject_id)
    if subj is None or subj["username"] != username:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject '{payload.subject_id}' not found for user '{username}'.",
        )

    session_id = str(uuid.uuid4())
    session_dict = {
        "id": session_id,
        "username": username,
        "subject_id": payload.subject_id,
        "duration_minutes": payload.duration_minutes,
        "notes": payload.notes,
        "created_at": _now_iso(),
    }
    storage.study_sessions[session_id] = session_dict
    return StudySessionOut(**session_dict)


@router.get("/summary", response_model=StudySummaryOut)
def get_study_summary(username: str) -> StudySummaryOut:
    """Return aggregated study statistics for the user.

    Includes total hours studied, total session count, and a breakdown
    of hours per subject.  Returns 404 if the user does not exist.
    """
    _require_user(username)

    sessions = [
        s for s in storage.study_sessions.values() if s["username"] == username
    ]

    total_minutes = sum(s["duration_minutes"] for s in sessions)
    total_hours = round(total_minutes / 60, 2)

    # Aggregate by subject
    subject_minutes: dict[str, int] = {}
    for s in sessions:
        subject_minutes[s["subject_id"]] = (
            subject_minutes.get(s["subject_id"], 0) + s["duration_minutes"]
        )

    hours_per_subject: List[StudySummarySubjectEntry] = []
    for subj_id, mins in subject_minutes.items():
        subj = storage.subjects.get(subj_id)
        subj_name = subj["name"] if subj else "Unknown"
        hours_per_subject.append(
            StudySummarySubjectEntry(
                subject_id=subj_id,
                subject_name=subj_name,
                total_minutes=mins,
                total_hours=round(mins / 60, 2),
            )
        )

    return StudySummaryOut(
        total_hours=total_hours,
        total_sessions=len(sessions),
        hours_per_subject=hours_per_subject,
    )


@router.get("", response_model=List[StudySessionOut])
def list_study_sessions(username: str) -> List[StudySessionOut]:
    """List all study sessions for the user, newest first.

    Returns 404 if the user does not exist.
    """
    _require_user(username)

    sessions = [
        StudySessionOut(**s)
        for s in storage.study_sessions.values()
        if s["username"] == username
    ]
    sessions.sort(key=lambda s: s.created_at, reverse=True)
    return sessions
