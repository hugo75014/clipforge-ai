"""Clip routes — list/update/reorder/render."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.security import get_current_user
from app.db.session import get_db
from app.models import Clip, Job, Project, User
from app.schemas.clip import ClipOut, ClipReorderItem, ClipUpdate
from app.schemas.job import JobOut
from app.services import job as job_service
from app.services.video import run_ai_edit_pipeline, run_render_pipeline


router = APIRouter()
log = get_logger(__name__)


async def _load_clip(db: AsyncSession, clip_id: str, user: User) -> Clip:
    clip = await db.get(Clip, clip_id)
    if clip is None:
        raise HTTPException(status_code=404, detail="Clip not found")
    project = await db.get(Project, clip.project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != user.id and not user.is_admin:
        raise HTTPException(status_code=403, detail="Not your clip")
    return clip


@router.get("/{clip_id}", response_model=ClipOut)
async def get_clip(
    clip_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ClipOut:
    clip = await _load_clip(db, clip_id, user)
    return ClipOut.model_validate(clip)


@router.patch("/{clip_id}", response_model=ClipOut)
async def update_clip(
    clip_id: str,
    payload: ClipUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ClipOut:
    clip = await _load_clip(db, clip_id, user)
    data = payload.model_dump(exclude_unset=True)
    # JSON fields are typed natively on the model — just assign.
    for k in ("config", "hashtags", "keywords",
              "start_sec", "end_sec", "edit_start_sec", "edit_end_sec",
              "title", "hook", "description", "selected", "sort_order", "status"):
        if k in data and data[k] is not None:
            setattr(clip, k, data[k])
    await db.commit()
    await db.refresh(clip)
    return ClipOut.model_validate(clip)


@router.delete("/{clip_id}", status_code=204)
async def delete_clip(
    clip_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    clip = await _load_clip(db, clip_id, user)
    await db.delete(clip)
    await db.commit()


@router.post("/reorder")
async def reorder(
    items: list[ClipReorderItem],
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    updated = 0
    for item in items:
        clip = await _load_clip(db, item.id, user)
        clip.sort_order = item.sort_order
        if item.selected is not None:
            clip.selected = item.selected
        updated += 1
    await db.commit()
    return {"ok": True, "updated": updated}


# =============================================================================
# Render
# =============================================================================
@router.post("/{clip_id}/render", response_model=JobOut, status_code=202)
async def render(
    clip_id: str,
    background: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    aspect: str = "9:16",
    resolution: str = "1080p",
    burn_subtitles: bool = True,
    caption_style: Optional[str] = "viral",
    caption_position: str = "bottom",
) -> JobOut:
    clip = await _load_clip(db, clip_id, user)
    project = await db.get(Project, clip.project_id)
    job = await job_service.create_job(
        db, type_="render", project_id=project.id, clip_id=clip.id, user_id=user.id,
        payload={"aspect": aspect, "resolution": resolution, "burn_subtitles": burn_subtitles,
                 "caption_style": caption_style, "caption_position": caption_position},
    )

    async def _runner():
        from app.db.session import SessionLocal as _SL

        async with _SL() as session:
            try:
                clip_local = await session.get(Clip, clip.id)
                project_local = await session.get(Project, project.id)
                j = await job_service.get_job(session, job.id)
                if not (clip_local and project_local and j):
                    return
                await job_service.start_job(session, j)

                async def progress(p, msg, stage=None):
                    jj = await job_service.get_job(session, j.id)
                    if jj:
                        await job_service.update_progress(session, jj, percent=p, message=msg, stage=stage)

                await run_render_pipeline(
                    session,
                    clip_local,
                    project_local,
                    j,
                    progress,
                    aspect=aspect,
                    resolution=resolution,
                    burn_subtitles=burn_subtitles,
                    caption_style=caption_style,
                    caption_position=caption_position,
                )
                jj = await job_service.get_job(session, j.id)
                if jj:
                    await job_service.complete_job(session, jj, message="Render complete")
            except Exception as exc:  # noqa: BLE001
                log.exception("Render job %s failed", job.id)
                try:
                    j = await job_service.get_job(session, job.id)
                    if j:
                        await job_service.fail_job(session, j, error=str(exc))
                except Exception:
                    pass

    import asyncio
    background.add_task(asyncio.create_task, _runner())
    return JobOut.model_validate(job)


@router.post("/{clip_id}/render/sync", response_model=dict)
async def render_sync(
    clip_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    aspect: str = "9:16",
    resolution: str = "1080p",
    burn_subtitles: bool = True,
    caption_style: Optional[str] = "viral",
    caption_position: str = "bottom",
) -> dict:
    clip = await _load_clip(db, clip_id, user)
    project = await db.get(Project, clip.project_id)
    job = await job_service.create_job(
        db, type_="render", project_id=project.id, clip_id=clip.id, user_id=user.id
    )
    try:
        await job_service.start_job(db, job)
        async def progress(p, msg, stage=None):
            await job_service.update_progress(db, job, percent=p, message=msg, stage=stage)
        result = await run_render_pipeline(
            db, clip, project, job, progress,
            aspect=aspect,
            resolution=resolution,
            burn_subtitles=burn_subtitles,
            caption_style=caption_style,
            caption_position=caption_position,
        )
        await job_service.complete_job(db, job, message="Render complete", extra=result)
        return {"ok": True, "job": JobOut.model_validate(job).model_dump(), "result": result, "clip": ClipOut.model_validate(clip).model_dump()}
    except Exception as exc:
        log.exception("Sync render failed")
        await job_service.fail_job(db, job, error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))


# =============================================================================
# AI Edit
# =============================================================================
@router.post("/{clip_id}/ai-edit", response_model=dict)
async def ai_edit(
    clip_id: str,
    payload: dict,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    instruction = (payload or {}).get("instruction") or ""
    if not instruction.strip():
        raise HTTPException(status_code=400, detail="Missing 'instruction' field")
    clip = await _load_clip(db, clip_id, user)
    project = await db.get(Project, clip.project_id)
    job = await job_service.create_job(
        db, type_="ai_edit", project_id=project.id, clip_id=clip.id, user_id=user.id,
        payload={"instruction": instruction},
    )
    try:
        await job_service.start_job(db, job)
        async def progress(p, msg, stage=None):
            await job_service.update_progress(db, job, percent=p, message=msg, stage=stage)
        result = await run_ai_edit_pipeline(db, clip, project, job, progress, instruction=instruction)
        await job_service.complete_job(db, job, message="AI edit applied", extra=result)
        return {"ok": True, "job": JobOut.model_validate(job).model_dump(), "result": result, "clip": ClipOut.model_validate(clip).model_dump()}
    except Exception as exc:
        log.exception("AI edit failed")
        await job_service.fail_job(db, job, error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))
