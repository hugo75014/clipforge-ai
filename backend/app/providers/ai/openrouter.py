"""OpenRouter provider — unified access to many models via OpenAI-compatible API."""

from __future__ import annotations

import os
from typing import AsyncIterator

from app.providers.ai.openai import OpenAIProvider


class OpenRouterProvider(OpenAIProvider):
    name = "openrouter"

    def __init__(
        self,
        api_key: str | None = None,
        default_model: str = "anthropic/claude-3.5-sonnet",
    ) -> None:
        super().__init__(api_key=api_key or os.getenv("OPENROUTER_API_KEY"), default_model=default_model)
        # Override client with custom base_url
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(
            api_key=self.api_key,
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://clipforge.ai",
                "X-Title": "ClipForge AI",
            },
        )
