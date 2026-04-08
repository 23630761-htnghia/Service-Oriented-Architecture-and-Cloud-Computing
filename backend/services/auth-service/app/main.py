from __future__ import annotations

from fastapi import FastAPI, HTTPException

from app.schemas import HealthResponse, LoginRequest, LoginResponse

app = FastAPI(
    title="Auth Service",
    version="0.2.0",
    description="Demo authentication service for livestream management platform.",
)

DEMO_USERS = {
    "admin@smartlive.vn": {
        "password": "123456",
        "id": "user-admin",
        "name": "Tran Minh Quan",
        "role": "admin",
        "department": "Trung tam van hanh livestream",
    },
    "staff@smartlive.vn": {
        "password": "123456",
        "id": "user-staff",
        "name": "Nguyen Bao Tram",
        "role": "staff",
        "department": "Kinh doanh livestream",
    },
}


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service="auth-service")


@app.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    user = DEMO_USERS.get(payload.email)
    if not user or user["password"] != payload.password:
        raise HTTPException(status_code=401, detail="Email hoac mat khau khong dung.")

    return LoginResponse(
        access_token=f"demo-token-{user['id']}",
        user={
            "id": user["id"],
            "name": user["name"],
            "email": payload.email,
            "role": user["role"],
            "department": user["department"],
        },
    )


@app.get("/me")
def me():
    return {
        "id": "user-admin",
        "name": "Tran Minh Quan",
        "email": "admin@smartlive.vn",
        "role": "admin",
        "department": "Trung tam van hanh livestream",
    }
