"""Local LLM provider via Ollama-compatible HTTP API.

Assumes a local server at `LOCAL_LLM_URL` (default http://localhost:11434).
If unreachable, raises a clear error.
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import AsyncIterator

from app.providers.ai.base import AIProvider, AIRequest, AIResponse


class LocalProvider:
    name = "local"

    def __init__(self, base_url: str | None = None, default_model: str = "llama3.1") -> None:
        self.base_url = (base_url or os.getenv("LOCAL_LLM_URL") or "http://localhost:11434").rstrip("/")
        self.default_model = os.getenv("LOCAL_LLM_MODEL", default_model)

    async def complete(self, request: AIRequest) -> AIResponse:
        import httpx

        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": request.model or self.default_model,
                    "stream": False,
                    "messages": [
                        {"role": "system", "content": request.system},
                        {"role": "user", "content": request.user},
                    ],
                    "options": {
                        "temperature": request.temperature,
                        "num_predict": request.max_tokens,
                    },
                },
            )
            r.raise_for_status()
            data = r.json()
            text = data.get("message", {}).get("content", "")
            return AIResponse(
                text=text,
                model=data.get("model", self.default_model),
                provider=self.name,
                usage={
                    "prompt_tokens": data.get("prompt_eval_count"),
                    "completion_tokens": data.get("eval_count"),
                },
                cost_usd=0.0,
                raw=data,
            )

    async def stream(self, request: AIRequest) -> AsyncIterator[str]:
        import httpx

        async with httpx.AsyncClient(timeout=300) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json={
                    "model": request.model or self.default_model,
                    "stream": True,
                    "messages": [
                        {"role": "system", "content": request.system},
                        {"role": "user", "content": request.user},
                    ],
                    "options": {
                        "temperature": request.temperature,
                        "num_predict": request.max_tokens,
                    },
                },
            ) as r:
                async for line in r.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        d = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    msg = d.get("message", {}).get("content")
                    if msg:
                        yield msg
