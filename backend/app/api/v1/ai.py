"""AI routes — provider health, custom completions, etc."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core import settings
from app.core.security import get_current_user
from app.models import User
from app.providers.ai import get_ai_provider
from app.providers.ai.base import AIRequest


router = APIRouter()


class CompleteRequest(BaseModel):
    system: str = "You are a helpful assistant."
    user: str
    temperature: float = 0.7
    max_tokens: int = 1024
    json_mode: bool = False
    model: str | None = None


class CompleteResponse(BaseModel):
    text: str
    provider: str
    model: str
    usage: dict[str, Any] | None = None
    cost_usd: float | None = None
    demo: bool


@router.get("/info")
async def info(_: User = Depends(get_current_user)) -> dict:
    provider = get_ai_provider()
    return {
        "provider": provider.name,
        "model": settings.ai_model,
        "demo_mode": settings.demo_mode,
    }


@router.post("/complete", response_model=CompleteResponse)
async def complete(
    payload: CompleteRequest,
    _: User = Depends(get_current_user),
) -> CompleteResponse:
    provider = get_ai_provider()
    try:
        resp = await provider.complete(
            AIRequest(
                system=payload.system,
                user=payload.user,
                temperature=payload.temperature,
                max_tokens=payload.max_tokens,
                json_mode=payload.json_mode,
                model=payload.model,
            )
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI provider error: {exc}")
    return CompleteResponse(
        text=resp.text,
        provider=resp.provider,
        model=resp.model,
        usage=resp.usage,
        cost_usd=resp.cost_usd,
        demo=settings.demo_mode,
    )
