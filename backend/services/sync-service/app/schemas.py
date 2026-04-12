from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


SyncJobStatus = Literal["completed", "queued", "failed", "processing"]
CommentSyncStatus = Literal["synced", "analysis_failed"]


class HealthResponse(BaseModel):
    status: str
    service: str


class SyncJob(BaseModel):
    job_id: str
    source: str
    status: SyncJobStatus
    records_synced: int = Field(..., ge=0)
    scheduled_at: str


class SyncCommentRequest(BaseModel):
    comment: str = Field(..., min_length=1, max_length=1000)
    username: str | None = Field(default=None, max_length=100)
    livestream_id: str | None = Field(default=None, max_length=100)
    account_id: str | None = Field(default=None, max_length=100)
    platform: str = Field(..., min_length=1, max_length=50)
    source: str = Field(..., min_length=1, max_length=100)
    source_comment_id: str | None = Field(default=None, max_length=100)


class SyncBatchRequest(BaseModel):
    comments: list[SyncCommentRequest] = Field(..., min_length=1, max_length=100)


class SyncedComment(BaseModel):
    sync_record_id: str
    source: str
    source_comment_id: str
    platform: str
    account_id: str | None = None
    livestream_id: str | None = None
    username: str | None = None
    comment: str
    synced_at: str
    sync_status: CommentSyncStatus
    analysis: dict | None = None


class SyncExecutionResponse(BaseModel):
    job: SyncJob
    synced_count: int = Field(..., ge=0)
    failed_count: int = Field(..., ge=0)
    records: list[SyncedComment]


class SyncSummary(BaseModel):
    total_jobs: int = Field(..., ge=0)
    successful_jobs: int = Field(..., ge=0)
    failed_jobs: int = Field(..., ge=0)
    total_comments_synced: int = Field(..., ge=0)
    total_comments_failed: int = Field(..., ge=0)
    jobs: list[SyncJob]

