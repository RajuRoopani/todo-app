"""
Additional tests for the Pomodoro router (AC36-38).

This file supplements test_analytics_pomodoro.py with deeper edge-case
and multi-user isolation coverage:

  TestPomodoroStartExtended    — multiple sessions, response schema, user isolation
  TestPomodoroCompleteExtended — duration computed correctly, response schema
  TestPomodoroStatsExtended    — multi-session accumulation, user isolation, zeros
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helper utilities (NOT fixtures — take client as a parameter)
# ---------------------------------------------------------------------------


def _create_user(client: TestClient, username: str) -> str:
    """Create a user and return the username."""
    res = client.post(
        "/users",
        json={
            "username": username,
            "display_name": username.capitalize(),
            "email": f"{username}@example.com",
        },
    )
    assert res.status_code == 201, f"_create_user: {res.status_code} {res.text}"
    return res.json()["username"]


def _create_task(
    client: TestClient,
    username: str,
    title: str = "Task",
) -> str:
    """Create a task and return its ID."""
    res = client.post(
        f"/users/{username}/tasks",
        json={"title": title, "priority": "medium", "category": "study"},
    )
    assert res.status_code == 201, f"_create_task: {res.status_code} {res.text}"
    return res.json()["id"]


def _start_pomodoro(
    client: TestClient,
    username: str,
    task_id: str | None = None,
) -> dict:
    """Start a pomodoro session and return the session dict."""
    payload: dict = {}
    if task_id is not None:
        payload["task_id"] = task_id
    res = client.post(f"/users/{username}/pomodoro/start", json=payload)
    assert res.status_code == 201, f"_start_pomodoro: {res.status_code} {res.text}"
    return res.json()


def _complete_pomodoro(client: TestClient, username: str, session_id: str) -> dict:
    """Complete a pomodoro session and return the updated session dict."""
    res = client.post(f"/users/{username}/pomodoro/{session_id}/complete")
    assert res.status_code == 200, f"_complete_pomodoro: {res.status_code} {res.text}"
    return res.json()


# ---------------------------------------------------------------------------
# Start endpoint extended tests
# ---------------------------------------------------------------------------


class TestPomodoroStartExtended:
    """Extended start tests: multiple sessions, response schema validation."""

    def test_start_multiple_concurrent_sessions(self, client: TestClient) -> None:
        """A user can have multiple open (incomplete) pomodoro sessions at once."""
        _create_user(client, "alice")
        pomo1 = _start_pomodoro(client, "alice")
        pomo2 = _start_pomodoro(client, "alice")
        pomo3 = _start_pomodoro(client, "alice")

        # All three should have distinct IDs
        ids = {pomo1["id"], pomo2["id"], pomo3["id"]}
        assert len(ids) == 3, "Each start should produce a unique session ID"

    def test_start_response_schema_complete(self, client: TestClient) -> None:
        """POST /start response must contain all expected fields with correct types."""
        _create_user(client, "alice")
        res = client.post("/users/alice/pomodoro/start", json={})
        assert res.status_code == 201
        data = res.json()

        assert isinstance(data["id"], str) and len(data["id"]) > 0
        assert data["username"] == "alice"
        assert data["task_id"] is None
        assert isinstance(data["start_time"], str)
        assert data["end_time"] is None
        assert data["completed"] is False
        assert data["duration_minutes"] is None

    def test_start_with_task_links_correctly(self, client: TestClient) -> None:
        """session.task_id must equal the task_id provided at start."""
        _create_user(client, "alice")
        task_id = _create_task(client, "alice", title="Focus task")

        pomo = _start_pomodoro(client, "alice", task_id=task_id)
        assert pomo["task_id"] == task_id

    def test_start_without_task_has_null_task_id(self, client: TestClient) -> None:
        """When no task_id is supplied, session.task_id must be null."""
        _create_user(client, "alice")
        pomo = _start_pomodoro(client, "alice")
        assert pomo["task_id"] is None

    def test_start_user_isolation(self, client: TestClient) -> None:
        """Bob's task ID must not be usable when starting Alice's pomodoro."""
        _create_user(client, "alice")
        _create_user(client, "bob")

        # Bob has a task; Alice tries to link to it
        bob_task_id = _create_task(client, "bob", title="Bob's task")

        res = client.post(
            "/users/alice/pomodoro/start",
            json={"task_id": bob_task_id},
        )
        assert res.status_code == 404, (
            "Alice should not be able to link a pomodoro to Bob's task"
        )

    def test_start_nonexistent_user_returns_404(self, client: TestClient) -> None:
        """Starting a pomodoro for a non-existent user should return 404."""
        res = client.post("/users/nobody/pomodoro/start", json={})
        assert res.status_code == 404


# ---------------------------------------------------------------------------
# Complete endpoint extended tests
# ---------------------------------------------------------------------------


class TestPomodoroCompleteExtended:
    """Extended complete tests: duration semantics, 200 status, schema."""

    def test_complete_returns_200(self, client: TestClient) -> None:
        """POST /{session_id}/complete should return HTTP 200."""
        _create_user(client, "alice")
        pomo = _start_pomodoro(client, "alice")
        res = client.post(f"/users/alice/pomodoro/{pomo['id']}/complete")
        assert res.status_code == 200

    def test_complete_sets_completed_true(self, client: TestClient) -> None:
        """After completion, session.completed must be True."""
        _create_user(client, "alice")
        pomo = _start_pomodoro(client, "alice")
        result = _complete_pomodoro(client, "alice", pomo["id"])
        assert result["completed"] is True

    def test_complete_sets_end_time(self, client: TestClient) -> None:
        """After completion, session.end_time must be a non-null ISO string."""
        _create_user(client, "alice")
        pomo = _start_pomodoro(client, "alice")
        result = _complete_pomodoro(client, "alice", pomo["id"])
        assert result["end_time"] is not None
        assert isinstance(result["end_time"], str) and len(result["end_time"]) > 0

    def test_complete_duration_minimum_one_minute(self, client: TestClient) -> None:
        """Duration of a just-started session should be at least 1 minute."""
        _create_user(client, "alice")
        pomo = _start_pomodoro(client, "alice")
        result = _complete_pomodoro(client, "alice", pomo["id"])
        assert result["duration_minutes"] is not None
        assert result["duration_minutes"] >= 1, (
            "duration_minutes should be >= 1 even for instantly completed sessions"
        )

    def test_complete_session_id_preserved(self, client: TestClient) -> None:
        """The session ID in the response must match the one used in the request."""
        _create_user(client, "alice")
        pomo = _start_pomodoro(client, "alice")
        result = _complete_pomodoro(client, "alice", pomo["id"])
        assert result["id"] == pomo["id"]

    def test_complete_wrong_user_returns_404(self, client: TestClient) -> None:
        """Completing another user's session via the wrong username must return 404."""
        _create_user(client, "alice")
        _create_user(client, "bob")

        alice_pomo = _start_pomodoro(client, "alice")

        # Bob attempts to complete Alice's session
        res = client.post(
            f"/users/bob/pomodoro/{alice_pomo['id']}/complete"
        )
        assert res.status_code == 404

    def test_complete_random_session_id_returns_404(self, client: TestClient) -> None:
        """Completing a session that doesn't exist must return 404."""
        _create_user(client, "alice")
        res = client.post("/users/alice/pomodoro/does-not-exist/complete")
        assert res.status_code == 404

    def test_double_complete_returns_400(self, client: TestClient) -> None:
        """Completing an already-completed session must return 400."""
        _create_user(client, "alice")
        pomo = _start_pomodoro(client, "alice")
        _complete_pomodoro(client, "alice", pomo["id"])

        res = client.post(f"/users/alice/pomodoro/{pomo['id']}/complete")
        assert res.status_code == 400
        assert "already completed" in res.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Stats endpoint extended tests
# ---------------------------------------------------------------------------


class TestPomodoroStatsExtended:
    """Extended stats tests: accumulation, user isolation, schema."""

    def test_stats_schema_all_fields_present(self, client: TestClient) -> None:
        """GET /pomodoro/stats response must contain total_pomodoros, total_focus_minutes, today_count."""
        _create_user(client, "alice")
        res = client.get("/users/alice/pomodoro/stats")
        assert res.status_code == 200
        data = res.json()
        assert "total_pomodoros" in data
        assert "total_focus_minutes" in data
        assert "today_count" in data

    def test_stats_focus_minutes_accumulate(self, client: TestClient) -> None:
        """total_focus_minutes should be the sum of all completed session durations."""
        _create_user(client, "alice")

        # Complete 3 sessions
        for _ in range(3):
            pomo = _start_pomodoro(client, "alice")
            _complete_pomodoro(client, "alice", pomo["id"])

        res = client.get("/users/alice/pomodoro/stats")
        data = res.json()
        assert data["total_pomodoros"] == 3
        # Each session is at least 1 minute, so total is at least 3
        assert data["total_focus_minutes"] >= 3

    def test_stats_total_pomodoros_increments(self, client: TestClient) -> None:
        """total_pomodoros should increment by 1 for each completed session."""
        _create_user(client, "alice")

        for expected_count in range(1, 4):
            pomo = _start_pomodoro(client, "alice")
            _complete_pomodoro(client, "alice", pomo["id"])
            res = client.get("/users/alice/pomodoro/stats")
            assert res.json()["total_pomodoros"] == expected_count

    def test_stats_user_isolation(self, client: TestClient) -> None:
        """Bob's completed sessions must not appear in Alice's stats."""
        _create_user(client, "alice")
        _create_user(client, "bob")

        # Bob completes 5 sessions
        for _ in range(5):
            pomo = _start_pomodoro(client, "bob")
            _complete_pomodoro(client, "bob", pomo["id"])

        # Alice has no sessions at all
        res = client.get("/users/alice/pomodoro/stats")
        data = res.json()
        assert data["total_pomodoros"] == 0
        assert data["total_focus_minutes"] == 0
        assert data["today_count"] == 0

    def test_stats_incomplete_sessions_excluded(self, client: TestClient) -> None:
        """Incomplete sessions must not affect any stats field."""
        _create_user(client, "alice")

        # Start 3 sessions but complete only 1
        for _ in range(3):
            _start_pomodoro(client, "alice")

        pomo_to_complete = _start_pomodoro(client, "alice")
        _complete_pomodoro(client, "alice", pomo_to_complete["id"])

        res = client.get("/users/alice/pomodoro/stats")
        data = res.json()
        assert data["total_pomodoros"] == 1, "Only completed sessions should be counted"
        assert data["total_focus_minutes"] >= 1

    def test_stats_nonexistent_user_returns_404(self, client: TestClient) -> None:
        """GET /pomodoro/stats for a non-existent user should return 404."""
        res = client.get("/users/ghost/pomodoro/stats")
        assert res.status_code == 404
