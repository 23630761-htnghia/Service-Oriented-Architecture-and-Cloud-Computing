from __future__ import annotations

import os


class Settings:
    ai_service_url: str = os.getenv("AI_SERVICE_URL", "http://localhost:8001")
    auth_service_url: str = os.getenv("AUTH_SERVICE_URL", "http://localhost:8002")
    account_service_url: str = os.getenv("ACCOUNT_SERVICE_URL", "http://localhost:8003")
    catalog_service_url: str = os.getenv("CATALOG_SERVICE_URL", "http://localhost:8006")
    livestream_service_url: str = os.getenv("LIVESTREAM_SERVICE_URL", "http://localhost:8007")
    sync_service_url: str = os.getenv("SYNC_SERVICE_URL", "http://localhost:8004")
    report_service_url: str = os.getenv("REPORT_SERVICE_URL", "http://localhost:8005")


settings = Settings()
