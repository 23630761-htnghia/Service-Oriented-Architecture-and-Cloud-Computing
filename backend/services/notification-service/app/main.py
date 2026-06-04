from fastapi import FastAPI

app = FastAPI(title="SmartLive Notification Service", version="1.0.0")
notifications: list[dict] = []


@app.get("/health")
def health():
    return {"status": "ok", "service": "notification-service"}


@app.get("/ready")
def ready():
    return {"status": "ready", "service": "notification-service"}


@app.post("/events/ai-reply-failed")
def notify_seller(payload: dict):
    notification = {"type": "need_seller_support", "event": "ai.reply.failed", "payload": payload}
    notifications.append(notification)
    return notification


@app.get("/notifications")
def list_notifications():
    return notifications
