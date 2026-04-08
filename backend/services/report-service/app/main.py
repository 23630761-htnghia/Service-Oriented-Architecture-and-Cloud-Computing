from __future__ import annotations

from fastapi import FastAPI

from app.schemas import HealthResponse, KpiOverview

app = FastAPI(title="Report Service", version="0.1.0", description="Mock reporting service for livestream KPIs.")


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service="report-service")


@app.get("/kpis/overview", response_model=KpiOverview)
def kpi_overview() -> KpiOverview:
    return KpiOverview(total_platforms=2, total_accounts=20, total_products=10, total_suppliers=5, active_offers=10, top_platform="tiktok")
