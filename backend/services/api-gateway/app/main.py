from __future__ import annotations

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.schemas import GatewayHealthResponse


app = FastAPI(
    title="SmartLive Chatbot API Gateway",
    version="1.0.0",
    description="Minimal gateway for the SmartLive livestream chatbot app.",
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


async def check_ai_service() -> dict:
    try:
        response = await app.state.client.get(f"{settings.ai_service_url}/health")
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError:
        return {"status": "unreachable", "service": "ai-service"}


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
        "message": "SmartLive Chatbot API Gateway is running.",
        "health_url": "/health",
        "main_routes": ["/api/v1/chatbot/reply"],
    }


@app.get("/health", response_model=GatewayHealthResponse)
async def health_check():
    return GatewayHealthResponse(
        status="ok",
        service="api-gateway",
        dependencies={"ai_service": await check_ai_service()},
    )


@app.post("/api/v1/chatbot/reply")
async def create_chatbot_reply(payload: dict):
    return await forward_post(settings.ai_service_url, "/chatbot/reply", payload)
