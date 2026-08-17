"""Google Gemini provider."""

from __future__ import annotations

import os
from typing import AsyncIterator

from app.providers.ai.base import AIProvider, AIRequest, AIResponse


class GeminiProvider:
    name = "gemini"

    def __init__(self, api_key: str | None = None, default_model: str = "gemini-1.5-flash") -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is required for Gemini provider")
        self.default_model = default_model
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import google.generativeai as genai  # type: ignore
            except ImportError as exc:  # pragma: no cover
                raise RuntimeError(
                    "google-generativeai package not installed. pip install google-generativeai"
                ) from exc
            genai.configure(api_key=self.api_key)
            self._client = genai.GenerativeModel(self.default_model)
        return self._client

    async def complete(self, request: AIRequest) -> AIResponse:
        # google.generativeai is sync; we offload to a thread.
        import asyncio

        model = self._get_client()
        prompt = f"{request.system}\n\n{request.user}"
        resp = await asyncio.to_thread(
            model.generate_content,
            prompt,
            {"temperature": request.temperature, "max_output_tokens": request.max_tokens},
        )
        text = resp.text or ""
        return AIResponse(
            text=text,
            model=self.default_model,
            provider=self.name,
            usage={
                "prompt_tokens": getattr(resp.usage_metadata, "prompt_token_count", None) if resp.usage_metadata else None,
                "completion_tokens": getattr(resp.usage_metadata, "candidates_token_count", None) if resp.usage_metadata else None,
            },
            cost_usd=None,
            raw=resp,
        )

    async def stream(self, request: AIRequest) -> AsyncIterator[str]:
        import asyncio

        model = self._get_client()
        resp = await asyncio.to_thread(
            model.generate_content,
            f"{request.system}\n\n{request.user}",
            {"temperature": request.temperature},
            stream=True,
        )
        for chunk in resp:
            if chunk.text:
                yield chunk.text
                await asyncio.sleep(0)
