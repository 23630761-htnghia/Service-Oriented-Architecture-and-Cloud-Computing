from __future__ import annotations

import asyncio
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
    SyncRecordExport,
    SyncedComment,
    SyncSummary,
)

app = FastAPI(
    title="Sync Service",
    version="0.2.0",
    description="Sync service for livestream comments with AI enrichment.",
)

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8001")
SYNC_BATCH_CONCURRENCY = max(1, int(os.getenv("SYNC_BATCH_CONCURRENCY", "8")))

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


def build_sync_record(
    *,
    payload: SyncCommentRequest,
    sync_record_id: str,
    synced_at: str,
    analysis: dict | None,
    error_detail: str | None = None,
) -> SyncedComment:
    return SyncedComment(
        sync_record_id=sync_record_id,
        source=payload.source,
        source_comment_id=payload.source_comment_id or sync_record_id,
        platform=payload.platform,
        account_id=payload.account_id,
        livestream_id=payload.livestream_id,
        username=payload.username,
        comment=payload.comment,
        synced_at=synced_at,
        sync_status="synced" if analysis is not None else "analysis_failed",
        analysis=analysis,
        error_detail=error_detail,
    )


def build_export_record(record: SyncedComment) -> SyncRecordExport:
    analysis = record.analysis or {}
    event_date = record.synced_at.split("T", maxsplit=1)[0] if "T" in record.synced_at else record.synced_at
    return SyncRecordExport(
        sync_record_id=record.sync_record_id,
        source=record.source,
        source_comment_id=record.source_comment_id,
        platform=record.platform,
        account_id=record.account_id,
        livestream_id=record.livestream_id,
        username=record.username,
        comment=record.comment,
        synced_at=record.synced_at,
        event_date=event_date,
        sync_status=record.sync_status,
        intent=analysis.get("intent"),
        sentiment=analysis.get("sentiment"),
        lead_score=analysis.get("lead_score"),
        priority=analysis.get("priority"),
        error_detail=record.error_detail,
        analysis=record.analysis,
    )


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
    start_index = len(SYNC_RECORDS)
    semaphore = asyncio.Semaphore(min(SYNC_BATCH_CONCURRENCY, len(payloads) or 1))

    async def sync_one(index: int, payload: SyncCommentRequest) -> SyncedComment:
        sync_record_id = f"record-{start_index + index:04d}"
        try:
            async with semaphore:
                analysis = await analyze_comment(payload)
            return build_sync_record(
                payload=payload,
                sync_record_id=sync_record_id,
                synced_at=synced_at,
                analysis=analysis,
            )
        except HTTPException as exc:
            return build_sync_record(
                payload=payload,
                sync_record_id=sync_record_id,
                synced_at=synced_at,
                analysis=None,
                error_detail=str(exc.detail),
            )

    records = await asyncio.gather(
        *(sync_one(index, payload) for index, payload in enumerate(payloads, start=1))
    )
    failed_count = sum(1 for record in records if record.sync_status == "analysis_failed")
    synced_count = len(records) - failed_count

    SYNC_RECORDS[0:0] = list(reversed(records))
    job = create_job(source=source, synced_count=synced_count, failed_count=failed_count, scheduled_at=synced_at)
    return SyncExecutionResponse(job=job, synced_count=synced_count, failed_count=failed_count, records=records)


@app.on_event("startup")
async def startup_event() -> None:
    app.state.client = httpx.AsyncClient(timeout=10.0)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await app.state.client.aclose()


@app.get("/")
def root():
    return {
        "service": "sync-service",
        "status": "ok",
        "message": "Sync Service is running.",
        "docs_url": "/docs",
        "health_url": "/health",
        "main_routes": [
            "/sync-jobs",
            "/sync-records",
            "/sync-records/export",
            "/sync-summary",
            "/sync-comments",
        ],
    }


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service="sync-service")


@app.get("/sync-jobs", response_model=list[SyncJob])
def list_sync_jobs() -> list[SyncJob]:
    return list(reversed(SYNC_JOBS))


@app.get("/sync-records", response_model=list[SyncedComment])
def list_sync_records() -> list[SyncedComment]:
    return SYNC_RECORDS


@app.get("/sync-records/export", response_model=list[SyncRecordExport])
def export_sync_records() -> list[SyncRecordExport]:
    return [build_export_record(record) for record in reversed(SYNC_RECORDS)]


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
