from __future__ import annotations

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.schemas import GatewayHealthResponse


app = FastAPI(
    title="API Gateway",
    version="0.2.0",
    description="Gateway for livestream management platform.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def forward_post(base_url: str, path: str, payload: dict):
    response = await app.state.client.post(f"{base_url}{path}", json=payload)
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


async def forward_get(base_url: str, path: str):
    response = await app.state.client.get(f"{base_url}{path}")
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@app.on_event("startup")
async def startup_event():
    app.state.client = httpx.AsyncClient(timeout=10.0)


@app.on_event("shutdown")
async def shutdown_event():
    await app.state.client.aclose()


@app.get("/health", response_model=GatewayHealthResponse)
async def health_check():
    dependencies = {
        "ai_service": {"status": "unknown"},
        "auth_service": {"status": "unknown"},
        "account_service": {"status": "unknown"},
    }
    service_map = {
        "ai_service": settings.ai_service_url,
        "auth_service": settings.auth_service_url,
        "account_service": settings.account_service_url,
    }
    for service_name, base_url in service_map.items():
        try:
            response = await app.state.client.get(f"{base_url}/health")
            dependencies[service_name] = response.json()
        except httpx.HTTPError:
            dependencies[service_name] = {"status": "unreachable"}

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


@app.get("/api/v1/auth/me")
async def me():
    return await forward_get(settings.auth_service_url, "/me")


@app.get("/api/v1/livestream-accounts")
async def list_livestream_accounts():
    return await forward_get(settings.account_service_url, "/livestream-accounts")


@app.get("/api/v1/livestream-accounts/grouped")
async def list_grouped_livestream_accounts():
    return await forward_get(settings.account_service_url, "/livestream-accounts/grouped")


@app.get("/api/v1/platform-summaries")
async def list_platform_summaries():
    return await forward_get(settings.account_service_url, "/platform-summaries")


@app.get("/api/v1/platforms/{platform}/accounts")
async def list_accounts_by_platform(platform: str):
    return await forward_get(settings.account_service_url, f"/platforms/{platform}/accounts")


@app.post("/api/v1/livestream-accounts")
async def create_livestream_account(payload: dict):
    return await forward_post(settings.account_service_url, "/livestream-accounts", payload)
