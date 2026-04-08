from __future__ import annotations

from fastapi import FastAPI

from app.schemas import HealthResponse, SyncJob, SyncSummary

app = FastAPI(title="Sync Service", version="0.1.0", description="Mock sync service for livestream events and comments.")

SYNC_JOBS = [
    SyncJob(job_id="sync-001", source="tiktok-comments", status="completed", records_synced=245, scheduled_at="2026-04-08T20:00:00"),
    SyncJob(job_id="sync-002", source="facebook-comments", status="completed", records_synced=198, scheduled_at="2026-04-08T20:05:00"),
    SyncJob(job_id="sync-003", source="warehouse-stock", status="queued", records_synced=0, scheduled_at="2026-04-08T22:30:00"),
]


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service="sync-service")


@app.get("/sync-jobs", response_model=list[SyncJob])
def list_sync_jobs() -> list[SyncJob]:
    return SYNC_JOBS


@app.get("/sync-summary", response_model=SyncSummary)
def sync_summary() -> SyncSummary:
    successful_jobs = sum(1 for job in SYNC_JOBS if job.status == "completed")
    failed_jobs = sum(1 for job in SYNC_JOBS if job.status == "failed")
    return SyncSummary(total_jobs=len(SYNC_JOBS), successful_jobs=successful_jobs, failed_jobs=failed_jobs, jobs=SYNC_JOBS)
