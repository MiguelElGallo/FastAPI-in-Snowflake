"""User management endpoints."""

from fastapi import APIRouter, HTTPException, Query

from app.crud.user import (
    create_user,
    delete_user,
    get_user_by_email,
    get_user_by_id,
    get_users,
    update_user,
)
from app.dependencies import CurrentSuperuser, CurrentUser
from app.models.user import UserCreate, UserRead, UsersRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=UsersRead)
def read_users(
    _current_user: CurrentSuperuser,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
) -> UsersRead:
    """List all users (superuser only)."""
    users, count = get_users(skip=skip, limit=limit)
    return UsersRead(data=users, count=count)


@router.get("/me", response_model=UserRead)
def read_user_me(current_user: CurrentUser) -> UserRead:
    """Get the current authenticated user."""
    return current_user


@router.patch("/me", response_model=UserRead)
def update_user_me(current_user: CurrentUser, user_in: UserUpdate) -> UserRead:
    """Update the current user's own profile."""
    # Prevent non-superusers from escalating privileges
    if user_in.is_superuser is not None and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Cannot modify superuser status")
    updated = update_user(current_user.id, user_in)
    if updated is None:
        raise HTTPException(status_code=404, detail="User not found")
    return updated


@router.post("/", response_model=UserRead, status_code=201)
def create_new_user(_current_user: CurrentSuperuser, user_in: UserCreate) -> UserRead:
    """Create a new user (superuser only)."""
    existing = get_user_by_email(user_in.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    return create_user(user_in)


@router.get("/{user_id}", response_model=UserRead)
def read_user_by_id(user_id: str, _current_user: CurrentSuperuser) -> UserRead:
    """Get a user by ID (superuser only)."""
    user = get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete("/{user_id}", status_code=204)
def delete_user_by_id(user_id: str, current_user: CurrentSuperuser) -> None:
    """Delete a user (superuser only). Cannot delete yourself."""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    user = get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    delete_user(user_id)
