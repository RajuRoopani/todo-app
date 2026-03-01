"""
Additional tests for the Analytics router (AC31-35).

This file supplements test_analytics_pomodoro.py with deeper edge-case
and multi-user isolation coverage:

  TestAnalyticsSummaryExtended   — overdue detection, 100% rate, user isolation
  TestAnalyticsByCategoryExtended — user isolation, data accuracy
  TestAnalyticsByPriorityExtended — 404 for unknown user, multi-task counts
  TestAnalyticsStudyHoursExtended — 404 for unknown user, user isolation
  TestAnalyticsStreakExtended     — streak break, non-done tasks ignored, isolation
"""

from __future__ import annotations

from typing import Tuple

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helper utilities (NOT fixtures — take client as a parameter)
# ---------------------------------------------------------------------------


def _create_user(client: TestClient, username: str, display_name: str = "Test") -> str:
    """Create a user and return the username."""
    res = client.post(
        "/users",
        json={
            "username": username,
            "display_name": display_name,
            "email": f"{username}@example.com",
        },
    )
    assert res.status_code == 201, f"_create_user: {res.status_code} {res.text}"
    return res.json()["username"]


def _create_task(
    client: TestClient,
    username: str,
    title: str = "Task",
    priority: str = "medium",
    category: str = "study",
    due_date: str | None = None,
) -> dict:
    """Create a task and return the task dict."""
    payload: dict = {"title": title, "priority": priority, "category": category}
    if due_date is not None:
        payload["due_date"] = due_date
    res = client.post(f"/users/{username}/tasks", json=payload)
    assert res.status_code == 201, f"_create_task: {res.status_code} {res.text}"
    return res.json()


def _complete_task(client: TestClient, username: str, task_id: str) -> None:
    """Advance a task from todo → in_progress → done."""
    r1 = client.patch(
        f"/users/{username}/tasks/{task_id}/status",
        json={"status": "in_progress"},
    )
    assert r1.status_code == 200, f"_complete_task (in_progress): {r1.status_code}"
    r2 = client.patch(
        f"/users/{username}/tasks/{task_id}/status",
        json={"status": "done"},
    )
    assert r2.status_code == 200, f"_complete_task (done): {r2.status_code}"


def _create_subject(client: TestClient, username: str, name: str = "Math") -> str:
    """Create a subject and return its ID."""
    res = client.post(
        f"/users/{username}/subjects",
        json={"name": name, "teacher": None, "color": "#AABBCC"},
    )
    assert res.status_code == 201, f"_create_subject: {res.status_code} {res.text}"
    return res.json()["id"]


def _log_session(
    client: TestClient, username: str, subject_id: str, duration_minutes: int
) -> dict:
    """Log a study session and return the session dict."""
    res = client.post(
        f"/users/{username}/study-sessions",
        json={"subject_id": subject_id, "duration_minutes": duration_minutes},
    )
    assert res.status_code == 201, f"_log_session: {res.status_code} {res.text}"
    return res.json()


# ---------------------------------------------------------------------------
# Summary extended tests
# ---------------------------------------------------------------------------


class TestAnalyticsSummaryExtended:
    """Extended summary tests: overdue detection, 100% completion, user isolation."""

    def test_overdue_task_with_past_due_date(self, client: TestClient) -> None:
        """A non-done task with a past due_date must appear in overdue_count."""
        _create_user(client, "alice")
        task = _create_task(
            client,
            "alice",
            title="Overdue homework",
            due_date="2020-01-01T00:00:00",  # firmly in the past
        )

        res = client.get("/users/alice/analytics/summary")
        assert res.status_code == 200
        data = res.json()
        assert data["overdue_count"] == 1, "Past due_date task should count as overdue"
        assert data["pending_tasks"] == 1
        assert data["completed_tasks"] == 0

    def test_future_due_date_not_overdue(self, client: TestClient) -> None:
        """A non-done task with a future due_date must NOT appear in overdue_count."""
        _create_user(client, "alice")
        _create_task(
            client,
            "alice",
            title="Future task",
            due_date="2099-12-31T23:59:00",  # far future
        )

        res = client.get("/users/alice/analytics/summary")
        assert res.status_code == 200
        data = res.json()
        assert data["overdue_count"] == 0, "Future due_date should not be overdue"

    def test_completed_task_not_counted_as_overdue(self, client: TestClient) -> None:
        """A DONE task with a past due_date must NOT appear in overdue_count."""
        _create_user(client, "alice")
        task = _create_task(
            client,
            "alice",
            title="Past-due but done",
            due_date="2020-01-01T00:00:00",
        )
        _complete_task(client, "alice", task["id"])

        res = client.get("/users/alice/analytics/summary")
        data = res.json()
        assert data["overdue_count"] == 0, "Done task should not count as overdue"
        assert data["completed_tasks"] == 1

    def test_summary_all_tasks_completed_100pct(self, client: TestClient) -> None:
        """When all tasks are done, completion_rate_pct must be 100.0."""
        _create_user(client, "alice")
        for i in range(3):
            task = _create_task(client, "alice", title=f"Task {i}")
            _complete_task(client, "alice", task["id"])

        res = client.get("/users/alice/analytics/summary")
        data = res.json()
        assert data["completion_rate_pct"] == 100.0
        assert data["pending_tasks"] == 0
        assert data["completed_tasks"] == 3
        assert data["overdue_count"] == 0

    def test_summary_user_isolation(self, client: TestClient) -> None:
        """Tasks from user B must not appear in user A's summary."""
        _create_user(client, "alice")
        _create_user(client, "bob")

        # Bob has 5 tasks; Alice has 1
        for i in range(5):
            _create_task(client, "bob", title=f"Bob task {i}")
        _create_task(client, "alice", title="Alice task")

        res = client.get("/users/alice/analytics/summary")
        data = res.json()
        assert data["total_tasks"] == 1, "Alice should only see her own tasks"

    def test_summary_mixed_overdue_and_future(self, client: TestClient) -> None:
        """Mix of overdue + future tasks — only past non-done tasks count as overdue."""
        _create_user(client, "alice")
        _create_task(client, "alice", title="Overdue 1", due_date="2010-06-01T00:00:00")
        _create_task(client, "alice", title="Overdue 2", due_date="2015-01-01T12:00:00")
        _create_task(client, "alice", title="Future", due_date="2099-12-31T00:00:00")
        _create_task(client, "alice", title="No due date")

        res = client.get("/users/alice/analytics/summary")
        data = res.json()
        assert data["total_tasks"] == 4
        assert data["overdue_count"] == 2


# ---------------------------------------------------------------------------
# By-category extended tests
# ---------------------------------------------------------------------------


class TestAnalyticsByCategoryExtended:
    """Extended by-category tests: user isolation, all categories present."""

    def test_by_category_user_isolation(self, client: TestClient) -> None:
        """Tasks from another user must not inflate category counts."""
        _create_user(client, "alice")
        _create_user(client, "bob")

        # Bob has 3 study tasks
        for i in range(3):
            _create_task(client, "bob", category="study", title=f"Bob study {i}")

        # Alice has 1 personal task
        _create_task(client, "alice", category="personal", title="Alice personal")

        res = client.get("/users/alice/analytics/by-category")
        assert res.status_code == 200
        data = res.json()
        cat_map = {item["category"]: item["count"] for item in data}
        assert cat_map["study"] == 0, "Bob's study tasks must not appear for Alice"
        assert cat_map["personal"] == 1

    def test_by_category_all_four_present(self, client: TestClient) -> None:
        """Response must include all 4 categories even when some have no tasks."""
        _create_user(client, "alice")
        _create_task(client, "alice", category="exam", title="Exam task")

        res = client.get("/users/alice/analytics/by-category")
        data = res.json()
        cats = {item["category"] for item in data}
        assert cats == {"study", "personal", "project", "exam"}

    def test_by_category_counts_all_categories(self, client: TestClient) -> None:
        """Tasks spread across all 4 categories are all counted correctly."""
        _create_user(client, "alice")
        for cat in ("study", "personal", "project", "exam"):
            _create_task(client, "alice", category=cat, title=f"{cat} task")

        res = client.get("/users/alice/analytics/by-category")
        data = res.json()
        cat_map = {item["category"]: item["count"] for item in data}
        for cat in ("study", "personal", "project", "exam"):
            assert cat_map[cat] == 1, f"Expected 1 task for category '{cat}'"


# ---------------------------------------------------------------------------
# By-priority extended tests
# ---------------------------------------------------------------------------


class TestAnalyticsByPriorityExtended:
    """Extended by-priority tests: 404 for unknown user, multi-task counts."""

    def test_by_priority_nonexistent_user_404(self, client: TestClient) -> None:
        """GET /analytics/by-priority for a non-existent user should return 404."""
        res = client.get("/users/ghost/analytics/by-priority")
        assert res.status_code == 404

    def test_by_priority_all_four_present(self, client: TestClient) -> None:
        """Response must include all 4 priorities even when most have zero tasks."""
        _create_user(client, "alice")
        _create_task(client, "alice", priority="urgent", title="Urgent task")

        res = client.get("/users/alice/analytics/by-priority")
        data = res.json()
        priorities = {item["priority"] for item in data}
        assert priorities == {"low", "medium", "high", "urgent"}

    def test_by_priority_multiple_tasks_same_priority(self, client: TestClient) -> None:
        """Multiple tasks at the same priority level should accumulate correctly."""
        _create_user(client, "alice")
        for i in range(4):
            _create_task(client, "alice", priority="high", title=f"High task {i}")
        _create_task(client, "alice", priority="low", title="Low task")

        res = client.get("/users/alice/analytics/by-priority")
        data = res.json()
        pri_map = {item["priority"]: item["count"] for item in data}
        assert pri_map["high"] == 4
        assert pri_map["low"] == 1
        assert pri_map["medium"] == 0
        assert pri_map["urgent"] == 0

    def test_by_priority_user_isolation(self, client: TestClient) -> None:
        """Another user's urgent tasks must not show up in my priority counts."""
        _create_user(client, "alice")
        _create_user(client, "bob")

        for i in range(3):
            _create_task(client, "bob", priority="urgent", title=f"Bob urgent {i}")
        _create_task(client, "alice", priority="low", title="Alice low")

        res = client.get("/users/alice/analytics/by-priority")
        data = res.json()
        pri_map = {item["priority"]: item["count"] for item in data}
        assert pri_map["urgent"] == 0
        assert pri_map["low"] == 1


# ---------------------------------------------------------------------------
# Study hours extended tests
# ---------------------------------------------------------------------------


class TestAnalyticsStudyHoursExtended:
    """Extended study-hours tests: 404, user isolation, fractional hours."""

    def test_study_hours_nonexistent_user_404(self, client: TestClient) -> None:
        """GET /analytics/study-hours for non-existent user should return 404."""
        res = client.get("/users/ghost/analytics/study-hours")
        assert res.status_code == 404

    def test_study_hours_exact_hour_boundary(self, client: TestClient) -> None:
        """60 minutes should map to exactly 1.0 hour."""
        _create_user(client, "alice")
        subj_id = _create_subject(client, "alice", "Physics")
        _log_session(client, "alice", subj_id, 60)

        res = client.get("/users/alice/analytics/study-hours")
        data = res.json()
        assert data["total_study_hours"] == 1.0
        assert data["by_subject"][0]["total_hours"] == 1.0

    def test_study_hours_user_isolation(self, client: TestClient) -> None:
        """Bob's study sessions must not appear in Alice's study-hours analytics."""
        _create_user(client, "alice")
        _create_user(client, "bob")

        # Bob logs 3 hours
        bob_subj = _create_subject(client, "bob", "Bob Subject")
        _log_session(client, "bob", bob_subj, 180)

        # Alice logs 0 hours
        res = client.get("/users/alice/analytics/study-hours")
        data = res.json()
        assert data["total_study_hours"] == 0.0
        assert data["by_subject"] == []

    def test_study_hours_multiple_sessions_same_subject(
        self, client: TestClient
    ) -> None:
        """Multiple sessions for the same subject should be summed correctly."""
        _create_user(client, "alice")
        subj_id = _create_subject(client, "alice", "Chemistry")

        _log_session(client, "alice", subj_id, 30)   # 0.5 h
        _log_session(client, "alice", subj_id, 90)   # 1.5 h
        _log_session(client, "alice", subj_id, 120)  # 2.0 h

        res = client.get("/users/alice/analytics/study-hours")
        data = res.json()
        assert data["total_study_hours"] == 4.0
        assert len(data["by_subject"]) == 1
        assert data["by_subject"][0]["total_hours"] == 4.0
        assert data["by_subject"][0]["subject_name"] == "Chemistry"


# ---------------------------------------------------------------------------
# Streak extended tests
# ---------------------------------------------------------------------------


class TestAnalyticsStreakExtended:
    """Extended streak tests: non-done tasks ignored, user isolation, 404."""

    def test_streak_nonexistent_user_404(self, client: TestClient) -> None:
        """GET /analytics/streak for non-existent user should return 404."""
        res = client.get("/users/ghost/analytics/streak")
        assert res.status_code == 404

    def test_streak_pending_tasks_do_not_count(self, client: TestClient) -> None:
        """Tasks that are todo or in_progress must NOT contribute to streak."""
        _create_user(client, "alice")
        # Create tasks but leave them pending
        _create_task(client, "alice", title="Todo task 1")
        task2 = _create_task(client, "alice", title="In-progress task")
        client.patch(
            f"/users/alice/tasks/{task2['id']}/status",
            json={"status": "in_progress"},
        )

        res = client.get("/users/alice/analytics/streak")
        data = res.json()
        assert data["current_streak"] == 0
        assert data["longest_streak"] == 0

    def test_streak_user_isolation(self, client: TestClient) -> None:
        """Completed tasks from user B must not influence user A's streak."""
        _create_user(client, "alice")
        _create_user(client, "bob")

        # Bob completes tasks (today)
        for i in range(3):
            task = _create_task(client, "bob", title=f"Bob task {i}")
            _complete_task(client, "bob", task["id"])

        # Alice has no completed tasks
        res = client.get("/users/alice/analytics/streak")
        data = res.json()
        assert data["current_streak"] == 0
        assert data["longest_streak"] == 0

    def test_streak_returns_correct_schema(self, client: TestClient) -> None:
        """Streak response must contain current_streak and longest_streak fields."""
        _create_user(client, "alice")

        res = client.get("/users/alice/analytics/streak")
        assert res.status_code == 200
        data = res.json()
        assert "current_streak" in data
        assert "longest_streak" in data
        assert isinstance(data["current_streak"], int)
        assert isinstance(data["longest_streak"], int)

    def test_streak_completed_today_contributes_to_current(
        self, client: TestClient
    ) -> None:
        """Tasks completed today should result in current_streak >= 1."""
        _create_user(client, "alice")
        task = _create_task(client, "alice", title="Today's task")
        _complete_task(client, "alice", task["id"])

        res = client.get("/users/alice/analytics/streak")
        data = res.json()
        # Completed today → current streak should be at least 1
        assert data["current_streak"] >= 1
        assert data["longest_streak"] >= 1
