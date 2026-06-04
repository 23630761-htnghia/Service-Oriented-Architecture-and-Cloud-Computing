from fastapi import FastAPI

app = FastAPI(title="SmartLive Shop Service", version="1.0.0")


@app.get("/health")
def health():
    return {"status": "ok", "service": "shop-service"}


@app.get("/ready")
def ready():
    return {"status": "ready", "service": "shop-service", "schema": "shop_db"}


@app.get("/shops/{shop_id}")
def shop(shop_id: str):
    return {"id": shop_id, "seller_id": "seller-01", "name": "SmartLive Beauty & Home"}
