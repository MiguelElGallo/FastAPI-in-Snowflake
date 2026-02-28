"""Item CRUD operations against Snowflake."""

from __future__ import annotations

from app.database import execute_query, execute_scalar
from app.models.item import ItemCreate, ItemRead, ItemUpdate


def _row_to_item(row: dict) -> ItemRead:
    """Normalize Snowflake column names (uppercase) to ItemRead fields."""
    return ItemRead(
        id=row["ID"],
        title=row["TITLE"],
        description=row.get("DESCRIPTION"),
        owner_id=row["OWNER_ID"],
        created_at=row.get("CREATED_AT"),
        updated_at=row.get("UPDATED_AT"),
    )


def get_item_by_id(item_id: str) -> ItemRead | None:
    rows = execute_query("SELECT * FROM items WHERE id = %s", (item_id,))
    if not rows:
        return None
    return _row_to_item(rows[0])


def get_items(
    *, owner_id: str | None = None, skip: int = 0, limit: int = 100
) -> tuple[list[ItemRead], int]:
    if owner_id:
        count = (
            execute_scalar(
                "SELECT COUNT(*) FROM items WHERE owner_id = %s", (owner_id,)
            )
            or 0
        )
        rows = execute_query(
            "SELECT * FROM items WHERE owner_id = %s ORDER BY created_at DESC LIMIT %s OFFSET %s",
            (owner_id, limit, skip),
        )
    else:
        count = execute_scalar("SELECT COUNT(*) FROM items") or 0
        rows = execute_query(
            "SELECT * FROM items ORDER BY created_at DESC LIMIT %s OFFSET %s",
            (limit, skip),
        )
    return [_row_to_item(r) for r in rows], int(count)


def create_item(item_in: ItemCreate, owner_id: str) -> ItemRead:
    execute_query(
        """
        INSERT INTO items (title, description, owner_id)
        VALUES (%s, %s, %s)
        """,
        (item_in.title, item_in.description, owner_id),
        fetch=False,
    )
    # Retrieve the latest item for this owner with this title
    rows = execute_query(
        "SELECT * FROM items WHERE owner_id = %s AND title = %s ORDER BY created_at DESC LIMIT 1",
        (owner_id, item_in.title),
    )
    return _row_to_item(rows[0])


def update_item(item_id: str, item_in: ItemUpdate) -> ItemRead | None:
    updates = item_in.model_dump(exclude_unset=True)
    if not updates:
        return get_item_by_id(item_id)

    set_clause = ", ".join(f"{k} = %s" for k in updates)
    values = list(updates.values()) + [item_id]

    execute_query(
        f"UPDATE items SET {set_clause}, updated_at = CURRENT_TIMESTAMP() WHERE id = %s",
        tuple(values),
        fetch=False,
    )
    return get_item_by_id(item_id)


def delete_item(item_id: str) -> bool:
    execute_query("DELETE FROM items WHERE id = %s", (item_id,), fetch=False)
    return True
