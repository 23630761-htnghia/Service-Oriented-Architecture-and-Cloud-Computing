from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str


class SyncJob(BaseModel):
    job_id: str
    source: str
    status: str
    records_synced: int = Field(..., ge=0)
    scheduled_at: str


class SyncSummary(BaseModel):
    total_jobs: int = Field(..., ge=0)
    successful_jobs: int = Field(..., ge=0)
    failed_jobs: int = Field(..., ge=0)
    jobs: list[SyncJob]
