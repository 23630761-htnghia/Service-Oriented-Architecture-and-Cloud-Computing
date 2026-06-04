from __future__ import annotations

import os


class Settings:
    ai_service_url: str = os.getenv("AI_SERVICE_URL", "http://localhost:8001")
    auth_service_url: str = os.getenv("AUTH_SERVICE_URL", "http://localhost:8010")
    user_service_url: str = os.getenv("USER_SERVICE_URL", "http://localhost:8011")
    shop_service_url: str = os.getenv("SHOP_SERVICE_URL", "http://localhost:8012")
    product_service_url: str = os.getenv("PRODUCT_SERVICE_URL", "http://localhost:8013")
    voucher_service_url: str = os.getenv("VOUCHER_SERVICE_URL", "http://localhost:8014")
    livestream_service_url: str = os.getenv("LIVESTREAM_SERVICE_URL", "http://localhost:8015")
    chat_service_url: str = os.getenv("CHAT_SERVICE_URL", "http://localhost:8016")
    order_service_url: str = os.getenv("ORDER_SERVICE_URL", "http://localhost:8017")
    notification_service_url: str = os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8018")
    analytics_service_url: str = os.getenv("ANALYTICS_SERVICE_URL", "http://localhost:8019")
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "120"))


settings = Settings()
