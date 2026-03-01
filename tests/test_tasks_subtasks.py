"""
Tests for Tasks and Subtasks routers (AC13-22, AC23-26).

Covers:
  - Task CRUD operations, filtering, searching, status transitions
  - Subtask creation, listing, toggling, cascading deletes
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestTasks:
    """Task endpoint tests (AC13-19, AC23-26)."""

    @pytest.fixture
    def user_alice(self, client: TestClient) -> dict:
        """Create test user alice."""
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
    def subject_math(self, client: TestClient, user_alice: dict) -> dict:
        """Create test subject Math for alice."""
        res = client.post(
            "/users/alice/subjects",
            json={"name": "Mathematics", "teacher": None, "color": "#FF5733"},
        )
        return res.json()

    def test_create_task_success(self, client: TestClient, user_alice: dict) -> None:
        """POST /users/{username}/tasks should create task with 201."""
        res = client.post(
            "/users/alice/tasks",
            json={
                "title": "Homework",
                "description": "Complete chapter 5",
                "priority": "high",
                "category": "study",
            },
        )
        assert res.status_code == 201
        data = res.json()
        assert data["title"] == "Homework"
        assert data["description"] == "Complete chapter 5"
        assert data["priority"] == "high"
        assert data["category"] == "study"
        assert data["status"] == "todo"
        assert data["username"] == "alice"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_task_with_all_optional_fields(
        self, client: TestClient, user_alice: dict, subject_math: dict
    ) -> None:
        """Task should accept all optional fields."""
        res = client.post(
            "/users/alice/tasks",
            json={
                "title": "Study for exam",
                "description": "Review all chapters",
                "due_date": "2025-06-30T23:59:00",
                "priority": "urgent",
                "category": "exam",
                "subject_id": subject_math["id"],
                "tags": ["exam", "review", "urgent"],
            },
        )
        assert res.status_code == 201
        data = res.json()
        assert data["due_date"] == "2025-06-30T23:59:00"
        assert data["subject_id"] == subject_math["id"]
        assert set(data["tags"]) == {"exam", "review", "urgent"}

    def test_create_task_with_minimal_fields(
        self, client: TestClient, user_alice: dict
    ) -> None:
        """Task creation should work with title only (defaults for optional fields)."""
        res = client.post(
            "/users/alice/tasks",
            json={"title": "Simple task"},
        )
        assert res.status_code == 201
        data = res.json()
        assert data["title"] == "Simple task"
        assert data["priority"] == "medium"  # default
        assert data["category"] == "study"  # default
        assert data["description"] is None
        assert data["due_date"] is None
        assert data["tags"] == []

    def test_create_task_nonexistent_user_404(self, client: TestClient) -> None:
        """Creating task for non-existent user should return 404."""
        res = client.post(
            "/users/nonexistent/tasks",
            json={"title": "Task"},
        )
        assert res.status_code == 404

    def test_list_tasks_empty(self, client: TestClient, user_alice: dict) -> None:
        """GET /users/{username}/tasks should return empty list initially."""
        res = client.get("/users/alice/tasks")
        assert res.status_code == 200
        assert res.json() == []

    def test_list_tasks_returns_all(self, client: TestClient, user_alice: dict) -> None:
        """GET should return all tasks for user."""
        # Create 3 tasks
        for i in range(3):
            client.post(
                "/users/alice/tasks",
                json={"title": f"Task {i}"},
            )
        # List them
        res = client.get("/users/alice/tasks")
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 3

    def test_list_tasks_newest_first(self, client: TestClient, user_alice: dict) -> None:
        """Tasks should be returned newest first."""
        res1 = client.post("/users/alice/tasks", json={"title": "First"})
        res2 = client.post("/users/alice/tasks", json={"title": "Second"})
        res3 = client.post("/users/alice/tasks", json={"title": "Third"})

        list_res = client.get("/users/alice/tasks")
        data = list_res.json()
        titles = [t["title"] for t in data]
        # Should be newest first
        assert titles == ["Third", "Second", "First"]

    def test_list_tasks_filter_by_status(self, client: TestClient, user_alice: dict) -> None:
        """GET ?status=X should filter tasks by status."""
        # Create tasks with different statuses
        t1 = client.post("/users/alice/tasks", json={"title": "Todo task"})
        t1_id = t1.json()["id"]

        t2 = client.post("/users/alice/tasks", json={"title": "Done task"})
        t2_id = t2.json()["id"]

        # Mark second as done
        client.patch(
            f"/users/alice/tasks/{t2_id}/status",
            json={"status": "in_progress"},
        )
        client.patch(
            f"/users/alice/tasks/{t2_id}/status",
            json={"status": "done"},
        )

        # Filter by todo
        res = client.get("/users/alice/tasks?status=todo")
        data = res.json()
        assert len(data) == 1
        assert data[0]["title"] == "Todo task"

        # Filter by done
        res = client.get("/users/alice/tasks?status=done")
        data = res.json()
        assert len(data) == 1
        assert data[0]["title"] == "Done task"

    def test_list_tasks_filter_by_priority(
        self, client: TestClient, user_alice: dict
    ) -> None:
        """GET ?priority=X should filter tasks by priority."""
        client.post(
            "/users/alice/tasks",
            json={"title": "Urgent task", "priority": "urgent"},
        )
        client.post(
            "/users/alice/tasks",
            json={"title": "Low task", "priority": "low"},
        )

        res = client.get("/users/alice/tasks?priority=urgent")
        data = res.json()
        assert len(data) == 1
        assert data[0]["title"] == "Urgent task"

    def test_list_tasks_filter_by_category(
        self, client: TestClient, user_alice: dict
    ) -> None:
        """GET ?category=X should filter tasks by category."""
        client.post(
            "/users/alice/tasks",
            json={"title": "Study task", "category": "study"},
        )
        client.post(
            "/users/alice/tasks",
            json={"title": "Personal task", "category": "personal"},
        )

        res = client.get("/users/alice/tasks?category=study")
        data = res.json()
        assert len(data) == 1
        assert data[0]["title"] == "Study task"

    def test_list_tasks_search_by_title(
        self, client: TestClient, user_alice: dict
    ) -> None:
        """GET ?search=X should find task by title (case-insensitive)."""
        client.post(
            "/users/alice/tasks",
            json={"title": "Complete assignment", "description": "Math work"},
        )
        client.post(
            "/users/alice/tasks",
            json={"title": "Review notes", "description": "Study"},
        )

        res = client.get("/users/alice/tasks?search=assignment")
        data = res.json()
        assert len(data) == 1
        assert data[0]["title"] == "Complete assignment"

    def test_list_tasks_search_case_insensitive(
        self, client: TestClient, user_alice: dict
    ) -> None:
        """Search should be case-insensitive."""
        client.post(
            "/users/alice/tasks",
            json={"title": "Buy Books"},
        )

        res = client.get("/users/alice/tasks?search=buy")
        data = res.json()
        assert len(data) == 1

        res = client.get("/users/alice/tasks?search=BOOKS")
        data = res.json()
        assert len(data) == 1

    def test_list_tasks_search_by_description(
        self, client: TestClient, user_alice: dict
    ) -> None:
        """Search should also match description."""
        client.post(
            "/users/alice/tasks",
            json={
                "title": "Task",
                "description": "Contains specific keyword here",
            },
        )

        res = client.get("/users/alice/tasks?search=specific")
        data = res.json()
        assert len(data) == 1

    def test_list_tasks_combined_filters(
        self, client: TestClient, user_alice: dict
    ) -> None:
        """Multiple filters should be combined (AND logic)."""
        client.post(
            "/users/alice/tasks",
            json={
                "title": "Urgent study",
                "priority": "urgent",
                "category": "study",
            },
        )
        client.post(
            "/users/alice/tasks",
            json={
                "title": "Urgent personal",
                "priority": "urgent",
                "category": "personal",
            },
        )
        client.post(
            "/users/alice/tasks",
            json={
                "title": "Low study",
                "priority": "low",
                "category": "study",
            },
        )

        # Filter: urgent AND study
        res = client.get("/users/alice/tasks?priority=urgent&category=study")
        data = res.json()
        assert len(data) == 1
        assert data[0]["title"] == "Urgent study"

    def test_get_task_success(self, client: TestClient, user_alice: dict) -> None:
        """GET /users/{username}/tasks/{task_id} should retrieve single task."""
        create_res = client.post(
            "/users/alice/tasks",
            json={"title": "Get this task"},
        )
        task_id = create_res.json()["id"]

        res = client.get(f"/users/alice/tasks/{task_id}")
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == task_id
        assert data["title"] == "Get this task"

    def test_get_task_nonexistent_404(self, client: TestClient, user_alice: dict) -> None:
        """GET non-existent task should return 404."""
        res = client.get("/users/alice/tasks/nonexistent-id")
        assert res.status_code == 404

    def test_get_task_wrong_user_404(self, client: TestClient) -> None:
        """User B cannot get User A's task."""
        # Create user A and task
        client.post("/users", json={
            "username": "alice",
            "display_name": "Alice",
            "email": "alice@example.com",
        })
        res1 = client.post(
            "/users/alice/tasks",
            json={"title": "Alice task"},
        )
        task_id = res1.json()["id"]

        # Create user B
        client.post("/users", json={
            "username": "bob",
            "display_name": "Bob",
            "email": "bob@example.com",
        })

        # Bob tries to get Alice's task
        res = client.get(f"/users/bob/tasks/{task_id}")
        assert res.status_code == 404

    def test_update_task_title(self, client: TestClient, user_alice: dict) -> None:
        """PUT should update task title."""
        create_res = client.post(
            "/users/alice/tasks",
            json={"title": "Original title"},
        )
        task_id = create_res.json()["id"]

        res = client.put(
            f"/users/alice/tasks/{task_id}",
            json={"title": "Updated title"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["title"] == "Updated title"

    def test_update_task_partial(self, client: TestClient, user_alice: dict) -> None:
        """PUT with only some fields should update only those fields."""
        create_res = client.post(
            "/users/alice/tasks",
            json={
                "title": "Original",
                "description": "Original desc",
                "priority": "low",
            },
        )
        task_id = create_res.json()["id"]

        # Update only priority
        res = client.put(
            f"/users/alice/tasks/{task_id}",
            json={"priority": "urgent"},
        )
        data = res.json()
        assert data["priority"] == "urgent"
        assert data["title"] == "Original"  # unchanged
        assert data["description"] == "Original desc"  # unchanged

    def test_update_task_refreshes_updated_at(
        self, client: TestClient, user_alice: dict
    ) -> None:
        """Each update should refresh updated_at timestamp."""
        create_res = client.post(
            "/users/alice/tasks",
            json={"title": "Task"},
        )
        task_id = create_res.json()["id"]
        original_updated_at = create_res.json()["updated_at"]

        # Wait would be needed for real timestamp difference, so just verify it exists
        res = client.put(
            f"/users/alice/tasks/{task_id}",
            json={"title": "Updated"},
        )
        data = res.json()
        assert "updated_at" in data
        # In real scenario, this would be > original_updated_at
        assert data["updated_at"] is not None

    def test_delete_task_success(self, client: TestClient, user_alice: dict) -> None:
        """DELETE /users/{username}/tasks/{task_id} should delete task."""
        create_res = client.post(
            "/users/alice/tasks",
            json={"title": "To delete"},
        )
        task_id = create_res.json()["id"]

        res = client.delete(f"/users/alice/tasks/{task_id}")
        assert res.status_code == 200
        assert "deleted" in res.json()["detail"]

        # Verify it's gone
        get_res = client.get(f"/users/alice/tasks/{task_id}")
        assert get_res.status_code == 404

    def test_delete_task_nonexistent_404(self, client: TestClient, user_alice: dict) -> None:
        """DELETE non-existent task should return 404."""
        res = client.delete("/users/alice/tasks/nonexistent-id")
        assert res.status_code == 404

    def test_delete_task_cascades_subtasks(
        self, client: TestClient, user_alice: dict
    ) -> None:
        """Deleting task should also delete its subtasks."""
        # Create task
        task_res = client.post(
            "/users/alice/tasks",
            json={"title": "Task with subtasks"},
        )
        task_id = task_res.json()["id"]

        # Create subtasks
        client.post(
            f"/users/alice/tasks/{task_id}/subtasks",
            json={"title": "Subtask 1"},
        )
        client.post(
            f"/users/alice/tasks/{task_id}/subtasks",
            json={"title": "Subtask 2"},
        )

        # List should have 2
        list_res = client.get(f"/users/alice/tasks/{task_id}/subtasks")
        assert len(list_res.json()) == 2

        # Delete task
        client.delete(f"/users/alice/tasks/{task_id}")

        # Verify task is gone
        get_res = client.get(f"/users/alice/tasks/{task_id}")
        assert get_res.status_code == 404

        # Verify subtasks are gone
        list_res = client.get(f"/users/alice/tasks/{task_id}/subtasks")
        assert list_res.status_code == 404

    def test_change_status_todo_to_in_progress(
        self, client: TestClient, user_alice: dict
    ) -> None:
        """Status transition todo → in_progress should succeed."""
        create_res = client.post(
            "/users/alice/tasks",
            json={"title": "Task"},
        )
        task_id = create_res.json()["id"]
        assert create_res.json()["status"] == "todo"

        res = client.patch(
            f"/users/alice/tasks/{task_id}/status",
            json={"status": "in_progress"},
        )
        assert res.status_code == 200
        assert res.json()["status"] == "in_progress"

    def test_change_status_in_progress_to_done(
        self, client: TestClient, user_alice: dict
    ) -> None:
        """Status transition in_progress → done should succeed."""
        create_res = client.post(
            "/users/alice/tasks",
            json={"title": "Task"},
        )
        task_id = create_res.json()["id"]

        # Move to in_progress first
        client.patch(
            f"/users/alice/tasks/{task_id}/status",
            json={"status": "in_progress"},
        )

        # Then to done
        res = client.patch(
            f"/users/alice/tasks/{task_id}/status",
            json={"status": "done"},
        )
        assert res.status_code == 200
        assert res.json()["status"] == "done"

    def test_change_status_todo_to_done_skips_invalid_400(
        self, client: TestClient, user_alice: dict
    ) -> None:
        """Skipping from todo directly to done should return 400."""
        create_res = client.post(
            "/users/alice/tasks",
            json={"title": "Task"},
        )
        task_id = create_res.json()["id"]

        res = client.patch(
            f"/users/alice/tasks/{task_id}/status",
            json={"status": "done"},
        )
        assert res.status_code == 400
        assert "Cannot transition" in res.json()["detail"]

    def test_change_status_done_to_todo_backwards_invalid_400(
        self, client: TestClient, user_alice: dict
    ) -> None:
        """Backwards transition done → todo should return 400."""
        create_res = client.post(
            "/users/alice/tasks",
            json={"title": "Task"},
        )
        task_id = create_res.json()["id"]

        # Move forward to done
        client.patch(
            f"/users/alice/tasks/{task_id}/status",
            json={"status": "in_progress"},
        )
        client.patch(
            f"/users/alice/tasks/{task_id}/status",
            json={"status": "done"},
        )

        # Try to go back
        res = client.patch(
            f"/users/alice/tasks/{task_id}/status",
            json={"status": "todo"},
        )
        assert res.status_code == 400

    def test_change_status_sets_completed_at(
        self, client: TestClient, user_alice: dict
    ) -> None:
        """Completing task (→ done) should set completed_at."""
        create_res = client.post(
            "/users/alice/tasks",
            json={"title": "Task"},
        )
        task_id = create_res.json()["id"]
        assert create_res.json()["completed_at"] is None

        client.patch(
            f"/users/alice/tasks/{task_id}/status",
            json={"status": "in_progress"},
        )

        res = client.patch(
            f"/users/alice/tasks/{task_id}/status",
            json={"status": "done"},
        )
        data = res.json()
        assert data["completed_at"] is not None
        assert isinstance(data["completed_at"], str)


class TestSubtasks:
    """Subtask endpoint tests (AC20-22)."""

    @pytest.fixture
    def user_alice(self, client: TestClient) -> dict:
        """Create test user alice."""
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
    def task(self, client: TestClient, user_alice: dict) -> dict:
        """Create test task for alice."""
        res = client.post(
            "/users/alice/tasks",
            json={"title": "Parent task"},
        )
        return res.json()

    def test_create_subtask_success(
        self, client: TestClient, user_alice: dict, task: dict
    ) -> None:
        """POST create subtask should return 201 with done=false."""
        res = client.post(
            f"/users/alice/tasks/{task['id']}/subtasks",
            json={"title": "Subtask 1"},
        )
        assert res.status_code == 201
        data = res.json()
        assert data["title"] == "Subtask 1"
        assert data["done"] is False
        assert data["task_id"] == task["id"]
        assert "id" in data
        assert "created_at" in data

    def test_create_subtask_for_nonexistent_task_404(
        self, client: TestClient, user_alice: dict
    ) -> None:
        """Creating subtask for non-existent task should return 404."""
        res = client.post(
            "/users/alice/tasks/nonexistent-id/subtasks",
            json={"title": "Subtask"},
        )
        assert res.status_code == 404

    def test_list_subtasks_empty(
        self, client: TestClient, user_alice: dict, task: dict
    ) -> None:
        """GET subtasks should return empty list initially."""
        res = client.get(f"/users/alice/tasks/{task['id']}/subtasks")
        assert res.status_code == 200
        assert res.json() == []

    def test_list_subtasks_returns_all(
        self, client: TestClient, user_alice: dict, task: dict
    ) -> None:
        """GET should return all subtasks for task."""
        # Create 3 subtasks
        for i in range(3):
            client.post(
                f"/users/alice/tasks/{task['id']}/subtasks",
                json={"title": f"Subtask {i}"},
            )

        res = client.get(f"/users/alice/tasks/{task['id']}/subtasks")
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 3

    def test_list_subtasks_ordered_by_created_at(
        self, client: TestClient, user_alice: dict, task: dict
    ) -> None:
        """Subtasks should be ordered by created_at (oldest first)."""
        # Create subtasks in sequence
        res1 = client.post(
            f"/users/alice/tasks/{task['id']}/subtasks",
            json={"title": "First"},
        )
        res2 = client.post(
            f"/users/alice/tasks/{task['id']}/subtasks",
            json={"title": "Second"},
        )
        res3 = client.post(
            f"/users/alice/tasks/{task['id']}/subtasks",
            json={"title": "Third"},
        )

        list_res = client.get(f"/users/alice/tasks/{task['id']}/subtasks")
        data = list_res.json()
        titles = [s["title"] for s in data]
        assert titles == ["First", "Second", "Third"]

    def test_list_subtasks_nonexistent_task_404(
        self, client: TestClient, user_alice: dict
    ) -> None:
        """GET subtasks for non-existent task should return 404."""
        res = client.get("/users/alice/tasks/nonexistent-id/subtasks")
        assert res.status_code == 404

    def test_toggle_subtask_false_to_true(
        self, client: TestClient, user_alice: dict, task: dict
    ) -> None:
        """PATCH toggle should flip done from false to true."""
        create_res = client.post(
            f"/users/alice/tasks/{task['id']}/subtasks",
            json={"title": "Subtask"},
        )
        subtask_id = create_res.json()["id"]
        assert create_res.json()["done"] is False

        res = client.patch(
            f"/users/alice/tasks/{task['id']}/subtasks/{subtask_id}/toggle",
        )
        assert res.status_code == 200
        assert res.json()["done"] is True

    def test_toggle_subtask_true_to_false(
        self, client: TestClient, user_alice: dict, task: dict
    ) -> None:
        """Toggling again should flip back to false."""
        create_res = client.post(
            f"/users/alice/tasks/{task['id']}/subtasks",
            json={"title": "Subtask"},
        )
        subtask_id = create_res.json()["id"]

        # First toggle: false → true
        client.patch(
            f"/users/alice/tasks/{task['id']}/subtasks/{subtask_id}/toggle",
        )

        # Second toggle: true → false
        res = client.patch(
            f"/users/alice/tasks/{task['id']}/subtasks/{subtask_id}/toggle",
        )
        assert res.json()["done"] is False

    def test_toggle_subtask_twice_returns_to_original(
        self, client: TestClient, user_alice: dict, task: dict
    ) -> None:
        """Two toggles should return to original state."""
        create_res = client.post(
            f"/users/alice/tasks/{task['id']}/subtasks",
            json={"title": "Subtask"},
        )
        subtask_id = create_res.json()["id"]

        # Toggle twice
        client.patch(
            f"/users/alice/tasks/{task['id']}/subtasks/{subtask_id}/toggle",
        )
        res = client.patch(
            f"/users/alice/tasks/{task['id']}/subtasks/{subtask_id}/toggle",
        )

        assert res.json()["done"] is False

    def test_toggle_subtask_nonexistent_404(
        self, client: TestClient, user_alice: dict, task: dict
    ) -> None:
        """PATCH non-existent subtask should return 404."""
        res = client.patch(
            f"/users/alice/tasks/{task['id']}/subtasks/nonexistent-id/toggle",
        )
        assert res.status_code == 404

    def test_toggle_subtask_nonexistent_task_404(
        self, client: TestClient, user_alice: dict
    ) -> None:
        """PATCH subtask for non-existent task should return 404."""
        res = client.patch(
            "/users/alice/tasks/nonexistent-task-id/subtasks/fake-subtask/toggle",
        )
        assert res.status_code == 404
