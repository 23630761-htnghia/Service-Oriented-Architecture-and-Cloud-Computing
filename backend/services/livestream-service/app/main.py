from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="SmartLive Livestream Service", version="1.0.0")
livestreams = {"live-01": {"id": "live-01", "shop_id": "shop-01", "title": "Flash sale tối nay", "status": "LIVE", "ai_enabled": True}}


class AIToggle(BaseModel):
    enabled: bool


@app.get("/health")
def health():
    return {"status": "ok", "service": "livestream-service"}


@app.get("/ready")
def ready():
    return {"status": "ready", "service": "livestream-service", "schema": "livestream_db"}


@app.get("/livestreams/{livestream_id}")
def get_livestream(livestream_id: str):
    return livestreams.get(livestream_id, {"id": livestream_id, "status": "DRAFT", "ai_enabled": False})


@app.post("/livestreams/{livestream_id}/start")
def start_livestream(livestream_id: str):
    livestream = livestreams.setdefault(livestream_id, {"id": livestream_id, "shop_id": "shop-01", "ai_enabled": True})
    livestream["status"] = "LIVE"
    return {"event": "livestream.started", "livestream": livestream}


@app.post("/livestreams/{livestream_id}/end")
def end_livestream(livestream_id: str):
    livestream = livestreams.setdefault(livestream_id, {"id": livestream_id, "shop_id": "shop-01", "ai_enabled": False})
    livestream["status"] = "ENDED"
    return {"event": "livestream.ended", "livestream": livestream}


@app.patch("/livestreams/{livestream_id}/ai-toggle")
def toggle_ai(livestream_id: str, payload: AIToggle):
    livestream = livestreams.setdefault(livestream_id, {"id": livestream_id, "shop_id": "shop-01", "status": "DRAFT"})
    livestream["ai_enabled"] = payload.enabled
    return livestream


@app.post("/livestreams/{livestream_id}/pin-product/{product_id}")
def pin_product(livestream_id: str, product_id: str):
    return {"event": "product_pinned", "livestream_id": livestream_id, "product_id": product_id}
