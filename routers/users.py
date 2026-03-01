"""
Users router — AC6-8.

Endpoints
---------
POST /users              — create a new student account
GET  /users/{username}   — retrieve user profile
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status

from student_app.models import UserCreate, UserOut
from student_app.storage import storage

router = APIRouter(prefix="/users", tags=["users"])


def _now_iso() -> str:
    """Return current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _require_user(username: str) -> dict:
    """Return the user dict or raise 404.

    Used by all routers that are scoped to a username path segment.
    """
    user = storage.users.get(username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found.",
        )
    return user


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("", status_code=status.HTTP_201_CREATED, response_model=UserOut)
def create_user(payload: UserCreate) -> UserOut:
    """Create a new student user account.

    Returns 409 if the username is already taken.
    """
    if payload.username in storage.users:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{payload.username}' is already taken.",
        )

    user_dict = {
        "username": payload.username,
        "display_name": payload.display_name,
        "email": payload.email,
        "created_at": _now_iso(),
    }
    storage.users[payload.username] = user_dict
    return UserOut(**user_dict)


@router.get("/{username}", response_model=UserOut)
def get_user(username: str) -> UserOut:
    """Retrieve a student user's profile.

    Returns 404 if the username does not exist.
    """
    user_dict = _require_user(username)
    return UserOut(**user_dict)
