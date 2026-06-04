from fastapi import FastAPI

app = FastAPI(title="SmartLive Voucher Service", version="1.0.0")


@app.get("/health")
def health():
    return {"status": "ok", "service": "voucher-service"}


@app.get("/ready")
def ready():
    return {"status": "ready", "service": "voucher-service", "schema": "voucher_db"}


@app.get("/shops/{shop_id}/vouchers")
def vouchers(shop_id: str):
    return [{"voucher_id": "voucher-01", "shop_id": shop_id, "code": "LIVE20", "discount_value": "giảm 20.000đ", "status": "ACTIVE"}]


@app.post("/vouchers/{code}/validate")
def validate_voucher(code: str):
    return {"code": code, "valid": code.upper() == "LIVE20"}
