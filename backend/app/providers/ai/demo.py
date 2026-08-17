"""Demo AI provider — deterministic, offline, no API keys required.

Returns realistic-looking JSON structures so the rest of the pipeline can be
exercised end-to-end. Output is shaped to match the real providers (so the
caller doesn't need to know whether it's demo or production).
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
from typing import AsyncIterator

from app.providers.ai.base import AIProvider, AIRequest, AIResponse


def _stable_hash(*parts: str) -> int:
    h = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return int(h[:8], 16)


def _seeded_jitter(*parts: str, low: float, high: float) -> float:
    h = _stable_hash(*parts)
    span = high - low
    return low + (h % 10000) / 10000.0 * span


def _looks_like_json_request(req: AIRequest) -> bool:
    """Cheap heuristic to choose the demo response shape."""
    if req.json_mode:
        return True
    user = req.user.lower()
    return any(
        k in user
        for k in (
            "json",
            "return",
            "list",
            "array",
            "score",
            "candidate",
            "clip",
            "moment",
            "object with",
        )
    )


def _mock_clip_suggestions(req: AIRequest) -> list[dict]:
    """Return 4-7 candidate clips derived from the input length, so the
    UI shows a realistic selection."""
    # Try to infer a duration from the prompt
    m = re.search(r"duration[:\s]+(\d+(?:\.\d+)?)\s*(s|sec|seconds|minutes|m)?", req.user, re.I)
    if m:
        val = float(m.group(1))
        if (m.group(2) or "").lower().startswith("m"):
            val *= 60
        duration = max(60.0, min(val, 7200.0))
    else:
        duration = 600.0

    rng_seed = _stable_hash(req.user) ^ _stable_hash(req.system)

    n = 4 + (rng_seed % 4)  # 4-7 clips
    candidates: list[dict] = []
    span = duration / n
    themes = [
        ("The opening hook", "Stop scrolling — here's the part everyone missed.", "contradiction"),
        ("The surprising stat", "Numbers don't lie, and this one breaks the rule.", "revelation"),
        ("The emotional beat", "When you realise what they actually meant…", "emotion"),
        ("The counter-intuitive tip", "Everyone gets this wrong. Here's the shortcut.", "advice"),
        ("The mic-drop moment", "If you've ever wondered why, this is it.", "curiosity"),
        ("The story arc", "From zero to the most unexpected ending.", "story"),
        ("The hidden lesson", "The advice nobody tells you, until now.", "advice"),
    ]
    for i in range(n):
        start = round(span * i + 1.0, 1)
        end = round(min(duration, start + 25 + (rng_seed >> (i * 2)) % 35), 1)
        title, hook, _reason = themes[i % len(themes)]
        candidates.append(
            {
                "start": start,
                "end": end,
                "title": f"{title} #{i + 1}",
                "hook": hook,
                "description": (
                    "High-signal moment detected by the AI clip finder. "
                    "Edit the window, tweak the hook, or regenerate variations."
                ),
                "hashtags": ["#shorts", "#viral", "#clipforge", f"#topic{i + 1}"],
                "keywords": ["surprise", "moment", "viral"],
                "reason": "Strong emotional contrast and clear hook in opening sentence.",
                "scores": {
                    "hook": round(_seeded_jitter(str(i), "hook", low=70, high=98), 1),
                    "emotion": round(_seeded_jitter(str(i), "emo", low=60, high=95), 1),
                    "information": round(_seeded_jitter(str(i), "info", low=50, high=92), 1),
                    "story": round(_seeded_jitter(str(i), "story", low=55, high=95), 1),
                    "curiosity": round(_seeded_jitter(str(i), "cur", low=65, high=97), 1),
                    "shareability": round(_seeded_jitter(str(i), "share", low=60, high=96), 1),
                    "completion": round(_seeded_jitter(str(i), "comp", low=60, high=95), 1),
                },
            }
        )
    return candidates


class DemoAIProvider:
    name = "demo"

    async def complete(self, request: AIRequest) -> AIResponse:
        # Simulate a small delay so the UI's progress feels real.
        await asyncio.sleep(0.05)
        if _looks_like_json_request(request):
            payload = _mock_clip_suggestions(request)
            text = json.dumps(payload, ensure_ascii=False)
        else:
            text = (
                "Demo AI response. Configure an AI provider in your .env "
                "(OPENAI_API_KEY, ANTHROPIC_API_KEY, …) and set AI_PROVIDER to "
                "switch from demo to a real model."
            )
        return AIResponse(
            text=text,
            model=request.model or "demo-mock-1",
            provider=self.name,
            usage={"prompt_tokens": len(request.user.split()), "completion_tokens": len(text.split())},
            cost_usd=0.0,
        )

    async def stream(self, request: AIRequest) -> AsyncIterator[str]:
        full = await self.complete(request)
        for word in full.text.split(" "):
            yield word + " "
            await asyncio.sleep(0.005)
