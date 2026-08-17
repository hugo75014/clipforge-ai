"""OpenAI provider."""

from __future__ import annotations

import asyncio
import os
from typing import AsyncIterator

from app.providers.ai.base import AIProvider, AIRequest, AIResponse


class OpenAIProvider:
    name = "openai"

    def __init__(self, api_key: str | None = None, default_model: str = "gpt-4o-mini") -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is required for OpenAI provider")
        self.default_model = default_model
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from openai import AsyncOpenAI
            except ImportError as exc:  # pragma: no cover
                raise RuntimeError("openai package not installed. pip install openai") from exc
            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client

    async def complete(self, request: AIRequest) -> AIResponse:
        client = self._get_client()
        kwargs = {
            "model": request.model or self.default_model,
            "messages": [
                {"role": "system", "content": request.system},
                {"role": "user", "content": request.user},
            ],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }
        if request.json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        resp = await client.chat.completions.create(**kwargs)
        text = resp.choices[0].message.content or ""
        usage = {
            "prompt_tokens": getattr(resp.usage, "prompt_tokens", None) if resp.usage else None,
            "completion_tokens": getattr(resp.usage, "completion_tokens", None) if resp.usage else None,
            "total_tokens": getattr(resp.usage, "total_tokens", None) if resp.usage else None,
        }
        return AIResponse(
            text=text,
            model=resp.model,
            provider=self.name,
            usage=usage,
            cost_usd=_estimate_cost_openai(resp.model, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)),
            raw=resp,
        )

    async def stream(self, request: AIRequest) -> AsyncIterator[str]:
        client = self._get_client()
        kwargs = {
            "model": request.model or self.default_model,
            "messages": [
                {"role": "system", "content": request.system},
                {"role": "user", "content": request.user},
            ],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": True,
        }
        if request.json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        stream = await client.chat.completions.create(**kwargs)
        async for chunk in stream:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                yield delta


def _estimate_cost_openai(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Very rough cost estimate. Update prices from openai.com/pricing."""
    pricing = {
        "gpt-4o-mini": (0.15 / 1e6, 0.60 / 1e6),
        "gpt-4o": (2.50 / 1e6, 10.00 / 1e6),
        "gpt-4-turbo": (10.00 / 1e6, 30.00 / 1e6),
        "gpt-3.5-turbo": (0.50 / 1e6, 1.50 / 1e6),
    }
    in_p, out_p = pricing.get(model, (0.5 / 1e6, 1.5 / 1e6))
    return round(prompt_tokens * in_p + completion_tokens * out_p, 6)
