"""
Pomodoro router — AC36-38.

# ROUTE ORDERING NOTE:
# GET /pomodoro/stats must be declared BEFORE POST /pomodoro/{session_id}/complete
# (even though different methods, keep statics first for clarity and safety).

Endpoints (all scoped to /users/{username}/pomodoro)
-----------------------------------------------------
POST /users/{username}/pomodoro/start                       — start a 25-min session
POST /users/{username}/pomodoro/{session_id}/complete       — mark session complete
GET  /users/{username}/pomodoro/stats                       — aggregated stats
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, status

from student_app.models import PomodoroOut, PomodoroStart, PomodoroStatsOut
from student_app.routers.users import _require_user
from student_app.storage import storage

router = APIRouter(
    prefix="/users/{username}/pomodoro",
    tags=["pomodoro"],
)

# Standard Pomodoro duration in minutes
POMODORO_DURATION_MINUTES = 25


def _now_iso() -> str:
    """Return current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _now_utc() -> datetime:
    """Return current UTC-aware datetime."""
    return datetime.now(timezone.utc)


def _parse_iso(dt_str: str) -> datetime:
    """Parse an ISO 8601 string to a UTC-aware datetime."""
    dt = datetime.fromisoformat(dt_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


# ---------------------------------------------------------------------------
# Endpoints — static paths before dynamic ones
# ---------------------------------------------------------------------------


@router.post("/start", status_code=status.HTTP_201_CREATED, response_model=PomodoroOut)
def start_pomodoro(username: str, payload: PomodoroStart) -> PomodoroOut:
    """Start a new 25-minute Pomodoro session.

    Optionally link to a specific task via ``task_id``.
    Returns 404 if the user does not exist.
    Returns 404 if task_id is provided but the task does not exist for this user.
    """
    _require_user(username)

    # Validate task ownership if task_id is provided
    if payload.task_id is not None:
        task = storage.tasks.get(payload.task_id)
        if task is None or task["username"] != username:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task '{payload.task_id}' not found for user '{username}'.",
            )

    session_id = str(uuid.uuid4())
    session_dict = {
        "id": session_id,
        "username": username,
        "task_id": payload.task_id,
        "start_time": _now_iso(),
        "end_time": None,
        "completed": False,
        "duration_minutes": None,
    }
    storage.pomodoro_sessions[session_id] = session_dict
    return PomodoroOut(**session_dict)


@router.get("/stats", response_model=PomodoroStatsOut)
def pomodoro_stats(username: str) -> PomodoroStatsOut:
    """Return aggregated Pomodoro statistics for the user.

    - total_pomodoros    : all completed sessions ever
    - total_focus_minutes: sum of actual duration_minutes for completed sessions
    - today_count        : completed sessions whose end_time is today (UTC)

    Returns 404 if the user does not exist.
    """
    _require_user(username)

    today: date = _now_utc().date()
    completed_sessions = [
        s for s in storage.pomodoro_sessions.values()
        if s["username"] == username and s["completed"]
    ]

    total_pomodoros = len(completed_sessions)
    total_focus_minutes = sum(
        s["duration_minutes"] for s in completed_sessions
        if s["duration_minutes"] is not None
    )

    today_count = 0
    for s in completed_sessions:
        if s.get("end_time"):
            try:
                end_dt = _parse_iso(s["end_time"])
                if end_dt.date() == today:
                    today_count += 1
            except ValueError:
                pass

    return PomodoroStatsOut(
        total_pomodoros=total_pomodoros,
        total_focus_minutes=total_focus_minutes,
        today_count=today_count,
    )


@router.post("/{session_id}/complete", response_model=PomodoroOut)
def complete_pomodoro(username: str, session_id: str) -> PomodoroOut:
    """Mark a Pomodoro session as complete and record its actual duration.

    Duration is computed as the difference between start_time and the
    moment this endpoint is called, rounded to whole minutes (minimum 1).
    Returns 404 if the user or session does not exist.
    Returns 400 if the session is already completed.
    """
    _require_user(username)

    session = storage.pomodoro_sessions.get(session_id)
    if session is None or session["username"] != username:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pomodoro session '{session_id}' not found for user '{username}'.",
        )

    if session["completed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Pomodoro session '{session_id}' is already completed.",
        )

    end_time = _now_utc()
    start_time = _parse_iso(session["start_time"])
    elapsed_seconds = (end_time - start_time).total_seconds()
    duration_minutes = max(1, round(elapsed_seconds / 60))

    session["end_time"] = end_time.isoformat()
    session["completed"] = True
    session["duration_minutes"] = duration_minutes

    return PomodoroOut(**session)
