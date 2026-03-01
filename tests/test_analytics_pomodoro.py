"""
Tests for Analytics and Pomodoro routers (AC31-38).

Covers:
  - Analytics: summary, by-category, by-priority, study-hours, streak
  - Pomodoro: start, complete, stats
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestAnalyticsSummary:
    """Analytics summary tests (AC31)."""

    @pytest.fixture
    def user_alice(self, client: TestClient) -> dict:
        """Create a test user alice."""
        res = client.post(
            "/users",
            json={
                "username": "alice",
                "display_name": "Alice",
                "email": "alice@example.com",
            },
        )
        return res.json()

    def test_summary_no_tasks(
        self, client: TestClient, user_alice: dict
    ) -> None:
        """Summary with no tasks should return all zeros."""
        res = client.get("/users/alice/analytics/summary")
        assert res.status_code == 200
        data = res.json()
        assert data["total_tasks"] == 0
        assert data["completed_tasks"] == 0
        assert data["pending_tasks"] == 0
        assert data["completion_rate_pct"] == 0.0
        assert data["overdue_count"] == 0

    def test_summary_single_task_pending(
        self, client: TestClient, user_alice: dict
    ) -> None:
        """Summary with one pending task."""
        client.post(
            "/users/alice/tasks",
            json={
                "title": "Task 1",
                "priority": "medium",
                "category": "study",
            },
        )
        res = client.get("/users/alice/analytics/summary")
        data = res.json()
        assert data["total_tasks"] == 1
        assert data["completed_tasks"] == 0
        assert data["pending_tasks"] == 1
        assert data["completion_rate_pct"] == 0.0
        assert data["overdue_count"] == 0

    def test_summary_mixed_task_statuses(
        self, client: TestClient, user_alice: dict
    ) -> None:
        """Summary should count tasks by status correctly."""
        # Create 4 tasks
        task1 = client.post(
            "/users/alice/tasks",
            json={"title": "Task 1", "priority": "medium", "category": "study"},
        ).json()
        task2 = client.post(
            "/users/alice/tasks",
            json={"title": "Task 2", "priority": "medium", "category": "study"},
        ).json()
        task3 = client.post(
            "/users/alice/tasks",
            json={"title": "Task 3", "priority": "medium", "category": "study"},
        ).json()
        task4 = client.post(
            "/users/alice/tasks",
            json={"title": "Task 4", "priority": "medium", "category": "study"},
        ).json()

        # Update 2 to done
        client.patch(
            f"/users/alice/tasks/{task1['id']}/status",
            json={"status": "in_progress"},
        )
        client.patch(
            f"/users/alice/tasks/{task1['id']}/status",
            json={"status": "done"},
        )
        client.patch(
            f"/users/alice/tasks/{task2['id']}/status",
            json={"status": "in_progress"},
        )
        client.patch(
            f"/users/alice/tasks/{task2['id']}/status",
            json={"status": "done"},
        )

        res = client.get("/users/alice/analytics/summary")
        data = res.json()
        assert data["total_tasks"] == 4
        assert data["completed_tasks"] == 2
        assert data["pending_tasks"] == 2
        assert data["completion_rate_pct"] == 50.0

    def test_summary_completion_rate_rounding(
        self, client: TestClient, user_alice: dict
    ) -> None:
        """Completion rate should be rounded to 1 decimal place."""
        # Create 3 tasks, complete 1 (33.33% -> 33.3%)
        task1 = client.post(
            "/users/alice/tasks",
            json={"title": "Task 1", "priority": "medium", "category": "study"},
        ).json()
        client.post(
            "/users/alice/tasks",
            json={"title": "Task 2", "priority": "medium", "category": "study"},
        )
        client.post(
            "/users/alice/tasks",
            json={"title": "Task 3", "priority": "medium", "category": "study"},
        )

        # Complete task 1
        client.patch(
            f"/users/alice/tasks/{task1['id']}/status",
            json={"status": "in_progress"},
        )
        client.patch(
            f"/users/alice/tasks/{task1['id']}/status",
            json={"status": "done"},
        )

        res = client.get("/users/alice/analytics/summary")
        data = res.json()
        assert data["completion_rate_pct"] == 33.3

    def test_summary_nonexistent_user_404(self, client: TestClient) -> None:
        """GET for non-existent user should return 404."""
        res = client.get("/users/nonexistent/analytics/summary")
        assert res.status_code == 404


class TestAnalyticsByCategory:
    """Analytics by-category tests (AC32)."""

    @pytest.fixture
    def user_alice(self, client: TestClient) -> dict:
        """Create a test user alice."""
        res = client.post(
            "/users",
            json={
                "username": "alice",
                "display_name": "Alice",
                "email": "alice@example.com",
            },
        )
        return res.json()

    def test_by_category_empty(
        self, client: TestClient, user_alice: dict
    ) -> None:
        """by-category should return all categories with count=0 when no tasks."""
        res = client.get("/users/alice/analytics/by-category")
        assert res.status_code == 200
        data = res.json()
        # Should have 4 categories
        assert len(data) == 4
        categories = {item["category"] for item in data}
        assert categories == {"study", "personal", "project", "exam"}
        for item in data:
            assert item["count"] == 0

    def test_by_category_with_tasks(
        self, client: TestClient, user_alice: dict
    ) -> None:
        """by-category should count tasks correctly."""
        # Create tasks in different categories
        client.post(
            "/users/alice/tasks",
            json={"title": "Task 1", "category": "study", "priority": "medium"},
        )
        client.post(
            "/users/alice/tasks",
            json={"title": "Task 2", "category": "study", "priority": "medium"},
        )
        client.post(
            "/users/alice/tasks",
            json={"title": "Task 3", "category": "personal", "priority": "medium"},
        )
        client.post(
            "/users/alice/tasks",
            json={"title": "Task 4", "category": "exam", "priority": "medium"},
        )

        res = client.get("/users/alice/analytics/by-category")
        data = res.json()
        category_map = {item["category"]: item["count"] for item in data}
        assert category_map["study"] == 2
        assert category_map["personal"] == 1
        assert category_map["project"] == 0
        assert category_map["exam"] == 1

    def test_by_category_nonexistent_user_404(self, client: TestClient) -> None:
        """GET for non-existent user should return 404."""
        res = client.get("/users/nonexistent/analytics/by-category")
        assert res.status_code == 404


class TestAnalyticsByPriority:
    """Analytics by-priority tests (AC33)."""

    @pytest.fixture
    def user_alice(self, client: TestClient) -> dict:
        """Create a test user alice."""
        res = client.post(
            "/users",
            json={
                "username": "alice",
                "display_name": "Alice",
                "email": "alice@example.com",
            },
        )
        return res.json()

    def test_by_priority_empty(
        self, client: TestClient, user_alice: dict
    ) -> None:
        """by-priority should return all priorities with count=0 when no tasks."""
        res = client.get("/users/alice/analytics/by-priority")
        assert res.status_code == 200
        data = res.json()
        # Should have 4 priorities
        assert len(data) == 4
        priorities = {item["priority"] for item in data}
        assert priorities == {"low", "medium", "high", "urgent"}
        for item in data:
            assert item["count"] == 0

    def test_by_priority_with_tasks(
        self, client: TestClient, user_alice: dict
    ) -> None:
        """by-priority should count tasks correctly."""
        # Create tasks with different priorities
        client.post(
            "/users/alice/tasks",
            json={"title": "Task 1", "priority": "low", "category": "study"},
        )
        client.post(
            "/users/alice/tasks",
            json={"title": "Task 2", "priority": "medium", "category": "study"},
        )
        client.post(
            "/users/alice/tasks",
            json={"title": "Task 3", "priority": "medium", "category": "study"},
        )
        client.post(
            "/users/alice/tasks",
            json={"title": "Task 4", "priority": "urgent", "category": "study"},
        )

        res = client.get("/users/alice/analytics/by-priority")
        data = res.json()
        priority_map = {item["priority"]: item["count"] for item in data}
        assert priority_map["low"] == 1
        assert priority_map["medium"] == 2
        assert priority_map["high"] == 0
        assert priority_map["urgent"] == 1


class TestAnalyticsStudyHours:
    """Analytics study-hours tests (AC34)."""

    @pytest.fixture
    def user_alice_with_subjects(self, client: TestClient) -> tuple[dict, dict, dict]:
        """Create alice and 2 subjects."""
        user_res = client.post(
            "/users",
            json={
                "username": "alice",
                "display_name": "Alice",
                "email": "alice@example.com",
            },
        )
        physics_res = client.post(
            "/users/alice/subjects",
            json={"name": "Physics", "teacher": None, "color": "#FF5733"},
        )
        chemistry_res = client.post(
            "/users/alice/subjects",
            json={"name": "Chemistry", "teacher": None, "color": "#4A90E2"},
        )
        return user_res.json(), physics_res.json(), chemistry_res.json()

    def test_study_hours_empty(
        self, client: TestClient, user_alice_with_subjects: tuple
    ) -> None:
        """study-hours with no sessions should return zero totals."""
        res = client.get("/users/alice/analytics/study-hours")
        assert res.status_code == 200
        data = res.json()
        assert data["total_study_hours"] == 0.0
        assert data["by_subject"] == []

    def test_study_hours_single_subject(
        self, client: TestClient, user_alice_with_subjects: tuple
    ) -> None:
        """study-hours should aggregate by subject."""
        user, physics, chemistry = user_alice_with_subjects
        # Create sessions for physics: 60min + 45min = 1.75 hours
        client.post(
            "/users/alice/study-sessions",
            json={"subject_id": physics["id"], "duration_minutes": 60},
        )
        client.post(
            "/users/alice/study-sessions",
            json={"subject_id": physics["id"], "duration_minutes": 45},
        )

        res = client.get("/users/alice/analytics/study-hours")
        data = res.json()
        assert data["total_study_hours"] == 1.75
        assert len(data["by_subject"]) == 1
        assert data["by_subject"][0]["subject_id"] == physics["id"]
        assert data["by_subject"][0]["subject_name"] == "Physics"
        assert data["by_subject"][0]["total_hours"] == 1.75

    def test_study_hours_multiple_subjects(
        self, client: TestClient, user_alice_with_subjects: tuple
    ) -> None:
        """study-hours should breakdown hours per subject."""
        user, physics, chemistry = user_alice_with_subjects
        # Physics: 60 minutes
        client.post(
            "/users/alice/study-sessions",
            json={"subject_id": physics["id"], "duration_minutes": 60},
        )
        # Chemistry: 120 minutes
        client.post(
            "/users/alice/study-sessions",
            json={"subject_id": chemistry["id"], "duration_minutes": 120},
        )

        res = client.get("/users/alice/analytics/study-hours")
        data = res.json()
        assert data["total_study_hours"] == 3.0
        assert len(data["by_subject"]) == 2

        subject_map = {s["subject_id"]: s for s in data["by_subject"]}
        assert subject_map[physics["id"]]["total_hours"] == 1.0
        assert subject_map[chemistry["id"]]["total_hours"] == 2.0


class TestAnalyticsStreak:
    """Analytics streak tests (AC35)."""

    @pytest.fixture
    def user_alice(self, client: TestClient) -> dict:
        """Create a test user alice."""
        res = client.post(
            "/users",
            json={
                "username": "alice",
                "display_name": "Alice",
                "email": "alice@example.com",
            },
        )
        return res.json()

    def test_streak_no_completed_tasks(
        self, client: TestClient, user_alice: dict
    ) -> None:
        """Streak with no completed tasks should be 0."""
        res = client.get("/users/alice/analytics/streak")
        assert res.status_code == 200
        data = res.json()
        assert data["current_streak"] == 0
        assert data["longest_streak"] == 0

    def test_streak_single_completed_task(
        self, client: TestClient, user_alice: dict
    ) -> None:
        """Single completed task should give streak of 1."""
        # Create and complete a task
        task = client.post(
            "/users/alice/tasks",
            json={"title": "Task 1", "priority": "medium", "category": "study"},
        ).json()

        client.patch(
            f"/users/alice/tasks/{task['id']}/status",
            json={"status": "in_progress"},
        )
        client.patch(
            f"/users/alice/tasks/{task['id']}/status",
            json={"status": "done"},
        )

        res = client.get("/users/alice/analytics/streak")
        data = res.json()
        # Current streak might be 0 or 1 depending on timing, but longest should be 1
        assert data["longest_streak"] == 1

    def test_streak_multiple_tasks_same_day_count_once(
        self, client: TestClient, user_alice: dict
    ) -> None:
        """Multiple tasks completed on same day should count as 1 day in streak."""
        # Create 3 tasks and complete all on same day
        task1 = client.post(
            "/users/alice/tasks",
            json={"title": "Task 1", "priority": "medium", "category": "study"},
        ).json()
        task2 = client.post(
            "/users/alice/tasks",
            json={"title": "Task 2", "priority": "medium", "category": "study"},
        ).json()
        task3 = client.post(
            "/users/alice/tasks",
            json={"title": "Task 3", "priority": "medium", "category": "study"},
        ).json()

        for task in [task1, task2, task3]:
            client.patch(
                f"/users/alice/tasks/{task['id']}/status",
                json={"status": "in_progress"},
            )
            client.patch(
                f"/users/alice/tasks/{task['id']}/status",
                json={"status": "done"},
            )

        res = client.get("/users/alice/analytics/streak")
        data = res.json()
        # Longest streak should be 1 (all on same day)
        assert data["longest_streak"] == 1


class TestPomodoroStart:
    """Pomodoro start tests (AC36)."""

    @pytest.fixture
    def user_alice(self, client: TestClient) -> dict:
        """Create a test user alice."""
        res = client.post(
            "/users",
            json={
                "username": "alice",
                "display_name": "Alice",
                "email": "alice@example.com",
            },
        )
        return res.json()

    @pytest.fixture
    def task_alice(self, client: TestClient, user_alice: dict) -> dict:
        """Create a task for alice."""
        res = client.post(
            "/users/alice/tasks",
            json={"title": "Study math", "priority": "high", "category": "study"},
        )
        return res.json()

    def test_start_pomodoro_success(
        self, client: TestClient, user_alice: dict
    ) -> None:
        """POST /users/{username}/pomodoro/start should create session with 201."""
        res = client.post(
            "/users/alice/pomodoro/start",
            json={},
        )
        assert res.status_code == 201
        data = res.json()
        assert data["username"] == "alice"
        assert data["task_id"] is None
        assert data["completed"] is False
        assert data["end_time"] is None
        assert data["duration_minutes"] is None
        assert "id" in data
        assert "start_time" in data

    def test_start_pomodoro_with_task(
        self, client: TestClient, user_alice: dict, task_alice: dict
    ) -> None:
        """POST should link pomodoro to task when task_id provided."""
        res = client.post(
            "/users/alice/pomodoro/start",
            json={"task_id": task_alice["id"]},
        )
        assert res.status_code == 201
        data = res.json()
        assert data["task_id"] == task_alice["id"]

    def test_start_pomodoro_invalid_task_id_404(
        self, client: TestClient, user_alice: dict
    ) -> None:
        """POST with non-existent task_id should return 404."""
        res = client.post(
            "/users/alice/pomodoro/start",
            json={"task_id": "nonexistent-id"},
        )
        assert res.status_code == 404
        assert "not found" in res.json()["detail"]

    def test_start_pomodoro_task_belongs_to_other_user_404(
        self, client: TestClient, user_alice: dict
    ) -> None:
        """Task belonging to other user should not be accessible."""
        # Create bob and his task
        bob_res = client.post(
            "/users",
            json={
                "username": "bob",
                "display_name": "Bob",
                "email": "bob@example.com",
            },
        )
        bob_task = client.post(
            "/users/bob/tasks",
            json={"title": "Bob's task", "priority": "medium", "category": "study"},
        ).json()

        # Alice tries to start pomodoro with Bob's task
        res = client.post(
            "/users/alice/pomodoro/start",
            json={"task_id": bob_task["id"]},
        )
        assert res.status_code == 404

    def test_start_pomodoro_nonexistent_user_404(self, client: TestClient) -> None:
        """POST for non-existent user should return 404."""
        res = client.post(
            "/users/nonexistent/pomodoro/start",
            json={},
        )
        assert res.status_code == 404


class TestPomodoroComplete:
    """Pomodoro complete tests (AC37)."""

    @pytest.fixture
    def user_alice_with_pomodoro(self, client: TestClient) -> tuple[dict, dict]:
        """Create alice and a pomodoro session."""
        user_res = client.post(
            "/users",
            json={
                "username": "alice",
                "display_name": "Alice",
                "email": "alice@example.com",
            },
        )
        pomo_res = client.post(
            "/users/alice/pomodoro/start",
            json={},
        )
        return user_res.json(), pomo_res.json()

    def test_complete_pomodoro_success(
        self, client: TestClient, user_alice_with_pomodoro: tuple
    ) -> None:
        """POST /{session_id}/complete should mark completed with 200."""
        user, pomo = user_alice_with_pomodoro
        res = client.post(
            f"/users/alice/pomodoro/{pomo['id']}/complete",
        )
        assert res.status_code == 200
        data = res.json()
        assert data["completed"] is True
        assert data["end_time"] is not None
        assert data["duration_minutes"] is not None
        assert data["duration_minutes"] >= 1

    def test_complete_pomodoro_nonexistent_session_404(
        self, client: TestClient, user_alice_with_pomodoro: tuple
    ) -> None:
        """Completing non-existent session should return 404."""
        user, pomo = user_alice_with_pomodoro
        res = client.post(
            "/users/alice/pomodoro/nonexistent-id/complete",
        )
        assert res.status_code == 404

    def test_complete_pomodoro_already_completed_400(
        self, client: TestClient, user_alice_with_pomodoro: tuple
    ) -> None:
        """Completing already-completed session should return 400."""
        user, pomo = user_alice_with_pomodoro
        # Complete once
        client.post(
            f"/users/alice/pomodoro/{pomo['id']}/complete",
        )
        # Try to complete again
        res = client.post(
            f"/users/alice/pomodoro/{pomo['id']}/complete",
        )
        assert res.status_code == 400
        assert "already completed" in res.json()["detail"]

    def test_complete_pomodoro_session_belongs_to_other_user_404(
        self, client: TestClient, user_alice_with_pomodoro: tuple
    ) -> None:
        """User B should not be able to complete user A's pomodoro."""
        user, pomo = user_alice_with_pomodoro

        # Create bob
        client.post(
            "/users",
            json={
                "username": "bob",
                "display_name": "Bob",
                "email": "bob@example.com",
            },
        )

        # Bob tries to complete Alice's pomodoro
        res = client.post(
            f"/users/bob/pomodoro/{pomo['id']}/complete",
        )
        assert res.status_code == 404


class TestPomodoroStats:
    """Pomodoro stats tests (AC38)."""

    @pytest.fixture
    def user_alice(self, client: TestClient) -> dict:
        """Create a test user alice."""
        res = client.post(
            "/users",
            json={
                "username": "alice",
                "display_name": "Alice",
                "email": "alice@example.com",
            },
        )
        return res.json()

    def test_stats_no_sessions(
        self, client: TestClient, user_alice: dict
    ) -> None:
        """Stats with no sessions should return all zeros."""
        res = client.get("/users/alice/pomodoro/stats")
        assert res.status_code == 200
        data = res.json()
        assert data["total_pomodoros"] == 0
        assert data["total_focus_minutes"] == 0
        assert data["today_count"] == 0

    def test_stats_incomplete_sessions_not_counted(
        self, client: TestClient, user_alice: dict
    ) -> None:
        """Incomplete pomodoro sessions should not be counted."""
        # Start a pomodoro but don't complete it
        client.post(
            "/users/alice/pomodoro/start",
            json={},
        )

        res = client.get("/users/alice/pomodoro/stats")
        data = res.json()
        assert data["total_pomodoros"] == 0
        assert data["total_focus_minutes"] == 0

    def test_stats_completed_sessions_counted(
        self, client: TestClient, user_alice: dict
    ) -> None:
        """Only completed sessions should be counted."""
        # Start and complete 2 pomodoros
        pomo1 = client.post(
            "/users/alice/pomodoro/start",
            json={},
        ).json()
        pomo2 = client.post(
            "/users/alice/pomodoro/start",
            json={},
        ).json()

        client.post(f"/users/alice/pomodoro/{pomo1['id']}/complete")
        client.post(f"/users/alice/pomodoro/{pomo2['id']}/complete")

        res = client.get("/users/alice/pomodoro/stats")
        data = res.json()
        assert data["total_pomodoros"] == 2
        assert data["total_focus_minutes"] >= 2  # at least 1 minute each

    def test_stats_today_count(
        self, client: TestClient, user_alice: dict
    ) -> None:
        """today_count should count completed sessions with end_time today."""
        # Start and complete a pomodoro
        pomo = client.post(
            "/users/alice/pomodoro/start",
            json={},
        ).json()

        client.post(f"/users/alice/pomodoro/{pomo['id']}/complete")

        res = client.get("/users/alice/pomodoro/stats")
        data = res.json()
        # Should count at least 1 (if completed today)
        assert data["today_count"] >= 1

    def test_stats_nonexistent_user_404(self, client: TestClient) -> None:
        """GET stats for non-existent user should return 404."""
        res = client.get("/users/nonexistent/pomodoro/stats")
        assert res.status_code == 404
