from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str


class LivestreamAccount(BaseModel):
    account_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    platform: str = Field(..., min_length=1)
    owner_name: str = Field(..., min_length=1)
    current_viewers: int = Field(..., ge=0)
    max_capacity: int = Field(..., gt=0)
    engagement_rate: float = Field(..., ge=0, le=1)
    lag_signal: float = Field(..., ge=0, le=1)
    status: str


class LivestreamAccountCreate(BaseModel):
    name: str = Field(..., min_length=1)
    platform: str = Field(..., min_length=1)
    owner_name: str = Field(..., min_length=1)
    current_viewers: int = Field(..., ge=0)
    max_capacity: int = Field(..., gt=0)
    engagement_rate: float = Field(..., ge=0, le=1)
    lag_signal: float = Field(..., ge=0, le=1)
    status: str = "active"


class PlatformSummary(BaseModel):
    platform: str
    display_name: str
    total_accounts: int = Field(..., ge=0)
    active_accounts: int = Field(..., ge=0)
    total_viewers: int = Field(..., ge=0)
    total_capacity: int = Field(..., ge=0)
    average_lag_signal: float = Field(..., ge=0, le=1)


class PlatformAccountsGroup(BaseModel):
    platform: str
    display_name: str
    accounts: list[LivestreamAccount]
    summary: PlatformSummary
