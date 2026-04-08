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
