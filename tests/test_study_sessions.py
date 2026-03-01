"""
Tests for Study Sessions router (AC27-30).

Covers:
  - Create study session with valid data
  - Error handling (404 for invalid subject_id, 422 for invalid duration)
  - Listing sessions (newest first)
  - Summary statistics (total_hours, total_sessions, per-subject breakdown)
  - User scoping (user A can't see user B's sessions)
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestStudySessionsCreate:
    """Study session creation tests (AC27)."""

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
    def subject_alice_physics(self, client: TestClient, user_alice: dict) -> dict:
        """Create a Physics subject for alice."""
        res = client.post(
            "/users/alice/subjects",
            json={
                "name": "Physics",
                "teacher": "Prof. Newton",
                "color": "#FF5733",
            },
        )
        return res.json()

    def test_create_study_session_success(
        self, client: TestClient, user_alice: dict, subject_alice_physics: dict
    ) -> None:
        """POST /users/{username}/study-sessions should create session with 201."""
        res = client.post(
            "/users/alice/study-sessions",
            json={
                "subject_id": subject_alice_physics["id"],
                "duration_minutes": 60,
                "notes": "Reviewed Newton's laws",
            },
        )
        assert res.status_code == 201
        data = res.json()
        assert data["username"] == "alice"
        assert data["subject_id"] == subject_alice_physics["id"]
        assert data["duration_minutes"] == 60
        assert data["notes"] == "Reviewed Newton's laws"
        assert "id" in data
        assert "created_at" in data

    def test_create_study_session_without_notes(
        self, client: TestClient, user_alice: dict, subject_alice_physics: dict
    ) -> None:
        """Study session should be creatable without notes."""
        res = client.post(
            "/users/alice/study-sessions",
            json={
                "subject_id": subject_alice_physics["id"],
                "duration_minutes": 45,
            },
        )
        assert res.status_code == 201
        data = res.json()
        assert data["notes"] is None
        assert data["duration_minutes"] == 45

    def test_create_study_session_invalid_subject_id_404(
        self, client: TestClient, user_alice: dict
    ) -> None:
        """POST with non-existent subject_id should return 404."""
        res = client.post(
            "/users/alice/study-sessions",
            json={
                "subject_id": "nonexistent-id",
                "duration_minutes": 30,
            },
        )
        assert res.status_code == 404
        assert "not found" in res.json()["detail"]

    def test_create_study_session_duration_zero_422(
        self, client: TestClient, user_alice: dict, subject_alice_physics: dict
    ) -> None:
        """POST with duration_minutes=0 should return 422 (validation error)."""
        res = client.post(
            "/users/alice/study-sessions",
            json={
                "subject_id": subject_alice_physics["id"],
                "duration_minutes": 0,
            },
        )
        assert res.status_code == 422

    def test_create_study_session_duration_negative_422(
        self, client: TestClient, user_alice: dict, subject_alice_physics: dict
    ) -> None:
        """POST with negative duration_minutes should return 422."""
        res = client.post(
            "/users/alice/study-sessions",
            json={
                "subject_id": subject_alice_physics["id"],
                "duration_minutes": -10,
            },
        )
        assert res.status_code == 422

    def test_create_study_session_nonexistent_user_404(self, client: TestClient) -> None:
        """POST for non-existent user should return 404."""
        res = client.post(
            "/users/nonexistent/study-sessions",
            json={
                "subject_id": "some-id",
                "duration_minutes": 30,
            },
        )
        assert res.status_code == 404

    def test_create_study_session_subject_belongs_to_other_user_404(
        self, client: TestClient, user_alice: dict
    ) -> None:
        """Subject owned by user B should not be accessible to user A."""
        # Create user bob and his subject
        bob_res = client.post(
            "/users",
            json={
                "username": "bob",
                "display_name": "Bob",
                "email": "bob@example.com",
            },
        )
        bob_subj_res = client.post(
            "/users/bob/subjects",
            json={"name": "Biology", "teacher": None, "color": "#4A90E2"},
        )
        bob_subject_id = bob_subj_res.json()["id"]

        # Alice tries to create a session with Bob's subject
        res = client.post(
            "/users/alice/study-sessions",
            json={
                "subject_id": bob_subject_id,
                "duration_minutes": 30,
            },
        )
        assert res.status_code == 404


class TestStudySessionsList:
    """Study session list tests (AC28)."""

    @pytest.fixture
    def user_alice_with_subject(self, client: TestClient) -> tuple[dict, dict]:
        """Create alice and a Physics subject."""
        user_res = client.post(
            "/users",
            json={
                "username": "alice",
                "display_name": "Alice",
                "email": "alice@example.com",
            },
        )
        subj_res = client.post(
            "/users/alice/subjects",
            json={"name": "Physics", "teacher": None, "color": "#FF5733"},
        )
        return user_res.json(), subj_res.json()

    def test_list_sessions_empty(
        self, client: TestClient, user_alice_with_subject: tuple
    ) -> None:
        """GET should return empty list when no sessions exist."""
        user, subject = user_alice_with_subject
        res = client.get("/users/alice/study-sessions")
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_list_sessions_returns_all(
        self, client: TestClient, user_alice_with_subject: tuple
    ) -> None:
        """GET should return all sessions for the user."""
        user, subject = user_alice_with_subject
        # Create 3 sessions
        client.post(
            "/users/alice/study-sessions",
            json={"subject_id": subject["id"], "duration_minutes": 30},
        )
        client.post(
            "/users/alice/study-sessions",
            json={"subject_id": subject["id"], "duration_minutes": 45},
        )
        client.post(
            "/users/alice/study-sessions",
            json={"subject_id": subject["id"], "duration_minutes": 60},
        )
        # Retrieve list
        res = client.get("/users/alice/study-sessions")
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 3

    def test_list_sessions_newest_first(
        self, client: TestClient, user_alice_with_subject: tuple
    ) -> None:
        """Sessions should be ordered by created_at, newest first."""
        user, subject = user_alice_with_subject
        # Create 3 sessions in sequence
        res1 = client.post(
            "/users/alice/study-sessions",
            json={"subject_id": subject["id"], "duration_minutes": 30},
        )
        res2 = client.post(
            "/users/alice/study-sessions",
            json={"subject_id": subject["id"], "duration_minutes": 45},
        )
        res3 = client.post(
            "/users/alice/study-sessions",
            json={"subject_id": subject["id"], "duration_minutes": 60},
        )
        session1_id = res1.json()["id"]
        session2_id = res2.json()["id"]
        session3_id = res3.json()["id"]

        # Retrieve list
        res = client.get("/users/alice/study-sessions")
        data = res.json()
        # Newest first: session3, session2, session1
        assert [s["id"] for s in data] == [session3_id, session2_id, session1_id]

    def test_list_sessions_scoped_to_user(self, client: TestClient) -> None:
        """User A's sessions should not be visible to user B."""
        # Create users
        client.post(
            "/users",
            json={"username": "alice", "display_name": "Alice", "email": "alice@test.com"},
        )
        client.post(
            "/users",
            json={"username": "bob", "display_name": "Bob", "email": "bob@test.com"},
        )

        # Create subjects
        alice_subj_res = client.post(
            "/users/alice/subjects",
            json={"name": "Physics", "teacher": None, "color": "#FF5733"},
        )
        bob_subj_res = client.post(
            "/users/bob/subjects",
            json={"name": "Chemistry", "teacher": None, "color": "#4A90E2"},
        )

        # Create sessions for each user
        client.post(
            "/users/alice/study-sessions",
            json={"subject_id": alice_subj_res.json()["id"], "duration_minutes": 30},
        )
        client.post(
            "/users/bob/study-sessions",
            json={"subject_id": bob_subj_res.json()["id"], "duration_minutes": 45},
        )

        # Alice's list should only have 1 session
        alice_list = client.get("/users/alice/study-sessions").json()
        assert len(alice_list) == 1

        # Bob's list should only have 1 session
        bob_list = client.get("/users/bob/study-sessions").json()
        assert len(bob_list) == 1

    def test_list_sessions_nonexistent_user_404(self, client: TestClient) -> None:
        """GET for non-existent user should return 404."""
        res = client.get("/users/nonexistent/study-sessions")
        assert res.status_code == 404


class TestStudySummary:
    """Study summary and statistics tests (AC29-30)."""

    @pytest.fixture
    def user_alice_with_subjects(self, client: TestClient) -> tuple[dict, dict, dict]:
        """Create alice and 2 subjects (Physics, Chemistry)."""
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

    def test_summary_no_sessions(
        self, client: TestClient, user_alice_with_subjects: tuple
    ) -> None:
        """Summary with no sessions should return all zeros."""
        user, physics, chemistry = user_alice_with_subjects
        res = client.get("/users/alice/study-sessions/summary")
        assert res.status_code == 200
        data = res.json()
        assert data["total_hours"] == 0.0
        assert data["total_sessions"] == 0
        assert data["hours_per_subject"] == []

    def test_summary_single_session(
        self, client: TestClient, user_alice_with_subjects: tuple
    ) -> None:
        """Summary with one session should show correct totals."""
        user, physics, chemistry = user_alice_with_subjects
        # Create a 60-minute session
        client.post(
            "/users/alice/study-sessions",
            json={"subject_id": physics["id"], "duration_minutes": 60},
        )
        res = client.get("/users/alice/study-sessions/summary")
        data = res.json()
        assert data["total_sessions"] == 1
        assert data["total_hours"] == 1.0
        assert len(data["hours_per_subject"]) == 1
        assert data["hours_per_subject"][0]["subject_id"] == physics["id"]
        assert data["hours_per_subject"][0]["subject_name"] == "Physics"
        assert data["hours_per_subject"][0]["total_minutes"] == 60
        assert data["hours_per_subject"][0]["total_hours"] == 1.0

    def test_summary_multiple_sessions_same_subject(
        self, client: TestClient, user_alice_with_subjects: tuple
    ) -> None:
        """Multiple sessions same subject should aggregate correctly."""
        user, physics, chemistry = user_alice_with_subjects
        # Create 3 Physics sessions: 30min, 45min, 60min = 135min = 2.25 hours
        client.post(
            "/users/alice/study-sessions",
            json={"subject_id": physics["id"], "duration_minutes": 30},
        )
        client.post(
            "/users/alice/study-sessions",
            json={"subject_id": physics["id"], "duration_minutes": 45},
        )
        client.post(
            "/users/alice/study-sessions",
            json={"subject_id": physics["id"], "duration_minutes": 60},
        )
        res = client.get("/users/alice/study-sessions/summary")
        data = res.json()
        assert data["total_sessions"] == 3
        assert data["total_hours"] == 2.25
        assert len(data["hours_per_subject"]) == 1
        assert data["hours_per_subject"][0]["total_minutes"] == 135
        assert data["hours_per_subject"][0]["total_hours"] == 2.25

    def test_summary_multiple_subjects(
        self, client: TestClient, user_alice_with_subjects: tuple
    ) -> None:
        """Summary should breakdown hours per subject."""
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
        res = client.get("/users/alice/study-sessions/summary")
        data = res.json()
        assert data["total_sessions"] == 2
        assert data["total_hours"] == 3.0  # 60 + 120 = 180 minutes = 3 hours
        assert len(data["hours_per_subject"]) == 2

        # Check per-subject breakdown
        subject_map = {s["subject_id"]: s for s in data["hours_per_subject"]}
        assert subject_map[physics["id"]]["total_hours"] == 1.0
        assert subject_map[chemistry["id"]]["total_hours"] == 2.0

    def test_summary_scoped_to_user(self, client: TestClient) -> None:
        """Summary should only include sessions for that user."""
        # Create users
        client.post(
            "/users",
            json={"username": "alice", "display_name": "Alice", "email": "alice@test.com"},
        )
        client.post(
            "/users",
            json={"username": "bob", "display_name": "Bob", "email": "bob@test.com"},
        )

        # Create subjects
        alice_subj = client.post(
            "/users/alice/subjects",
            json={"name": "Physics", "teacher": None, "color": "#FF5733"},
        ).json()
        bob_subj = client.post(
            "/users/bob/subjects",
            json={"name": "Chemistry", "teacher": None, "color": "#4A90E2"},
        ).json()

        # Create sessions
        client.post(
            "/users/alice/study-sessions",
            json={"subject_id": alice_subj["id"], "duration_minutes": 60},
        )
        client.post(
            "/users/bob/study-sessions",
            json={"subject_id": bob_subj["id"], "duration_minutes": 120},
        )

        # Alice's summary should only show her 60 minutes
        alice_summary = client.get("/users/alice/study-sessions/summary").json()
        assert alice_summary["total_hours"] == 1.0
        assert alice_summary["total_sessions"] == 1

        # Bob's summary should only show his 120 minutes
        bob_summary = client.get("/users/bob/study-sessions/summary").json()
        assert bob_summary["total_hours"] == 2.0
        assert bob_summary["total_sessions"] == 1

    def test_summary_nonexistent_user_404(self, client: TestClient) -> None:
        """Summary for non-existent user should return 404."""
        res = client.get("/users/nonexistent/study-sessions/summary")
        assert res.status_code == 404
