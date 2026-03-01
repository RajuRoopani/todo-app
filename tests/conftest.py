"""
Pytest configuration for the Student Productivity App test suite.

Fixtures
--------
reset_storage  (autouse, function-scope)
               Wipes all in-memory state before and after each test so that
               tests are fully isolated regardless of execution order.

client         Synchronous FastAPI TestClient wrapping the app ASGI transport.

sample_user    Creates a test user via POST /users and returns the username str.

sample_subject Creates a user + subject, returns (username, subject_id) tuple.

sample_task    Creates a user + task (using sample_user internally), returns
               (username, task_id) tuple.
"""

from __future__ import annotations

from typing import Tuple

import pytest
from fastapi.testclient import TestClient

from student_app.main import app
from student_app.storage import storage


# ---------------------------------------------------------------------------
# Core fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_storage() -> None:
    """Wipe storage before and after every test for full isolation.

    Autouse + function scope means this runs around every single test
    automatically — no need to explicitly request it.
    """
    storage.reset()
    yield
    storage.reset()


@pytest.fixture
def client() -> TestClient:
    """Return a synchronous TestClient bound to the FastAPI app."""
    return TestClient(app)


# ---------------------------------------------------------------------------
# Convenience fixtures (composable)
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_user(client: TestClient) -> str:
    """Create a default test user via POST /users and return the username.

    Returns
    -------
    str
        The username of the newly created user ("testuser").
    """
    payload = {
        "username": "testuser",
        "display_name": "Test User",
        "email": "testuser@example.com",
    }
    res = client.post("/users", json=payload)
    assert res.status_code == 201, (
        f"sample_user: expected 201, got {res.status_code}: {res.text}"
    )
    return res.json()["username"]


@pytest.fixture
def sample_subject(client: TestClient, sample_user: str) -> Tuple[str, str]:
    """Create a user + subject and return (username, subject_id).

    Depends on sample_user so the user already exists when the subject
    is created.

    Returns
    -------
    Tuple[str, str]
        (username, subject_id) for the newly created subject.
    """
    payload = {
        "name": "Mathematics",
        "teacher": "Prof. Smith",
        "color": "#4A90E2",
    }
    res = client.post(f"/users/{sample_user}/subjects", json=payload)
    assert res.status_code == 201, (
        f"sample_subject: expected 201, got {res.status_code}: {res.text}"
    )
    return sample_user, res.json()["id"]


@pytest.fixture
def sample_task(client: TestClient, sample_user: str) -> Tuple[str, str]:
    """Create a user + task and return (username, task_id).

    Depends on sample_user so the user already exists when the task
    is created.  The task starts in status 'todo'.

    Returns
    -------
    Tuple[str, str]
        (username, task_id) for the newly created task.
    """
    payload = {
        "title": "Complete homework",
        "description": "Finish chapter 5 exercises",
        "priority": "high",
        "category": "study",
        "tags": ["homework", "math"],
    }
    res = client.post(f"/users/{sample_user}/tasks", json=payload)
    assert res.status_code == 201, (
        f"sample_task: expected 201, got {res.status_code}: {res.text}"
    )
    return sample_user, res.json()["id"]
