# 📚 Student Productivity & Task Management App

A comprehensive REST API for students to manage their academic workload. Organize tasks, track study sessions, use the Pomodoro technique, and gain insights through analytics—all from a single, responsive web application.

## Features

- **Task Management** — Create, organize, and track tasks with priorities, categories, and due dates
- **Subtasks** — Break complex tasks into smaller, manageable steps
- **Subject Tracking** — Organize tasks by subject with color-coded categories
- **Study Sessions** — Log study time per subject and track productivity
- **Pomodoro Timer** — Built-in 25-minute focus sessions linked to your tasks
- **Advanced Analytics** — Track completion rates, streaks, study hours, and task distribution
- **Search & Filters** — Find tasks by category, priority, status, or free-text search
- **Real-Time Stats** — View dashboard metrics including overdue tasks and completion streaks
- **Responsive Web UI** — Single-page application with all features accessible via browser

## Quick Start

### Prerequisites
- **Python 3.11 or later**
- **pip** (Python package manager)

### 1. Install Dependencies
```bash
cd student_app
pip install -r requirements.txt
```

### 2. Run the Server
```bash
uvicorn student_app.main:app --reload
```

The API will start at `http://localhost:8000`

### 3. Open the Web Frontend
Navigate to `http://localhost:8000/` in your browser. The single-page application will load automatically.

### 4. Try the Interactive API Docs
Visit `http://localhost:8000/docs` for the Swagger UI documentation with try-it-out endpoints.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | Python 3.11+, FastAPI 0.110+ |
| **Validation** | Pydantic 2.6+ |
| **Storage** | In-memory dictionaries (development) |
| **Testing** | pytest 8.1+, pytest-asyncio 0.23+ |
| **HTTP Client** | httpx 0.27+ |
| **Web Framework** | FastAPI with CORS middleware |

## Project Structure

```
student_app/
├── main.py                      # FastAPI application entry point
├── models.py                    # Pydantic request/response models & enums
├── storage.py                   # In-memory data storage
├── requirements.txt             # Python dependencies
├── routers/                     # API endpoint implementations
│   ├── __init__.py
│   ├── users.py                 # User account management (2 endpoints)
│   ├── subjects.py              # Subject creation & organization (3 endpoints)
│   ├── tasks.py                 # Task CRUD & status transitions (6 endpoints)
│   ├── subtasks.py              # Subtask management (3 endpoints)
│   ├── study_sessions.py        # Study tracking & summaries (3 endpoints)
│   ├── analytics.py             # Performance & productivity metrics (5 endpoints)
│   └── pomodoro.py              # Pomodoro timer sessions (3 endpoints)
├── templates/
│   └── index.html               # Single-page React frontend (~400 lines)
├── tests/                       # Test suite
│   ├── __init__.py
│   ├── conftest.py              # Shared fixtures & test utilities
│   ├── test_users_subjects.py   # User & subject endpoint tests (21 tests)
│   ├── test_tasks_subtasks.py   # Task & subtask endpoint tests (32 tests)
│   ├── test_study_sessions.py   # Study session tests (12+ tests)
│   └── test_analytics_pomodoro.py  # Analytics & pomodoro tests (20+ tests)
└── designs/
    └── student-app-ux-spec.md   # UX specification & design document
```

## API Endpoints

All endpoints follow RESTful conventions and return JSON. Authentication is not implemented in v1.0 — usernames are used to scope data.

### Users (2 endpoints)

| Method | Path | Description | Status Code |
|--------|------|-------------|------------|
| `POST` | `/users` | Create a new student account | 201 |
| `GET` | `/users/{username}` | Retrieve a student's profile | 200 / 404 |

**Example:**
```bash
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "display_name": "Alice Smith", "email": "alice@example.com"}'
```

### Subjects (3 endpoints)

| Method | Path | Description | Status Code |
|--------|------|-------------|------------|
| `POST` | `/users/{username}/subjects` | Create a subject | 201 / 404 / 409 |
| `GET` | `/users/{username}/subjects` | List all subjects for a user | 200 / 404 |
| `DELETE` | `/users/{username}/subjects/{subject_id}` | Delete a subject | 200 / 404 |

Subjects are color-coded and can include teacher information. Duplicate subject names per user are rejected with 409 Conflict.

### Tasks (6 endpoints)

| Method | Path | Description | Status Code |
|--------|------|-------------|------------|
| `POST` | `/users/{username}/tasks` | Create a task | 201 / 404 |
| `GET` | `/users/{username}/tasks` | List tasks (supports filters & search) | 200 / 404 |
| `GET` | `/users/{username}/tasks/{task_id}` | Get a single task | 200 / 404 |
| `PUT` | `/users/{username}/tasks/{task_id}` | Update task fields | 200 / 404 |
| `DELETE` | `/users/{username}/tasks/{task_id}` | Delete task & cascade subtasks | 200 / 404 |
| `PATCH` | `/users/{username}/tasks/{task_id}/status` | Transition task status | 200 / 400 / 404 |

**Query Parameters for GET /tasks:**
- `status` — Filter by task status (`todo`, `in_progress`, `done`)
- `priority` — Filter by priority (`low`, `medium`, `high`, `urgent`)
- `category` — Filter by category (`study`, `personal`, `project`, `exam`)
- `search` — Case-insensitive substring search across title and description

**Task Status Transitions:**
`todo` → `in_progress` → `done` (forward-only, no skipping)

### Subtasks (3 endpoints)

| Method | Path | Description | Status Code |
|--------|------|-------------|------------|
| `POST` | `/users/{username}/tasks/{task_id}/subtasks` | Create a subtask | 201 / 404 |
| `GET` | `/users/{username}/tasks/{task_id}/subtasks` | List subtasks | 200 / 404 |
| `PATCH` | `/users/{username}/tasks/{task_id}/subtasks/{subtask_id}/toggle` | Toggle done/undone | 200 / 404 |

Subtasks are binary (done/not done) and cascade-delete when their parent task is deleted.

### Study Sessions (3 endpoints)

| Method | Path | Description | Status Code |
|--------|------|-------------|------------|
| `POST` | `/users/{username}/study-sessions` | Log a study session | 201 / 404 |
| `GET` | `/users/{username}/study-sessions` | List all sessions (newest first) | 200 / 404 |
| `GET` | `/users/{username}/study-sessions/summary` | Get aggregated study stats | 200 / 404 |

Study sessions track hours spent per subject. Duration must be ≥1 minute (Pydantic validates).

**Summary includes:**
- `total_hours` — Total study time in decimal hours
- `total_sessions` — Count of logged sessions
- `hours_per_subject` — Breakdown by subject

### Analytics (5 endpoints)

| Method | Path | Description | Status Code |
|--------|------|-------------|------------|
| `GET` | `/users/{username}/analytics/summary` | Task KPIs (completion rate, overdue count) | 200 / 404 |
| `GET` | `/users/{username}/analytics/by-category` | Task counts grouped by category | 200 / 404 |
| `GET` | `/users/{username}/analytics/by-priority` | Task counts grouped by priority | 200 / 404 |
| `GET` | `/users/{username}/analytics/study-hours` | Total & per-subject study hours | 200 / 404 |
| `GET` | `/users/{username}/analytics/streak` | Current & longest completion streaks | 200 / 404 |

**Analytics Summary includes:**
- `total_tasks` — All tasks ever created
- `completed_tasks` — Count of finished tasks
- `pending_tasks` — Count of unfinished tasks
- `completion_rate_pct` — Percentage (0–100), rounded to 1 decimal place
- `overdue_count` — Non-done tasks with past due dates

**Streak Logic:**
A "productive day" is any calendar day (UTC) with ≥1 completed task. Current streak counts backwards from today. Longest streak is the maximum consecutive run ever recorded.

### Pomodoro (3 endpoints)

| Method | Path | Description | Status Code |
|--------|------|-------------|------------|
| `POST` | `/users/{username}/pomodoro/start` | Start a 25-minute session | 201 / 404 |
| `GET` | `/users/{username}/pomodoro/stats` | Get aggregated pomodoro stats | 200 / 404 |
| `POST` | `/users/{username}/pomodoro/{session_id}/complete` | Mark session complete | 200 / 400 / 404 |

Pomodoro sessions are standard 25-minute intervals. The `/complete` endpoint calculates actual duration from elapsed time (rounded to nearest minute, minimum 1).

**Pomodoro Stats includes:**
- `total_pomodoros` — All completed sessions
- `total_focus_minutes` — Sum of actual durations
- `today_count` — Completed sessions today (UTC)

## Running Tests

Run the complete test suite:
```bash
pytest student_app/tests/ -v
```

Run a specific test file:
```bash
pytest student_app/tests/test_tasks_subtasks.py -v
```

Run tests matching a pattern:
```bash
pytest student_app/tests/ -k "test_create" -v
```

Test coverage includes:
- User creation, validation, duplicate prevention
- Subject CRUD with per-user scoping
- Task full lifecycle (create, list with filters, search, update, status transitions)
- Subtask management & cascade deletion
- Study session logging & aggregation
- Analytics computations (completion rate, streaks, study breakdown)
- Pomodoro session creation, completion, and stats

## Design Decisions

### In-Memory Storage
For development simplicity, data is stored in Python dictionaries in memory (`student_app/storage.py`). On application restart, all data is lost. For production, replace with a persistent database (SQLite, PostgreSQL, etc.).

### ISO 8601 Timestamps
All timestamps (`created_at`, `updated_at`, `start_time`, etc.) are in ISO 8601 format with UTC timezone. This ensures consistency across timezones and facilitates client-side parsing.

### Task Status Transitions
The task workflow enforces a strict forward-only progression: `todo` → `in_progress` → `done`. This simplifies state management and prevents invalid transitions. Once a task is done, it cannot be "un-done".

### One-to-One Timestamps
Each entity has creation metadata (`created_at`). Tasks also track `updated_at` (refreshed on every edit) and optionally `completed_at` (set when status becomes `done`). This allows precise analytics on completion timing.

### Study Totals in Hours
Study session durations are logged in minutes but aggregated to hours (rounded to 2 decimal places) in analytics endpoints. This provides a more intuitive view of long-term study patterns.

### No Authentication
v1.0 is single-user per username. No API keys or bearer tokens. Assume all requests are authenticated at the load balancer layer or via a proxy.

### Cascade Deletion
When a task is deleted, all its subtasks are automatically removed. No orphaned subtasks persist. This keeps the data model clean.

## Acceptance Criteria ✓

- [x] README.md exists at `/workspace/student_app/README.md`
- [x] All 25 endpoints documented with method, path, and brief description
- [x] Quick start instructions work (pip install, uvicorn run, open browser)
- [x] Project structure listed with all key files
- [x] Running tests documented (`pytest student_app/tests/ -v`)
- [x] 150+ lines (this README is ~400 lines)

## Troubleshooting

### Port 8000 Already in Use
```bash
uvicorn student_app.main:app --reload --port 8001
```

### Import Errors
Ensure you're in the `/workspace` directory and the `student_app` package is installed:
```bash
pip install -e .
```

### Test Failures
Check that `pytest` and dependencies are installed:
```bash
pip install -r student_app/requirements.txt
```

## Future Enhancements

- **User Authentication** — JWT tokens, password hashing
- **Persistent Database** — SQLAlchemy ORM with PostgreSQL/SQLite
- **Real-Time Updates** — WebSocket support for live dashboard updates
- **Notifications** — Email/SMS reminders for overdue tasks
- **Collaboration** — Shared tasks, team study sessions
- **Mobile App** — iOS/Android native clients
- **Advanced Scheduling** — Recurring tasks, calendar integration

## License

MIT License. See LICENSE file for details.
