from fastapi import FastAPI

app = FastAPI(title="SmartLive Product Service", version="1.0.0")

products = [
    {"product_id": "product-01", "shop_id": "shop-01", "name": "Serum Vitamin C LumiSkin", "price": 169000, "sale_price": 129000, "stock": 18},
    {"product_id": "product-02", "shop_id": "shop-01", "name": "Tai nghe Bluetooth TechGo MiniPods", "price": 259000, "sale_price": 219000, "stock": 12},
]


@app.get("/health")
def health():
    return {"status": "ok", "service": "product-service"}


@app.get("/ready")
def ready():
    return {"status": "ready", "service": "product-service", "schema": "product_db"}


@app.get("/livestreams/{livestream_id}/products")
def livestream_products(livestream_id: str):
    return {"livestream_id": livestream_id, "products": products}


@app.patch("/products/{product_id}/stock")
def update_stock(product_id: str, quantity: int):
    return {"event": "product.stock.updated", "product_id": product_id, "stock": quantity}
