from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


Role = Literal["CUSTOMER", "SELLER", "ADMIN"]
AccountStatus = Literal["ACTIVE", "LOCKED"]
LivestreamStatus = Literal["DRAFT", "LIVE", "ENDED"]
ProductStatus = Literal["ACTIVE", "INACTIVE"]
VoucherStatus = Literal["ACTIVE", "INACTIVE"]
SenderType = Literal["CUSTOMER", "SELLER", "AI"]
AIResponseStatus = Literal["ANSWERED", "NEED_SELLER_SUPPORT", "BLOCKED"]
OrderStatus = Literal["PENDING", "CONFIRMED", "CANCELLED"]


class GatewayHealthResponse(BaseModel):
    status: str
    service: str
    dependencies: dict[str, Any]


class UserPublic(BaseModel):
    id: str
    full_name: str
    email: str = Field(..., min_length=3, max_length=200)
    role: Role
    status: AccountStatus = "ACTIVE"
    created_at: str


class UserRecord(UserPublic):
    password_hash: str


class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=120)
    email: str = Field(..., min_length=3, max_length=200)
    password: str = Field(..., min_length=4, max_length=120)
    role: Role = "CUSTOMER"


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=200)
    password: str = Field(..., min_length=1, max_length=120)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class RoleUpdateRequest(BaseModel):
    role: Role


class StatusUpdateRequest(BaseModel):
    status: AccountStatus


class Shop(BaseModel):
    id: str
    seller_id: str
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)
    logo_url: str | None = Field(default=None, max_length=1000)
    created_at: str


class Livestream(BaseModel):
    id: str
    shop_id: str
    title: str = Field(..., min_length=1, max_length=300)
    description: str = Field(default="", max_length=1000)
    status: LivestreamStatus = "DRAFT"
    ai_enabled: bool = True
    started_at: str | None = None
    ended_at: str | None = None
    viewer_count: int = Field(default=0, ge=0)


class LivestreamInput(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    description: str = Field(default="", max_length=1000)
    status: LivestreamStatus = "LIVE"
    ai_enabled: bool = True


class Product(BaseModel):
    product_id: str = Field(..., min_length=1, max_length=100)
    shop_id: str = Field(default="shop-01", min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=300)
    description: str = Field(default="", max_length=1000)
    category: str | None = Field(default=None, max_length=100)
    brand: str | None = Field(default=None, max_length=100)
    retail_price: float = Field(..., ge=0)
    live_price: float | None = Field(default=None, ge=0)
    stock_quantity: int = Field(default=0, ge=0)
    variants: list[str] = Field(default_factory=list, max_length=30)
    image_url: str | None = Field(default=None, max_length=1000)
    purchase_url: str | None = Field(default=None, max_length=1000)
    related_product_ids: list[str] = Field(default_factory=list, max_length=20)
    status: ProductStatus = "ACTIVE"


class Voucher(BaseModel):
    voucher_id: str = Field(..., min_length=1, max_length=100)
    shop_id: str = Field(default="shop-01", min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=100)
    discount_type: str = Field(default="AMOUNT", max_length=30)
    discount_value: str = Field(..., min_length=1, max_length=200)
    min_order_value: float = Field(default=0, ge=0)
    conditions: str = Field(default="", max_length=1000)
    start_date: str | None = Field(default=None, max_length=100)
    valid_until: str | None = Field(default=None, max_length=100)
    applicable_product_ids: list[str] = Field(default_factory=list, max_length=100)
    remaining_quantity: int = Field(default=0, ge=0)
    status: VoucherStatus = "ACTIVE"


class SalesPolicy(BaseModel):
    shop_id: str = "shop-01"
    shipping_fee_note: str = Field(default="", max_length=1000)
    delivery_time_note: str = Field(default="", max_length=1000)
    return_policy: str = Field(default="", max_length=1000)
    warranty_policy: str = Field(default="", max_length=1000)
    sensitive_scope_note: str = Field(
        default="AI chỉ hỗ trợ nội dung bán hàng trong livestream.",
        max_length=1000,
    )


class ChatHistoryItem(BaseModel):
    chat_id: str
    livestream_id: str
    user_id: str | None = None
    customer_name: str | None = None
    message: str
    sender_type: SenderType = "CUSTOMER"
    ai_reply: str | None = None
    intent: str | None = None
    confidence_score: float | None = None
    ai_status: AIResponseStatus | None = None
    should_escalate: bool = False
    source_platform: str = "demo"
    created_at: str


class LivestreamMessageRequest(BaseModel):
    livestream_id: str = Field(default="live-01", min_length=1, max_length=100)
    customer_name: str | None = Field(default=None, max_length=100)
    message: str = Field(..., min_length=1, max_length=2000)
    product_id: str | None = Field(default=None, max_length=100)
    source_platform: str = Field(default="demo", max_length=50)


class AutoReplySettings(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    enabled: bool = True
    model_name: str = Field(default="llama3.1", max_length=100)
    temperature: float = Field(default=0.2, ge=0, le=2)
    max_tokens: int = Field(default=220, ge=32, le=4096)
    tone: str = Field(default="Thân thiện, ngắn gọn, có tính chốt đơn.", max_length=300)
    reply_style: str = Field(default="ngắn gọn, thân thiện, chốt đơn", max_length=300)
    auto_reply_enabled: bool = True
    fallback_to_seller_enabled: bool = True


class LivestreamMessageResponse(BaseModel):
    chat: ChatHistoryItem
    auto_reply_enabled: bool


class CartItemRequest(BaseModel):
    product_id: str
    quantity: int = Field(default=1, ge=1)


class CartItem(BaseModel):
    product_id: str
    quantity: int


class OrderItem(BaseModel):
    product_id: str
    quantity: int
    price: float


class Order(BaseModel):
    id: str
    customer_id: str
    shop_id: str
    total_amount: float
    status: OrderStatus = "PENDING"
    items: list[OrderItem]
    created_at: str


class CreateOrderRequest(BaseModel):
    items: list[CartItemRequest] = Field(default_factory=list)


class ManualReplyRequest(BaseModel):
    chat_id: str | None = None
    message: str = Field(..., min_length=1, max_length=2000)


class AILog(BaseModel):
    id: str
    livestream_id: str
    customer_message_id: str
    ai_message_id: str | None = None
    question_type: str | None = None
    retrieved_context: dict | None = None
    prompt: str | None = None
    raw_model_response: str | None = None
    final_reply: str | None = None
    confidence_score: float
    status: AIResponseStatus
    error_message: str | None = None
    created_at: str
