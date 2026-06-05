from __future__ import annotations

import os


class Settings:
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.1")
    ollama_timeout_seconds: float = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "12"))
    ai_temperature: float = float(os.getenv("AI_TEMPERATURE", os.getenv("OLLAMA_TEMPERATURE", "0.2")))
    ai_max_tokens: int = int(os.getenv("AI_MAX_TOKENS", os.getenv("OLLAMA_MAX_TOKENS", "220")))
    database_url: str | None = os.getenv("DATABASE_URL")


settings = Settings()
