"""
In-memory storage singleton for the Student Productivity App.

All data lives in plain Python dicts keyed by their primary identifier.
Calling reset() wipes all state — used between test runs for isolation.

Dict shapes
-----------
users            : Dict[str, dict]   — keyed by username
subjects         : Dict[str, dict]   — keyed by subject_id
tasks            : Dict[str, dict]   — keyed by task_id
subtasks         : Dict[str, dict]   — keyed by subtask_id
study_sessions   : Dict[str, dict]   — keyed by session_id
pomodoro_sessions: Dict[str, dict]   — keyed by session_id

Every non-user entity carries a ``username`` field so it can be
filtered to a specific user without a join.
Subtasks carry a ``task_id`` field for the same reason.
"""

from __future__ import annotations

from typing import Any, Dict


class Storage:
    """Central in-memory data store.

    Only one instance (``storage``) is created at module level.
    Every router imports that singleton.
    """

    def __init__(self) -> None:
        """Initialise empty storage."""
        self.reset()

    def reset(self) -> None:
        """Wipe all stored data.  Called at test teardown."""
        self.users: Dict[str, Any] = {}
        self.subjects: Dict[str, Any] = {}
        self.tasks: Dict[str, Any] = {}
        self.subtasks: Dict[str, Any] = {}
        self.study_sessions: Dict[str, Any] = {}
        self.pomodoro_sessions: Dict[str, Any] = {}


# Module-level singleton — import this from routers/tests
storage = Storage()
