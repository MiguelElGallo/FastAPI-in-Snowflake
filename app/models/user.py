"""User Pydantic models."""

from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None
    is_active: bool = True
    is_superuser: bool = False


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = None
    password: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None


class UserRead(UserBase):
    id: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class UsersRead(BaseModel):
    data: list[UserRead]
    count: int


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
