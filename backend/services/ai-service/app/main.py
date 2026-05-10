from __future__ import annotations

from fastapi import FastAPI

from app.chatbot import build_chatbot_reply
from app.schemas import ChatbotReplyRequest, ChatbotReplyResponse, HealthResponse


app = FastAPI(
    title="SmartLive AI Chatbot Service",
    version="1.0.0",
    description="Chatbot reply service for the SmartLive livestream demo.",
)


@app.get("/")
def root():
    return {
        "service": "ai-service",
        "status": "ok",
        "message": "SmartLive AI Chatbot Service is running.",
        "health_url": "/health",
        "main_routes": ["/chatbot/reply"],
    }


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service="ai-service")


@app.post("/chatbot/reply", response_model=ChatbotReplyResponse)
def create_chatbot_reply(payload: ChatbotReplyRequest) -> ChatbotReplyResponse:
    return build_chatbot_reply(payload)
