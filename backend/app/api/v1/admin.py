"""Admin dashboard routes — system overview, jobs, errors, providers, health."""

from __future__ import annotations

import platform
import sys
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import settings
from app.core.security import require_admin
from app.db.session import get_db
from app.models import Clip, ExportRecord, Job, Project, User
from app.providers.ai import get_ai_provider
from app.providers.transcription import get_transcription_provider
from app.services.storage import get_storage


router = APIRouter()


@router.get("/stats")
async def stats(
    _user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    users = (await db.execute(select(func.count()).select_from(User))).scalar_one()
    projects = (await db.execute(select(func.count()).select_from(Project))).scalar_one()
    clips = (await db.execute(select(func.count()).select_from(Clip))).scalar_one()
    exports = (await db.execute(select(func.count()).select_from(ExportRecord))).scalar_one()
    jobs = (await db.execute(select(func.count()).select_from(Job))).scalar_one()
    failed = (await db.execute(select(func.count()).select_from(Job).where(Job.status == "failed"))).scalar_one()
    processing = (await db.execute(select(func.count()).select_from(Job).where(Job.status == "processing"))).scalar_one()
    completed = (await db.execute(select(func.count()).select_from(Job).where(Job.status == "completed"))).scalar_one()
    total_clip_seconds = (await db.execute(select(func.coalesce(func.sum(Clip.render_duration_sec), 0.0)))).scalar_one() or 0.0
    total_storage_bytes = (await db.execute(select(func.coalesce(func.sum(Project.source_size_bytes), 0)))).scalar_one() or 0
    total_cost = (await db.execute(select(func.coalesce(func.sum(Job.estimated_cost_usd), 0.0)))).scalar_one() or 0.0
    return {
        "users": int(users),
        "projects": int(projects),
        "clips": int(clips),
        "exports": int(exports),
        "jobs": {
            "total": int(jobs),
            "completed": int(completed),
            "processing": int(processing),
            "failed": int(failed),
        },
        "total_clip_seconds": float(total_clip_seconds),
        "total_storage_bytes": int(total_storage_bytes),
        "total_estimated_cost_usd": float(total_cost),
    }


@router.get("/jobs")
async def recent_jobs(
    limit: int = 100,
    status_filter: str | None = None,
    type_filter: str | None = None,
    _user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    stmt = select(Job).order_by(Job.created_at.desc()).limit(max(1, min(500, limit)))
    if status_filter:
        stmt = stmt.where(Job.status == status_filter)
    if type_filter:
        stmt = stmt.where(Job.type == type_filter)
    res = await db.execute(stmt)
    out = []
    for j in res.scalars().all():
        out.append({
            "id": j.id,
            "type": j.type,
            "status": j.status,
            "project_id": j.project_id,
            "clip_id": j.clip_id,
            "user_id": j.user_id,
            "progress": j.progress,
            "current_stage": j.current_stage,
            "message": j.message,
            "error": (j.error or "")[:500],
            "provider": j.provider,
            "model": j.model,
            "estimated_cost_usd": j.estimated_cost_usd,
            "duration_ms": j.duration_ms,
            "created_at": j.created_at.isoformat() if j.created_at else None,
            "updated_at": j.updated_at.isoformat() if j.updated_at else None,
        })
    return out


@router.get("/config")
async def config(_user: User = Depends(require_admin)) -> dict:
    storage = get_storage()
    return {
        "app": {
            "name": settings.app_name,
            "env": settings.app_env,
            "version": settings.app_version,
            "debug": settings.app_debug,
            "url": settings.app_url,
        },
        "ai": {
            "provider": settings.ai_provider,
            "model": settings.ai_model,
            "demo_mode": settings.demo_mode,
        },
        "transcription": {
            "provider": settings.transcription_provider,
            "whisper_model": settings.whisper_model,
            "whisper_device": settings.whisper_device,
        },
        "storage": {
            "backend": storage.backend,
        },
        "system": {
            "python": sys.version,
            "platform": platform.platform(),
        },
    }


@router.get("/health-deep")
async def health_deep(_user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)) -> dict:
    from app.api.v1.health import _check_db, _check_storage, _check_ffmpeg, _check_redis
    import asyncio
    db_h, st_h = await asyncio.gather(_check_db(db), _check_storage())
    return {
        "database": db_h,
        "storage": st_h,
        "ffmpeg": _check_ffmpeg(),
        "redis": _check_redis(),
        "ai_provider": {"name": get_ai_provider().name, "status": "up"},
        "transcription": {"name": get_transcription_provider().name, "status": "up"},
    }
