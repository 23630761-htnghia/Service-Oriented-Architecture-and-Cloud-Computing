from __future__ import annotations

import os
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

app = FastAPI(title="SmartLive Chat Service", version="1.0.0")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
rooms: dict[str, list[WebSocket]] = {}
messages: list[dict] = []
published_events: list[dict] = []


class ChatMessage(BaseModel):
    livestream_id: str
    user_id: str | None = None
    message: str
    sender_type: str = "CUSTOMER"


def publish_event(topic: str, payload: dict) -> dict:
    event = {"topic": topic, "payload": payload, "broker": KAFKA_BOOTSTRAP_SERVERS}
    published_events.append(event)
    return event


async def broadcast(livestream_id: str, event: str, payload: dict) -> None:
    for socket in list(rooms.get(livestream_id, [])):
        await socket.send_json({"event": event, "payload": payload})


@app.get("/health")
def health():
    return {"status": "ok", "service": "chat-service"}


@app.get("/ready")
def ready():
    return {"status": "ready", "service": "chat-service", "kafka": KAFKA_BOOTSTRAP_SERVERS}


@app.post("/chat/messages")
async def create_message(payload: ChatMessage):
    message = {
        "id": str(uuid4()),
        "livestream_id": payload.livestream_id,
        "user_id": payload.user_id,
        "message": payload.message,
        "sender_type": payload.sender_type,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    messages.append(message)
    topic = "customer.message.created" if payload.sender_type == "CUSTOMER" else "seller.manual.reply.created"
    publish_event(topic, message)
    await broadcast(payload.livestream_id, topic, message)
    return message


@app.post("/events/ai-reply-generated")
async def on_ai_reply_generated(payload: dict):
    publish_event("chat.ai_reply.persisted", payload)
    await broadcast(payload["livestream_id"], "ai_reply", payload)
    return {"delivered": True}


@app.websocket("/ws/livestreams/{livestream_id}")
async def websocket_endpoint(websocket: WebSocket, livestream_id: str):
    await websocket.accept()
    rooms.setdefault(livestream_id, []).append(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("event") == "customer_message":
                await create_message(ChatMessage(livestream_id=livestream_id, user_id=data.get("user_id"), message=data.get("message", "")))
    except WebSocketDisconnect:
        rooms[livestream_id].remove(websocket)
