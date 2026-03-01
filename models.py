"""
Pydantic models for the Student Productivity & Task Management App.

All request/response models live here.  Enums encode the valid values
for priority, category, task-status and pomodoro state so that FastAPI
auto-validates incoming payloads.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class Priority(str, Enum):
    """Task urgency levels."""
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class Category(str, Enum):
    """Broad task categories for a student."""
    study = "study"
    personal = "personal"
    project = "project"
    exam = "exam"


class TaskStatus(str, Enum):
    """Lifecycle states for a task.  Transitions: todo → in_progress → done."""
    todo = "todo"
    in_progress = "in_progress"
    done = "done"


# Valid one-step forward-only transitions.
# Keys and values are plain strings so they match storage dict values directly.
# todo can only move to in_progress; in_progress can only move to done.
VALID_TRANSITIONS: dict[str, set[str]] = {
    "todo": {"in_progress"},
    "in_progress": {"done"},
    "done": set(),  # terminal state
}


# ---------------------------------------------------------------------------
# User models
# ---------------------------------------------------------------------------


class UserCreate(BaseModel):
    """Payload for creating a new user."""
    username: str = Field(..., min_length=1, max_length=64,
                          description="Unique username (primary key)")
    display_name: str = Field(..., min_length=1, max_length=128)
    email: str = Field(..., description="User's email address")


class UserOut(BaseModel):
    """Public representation of a user."""
    username: str
    display_name: str
    email: str
    created_at: str


# ---------------------------------------------------------------------------
# Subject models
# ---------------------------------------------------------------------------


class SubjectCreate(BaseModel):
    """Payload for creating a subject."""
    name: str = Field(..., min_length=1, max_length=128)
    teacher: Optional[str] = Field(default=None, max_length=128)
    color: Optional[str] = Field(default="#4A90E2", max_length=32,
                                  description="Hex colour code for UI display")


class SubjectOut(BaseModel):
    """Public representation of a subject."""
    id: str
    username: str
    name: str
    teacher: Optional[str]
    color: Optional[str]
    created_at: str


# ---------------------------------------------------------------------------
# Task models
# ---------------------------------------------------------------------------


class TaskCreate(BaseModel):
    """Payload for creating a task."""
    title: str = Field(..., min_length=1, max_length=256)
    description: Optional[str] = Field(default=None, max_length=2048)
    due_date: Optional[str] = Field(
        default=None,
        description="ISO 8601 datetime string, e.g. 2025-06-01T23:59:00"
    )
    priority: Priority = Field(default=Priority.medium)
    category: Category = Field(default=Category.study)
    subject_id: Optional[str] = Field(default=None)
    tags: List[str] = Field(default_factory=list)


class TaskUpdate(BaseModel):
    """Payload for updating an existing task (all fields optional)."""
    title: Optional[str] = Field(default=None, min_length=1, max_length=256)
    description: Optional[str] = Field(default=None, max_length=2048)
    due_date: Optional[str] = None
    priority: Optional[Priority] = None
    category: Optional[Category] = None
    subject_id: Optional[str] = None
    tags: Optional[List[str]] = None


class TaskStatusUpdate(BaseModel):
    """Payload for the PATCH /status endpoint."""
    status: TaskStatus


class TaskOut(BaseModel):
    """Full public representation of a task."""
    id: str
    username: str
    title: str
    description: Optional[str]
    due_date: Optional[str]
    priority: Priority
    category: Category
    subject_id: Optional[str]
    tags: List[str]
    status: TaskStatus
    created_at: str
    updated_at: str
    completed_at: Optional[str]


# ---------------------------------------------------------------------------
# Subtask models
# ---------------------------------------------------------------------------


class SubtaskCreate(BaseModel):
    """Payload for creating a subtask."""
    title: str = Field(..., min_length=1, max_length=256)


class SubtaskOut(BaseModel):
    """Public representation of a subtask."""
    id: str
    task_id: str
    title: str
    done: bool
    created_at: str


# ---------------------------------------------------------------------------
# Study session models
# ---------------------------------------------------------------------------


class StudySessionCreate(BaseModel):
    """Payload for logging a study session."""
    subject_id: str = Field(..., description="ID of the subject studied")
    duration_minutes: int = Field(
        ..., ge=1,
        description="Duration in whole minutes; must be a positive integer"
    )
    notes: Optional[str] = Field(default=None, max_length=2048)


class StudySessionOut(BaseModel):
    """Public representation of a study session."""
    id: str
    username: str
    subject_id: str
    duration_minutes: int
    notes: Optional[str]
    created_at: str


class StudySummarySubjectEntry(BaseModel):
    """Per-subject breakdown inside a study summary."""
    subject_id: str
    subject_name: str
    total_minutes: int
    total_hours: float


class StudySummaryOut(BaseModel):
    """Aggregated study statistics for a user."""
    total_hours: float
    total_sessions: int
    hours_per_subject: List[StudySummarySubjectEntry]


# ---------------------------------------------------------------------------
# Analytics models
# ---------------------------------------------------------------------------


class AnalyticsSummaryOut(BaseModel):
    """High-level task statistics."""
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    completion_rate_pct: float
    overdue_count: int


class CategoryCountOut(BaseModel):
    """Task count for a single category."""
    category: str
    count: int


class PriorityCountOut(BaseModel):
    """Task count for a single priority level."""
    priority: str
    count: int


class StudyHoursSubjectOut(BaseModel):
    """Study hours breakdown per subject."""
    subject_id: str
    subject_name: str
    total_hours: float


class StudyHoursOut(BaseModel):
    """Study hours analytics."""
    total_study_hours: float
    by_subject: List[StudyHoursSubjectOut]


class StreakOut(BaseModel):
    """Streak analytics for completed tasks."""
    current_streak: int
    longest_streak: int


# ---------------------------------------------------------------------------
# Pomodoro models
# ---------------------------------------------------------------------------


class PomodoroStart(BaseModel):
    """Payload for starting a pomodoro session."""
    task_id: Optional[str] = Field(
        default=None,
        description="Optional task ID this pomodoro is focused on"
    )


class PomodoroOut(BaseModel):
    """Public representation of a pomodoro session."""
    id: str
    username: str
    task_id: Optional[str]
    start_time: str
    end_time: Optional[str]
    completed: bool
    duration_minutes: Optional[int]


class PomodoroStatsOut(BaseModel):
    """Aggregated pomodoro statistics."""
    total_pomodoros: int
    total_focus_minutes: int
    today_count: int
