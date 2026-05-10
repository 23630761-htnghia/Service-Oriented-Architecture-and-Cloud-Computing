from __future__ import annotations

import os


class Settings:
    ai_service_url: str = os.getenv("AI_SERVICE_URL", "http://localhost:8001")


settings = Settings()
