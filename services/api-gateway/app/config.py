from __future__ import annotations

import os


class Settings:
    ai_service_url: str = os.getenv("AI_SERVICE_URL", "http://localhost:8001")
    auth_service_url: str = os.getenv("AUTH_SERVICE_URL", "http://localhost:8002")
    account_service_url: str = os.getenv("ACCOUNT_SERVICE_URL", "http://localhost:8003")


settings = Settings()
