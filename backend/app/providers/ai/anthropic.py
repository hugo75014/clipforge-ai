"""Anthropic Claude provider."""

from __future__ import annotations

import os
from typing import AsyncIterator

from app.providers.ai.base import AIProvider, AIRequest, AIResponse


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, api_key: str | None = None, default_model: str = "claude-3-5-sonnet-latest") -> None:
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is required for Anthropic provider")
        self.default_model = default_model
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from anthropic import AsyncAnthropic
            except ImportError as exc:  # pragma: no cover
                raise RuntimeError("anthropic package not installed. pip install anthropic") from exc
            self._client = AsyncAnthropic(api_key=self.api_key)
        return self._client

    async def complete(self, request: AIRequest) -> AIResponse:
        client = self._get_client()
        msg = await client.messages.create(
            model=request.model or self.default_model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            system=request.system,
            messages=[{"role": "user", "content": request.user}],
        )
        text = "".join(getattr(b, "text", "") for b in msg.content)
        usage = {
            "input_tokens": getattr(msg.usage, "input_tokens", None),
            "output_tokens": getattr(msg.usage, "output_tokens", None),
        }
        return AIResponse(
            text=text,
            model=msg.model,
            provider=self.name,
            usage=usage,
            cost_usd=_estimate_cost_anthropic(msg.model, usage["input_tokens"] or 0, usage["output_tokens"] or 0),
            raw=msg,
        )

    async def stream(self, request: AIRequest) -> AsyncIterator[str]:
        client = self._get_client()
        async with client.messages.stream(
            model=request.model or self.default_model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            system=request.system,
            messages=[{"role": "user", "content": request.user}],
        ) as stream:
            async for delta in stream.text_stream:
                yield delta


def _estimate_cost_anthropic(model: str, input_tokens: int, output_tokens: int) -> float:
    pricing = {
        "claude-3-5-sonnet-latest": (3.0 / 1e6, 15.0 / 1e6),
        "claude-3-5-haiku-latest": (0.8 / 1e6, 4.0 / 1e6),
        "claude-3-opus-latest": (15.0 / 1e6, 75.0 / 1e6),
    }
    in_p, out_p = pricing.get(model, (3.0 / 1e6, 15.0 / 1e6))
    return round(input_tokens * in_p + output_tokens * out_p, 6)
