from __future__ import annotations

import os
import time
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel


SERVICE_NAME = "auth-service"
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")

app = FastAPI(title="SmartLive Auth Service", version="1.0.0")
users = {
    "customer@smartlive.test": {"id": "customer-01", "password": "123456", "role": "CUSTOMER"},
    "seller@smartlive.test": {"id": "seller-01", "password": "123456", "role": "SELLER"},
    "admin@smartlive.test": {"id": "admin-01", "password": "123456", "role": "ADMIN"},
}
sessions: dict[str, dict] = {}


class LoginRequest(BaseModel):
    email: str
    password: str


@app.get("/health")
def health():
    return {"status": "ok", "service": SERVICE_NAME}


@app.get("/ready")
def ready():
    return {"status": "ready", "service": SERVICE_NAME, "jwt_configured": bool(JWT_SECRET)}


@app.post("/auth/login")
def login(payload: LoginRequest):
    user = users.get(payload.email.lower())
    if not user or user["password"] != payload.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = f"jwt-demo-{uuid4().hex}"
    sessions[token] = {"sub": user["id"], "email": payload.email.lower(), "role": user["role"], "iat": int(time.time())}
    return {"access_token": token, "token_type": "bearer", "user": sessions[token]}


@app.get("/auth/verify")
def verify(authorization: str | None = Header(default=None)):
    token = (authorization or "").replace("Bearer ", "")
    claims = sessions.get(token)
    if not claims:
        raise HTTPException(status_code=401, detail="Invalid token")
    return claims
