from fastapi import FastAPI

app = FastAPI(title="SmartLive Analytics Service", version="1.0.0")


@app.get("/health")
def health():
    return {"status": "ok", "service": "analytics-service"}


@app.get("/ready")
def ready():
    return {"status": "ready", "service": "analytics-service"}


@app.get("/analytics/livestreams/{livestream_id}")
def livestream_analytics(livestream_id: str):
    return {
        "livestream_id": livestream_id,
        "question_count": 0,
        "ai_answered_count": 0,
        "order_count": 0,
        "revenue": 0,
    }
