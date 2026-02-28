"""User CRUD operations against Snowflake."""

from __future__ import annotations

from app.database import execute_query, execute_scalar
from app.models.user import UserCreate, UserRead, UserUpdate
from app.security import get_password_hash, verify_password


def _row_to_user(row: dict) -> UserRead:
    """Normalize Snowflake column names (uppercase) to UserRead fields."""
    return UserRead(
        id=row["ID"],
        email=row["EMAIL"],
        full_name=row.get("FULL_NAME"),
        is_active=row.get("IS_ACTIVE", True),
        is_superuser=row.get("IS_SUPERUSER", False),
        created_at=row.get("CREATED_AT"),
        updated_at=row.get("UPDATED_AT"),
    )


def get_user_by_id(user_id: str) -> UserRead | None:
    rows = execute_query("SELECT * FROM users WHERE id = %s", (user_id,))
    if not rows:
        return None
    return _row_to_user(rows[0])


def get_user_by_email(email: str) -> UserRead | None:
    rows = execute_query("SELECT * FROM users WHERE email = %s", (email,))
    if not rows:
        return None
    return _row_to_user(rows[0])


def get_user_hashed_password(email: str) -> tuple[UserRead, str] | None:
    """Return user + hashed password for authentication."""
    rows = execute_query("SELECT * FROM users WHERE email = %s", (email,))
    if not rows:
        return None
    row = rows[0]
    return _row_to_user(row), row["HASHED_PASSWORD"]


def authenticate_user(email: str, password: str) -> UserRead | None:
    result = get_user_hashed_password(email)
    if result is None:
        return None
    user, hashed = result
    if not verify_password(password, hashed):
        return None
    return user


def get_users(*, skip: int = 0, limit: int = 100) -> tuple[list[UserRead], int]:
    count = execute_scalar("SELECT COUNT(*) FROM users") or 0
    rows = execute_query(
        "SELECT * FROM users ORDER BY created_at DESC LIMIT %s OFFSET %s",
        (limit, skip),
    )
    return [_row_to_user(r) for r in rows], int(count)


def create_user(user_in: UserCreate) -> UserRead:
    hashed = get_password_hash(user_in.password)
    rows = execute_query(
        """
        INSERT INTO users (email, hashed_password, full_name, is_active, is_superuser)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (
            user_in.email,
            hashed,
            user_in.full_name,
            user_in.is_active,
            user_in.is_superuser,
        ),
        fetch=False,
    )
    # Retrieve the created user
    return get_user_by_email(user_in.email)  # type: ignore[return-value]


def update_user(user_id: str, user_in: UserUpdate) -> UserRead | None:
    updates = user_in.model_dump(exclude_unset=True)
    if not updates:
        return get_user_by_id(user_id)

    if "password" in updates:
        updates["hashed_password"] = get_password_hash(updates.pop("password"))

    set_clause = ", ".join(f"{k} = %s" for k in updates)
    values = list(updates.values()) + [user_id]

    execute_query(
        f"UPDATE users SET {set_clause}, updated_at = CURRENT_TIMESTAMP() WHERE id = %s",
        tuple(values),
        fetch=False,
    )
    return get_user_by_id(user_id)


def delete_user(user_id: str) -> bool:
    execute_query("DELETE FROM users WHERE id = %s", (user_id,), fetch=False)
    return True
