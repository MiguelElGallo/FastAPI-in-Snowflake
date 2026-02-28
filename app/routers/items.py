"""Item CRUD endpoints."""

from fastapi import APIRouter, HTTPException, Query

from app.crud.item import (
    create_item,
    delete_item,
    get_item_by_id,
    get_items,
    update_item,
)
from app.dependencies import CurrentUser
from app.models.item import ItemCreate, ItemRead, ItemsRead, ItemUpdate

router = APIRouter(prefix="/items", tags=["items"])


@router.get("/", response_model=ItemsRead)
def read_items(
    current_user: CurrentUser,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
) -> ItemsRead:
    """List items owned by the current user."""
    items, count = get_items(owner_id=current_user.id, skip=skip, limit=limit)
    return ItemsRead(data=items, count=count)


@router.post("/", response_model=ItemRead, status_code=201)
def create_new_item(current_user: CurrentUser, item_in: ItemCreate) -> ItemRead:
    """Create a new item owned by the current user."""
    return create_item(item_in, owner_id=current_user.id)


@router.get("/{item_id}", response_model=ItemRead)
def read_item(item_id: str, current_user: CurrentUser) -> ItemRead:
    """Get a specific item. Users can only access their own items."""
    item = get_item_by_id(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough privileges")
    return item


@router.patch("/{item_id}", response_model=ItemRead)
def update_existing_item(
    item_id: str, current_user: CurrentUser, item_in: ItemUpdate
) -> ItemRead:
    """Update an item. Users can only update their own items."""
    item = get_item_by_id(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough privileges")
    updated = update_item(item_id, item_in)
    if updated is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated


@router.delete("/{item_id}", status_code=204)
def delete_existing_item(item_id: str, current_user: CurrentUser) -> None:
    """Delete an item. Users can only delete their own items."""
    item = get_item_by_id(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough privileges")
    delete_item(item_id)
