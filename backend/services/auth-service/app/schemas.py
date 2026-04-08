from __future__ import annotations

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=3)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class HealthResponse(BaseModel):
    status: str
    service: str
