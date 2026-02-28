"""Item Pydantic models."""

from datetime import datetime

from pydantic import BaseModel


class ItemBase(BaseModel):
    title: str
    description: str | None = None


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    title: str | None = None
    description: str | None = None


class ItemRead(ItemBase):
    id: str
    owner_id: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ItemsRead(BaseModel):
    data: list[ItemRead]
    count: int
