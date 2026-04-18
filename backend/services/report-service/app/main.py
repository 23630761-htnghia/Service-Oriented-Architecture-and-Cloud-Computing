from __future__ import annotations

import asyncio
import os
from collections import defaultdict
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI, HTTPException

from app.schemas import HealthResponse, KpiOverview, OperationsReport, PlatformSyncMetric

app = FastAPI(title="Report Service", version="0.2.0", description="Reporting service for livestream KPIs.")

ACCOUNT_SERVICE_URL = os.getenv("ACCOUNT_SERVICE_URL", "http://localhost:8003")
CATALOG_SERVICE_URL = os.getenv("CATALOG_SERVICE_URL", "http://localhost:8006")
LIVESTREAM_SERVICE_URL = os.getenv("LIVESTREAM_SERVICE_URL", "http://localhost:8007")
SYNC_SERVICE_URL = os.getenv("SYNC_SERVICE_URL", "http://localhost:8004")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


async def fetch_json(base_url: str, path: str) -> dict | list:
    try:
        response = await app.state.client.get(f"{base_url}{path}")
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Không thể gọi service phụ thuộc: {exc}") from exc


async def build_report_payload() -> tuple[KpiOverview, list[PlatformSyncMetric], list[dict]]:
    overview, sync_summary, sync_records = await asyncio.gather(
        build_database_overview(),
        fetch_json(SYNC_SERVICE_URL, "/sync-summary"),
        fetch_json(SYNC_SERVICE_URL, "/sync-records"),
    )

    platform_metrics_map: dict[str, dict] = defaultdict(
        lambda: {"total_comments": 0, "high_priority_comments": 0, "lead_scores": []}
    )
    for record in sync_records:
        platform = record.get("platform", "unknown")
        platform_metrics_map[platform]["total_comments"] += 1
        analysis = record.get("analysis") or {}
        lead_score = analysis.get("lead_score", 0)
        platform_metrics_map[platform]["lead_scores"].append(lead_score)
        if analysis.get("priority") == "high":
            platform_metrics_map[platform]["high_priority_comments"] += 1

    platform_metrics = [
        PlatformSyncMetric(
            platform=platform,
            total_comments=data["total_comments"],
            high_priority_comments=data["high_priority_comments"],
            average_lead_score=round(sum(data["lead_scores"]) / len(data["lead_scores"]), 2) if data["lead_scores"] else 0,
        )
        for platform, data in sorted(platform_metrics_map.items())
    ]

    platform_summaries = overview.get("platform_summaries", [])
    top_platform = ""
    if platform_summaries:
        top_platform = max(platform_summaries, key=lambda item: item.get("total_viewers", 0)).get("platform", "")

    high_priority_comments = sum(metric.high_priority_comments for metric in platform_metrics)
    kpi = KpiOverview(
        total_platforms=len(platform_summaries),
        total_accounts=len(overview.get("livestream_accounts", [])),
        total_products=len(overview.get("products", [])),
        total_suppliers=len(overview.get("suppliers", [])),
        active_offers=sum(1 for offer in overview.get("supplier_offers", []) if offer.get("status") == "active"),
        top_platform=top_platform,
        total_sync_jobs=sync_summary.get("total_jobs", 0),
        total_synced_comments=sync_summary.get("total_comments_synced", 0),
        high_priority_comments=high_priority_comments,
    )
    latest_jobs = sync_summary.get("jobs", [])[:5]
    return kpi, platform_metrics, latest_jobs


async def build_database_overview() -> dict:
    (
        users,
        customers,
        platform_summaries,
        livestream_accounts,
        live_offers,
        products,
        suppliers,
        supplier_offers,
        assignments,
    ) = await asyncio.gather(
        fetch_json(ACCOUNT_SERVICE_URL, "/users"),
        fetch_json(ACCOUNT_SERVICE_URL, "/customers"),
        fetch_json(LIVESTREAM_SERVICE_URL, "/platform-summaries"),
        fetch_json(LIVESTREAM_SERVICE_URL, "/livestream-accounts"),
        fetch_json(LIVESTREAM_SERVICE_URL, "/livestream-product-offers"),
        fetch_json(CATALOG_SERVICE_URL, "/products"),
        fetch_json(CATALOG_SERVICE_URL, "/suppliers"),
        fetch_json(CATALOG_SERVICE_URL, "/supplier-offers"),
        fetch_json(LIVESTREAM_SERVICE_URL, "/livestream-product-assignments"),
    )
    return {
        "users": users,
        "customers": customers,
        "platform_summaries": platform_summaries,
        "livestream_accounts": livestream_accounts,
        "livestream_product_offers": live_offers,
        "products": products,
        "suppliers": suppliers,
        "supplier_offers": supplier_offers,
        "livestream_product_assignments": assignments,
    }


@app.on_event("startup")
async def startup_event() -> None:
    app.state.client = httpx.AsyncClient(timeout=10.0)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await app.state.client.aclose()


@app.get("/")
def root():
    return {
        "service": "report-service",
        "status": "ok",
        "message": "Report Service is running.",
        "docs_url": "/docs",
        "health_url": "/health",
        "main_routes": [
            "/database-overview",
            "/kpis/overview",
            "/reports/operations",
        ],
    }


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service="report-service")


@app.get("/kpis/overview", response_model=KpiOverview)
async def kpi_overview() -> KpiOverview:
    kpi, _, _ = await build_report_payload()
    return kpi


@app.get("/database-overview")
async def database_overview() -> dict:
    return await build_database_overview()


@app.get("/reports/operations", response_model=OperationsReport)
async def operations_report() -> OperationsReport:
    kpi, platform_metrics, latest_jobs = await build_report_payload()
    return OperationsReport(
        generated_at=utc_now_iso(),
        sync=kpi,
        platform_metrics=platform_metrics,
        latest_jobs=latest_jobs,
    )
