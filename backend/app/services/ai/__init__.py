"""AI services — glue between providers, scoring, and project lifecycle."""

from __future__ import annotations

import json
from typing import List, Optional

from app.providers.ai import get_ai_provider
from shared.types import DetectedClip
from ai_engine.scoring import detect_clips as heuristic_detect
from ai_engine.prompts import format_enrichment_prompt


async def detect_and_enrich(
    transcript,
    *,
    target_duration: float = 45.0,
    min_duration: float = 15.0,
    max_duration: float = 90.0,
    top_k: int = 10,
    min_score: float = 0.0,
) -> List[DetectedClip]:
    """Run heuristic detection then enrich the top picks with the LLM provider."""
    base = heuristic_detect(
        transcript,
        target_duration=target_duration,
        min_duration=min_duration,
        max_duration=max_duration,
        top_k=top_k,
        min_score=min_score,
    )
    if not base:
        return base

    provider = get_ai_provider()
    # Build input payload
    candidates_payload = [
        {
            "id": f"c{i}",
            "start": c.start,
            "end": c.end,
            "transcript": c.transcript[:500],
            "scores": c.scores.to_dict(),
        }
        for i, c in enumerate(base)
    ]
    system, user = format_enrichment_prompt(json.dumps(candidates_payload, ensure_ascii=False))

    try:
        from app.providers.ai.base import AIRequest

        resp = await provider.complete(
            AIRequest(
                system=system,
                user=user,
                temperature=0.7,
                max_tokens=2048,
                json_mode=True,
            )
        )
        data = _safe_json_loads(resp.text)
        if not data or not isinstance(data, dict):
            return base
        candidates = data.get("candidates") or []
        # Map back
        by_id = {c["id"]: c for c in candidates if isinstance(c, dict) and "id" in c}
        for i, det in enumerate(base):
            key = f"c{i}"
            if key in by_id:
                upd = by_id[key]
                if isinstance(upd.get("title"), str) and upd["title"].strip():
                    det.title = upd["title"].strip()[:120]
                if isinstance(upd.get("hook"), str) and upd["hook"].strip():
                    det.hook = upd["hook"].strip()[:200]
                if isinstance(upd.get("description"), str) and upd["description"].strip():
                    det.description = upd["description"].strip()[:500]
                if isinstance(upd.get("hashtags"), list):
                    det.hashtags = [str(h) for h in upd["hashtags"] if isinstance(h, (str,))]
                if isinstance(upd.get("reason"), str) and upd["reason"].strip():
                    det.reason = upd["reason"].strip()[:300]
        return base
    except Exception as exc:  # noqa: BLE001
        # Provider failed — return the heuristic candidates untouched.
        from app.core.logging import get_logger
        get_logger(__name__).warning("AI enrichment failed, using heuristic output: %s", exc)
        return base


def _safe_json_loads(text: str):
    if not text:
        return None
    text = text.strip()
    # Strip code fences if present
    if text.startswith("```"):
        text = text.strip("`")
        if "\n" in text:
            text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text[:-3]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find the first { ... } block
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                return None
        return None
