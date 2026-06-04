from __future__ import annotations

from fastapi import FastAPI

from app.chatbot import PROMPT_TEMPLATE, build_chatbot_reply
from app.schemas import ChatbotReplyRequest, ChatbotReplyResponse, HealthResponse


app = FastAPI(
    title="SmartLive AI Assistant Service",
    version="1.0.0",
    description="Independent AI Assistant Service for livestream auto-reply with Ollama/LLM support.",
)


@app.get("/")
def root():
    return {
        "service": "ai-assistant-service",
        "status": "ok",
        "message": "SmartLive AI Assistant Service is running.",
        "health_url": "/health",
        "main_routes": ["/chatbot/reply", "/events/customer-message-created", "/chatbot/prompt-template"],
    }


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service="ai-assistant-service")


@app.get("/ready", response_model=HealthResponse)
def readiness_check() -> HealthResponse:
    return HealthResponse(status="ok", service="ai-assistant-service")


@app.post("/chatbot/reply", response_model=ChatbotReplyResponse)
def create_chatbot_reply(payload: ChatbotReplyRequest) -> ChatbotReplyResponse:
    return build_chatbot_reply(payload)


@app.post("/events/customer-message-created")
def handle_customer_message_created(payload: ChatbotReplyRequest):
    response = build_chatbot_reply(payload)
    event_name = "ai.reply.failed" if response.should_escalate else "ai.reply.generated"
    return {"event": event_name, "payload": response.model_dump()}


@app.get("/chatbot/prompt-template")
def get_prompt_template():
    return {"prompt_template": PROMPT_TEMPLATE}
