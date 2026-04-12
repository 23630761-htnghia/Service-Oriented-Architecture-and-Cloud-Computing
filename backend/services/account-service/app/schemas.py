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


class UserDeleteResponse(BaseModel):
    user_id: str = Field(..., min_length=1)
    removed_email: str = Field(..., min_length=1)
    reassigned_accounts: int = Field(..., ge=0)
    message: str = Field(..., min_length=1)


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


class ProductItem(BaseModel):
    product_id: str = Field(..., min_length=1)
    sku: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    brand: str = Field(..., min_length=1)
    cost_price: float = Field(..., ge=0)
    retail_price: float = Field(..., ge=0)
    stock_quantity: int = Field(..., ge=0)
    reorder_level: int = Field(..., ge=0)
    unit: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    is_active: bool


class Supplier(BaseModel):
    supplier_id: str = Field(..., min_length=1)
    supplier_code: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    contact_name: str = Field(..., min_length=1)
    phone: str = Field(..., min_length=1)
    email: str = Field(..., min_length=1)
    address: str = Field(..., min_length=1)
    rating: float = Field(..., ge=0, le=5)
    lead_time_days: int = Field(..., ge=0)
    status: str = Field(..., min_length=1)


class SupplierOffer(BaseModel):
    offer_id: str = Field(..., min_length=1)
    offer_code: str = Field(..., min_length=1)
    offer_title: str = Field(..., min_length=1)
    supplier_id: str = Field(..., min_length=1)
    supplier_name: str = Field(..., min_length=1)
    product_id: str = Field(..., min_length=1)
    product_name: str = Field(..., min_length=1)
    min_order_quantity: int = Field(..., ge=1)
    unit_price: float = Field(..., ge=0)
    discount_percent: float = Field(..., ge=0, le=100)
    start_date: str = Field(..., min_length=1)
    end_date: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    notes: str = Field(..., min_length=1)


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


class DatabaseOverview(BaseModel):
    users: list[UserAccount]
    platform_summaries: list[PlatformSummary]
    livestream_accounts: list[LivestreamAccount]
    products: list[ProductItem]
    suppliers: list[Supplier]
    supplier_offers: list[SupplierOffer]
