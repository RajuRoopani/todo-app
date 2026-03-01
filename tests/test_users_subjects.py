"""
Tests for Users and Subjects routers (AC6-12).

Covers:
  - User creation, retrieval, duplicate handling
  - Subject CRUD operations, scoping, uniqueness per user
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestUsers:
    """User endpoint tests (AC6-8)."""

    def test_create_user_success(self, client: TestClient) -> None:
        """POST /users should create a new user with 201 status."""
        res = client.post(
            "/users",
            json={
                "username": "alice",
                "display_name": "Alice Smith",
                "email": "alice@example.com",
            },
        )
        assert res.status_code == 201
        data = res.json()
        assert data["username"] == "alice"
        assert data["display_name"] == "Alice Smith"
        assert data["email"] == "alice@example.com"
        assert "created_at" in data

    def test_create_user_has_correct_fields(self, client: TestClient) -> None:
        """User response should contain all required fields."""
        res = client.post(
            "/users",
            json={
                "username": "bob",
                "display_name": "Bob Jones",
                "email": "bob@example.com",
            },
        )
        assert res.status_code == 201
        data = res.json()
        required_fields = {"username", "display_name", "email", "created_at"}
        assert set(data.keys()) == required_fields

    def test_create_user_duplicate_username_409(self, client: TestClient) -> None:
        """POST /users should return 409 when username already exists."""
        client.post(
            "/users",
            json={
                "username": "charlie",
                "display_name": "Charlie Brown",
                "email": "charlie@example.com",
            },
        )
        # Try to create again with same username
        res = client.post(
            "/users",
            json={
                "username": "charlie",
                "display_name": "Charlie Brown 2",
                "email": "charlie2@example.com",
            },
        )
        assert res.status_code == 409
        assert "already taken" in res.json()["detail"]

    def test_create_user_duplicate_email_allowed(self, client: TestClient) -> None:
        """POST /users should allow duplicate emails (only username must be unique)."""
        res1 = client.post(
            "/users",
            json={
                "username": "user1",
                "display_name": "User One",
                "email": "shared@example.com",
            },
        )
        assert res1.status_code == 201

        res2 = client.post(
            "/users",
            json={
                "username": "user2",
                "display_name": "User Two",
                "email": "shared@example.com",  # same email, different username
            },
        )
        assert res2.status_code == 201

    def test_get_user_success(self, client: TestClient) -> None:
        """GET /users/{username} should retrieve an existing user."""
        # Create user first
        client.post(
            "/users",
            json={
                "username": "david",
                "display_name": "David Lee",
                "email": "david@example.com",
            },
        )
        # Retrieve it
        res = client.get("/users/david")
        assert res.status_code == 200
        data = res.json()
        assert data["username"] == "david"
        assert data["display_name"] == "David Lee"
        assert data["email"] == "david@example.com"

    def test_get_user_nonexistent_404(self, client: TestClient) -> None:
        """GET /users/{username} should return 404 for non-existent user."""
        res = client.get("/users/nonexistent")
        assert res.status_code == 404
        assert "not found" in res.json()["detail"]

    def test_get_user_case_sensitive(self, client: TestClient) -> None:
        """Usernames should be case-sensitive in lookups."""
        client.post(
            "/users",
            json={
                "username": "Eve",
                "display_name": "Eve Adams",
                "email": "eve@example.com",
            },
        )
        # Eve exists, eve does not
        res_correct = client.get("/users/Eve")
        assert res_correct.status_code == 200

        res_wrong = client.get("/users/eve")
        assert res_wrong.status_code == 404


class TestSubjects:
    """Subject endpoint tests (AC9-12)."""

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
    def user_bob(self, client: TestClient) -> dict:
        """Create a test user bob."""
        res = client.post(
            "/users",
            json={
                "username": "bob",
                "display_name": "Bob",
                "email": "bob@example.com",
            },
        )
        return res.json()

    def test_create_subject_success(
        self, client: TestClient, user_alice: dict
    ) -> None:
        """POST /users/{username}/subjects should create subject with 201."""
        res = client.post(
            "/users/alice/subjects",
            json={
                "name": "Physics",
                "teacher": "Prof. Newton",
                "color": "#FF5733",
            },
        )
        assert res.status_code == 201
        data = res.json()
        assert data["name"] == "Physics"
        assert data["teacher"] == "Prof. Newton"
        assert data["color"] == "#FF5733"
        assert data["username"] == "alice"
        assert "id" in data
        assert "created_at" in data

    def test_create_subject_has_correct_fields(
        self, client: TestClient, user_alice: dict
    ) -> None:
        """Subject response should have all required fields."""
        res = client.post(
            "/users/alice/subjects",
            json={
                "name": "Chemistry",
                "teacher": None,
                "color": "#4A90E2",
            },
        )
        assert res.status_code == 201
        data = res.json()
        required_fields = {"id", "username", "name", "teacher", "color", "created_at"}
        assert set(data.keys()) == required_fields

    def test_create_subject_nonexistent_user_404(self, client: TestClient) -> None:
        """POST for non-existent user should return 404."""
        res = client.post(
            "/users/nonexistent/subjects",
            json={
                "name": "Math",
                "teacher": "Prof. Gauss",
                "color": "#6C63FF",
            },
        )
        assert res.status_code == 404
        assert "not found" in res.json()["detail"]

    def test_create_subject_duplicate_name_same_user_409(
        self, client: TestClient, user_alice: dict
    ) -> None:
        """Duplicate subject name for same user should return 409."""
        client.post(
            "/users/alice/subjects",
            json={
                "name": "Biology",
                "teacher": "Dr. Darwin",
                "color": "#22C55E",
            },
        )
        # Try to create duplicate
        res = client.post(
            "/users/alice/subjects",
            json={
                "name": "Biology",
                "teacher": "Dr. Darwin Jr.",
                "color": "#06B6D4",
            },
        )
        assert res.status_code == 409
        assert "already exists" in res.json()["detail"]

    def test_create_subject_same_name_different_user_allowed(
        self, client: TestClient, user_alice: dict, user_bob: dict
    ) -> None:
        """Same subject name should be allowed for different users."""
        res1 = client.post(
            "/users/alice/subjects",
            json={
                "name": "Algebra",
                "teacher": "Prof. A",
                "color": "#FF5733",
            },
        )
        assert res1.status_code == 201

        res2 = client.post(
            "/users/bob/subjects",
            json={
                "name": "Algebra",
                "teacher": "Prof. B",
                "color": "#4A90E2",
            },
        )
        assert res2.status_code == 201

    def test_list_subjects_empty(
        self, client: TestClient, user_alice: dict
    ) -> None:
        """GET /users/{username}/subjects should return empty list when none exist."""
        res = client.get("/users/alice/subjects")
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_list_subjects_returns_all(
        self, client: TestClient, user_alice: dict
    ) -> None:
        """GET /users/{username}/subjects should return all subjects for user."""
        # Create 3 subjects
        client.post(
            "/users/alice/subjects",
            json={"name": "Math", "teacher": None, "color": "#FF5733"},
        )
        client.post(
            "/users/alice/subjects",
            json={"name": "Science", "teacher": None, "color": "#4A90E2"},
        )
        client.post(
            "/users/alice/subjects",
            json={"name": "History", "teacher": None, "color": "#22C55E"},
        )
        # Retrieve list
        res = client.get("/users/alice/subjects")
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 3
        names = {s["name"] for s in data}
        assert names == {"Math", "Science", "History"}

    def test_list_subjects_scoped_to_user(
        self, client: TestClient, user_alice: dict, user_bob: dict
    ) -> None:
        """Subjects should be scoped: user A's subjects not visible to user B."""
        # Alice creates subject
        client.post(
            "/users/alice/subjects",
            json={"name": "Algebra", "teacher": None, "color": "#FF5733"},
        )
        # Bob creates different subject
        client.post(
            "/users/bob/subjects",
            json={"name": "Geometry", "teacher": None, "color": "#4A90E2"},
        )
        # Alice's list should only have Algebra
        res_alice = client.get("/users/alice/subjects")
        assert res_alice.status_code == 200
        names_alice = {s["name"] for s in res_alice.json()}
        assert names_alice == {"Algebra"}

        # Bob's list should only have Geometry
        res_bob = client.get("/users/bob/subjects")
        assert res_bob.status_code == 200
        names_bob = {s["name"] for s in res_bob.json()}
        assert names_bob == {"Geometry"}

    def test_list_subjects_nonexistent_user_404(self, client: TestClient) -> None:
        """GET for non-existent user should return 404."""
        res = client.get("/users/nonexistent/subjects")
        assert res.status_code == 404

    def test_list_subjects_ordered_by_created_at(
        self, client: TestClient, user_alice: dict
    ) -> None:
        """Subjects should be returned in creation order (oldest first)."""
        # Create 3 subjects in sequence
        res1 = client.post(
            "/users/alice/subjects",
            json={"name": "First", "teacher": None, "color": "#FF5733"},
        )
        res2 = client.post(
            "/users/alice/subjects",
            json={"name": "Second", "teacher": None, "color": "#4A90E2"},
        )
        res3 = client.post(
            "/users/alice/subjects",
            json={"name": "Third", "teacher": None, "color": "#22C55E"},
        )
        # Retrieve list
        res = client.get("/users/alice/subjects")
        data = res.json()
        names = [s["name"] for s in data]
        assert names == ["First", "Second", "Third"]

    def test_delete_subject_success(
        self, client: TestClient, user_alice: dict
    ) -> None:
        """DELETE /users/{username}/subjects/{subject_id} should delete the subject."""
        # Create a subject
        create_res = client.post(
            "/users/alice/subjects",
            json={"name": "ToDelete", "teacher": None, "color": "#FF5733"},
        )
        subject_id = create_res.json()["id"]

        # Delete it
        res = client.delete(f"/users/alice/subjects/{subject_id}")
        assert res.status_code == 200
        assert "deleted" in res.json()["detail"]

        # Verify it's gone
        list_res = client.get("/users/alice/subjects")
        assert len(list_res.json()) == 0

    def test_delete_subject_nonexistent_404(
        self, client: TestClient, user_alice: dict
    ) -> None:
        """DELETE non-existent subject should return 404."""
        res = client.delete("/users/alice/subjects/nonexistent-id")
        assert res.status_code == 404
        assert "not found" in res.json()["detail"]

    def test_delete_subject_wrong_user_404(
        self, client: TestClient, user_alice: dict, user_bob: dict
    ) -> None:
        """User B should not be able to delete user A's subject."""
        # Alice creates subject
        create_res = client.post(
            "/users/alice/subjects",
            json={"name": "AliceSubject", "teacher": None, "color": "#FF5733"},
        )
        subject_id = create_res.json()["id"]

        # Bob tries to delete it
        res = client.delete(f"/users/bob/subjects/{subject_id}")
        assert res.status_code == 404

        # Verify subject still exists for Alice
        list_res = client.get("/users/alice/subjects")
        assert len(list_res.json()) == 1

    def test_delete_subject_nonexistent_user_404(self, client: TestClient) -> None:
        """DELETE for non-existent user should return 404."""
        res = client.delete("/users/nonexistent/subjects/fake-id")
        assert res.status_code == 404
