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


class DemoLoginRequest(BaseModel):
    identifier: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class DemoUserProfile(BaseModel):
    id: str = Field(..., min_length=1)
    role: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    email: str = Field(..., min_length=1)
    phone: str = Field(..., min_length=1)
    department: str | None = None
    shipping_address: str | None = None
    birth_year: int | None = None
    status: str = Field(..., min_length=1)


class DemoLoginResponse(BaseModel):
    user: DemoUserProfile


class CustomerProfile(BaseModel):
    customer_id: str = Field(..., min_length=1)
    phone: str = Field(..., min_length=1)
    email: str = Field(..., min_length=1)
    full_name: str = Field(..., min_length=1)
    shipping_address: str = Field(..., min_length=1)
    birth_year: int = Field(..., ge=1900)
    status: str = Field(..., min_length=1)
    created_at: str = Field(..., min_length=1)


class CustomerRegisterRequest(BaseModel):
    phone: str = Field(..., min_length=8)
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=3)
    full_name: str = Field(..., min_length=1)
    shipping_address: str = Field(..., min_length=1)
    birth_year: int = Field(..., ge=1900)


class CartItemCreateRequest(BaseModel):
    account_id: str = Field(..., min_length=1)
    product_id: str = Field(..., min_length=1)
    quantity: int = Field(default=1, ge=1)


class CartItemResponse(BaseModel):
    cart_item_id: str = Field(..., min_length=1)
    customer_id: str = Field(..., min_length=1)
    account_id: str = Field(..., min_length=1)
    account_name: str = Field(..., min_length=1)
    platform: str = Field(..., min_length=1)
    platform_display_name: str = Field(..., min_length=1)
    product_id: str = Field(..., min_length=1)
    product_name: str = Field(..., min_length=1)
    product_sku: str = Field(..., min_length=1)
    product_category: str = Field(..., min_length=1)
    quantity: int = Field(..., ge=1)
    unit_price: float = Field(..., ge=0)
    original_price: float = Field(..., ge=0)
    added_at: str = Field(..., min_length=1)
    line_total: float = Field(..., ge=0)


class CartMutationResponse(BaseModel):
    message: str = Field(..., min_length=1)
    items: list[CartItemResponse]


class CustomerOrderItem(BaseModel):
    order_item_id: str = Field(..., min_length=1)
    product_id: str = Field(..., min_length=1)
    product_name: str = Field(..., min_length=1)
    quantity: int = Field(..., ge=1)
    unit_price: float = Field(..., ge=0)
    original_price: float = Field(..., ge=0)
    line_total: float = Field(..., ge=0)


class CustomerOrder(BaseModel):
    order_id: str = Field(..., min_length=1)
    customer_id: str = Field(..., min_length=1)
    account_id: str = Field(..., min_length=1)
    account_name: str = Field(..., min_length=1)
    platform: str = Field(..., min_length=1)
    platform_display_name: str = Field(..., min_length=1)
    total_amount: float = Field(..., ge=0)
    shipping_address: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    created_at: str = Field(..., min_length=1)
    items: list[CustomerOrderItem]


class CheckoutResponse(BaseModel):
    message: str = Field(..., min_length=1)
    orders: list[CustomerOrder]
