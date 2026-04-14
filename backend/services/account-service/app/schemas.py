from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str


class UserAccount(BaseModel):
    user_id: str = Field(..., min_length=1)
    staff_code: str | None = None
    email: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    full_name: str = Field(..., min_length=1)
    role: str = Field(..., min_length=1)
    phone: str = Field(..., min_length=1)
    department: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    created_at: str = Field(..., min_length=1)
    last_login_at: str | None = None


class UserPasswordUpdate(BaseModel):
    password: str = Field(..., min_length=3)


class StaffUserCreate(BaseModel):
    staff_code: str = Field(..., min_length=2)
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=3)
    full_name: str = Field(..., min_length=1)
    phone: str = Field(..., min_length=1)
    department: str = Field(..., min_length=1)
    status: str = "active"


class ManagedUserCreate(StaffUserCreate):
    role: str = Field(..., pattern="^(staff|product_manager)$")


class UserDeleteResponse(BaseModel):
    user_id: str = Field(..., min_length=1)
    removed_email: str = Field(..., min_length=1)
    reassigned_accounts: int = Field(..., ge=0)
    message: str = Field(..., min_length=1)
