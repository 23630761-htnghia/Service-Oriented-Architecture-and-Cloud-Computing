from __future__ import annotations

import base64
import html
import json
import os
from datetime import datetime, timedelta, timezone
from random import choice, randint
from urllib.error import URLError
from urllib.request import urlopen
from uuid import uuid4

from fastapi import FastAPI, HTTPException

from app.schemas import CaptchaResponse, HealthResponse, LoginRequest, LoginResponse

app = FastAPI(
    title="Auth Service",
    version="0.2.0",
    description="Authentication service for livestream management platform.",
)

ACCOUNT_SERVICE_URL = os.getenv("ACCOUNT_SERVICE_URL", "http://localhost:8003")

DEMO_USERS = {
    "admin@smartlive.vn": {
        "password": "123456",
        "id": "user-admin",
        "name": "Hoàng Trọng Nghĩa",
        "role": "admin",
        "department": "Trung tam van hanh livestream",
    },
    "staff@smartlive.vn": {
        "password": "staff01",
        "id": "user-staff",
        "name": "Nguyen Bao Tram",
        "role": "staff",
        "department": "Kinh doanh livestream",
    },
    "staff02@smartlive.vn": {
        "password": "staff02",
        "id": "user-staff-02",
        "name": "Le Hoang My",
        "role": "staff",
        "department": "Van hanh san",
    },
    "staff03@smartlive.vn": {
        "password": "staff03",
        "id": "user-staff-03",
        "name": "Pham Thu Ha",
        "role": "staff",
        "department": "Chot don livestream",
    },
    "staff04@smartlive.vn": {
        "password": "staff04",
        "id": "user-staff-04",
        "name": "Vo Gia Han",
        "role": "staff",
        "department": "Cham soc khach hang",
    },
}

CAPTCHA_TTL_SECONDS = 30
CAPTCHA_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
captcha_store: dict[str, dict[str, datetime | str]] = {}


def prune_expired_captchas() -> None:
    now = datetime.now(timezone.utc)
    expired_ids = [
        captcha_id
        for captcha_id, captcha in captcha_store.items()
        if captcha["expires_at"] <= now
    ]
    for captcha_id in expired_ids:
        captcha_store.pop(captcha_id, None)


def create_captcha() -> CaptchaResponse:
    prune_expired_captchas()
    captcha_text = "".join(choice(CAPTCHA_ALPHABET) for _ in range(5))
    captcha_id = str(uuid4())
    captcha_store[captcha_id] = {
        "answer": captcha_text,
        "expires_at": datetime.now(timezone.utc) + timedelta(seconds=CAPTCHA_TTL_SECONDS),
    }
    svg_markup = build_captcha_svg(captcha_text)
    return CaptchaResponse(
        captcha_id=captcha_id,
        image_svg_base64=base64.b64encode(svg_markup.encode("utf-8")).decode("ascii"),
        expires_in_seconds=CAPTCHA_TTL_SECONDS,
    )


def load_users() -> dict[str, dict[str, str]]:
    try:
        with urlopen(f"{ACCOUNT_SERVICE_URL}/users", timeout=2) as response:
            records = json.loads(response.read().decode("utf-8"))
        users = {
            record["email"]: {
                "password": record["password"],
                "id": record["user_id"],
                "name": record["full_name"],
                "role": record["role"],
                "department": record["department"],
            }
            for record in records
        }
        if users:
            return users
    except (URLError, OSError, ValueError, KeyError, json.JSONDecodeError):
        pass
    return DEMO_USERS


def build_captcha_svg(captcha_text: str) -> str:
    width = 180
    height = 64
    noise_lines = []
    for _ in range(6):
        noise_lines.append(
            f'<line x1="{randint(0, width)}" y1="{randint(0, height)}" '
            f'x2="{randint(0, width)}" y2="{randint(0, height)}" '
            f'stroke="rgba(49,108,189,0.28)" stroke-width="{randint(1, 3)}" />'
        )

    noise_dots = []
    for _ in range(18):
        noise_dots.append(
            f'<circle cx="{randint(0, width)}" cy="{randint(0, height)}" r="{randint(1, 2)}" fill="rgba(24,50,74,0.20)" />'
        )

    glyphs = []
    x = 18
    for letter in captcha_text:
        y = randint(38, 50)
        rotation = randint(-18, 18)
        font_size = randint(28, 34)
        glyphs.append(
            f'<text x="{x}" y="{y}" font-size="{font_size}" '
            f'font-family="Verdana, Arial, sans-serif" font-weight="700" '
            f'fill="#163f78" transform="rotate({rotation} {x} {y})">{html.escape(letter)}</text>'
        )
        x += randint(28, 34)

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        '<defs>'
        '<linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">'
        '<stop offset="0%" stop-color="#fdfefe" />'
        '<stop offset="100%" stop-color="#dcecff" />'
        '</linearGradient>'
        "</defs>"
        f'<rect width="{width}" height="{height}" rx="14" fill="url(#bg)" />'
        f'{"".join(noise_lines)}'
        f'{"".join(noise_dots)}'
        f'{"".join(glyphs)}'
        "</svg>"
    )


@app.get("/")
def root():
    return {
        "service": "auth-service",
        "status": "ok",
        "message": "Auth Service is running.",
        "docs_url": "/docs",
        "health_url": "/health",
        "main_routes": [
            "/captcha",
            "/login",
            "/me",
        ],
    }


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service="auth-service")


@app.get("/captcha", response_model=CaptchaResponse)
def get_captcha() -> CaptchaResponse:
    return create_captcha()


@app.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    prune_expired_captchas()
    captcha = captcha_store.pop(payload.captcha_id, None)
    if not captcha:
        raise HTTPException(status_code=400, detail="Captcha khong hop le hoac da het han.")
    if str(payload.captcha_answer).strip().upper() != captcha["answer"]:
        raise HTTPException(status_code=400, detail="Captcha khong chinh xac.")

    user = load_users().get(payload.email)
    if not user or user["password"] != payload.password:
        raise HTTPException(status_code=401, detail="Email hoac mat khau khong dung.")

    return LoginResponse(
        access_token=f"access-token-{user['id']}",
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
    admin = load_users().get("admin@smartlive.vn", DEMO_USERS["admin@smartlive.vn"])
    return {
        "id": admin["id"],
        "name": admin["name"],
        "email": "admin@smartlive.vn",
        "role": admin["role"],
        "department": admin["department"],
    }
