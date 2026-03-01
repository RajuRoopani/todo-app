"""
Analytics router — AC31-35.

Endpoints (all scoped to /users/{username}/analytics)
------------------------------------------------------
GET /users/{username}/analytics/summary         — task KPIs
GET /users/{username}/analytics/by-category     — task counts per category
GET /users/{username}/analytics/by-priority     — task counts per priority
GET /users/{username}/analytics/study-hours     — total + per-subject study hours
GET /users/{username}/analytics/streak          — current & longest completion streak
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter

from student_app.models import (
    AnalyticsSummaryOut,
    Category,
    CategoryCountOut,
    Priority,
    PriorityCountOut,
    StudyHoursOut,
    StudyHoursSubjectOut,
    StreakOut,
    TaskStatus,
)
from student_app.routers.users import _require_user
from student_app.storage import storage

router = APIRouter(
    prefix="/users/{username}/analytics",
    tags=["analytics"],
)


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
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/summary", response_model=AnalyticsSummaryOut)
def analytics_summary(username: str) -> AnalyticsSummaryOut:
    """Return high-level task statistics for the user.

    - total_tasks        : all tasks ever created
    - completed_tasks    : tasks with status == done
    - pending_tasks      : tasks with status != done
    - completion_rate_pct: (completed / total) * 100, rounded to 1 dp
    - overdue_count      : non-done tasks whose due_date is in the past
    """
    _require_user(username)

    tasks = [t for t in storage.tasks.values() if t["username"] == username]
    now = _now_utc()

    total = len(tasks)
    completed = sum(1 for t in tasks if t["status"] == TaskStatus.done)
    pending = total - completed
    rate = round((completed / total * 100), 1) if total else 0.0

    overdue = 0
    for t in tasks:
        if t["status"] != TaskStatus.done and t.get("due_date"):
            try:
                due = _parse_iso(t["due_date"])
                if due < now:
                    overdue += 1
            except ValueError:
                pass  # malformed date — skip

    return AnalyticsSummaryOut(
        total_tasks=total,
        completed_tasks=completed,
        pending_tasks=pending,
        completion_rate_pct=rate,
        overdue_count=overdue,
    )


@router.get("/by-category", response_model=List[CategoryCountOut])
def analytics_by_category(username: str) -> List[CategoryCountOut]:
    """Return task counts grouped by category.

    All categories are included in the response (count may be zero).
    Returns 404 if the user does not exist.
    """
    _require_user(username)

    counts: dict[str, int] = {c.value: 0 for c in Category}
    for t in storage.tasks.values():
        if t["username"] == username:
            counts[t["category"]] = counts.get(t["category"], 0) + 1

    return [CategoryCountOut(category=cat, count=cnt) for cat, cnt in counts.items()]


@router.get("/by-priority", response_model=List[PriorityCountOut])
def analytics_by_priority(username: str) -> List[PriorityCountOut]:
    """Return task counts grouped by priority level.

    All priority levels are included in the response (count may be zero).
    Returns 404 if the user does not exist.
    """
    _require_user(username)

    counts: dict[str, int] = {p.value: 0 for p in Priority}
    for t in storage.tasks.values():
        if t["username"] == username:
            counts[t["priority"]] = counts.get(t["priority"], 0) + 1

    return [PriorityCountOut(priority=pri, count=cnt) for pri, cnt in counts.items()]


@router.get("/study-hours", response_model=StudyHoursOut)
def analytics_study_hours(username: str) -> StudyHoursOut:
    """Return total study hours and a breakdown per subject.

    Returns 404 if the user does not exist.
    """
    _require_user(username)

    sessions = [
        s for s in storage.study_sessions.values() if s["username"] == username
    ]

    total_minutes = sum(s["duration_minutes"] for s in sessions)
    total_hours = round(total_minutes / 60, 2)

    subject_minutes: dict[str, int] = defaultdict(int)
    for s in sessions:
        subject_minutes[s["subject_id"]] += s["duration_minutes"]

    by_subject: List[StudyHoursSubjectOut] = []
    for subj_id, mins in subject_minutes.items():
        subj = storage.subjects.get(subj_id)
        subj_name = subj["name"] if subj else "Unknown"
        by_subject.append(
            StudyHoursSubjectOut(
                subject_id=subj_id,
                subject_name=subj_name,
                total_hours=round(mins / 60, 2),
            )
        )

    return StudyHoursOut(total_study_hours=total_hours, by_subject=by_subject)


@router.get("/streak", response_model=StreakOut)
def analytics_streak(username: str) -> StreakOut:
    """Return the current and longest streaks of consecutive productive days.

    A "productive day" is any calendar day (UTC) on which the user completed
    at least one task.  The current streak counts backwards from today;
    the longest streak is the maximum consecutive run ever recorded.

    Returns 404 if the user does not exist.
    """
    _require_user(username)

    # Collect all unique calendar days (UTC date objects) with at least one
    # completed task.
    completion_dates: set[date] = set()
    for t in storage.tasks.values():
        if t["username"] == username and t.get("completed_at"):
            try:
                dt = _parse_iso(t["completed_at"])
                completion_dates.add(dt.date())
            except ValueError:
                pass

    if not completion_dates:
        return StreakOut(current_streak=0, longest_streak=0)

    sorted_dates = sorted(completion_dates)

    # ---- longest streak ----
    longest = 1
    run = 1
    for i in range(1, len(sorted_dates)):
        delta = (sorted_dates[i] - sorted_dates[i - 1]).days
        if delta == 1:
            run += 1
            if run > longest:
                longest = run
        else:
            run = 1

    # ---- current streak (counting backwards from today) ----
    today: date = _now_utc().date()
    current = 0
    check = today
    while check in completion_dates:
        current += 1
        check = check - timedelta(days=1)

    return StreakOut(current_streak=current, longest_streak=longest)
