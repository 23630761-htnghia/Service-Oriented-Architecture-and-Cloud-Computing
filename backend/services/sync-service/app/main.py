from __future__ import annotations

import os
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI, HTTPException

from app.schemas import (
    HealthResponse,
    SyncBatchRequest,
    SyncCommentRequest,
    SyncExecutionResponse,
    SyncJob,
    SyncedComment,
    SyncSummary,
)

app = FastAPI(
    title="Sync Service",
    version="0.2.0",
    description="Sync service for livestream comments with AI enrichment.",
)

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8001")

SYNC_JOBS: list[SyncJob] = [
    SyncJob(job_id="sync-001", source="tiktok-comments", status="completed", records_synced=245, scheduled_at="2026-04-08T20:00:00Z"),
    SyncJob(job_id="sync-002", source="facebook-comments", status="completed", records_synced=198, scheduled_at="2026-04-08T20:05:00Z"),
]
SYNC_RECORDS: list[SyncedComment] = []


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


async def analyze_comment(payload: SyncCommentRequest) -> dict:
    try:
        response = await app.state.client.post(
            f"{AI_SERVICE_URL}/analyze-comment",
            json={
                "comment": payload.comment,
                "username": payload.username,
                "livestream_id": payload.livestream_id,
                "account_id": payload.account_id,
                "platform": payload.platform,
            },
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Khong the goi ai-service: {exc}") from exc


def create_job(source: str, synced_count: int, failed_count: int, scheduled_at: str) -> SyncJob:
    job = SyncJob(
        job_id=f"sync-{len(SYNC_JOBS) + 1:03d}",
        source=source,
        status="failed" if synced_count == 0 and failed_count > 0 else "completed",
        records_synced=synced_count,
        scheduled_at=scheduled_at,
    )
    SYNC_JOBS.append(job)
    return job


async def sync_comments(payloads: list[SyncCommentRequest]) -> SyncExecutionResponse:
    synced_at = utc_now_iso()
    source = payloads[0].source if payloads else "manual-sync"
    records: list[SyncedComment] = []
    failed_count = 0

    for index, payload in enumerate(payloads, start=1):
        analysis = await analyze_comment(payload)
        record = SyncedComment(
            sync_record_id=f"record-{len(SYNC_RECORDS) + index:04d}",
            source=payload.source,
            source_comment_id=payload.source_comment_id or f"{payload.source}-{len(SYNC_RECORDS) + index:04d}",
            platform=payload.platform,
            account_id=payload.account_id,
            livestream_id=payload.livestream_id,
            username=payload.username,
            comment=payload.comment,
            synced_at=synced_at,
            sync_status="synced",
            analysis=analysis,
        )
        records.append(record)

    SYNC_RECORDS[0:0] = list(reversed(records))
    job = create_job(source=source, synced_count=len(records), failed_count=failed_count, scheduled_at=synced_at)
    return SyncExecutionResponse(job=job, synced_count=len(records), failed_count=failed_count, records=records)


@app.on_event("startup")
async def startup_event() -> None:
    app.state.client = httpx.AsyncClient(timeout=10.0)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await app.state.client.aclose()


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service="sync-service")


@app.get("/sync-jobs", response_model=list[SyncJob])
def list_sync_jobs() -> list[SyncJob]:
    return list(reversed(SYNC_JOBS))


@app.get("/sync-records", response_model=list[SyncedComment])
def list_sync_records() -> list[SyncedComment]:
    return SYNC_RECORDS


@app.get("/sync-summary", response_model=SyncSummary)
def sync_summary() -> SyncSummary:
    successful_jobs = sum(1 for job in SYNC_JOBS if job.status == "completed")
    failed_jobs = sum(1 for job in SYNC_JOBS if job.status == "failed")
    total_comments_synced = sum(job.records_synced for job in SYNC_JOBS)
    total_comments_failed = sum(1 for record in SYNC_RECORDS if record.sync_status == "analysis_failed")
    return SyncSummary(
        total_jobs=len(SYNC_JOBS),
        successful_jobs=successful_jobs,
        failed_jobs=failed_jobs,
        total_comments_synced=total_comments_synced,
        total_comments_failed=total_comments_failed,
        jobs=list(reversed(SYNC_JOBS)),
    )


@app.post("/sync-comments", response_model=SyncExecutionResponse)
async def sync_single_comment(payload: SyncCommentRequest) -> SyncExecutionResponse:
    return await sync_comments([payload])


@app.post("/sync-comments/batch", response_model=SyncExecutionResponse)
async def sync_comment_batch(payload: SyncBatchRequest) -> SyncExecutionResponse:
    return await sync_comments(payload.comments)
