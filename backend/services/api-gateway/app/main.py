from __future__ import annotations

import asyncio
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.schemas import GatewayHealthResponse


app = FastAPI(
    title="API Gateway",
    version="0.3.0",
    description="Gateway for livestream management platform.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


SERVICE_URLS = {
    "ai_service": lambda: settings.ai_service_url,
    "auth_service": lambda: settings.auth_service_url,
    "account_service": lambda: settings.account_service_url,
    "sync_service": lambda: settings.sync_service_url,
    "report_service": lambda: settings.report_service_url,
}


async def forward_request(method: str, base_url: str, path: str, payload: dict | None = None):
    request_kwargs = {"json": payload} if payload is not None else {}
    response = await app.state.client.request(method, f"{base_url}{path}", **request_kwargs)
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


async def forward_get(base_url: str, path: str):
    return await forward_request("GET", base_url, path)


async def forward_delete(base_url: str, path: str):
    return await forward_request("DELETE", base_url, path)


async def forward_post(base_url: str, path: str, payload: dict):
    return await forward_request("POST", base_url, path, payload)


async def forward_patch(base_url: str, path: str, payload: dict):
    return await forward_request("PATCH", base_url, path, payload)


async def check_dependency(service_name: str, base_url: str) -> tuple[str, dict]:
    try:
        response = await app.state.client.get(f"{base_url}/health")
        response.raise_for_status()
        return service_name, response.json()
    except httpx.HTTPError:
        return service_name, {"status": "unreachable"}


@app.on_event("startup")
async def startup_event():
    app.state.client = httpx.AsyncClient(timeout=10.0)


@app.on_event("shutdown")
async def shutdown_event():
    await app.state.client.aclose()


@app.get("/")
async def root():
    return {
        "service": "api-gateway",
        "status": "ok",
        "message": "API Gateway is running.",
        "docs_url": "/docs",
        "health_url": "/health",
        "main_routes": [
            "/api/v1/auth/captcha",
            "/api/v1/livestream-accounts",
            "/api/v1/comments/analyze",
            "/api/v1/sync/summary",
            "/api/v1/reports/kpis/overview",
        ],
    }


@app.get("/health", response_model=GatewayHealthResponse)
async def health_check():
    dependencies = {service_name: {"status": "unknown"} for service_name in SERVICE_URLS}
    checks = await asyncio.gather(
        *(check_dependency(service_name, get_base_url()) for service_name, get_base_url in SERVICE_URLS.items())
    )
    for service_name, health_payload in checks:
        dependencies[service_name] = health_payload

    return GatewayHealthResponse(
        status="ok",
        service="api-gateway",
        dependencies=dependencies,
    )


@app.post("/api/v1/comments/analyze")
async def analyze_comment(payload: dict):
    return await forward_post(settings.ai_service_url, "/analyze-comment", payload)


@app.post("/api/v1/comments/analyze-batch")
async def analyze_comments_batch(payload: dict):
    return await forward_post(settings.ai_service_url, "/analyze-comments/batch", payload)


@app.post("/api/v1/streams/balance-viewers")
async def balance_stream_viewers(payload: dict):
    return await forward_post(settings.ai_service_url, "/balance-viewers", payload)


@app.post("/api/v1/streams/session-optimizer")
async def optimize_livestream_session(payload: dict):
    return await forward_post(settings.ai_service_url, "/session-optimizer", payload)


@app.post("/api/v1/auth/login")
async def login(payload: dict):
    return await forward_post(settings.auth_service_url, "/login", payload)


@app.get("/api/v1/auth/captcha")
async def get_captcha():
    return await forward_get(settings.auth_service_url, "/captcha")


@app.get("/api/v1/auth/me")
async def me():
    return await forward_get(settings.auth_service_url, "/me")


@app.get("/api/v1/users")
async def list_users():
    return await forward_get(settings.account_service_url, "/users")


@app.post("/api/v1/users/staff")
async def create_staff_user(payload: dict):
    return await forward_post(settings.account_service_url, "/users/staff", payload)


@app.post("/api/v1/users/managed")
async def create_managed_user(payload: dict):
    return await forward_post(settings.account_service_url, "/users/managed", payload)


@app.patch("/api/v1/users/{user_id}/password")
async def update_user_password(user_id: str, payload: dict):
    return await forward_patch(settings.account_service_url, f"/users/{user_id}/password", payload)


@app.delete("/api/v1/users/{user_id}")
async def delete_user(user_id: str):
    return await forward_delete(settings.account_service_url, f"/users/{user_id}")


@app.get("/api/v1/livestream-accounts")
async def list_livestream_accounts():
    return await forward_get(settings.account_service_url, "/livestream-accounts")


@app.get("/api/v1/livestream-accounts/grouped")
async def list_grouped_livestream_accounts():
    return await forward_get(settings.account_service_url, "/livestream-accounts/grouped")


@app.delete("/api/v1/livestream-accounts/{account_id}")
async def delete_livestream_account(account_id: str):
    return await forward_delete(settings.account_service_url, f"/livestream-accounts/{account_id}")


@app.get("/api/v1/platform-summaries")
async def list_platform_summaries():
    return await forward_get(settings.account_service_url, "/platform-summaries")


@app.get("/api/v1/platforms/{platform}/accounts")
async def list_accounts_by_platform(platform: str):
    return await forward_get(settings.account_service_url, f"/platforms/{platform}/accounts")


@app.get("/api/v1/products")
async def list_products():
    return await forward_get(settings.account_service_url, "/products")


@app.get("/api/v1/livestream-product-assignments")
async def list_livestream_product_assignments():
    return await forward_get(settings.account_service_url, "/livestream-product-assignments")


@app.post("/api/v1/livestream-product-assignments")
async def create_livestream_product_assignment(payload: dict):
    return await forward_post(settings.account_service_url, "/livestream-product-assignments", payload)


@app.delete("/api/v1/livestream-product-assignments/{assignment_id}")
async def delete_livestream_product_assignment(assignment_id: str):
    return await forward_delete(settings.account_service_url, f"/livestream-product-assignments/{assignment_id}")


@app.post("/api/v1/products")
async def create_product(payload: dict):
    return await forward_post(settings.account_service_url, "/products", payload)


@app.patch("/api/v1/products/{product_id}")
async def update_product(product_id: str, payload: dict):
    return await forward_patch(settings.account_service_url, f"/products/{product_id}", payload)


@app.delete("/api/v1/products/{product_id}")
async def delete_product(product_id: str):
    return await forward_delete(settings.account_service_url, f"/products/{product_id}")


@app.get("/api/v1/suppliers")
async def list_suppliers():
    return await forward_get(settings.account_service_url, "/suppliers")


@app.post("/api/v1/suppliers")
async def create_supplier(payload: dict):
    return await forward_post(settings.account_service_url, "/suppliers", payload)


@app.patch("/api/v1/suppliers/{supplier_id}")
async def update_supplier(supplier_id: str, payload: dict):
    return await forward_patch(settings.account_service_url, f"/suppliers/{supplier_id}", payload)


@app.delete("/api/v1/suppliers/{supplier_id}")
async def delete_supplier(supplier_id: str):
    return await forward_delete(settings.account_service_url, f"/suppliers/{supplier_id}")


@app.get("/api/v1/supplier-offers")
async def list_supplier_offers():
    return await forward_get(settings.account_service_url, "/supplier-offers")


@app.get("/api/v1/database-overview")
async def get_database_overview():
    return await forward_get(settings.account_service_url, "/database-overview")


@app.post("/api/v1/livestream-accounts")
async def create_livestream_account(payload: dict):
    return await forward_post(settings.account_service_url, "/livestream-accounts", payload)


@app.get("/api/v1/sync/jobs")
async def list_sync_jobs():
    return await forward_get(settings.sync_service_url, "/sync-jobs")


@app.get("/api/v1/sync/summary")
async def get_sync_summary():
    return await forward_get(settings.sync_service_url, "/sync-summary")


@app.get("/api/v1/sync/records")
async def list_sync_records():
    return await forward_get(settings.sync_service_url, "/sync-records")


@app.get("/api/v1/sync/records/export")
async def export_sync_records():
    return await forward_get(settings.sync_service_url, "/sync-records/export")


@app.post("/api/v1/sync/comments")
async def sync_comment(payload: dict):
    return await forward_post(settings.sync_service_url, "/sync-comments", payload)


@app.post("/api/v1/sync/comments/batch")
async def sync_comments_batch(payload: dict):
    return await forward_post(settings.sync_service_url, "/sync-comments/batch", payload)


@app.get("/api/v1/reports/kpis/overview")
async def get_kpis_overview():
    return await forward_get(settings.report_service_url, "/kpis/overview")


@app.get("/api/v1/reports/operations")
async def get_operations_report():
    return await forward_get(settings.report_service_url, "/reports/operations")
