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
PriorityLabel = Literal["high", "medium", "low"]
RiskLabel = Literal["low", "medium", "high", "critical"]


class CommentRequest(BaseModel):
    comment: str = Field(..., min_length=1, max_length=1000)
    username: str | None = Field(default=None, max_length=100)
    livestream_id: str | None = Field(default=None, max_length=100)
    account_id: str | None = Field(default=None, max_length=100)
    platform: str | None = Field(default=None, max_length=50)


class CommentAnalysis(BaseModel):
    comment: str
    username: str | None = None
    livestream_id: str | None = None
    account_id: str | None = None
    platform: str | None = None
    sentiment: SentimentLabel
    intent: IntentLabel
    lead_score: int = Field(..., ge=0, le=100)
    priority: PriorityLabel
    reasons: list[str]
    suggested_action: str
    should_auto_message: bool
    auto_message: str | None = None
    auto_message_reason: str


class BatchCommentRequest(BaseModel):
    comments: list[CommentRequest] = Field(..., min_length=1, max_length=100)


class ViewerAccount(BaseModel):
    account_id: str = Field(..., min_length=1, max_length=100)
    platform: str = Field(..., min_length=1, max_length=50)
    current_viewers: int = Field(..., ge=0)
    max_capacity: int = Field(..., gt=0)
    avg_watch_time_seconds: int = Field(default=0, ge=0)
    engagement_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    manual_priority: float = Field(default=1.0, ge=0.5, le=2.0)
    lag_signal: float = Field(default=0.0, ge=0.0, le=1.0)


class ViewerBalancingRequest(BaseModel):
    accounts: list[ViewerAccount] = Field(..., min_length=2, max_length=50)
    incoming_viewers: int = Field(default=0, ge=0)
    protect_high_engagement_streams: bool = True


class ViewerAllocation(BaseModel):
    account_id: str
    current_viewers: int
    target_viewers: int
    projected_viewers: int
    viewer_delta: int
    lag_risk: RiskLabel
    weighted_capacity: int
    recommendation: str


class TransferSuggestion(BaseModel):
    from_account_id: str
    to_account_id: str
    viewers_to_shift: int = Field(..., ge=1)
    reason: str


class ViewerBalancingResponse(BaseModel):
    summary: str
    total_current_viewers: int
    total_incoming_viewers: int
    allocations: list[ViewerAllocation]
    transfer_plan: list[TransferSuggestion]
    recommended_entry_account_id: str


class SessionOptimizationRequest(BaseModel):
    comments: list[CommentRequest] = Field(default_factory=list, max_length=100)
    accounts: list[ViewerAccount] = Field(..., min_length=2, max_length=50)
    incoming_viewers: int = Field(default=0, ge=0)


class SessionOptimizationResponse(BaseModel):
    hot_leads: list[CommentAnalysis]
    comment_summary: dict[str, int]
    balancing: ViewerBalancingResponse


class HealthResponse(BaseModel):
    status: str
    service: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value != "ok":
            raise ValueError("status must be 'ok'")
        return value
