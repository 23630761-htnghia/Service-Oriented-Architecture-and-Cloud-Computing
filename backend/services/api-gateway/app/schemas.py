from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class GatewayHealthResponse(BaseModel):
    status: str
    service: str
    dependencies: dict[str, Any]
