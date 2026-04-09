from __future__ import annotations

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=3)
    captcha_id: str = Field(..., min_length=8)
    captcha_answer: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class CaptchaResponse(BaseModel):
    captcha_id: str
    image_svg_base64: str
    expires_in_seconds: int


class HealthResponse(BaseModel):
    status: str
    service: str
