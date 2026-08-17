"""Prompts used by the AI provider to enrich heuristic clip candidates.

Each prompt asks the LLM to return a strict JSON shape so we can parse
deterministically. If the model misbehaves we fall back to the heuristic
title/hook/description.
"""

CLIP_ENRICHMENT_SYSTEM = (
    "You are a world-class short-form video editor. "
    "You turn long videos into viral 30-60 second clips. "
    "You always reply with strict JSON. No prose, no markdown."
)

CLIP_ENRICHMENT_USER_TEMPLATE = """You will receive a list of candidate clips detected by an upstream heuristic engine.
Each candidate has a transcript excerpt and per-axis scores (0-100).

For EACH candidate, improve:
  - title  (max 60 chars, punchy, clickbait-aware but not misleading)
  - hook   (the single best opening line for a TikTok caption)
  - description (1-2 sentences optimized for short-form platforms)
  - hashtags (5-8 hashtags, lower-case, no spaces, with the leading #)
  - reason (one sentence explaining why this is a strong candidate)

Reply with this exact JSON shape:
{{
  "candidates": [
    {{
      "id": "<the input id>",
      "title": "...",
      "hook": "...",
      "description": "...",
      "hashtags": ["#...", "..."],
      "reason": "..."
    }}
  ]
}}

Candidates (JSON):
{candidates_json}
"""


def format_enrichment_prompt(candidates_json: str) -> tuple[str, str]:
    return CLIP_ENRICHMENT_SYSTEM, CLIP_ENRICHMENT_USER_TEMPLATE.format(candidates_json=candidates_json)
