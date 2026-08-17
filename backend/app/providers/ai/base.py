"""AI provider interface."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, AsyncIterator, Protocol


@dataclass
class AIRequest:
    system: str
    user: str
    temperature: float = 0.7
    max_tokens: int = 2048
    model: str | None = None
    json_mode: bool = False
    extra: dict[str, Any] | None = None


@dataclass
class AIResponse:
    text: str
    model: str
    provider: str
    usage: dict[str, Any] | None = None
    cost_usd: float | None = None
    raw: Any = None


class AIProvider(Protocol):
    name: str

    async def complete(self, request: AIRequest) -> AIResponse: ...

    async def stream(self, request: AIRequest) -> AsyncIterator[str]: ...
