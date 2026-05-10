from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


SentimentLabel = Literal["positive", "neutral", "negative"]
IntentLabel = Literal[
    "ask_price",
    "buying_intent",
    "consult_request",
    "complaint",
    "spam",
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
    conversation_history: list[ChatHistoryMessage] = Field(default_factory=list, max_length=20)


class ChatbotReplyResponse(BaseModel):
    reply: str = Field(..., min_length=1, max_length=2000)
    intent: IntentLabel
    sentiment: SentimentLabel
    confidence: float = Field(..., ge=0.0, le=1.0)
    should_escalate: bool
    suggested_actions: list[str]
    used_product_id: str | None = None


class HealthResponse(BaseModel):
    status: str
    service: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value != "ok":
            raise ValueError("status must be 'ok'")
        return value
