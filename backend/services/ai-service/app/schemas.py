from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


SentimentLabel = Literal["positive", "neutral", "negative"]
IntentLabel = Literal[
    "ask_price",
    "ask_voucher",
    "ask_shipping",
    "ask_stock",
    "ask_policy",
    "buying_intent",
    "consult_request",
    "complaint",
    "spam",
    "out_of_scope",
    "other",
]


class ChatProductContext(BaseModel):
    product_id: str | None = Field(default=None, max_length=100)
    name: str = Field(..., min_length=1, max_length=300)
    category: str | None = Field(default=None, max_length=100)
    brand: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    retail_price: float | None = Field(default=None, ge=0)
    live_price: float | None = Field(default=None, ge=0)
    stock_quantity: int | None = Field(default=None, ge=0)
    variants: list[str] = Field(default_factory=list, max_length=30)
    image_url: str | None = Field(default=None, max_length=1000)
    purchase_url: str | None = Field(default=None, max_length=1000)


class ChatVoucherContext(BaseModel):
    voucher_id: str | None = Field(default=None, max_length=100)
    code: str = Field(..., min_length=1, max_length=100)
    discount_value: str = Field(..., min_length=1, max_length=200)
    conditions: str | None = Field(default=None, max_length=1000)
    valid_until: str | None = Field(default=None, max_length=100)
    applicable_product_ids: list[str] = Field(default_factory=list, max_length=100)
    remaining_quantity: int | None = Field(default=None, ge=0)


class SalesPolicyContext(BaseModel):
    shipping_fee_note: str | None = Field(default=None, max_length=1000)
    delivery_time_note: str | None = Field(default=None, max_length=1000)
    return_policy: str | None = Field(default=None, max_length=1000)
    sensitive_scope_note: str | None = Field(default=None, max_length=1000)


class AISettingsContext(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_name: str | None = Field(default=None, max_length=100)
    temperature: float | None = Field(default=None, ge=0, le=2)
    max_tokens: int | None = Field(default=None, ge=32, le=4096)
    reply_style: str | None = Field(default=None, max_length=300)


class ChatHistoryMessage(BaseModel):
    sender_role: str = Field(..., min_length=1, max_length=50)
    sender_name: str | None = Field(default=None, max_length=100)
    content: str = Field(..., min_length=1, max_length=2000)
    source: str | None = Field(default=None, max_length=50)
    created_at: str | None = Field(default=None, max_length=100)


class ChatbotReplyRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    customer_name: str | None = Field(default=None, max_length=100)
    account_name: str | None = Field(default=None, max_length=200)
    products: list[ChatProductContext] = Field(default_factory=list, max_length=20)
    vouchers: list[ChatVoucherContext] = Field(default_factory=list, max_length=20)
    policy: SalesPolicyContext | None = None
    ai_settings: AISettingsContext | None = None
    conversation_history: list[ChatHistoryMessage] = Field(default_factory=list, max_length=20)


class ChatbotReplyResponse(BaseModel):
    reply: str = Field(..., min_length=1, max_length=2000)
    intent: IntentLabel
    sentiment: SentimentLabel
    confidence: float = Field(..., ge=0.0, le=1.0)
    should_escalate: bool
    suggested_actions: list[str]
    used_product_id: str | None = None
    used_voucher_code: str | None = None
    retrieved_context: dict | None = None
    prompt: str | None = None
    raw_model_response: str | None = None
    error_message: str | None = None
    ai_status: str | None = None


class HealthResponse(BaseModel):
    status: str
    service: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value != "ok":
            raise ValueError("status must be 'ok'")
        return value
