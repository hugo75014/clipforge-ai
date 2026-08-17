"""Health-check endpoints — used by load balancer, monitoring, and the
admin dashboard's "System Health" page."""

from __future__ import annotations

import asyncio
import shutil
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import settings
from app.db.session import get_db
from app.providers.ai import get_ai_provider
from app.providers.transcription import get_transcription_provider
from app.services.storage import get_storage

router = APIRouter()


async def _check_db(db: AsyncSession) -> dict[str, Any]:
    try:
        t0 = asyncio.get_event_loop().time()
        await db.execute(text("SELECT 1"))
        return {"status": "up", "latency_ms": int((asyncio.get_event_loop().time() - t0) * 1000)}
    except Exception as exc:  # noqa: BLE001
        return {"status": "down", "error": str(exc)[:200]}


async def _check_storage() -> dict[str, Any]:
    try:
        s = get_storage()
        ok = await s.exists("__healthcheck__") or True  # don't fail if missing
        return {"status": "up" if ok else "down", "backend": s.backend}
    except Exception as exc:  # noqa: BLE001
        return {"status": "down", "error": str(exc)[:200]}


def _check_ffmpeg() -> dict[str, Any]:
    try:
        from video_engine.ffmpeg.runner import find_ffmpeg, find_ffprobe

        return {
            "status": "up",
            "ffmpeg": find_ffmpeg(),
            "ffprobe": find_ffprobe(),
        }
    except Exception as exc:  # noqa: BLE001
        return {"status": "down", "error": str(exc)[:200]}


def _check_redis() -> dict[str, Any]:
    # Best-effort, non-blocking
    try:
        import redis  # type: ignore

        r = redis.Redis.from_url(settings.redis_url, socket_connect_timeout=1.5)
        r.ping()
        return {"status": "up"}
    except Exception as exc:  # noqa: BLE001
        return {"status": "down", "error": str(exc)[:200]}


def _check_ai() -> dict[str, Any]:
    try:
        p = get_ai_provider()
        return {"status": "up", "provider": p.name, "demo": settings.demo_mode}
    except Exception as exc:  # noqa: BLE001
        return {"status": "down", "error": str(exc)[:200]}


def _check_transcription() -> dict[str, Any]:
    try:
        p = get_transcription_provider()
        return {"status": "up", "provider": p.name}
    except Exception as exc:  # noqa: BLE001
        return {"status": "down", "error": str(exc)[:200]}


@router.get("/health")
async def health() -> dict:
    return {"status": "ok", "version": settings.app_version}


@router.get("/health/deep")
async def deep_health(db: AsyncSession = Depends(get_db)) -> dict:
    """Detailed health: DB, storage, FFmpeg, Redis, AI, transcription."""
    db_h, storage_h = await asyncio.gather(_check_db(db), _check_storage())
    return {
        "status": "ok" if all(x.get("status") == "up" for x in (db_h, storage_h)) else "degraded",
        "version": settings.app_version,
        "env": settings.app_env,
        "components": {
            "database": db_h,
            "storage": storage_h,
            "ffmpeg": _check_ffmpeg(),
            "redis": _check_redis(),
            "ai_provider": _check_ai(),
            "transcription": _check_transcription(),
        },
    }
