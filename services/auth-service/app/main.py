from __future__ import annotations

from fastapi import FastAPI, HTTPException

from app.schemas import HealthResponse, LoginRequest, LoginResponse

app = FastAPI(
    title="Auth Service",
    version="0.1.0",
    description="Demo authentication service for livestream management platform.",
)

DEMO_USERS = {
    "admin@smartlive.vn": {
        "password": "123456",
        "id": "user-admin",
        "name": "Admin Demo",
        "role": "admin",
    },
    "staff@smartlive.vn": {
        "password": "123456",
        "id": "user-staff",
        "name": "Sales Staff Demo",
        "role": "staff",
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
        },
    )


@app.get("/me")
def me():
    return {
        "id": "user-admin",
        "name": "Admin Demo",
        "email": "admin@smartlive.vn",
        "role": "admin",
    }
