"""
Student Productivity & Task Management App — FastAPI entry point.

Run with:
    uvicorn student_app.main:app --reload

GET / serves the HTML frontend from student_app/templates/index.html.
All API routers are mounted with the /api prefix (except users which uses
/users directly to satisfy the nested-path pattern /users/{username}/...).
"""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from student_app.routers import (
    analytics,
    pomodoro,
    study_sessions,
    subjects,
    subtasks,
    tasks,
    users,
)

app = FastAPI(
    title="Student Productivity & Task Management API",
    description=(
        "A RESTful API for students to manage tasks, subjects, study sessions, "
        "analytics, and Pomodoro timers."
    ),
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# CORS — allow all origins for local development
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Mount routers
# ---------------------------------------------------------------------------
app.include_router(users.router)
app.include_router(subjects.router)
app.include_router(tasks.router)
app.include_router(subtasks.router)
app.include_router(study_sessions.router)
app.include_router(analytics.router)
app.include_router(pomodoro.router)


# ---------------------------------------------------------------------------
# Frontend
# ---------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def serve_frontend() -> HTMLResponse:
    """Serve the single-page frontend from templates/index.html."""
    here = os.path.dirname(__file__)
    template_path = os.path.join(here, "templates", "index.html")
    with open(template_path, "r", encoding="utf-8") as fh:
        html = fh.read()
    return HTMLResponse(content=html)
