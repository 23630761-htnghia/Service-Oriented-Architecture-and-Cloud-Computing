from __future__ import annotations

import httpx

from app.config import settings


class OllamaError(RuntimeError):
    pass


def generateReplyWithOllama(
    prompt: str,
    model_name: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> tuple[str, str]:
    payload = {
        "model": model_name or settings.ollama_model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": settings.ai_temperature if temperature is None else temperature,
            "num_predict": settings.ai_max_tokens if max_tokens is None else max_tokens,
        },
    }
    try:
        response = httpx.post(
            f"{settings.ollama_base_url.rstrip('/')}/api/generate",
            json=payload,
            timeout=settings.ollama_timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise OllamaError(str(exc)) from exc

    raw_response = str(data.get("response") or "").strip()
    if not raw_response:
        raise OllamaError("Ollama returned an empty response")
    return raw_response, raw_response
