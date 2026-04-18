from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str


class LivestreamAccount(BaseModel):
    account_id: str = Field(..., min_length=1)
    account_code: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    platform: str = Field(..., min_length=1)
    platform_display_name: str = Field(..., min_length=1)
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    owner_user_id: str | None = None
    owner_name: str = Field(..., min_length=1)
    owner_email: str | None = None
    owner_password: str | None = None
    backup_contact: str = Field(..., min_length=1)
    current_viewers: int = Field(..., ge=0)
    max_capacity: int = Field(..., gt=0)
    engagement_rate: float = Field(..., ge=0, le=1)
    lag_signal: float = Field(..., ge=0, le=1)
    status: str = Field(..., min_length=1)
    broadcast_status: str = Field(..., min_length=1)
    live_started_at: str | None = None
    last_heartbeat_at: str | None = None
    stream_url: str = Field(..., min_length=1)
    warehouse_location: str = Field(..., min_length=1)
    shift_label: str = Field(..., min_length=1)
    created_at: str = Field(..., min_length=1)


class LivestreamAccountCreate(BaseModel):
    name: str = Field(..., min_length=1)
    platform: str = Field(..., min_length=1)
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    owner_name: str = Field(..., min_length=1)
    owner_user_id: str | None = None
    backup_contact: str = Field(..., min_length=1)
    current_viewers: int = Field(..., ge=0)
    max_capacity: int = Field(..., gt=0)
    engagement_rate: float = Field(..., ge=0, le=1)
    lag_signal: float = Field(..., ge=0, le=1)
    status: str = "active"
    stream_url: str = Field(..., min_length=1)
    warehouse_location: str = Field(..., min_length=1)
    shift_label: str = Field(..., min_length=1)


class LivestreamAccountDeleteResponse(BaseModel):
    account_id: str = Field(..., min_length=1)
    account_name: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class LivestreamPresenceHeartbeat(BaseModel):
    viewer_id: str = Field(..., min_length=1)
    viewer_role: str = Field(..., min_length=1)
    viewer_name: str = Field(..., min_length=1)
    is_host: bool = False
    is_live: bool = False


class LivestreamPresenceDeleteResponse(BaseModel):
    account_id: str = Field(..., min_length=1)
    viewer_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class LivestreamProductAssignment(BaseModel):
    assignment_id: str = Field(..., min_length=1)
    account_id: str = Field(..., min_length=1)
    account_name: str = Field(..., min_length=1)
    platform: str = Field(..., min_length=1)
    platform_display_name: str = Field(..., min_length=1)
    product_id: str = Field(..., min_length=1)
    product_name: str = Field(..., min_length=1)
    product_sku: str = Field(..., min_length=1)
    product_category: str = Field(..., min_length=1)
    assigned_by_user_id: str | None = None
    assigned_by_name: str | None = None
    assigned_at: str = Field(..., min_length=1)


class LivestreamProductAssignmentCreate(BaseModel):
    account_id: str = Field(..., min_length=1)
    product_id: str = Field(..., min_length=1)
    assigned_by_user_id: str | None = None


class LivestreamProductAssignmentDeleteResponse(BaseModel):
    assignment_id: str = Field(..., min_length=1)
    account_id: str = Field(..., min_length=1)
    product_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class LivestreamProductOffer(BaseModel):
    live_offer_id: str = Field(..., min_length=1)
    account_id: str = Field(..., min_length=1)
    account_name: str = Field(..., min_length=1)
    platform: str = Field(..., min_length=1)
    platform_display_name: str = Field(..., min_length=1)
    product_id: str = Field(..., min_length=1)
    product_name: str = Field(..., min_length=1)
    product_sku: str = Field(..., min_length=1)
    product_category: str = Field(..., min_length=1)
    original_price: float = Field(..., ge=0)
    live_price: float = Field(..., ge=0)
    pinned_by_user_id: str | None = None
    pinned_by_name: str | None = None
    pinned_at: str = Field(..., min_length=1)


class LivestreamProductOfferUpsert(BaseModel):
    account_id: str = Field(..., min_length=1)
    product_id: str = Field(..., min_length=1)
    live_price: float = Field(..., gt=0)
    pinned_by_user_id: str | None = None


class LivestreamProductOfferDeleteResponse(BaseModel):
    account_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class PlatformSummary(BaseModel):
    platform: str
    display_name: str
    total_accounts: int = Field(..., ge=0)
    active_accounts: int = Field(..., ge=0)
    live_accounts: int = Field(..., ge=0)
    total_viewers: int = Field(..., ge=0)
    total_capacity: int = Field(..., ge=0)
    average_lag_signal: float = Field(..., ge=0, le=1)


class PlatformAccountsGroup(BaseModel):
    platform: str
    display_name: str
    accounts: list[LivestreamAccount]
    summary: PlatformSummary
