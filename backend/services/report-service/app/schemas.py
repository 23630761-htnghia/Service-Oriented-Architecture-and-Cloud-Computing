from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str


class KpiOverview(BaseModel):
    total_platforms: int = Field(..., ge=0)
    total_accounts: int = Field(..., ge=0)
    total_products: int = Field(..., ge=0)
    total_suppliers: int = Field(..., ge=0)
    active_offers: int = Field(..., ge=0)
    top_platform: str
    total_sync_jobs: int = Field(..., ge=0)
    total_synced_comments: int = Field(..., ge=0)
    high_priority_comments: int = Field(..., ge=0)


class PlatformSyncMetric(BaseModel):
    platform: str
    total_comments: int = Field(..., ge=0)
    high_priority_comments: int = Field(..., ge=0)
    average_lead_score: float = Field(..., ge=0, le=100)


class OperationsReport(BaseModel):
    generated_at: str
    sync: KpiOverview
    platform_metrics: list[PlatformSyncMetric]
    latest_jobs: list[dict]

