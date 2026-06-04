from fastapi import FastAPI

app = FastAPI(title="SmartLive User Service", version="1.0.0")


@app.get("/health")
def health():
    return {"status": "ok", "service": "user-service"}


@app.get("/ready")
def ready():
    return {"status": "ready", "service": "user-service", "schema": "user_db"}


@app.get("/users")
def users():
    return [
        {"id": "customer-01", "email": "customer@smartlive.test", "role": "CUSTOMER"},
        {"id": "seller-01", "email": "seller@smartlive.test", "role": "SELLER"},
        {"id": "admin-01", "email": "admin@smartlive.test", "role": "ADMIN"},
    ]
