from uuid import uuid4

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="SmartLive Order Service", version="1.0.0")
orders: list[dict] = []


class OrderRequest(BaseModel):
    customer_id: str
    shop_id: str
    items: list[dict]


@app.get("/health")
def health():
    return {"status": "ok", "service": "order-service"}


@app.get("/ready")
def ready():
    return {"status": "ready", "service": "order-service", "schema": "order_db"}


@app.post("/orders")
def create_order(payload: OrderRequest):
    total = sum(float(item.get("price", 0)) * int(item.get("quantity", 1)) for item in payload.items)
    order = {"id": f"order-{uuid4().hex[:8]}", **payload.model_dump(), "total_amount": total, "status": "PENDING", "event": "order.created"}
    orders.append(order)
    return order


@app.get("/orders")
def list_orders():
    return orders
