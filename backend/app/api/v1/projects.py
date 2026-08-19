"""Project routes — CRUD, upload, analysis."""

from __future__ import annotations

import asyncio
import json
import os
import shutil
from pathlib import Path
from typing import Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import settings
from app.core.security import get_current_user
from app.core.logging import get_logger
from app.db.session import SessionLocal, get_db
from app.models import Clip, Job, Project, TranscriptSegment as TSegment, User
from app.schemas.job import JobOut
from app.schemas.project import (
    ProjectCreate,
    ProjectDetailOut,
    ProjectListOut,
    ProjectOut,
    ProjectUpdate,
)
from app.schemas.transcript import (
    TranscriptOut,
    TranscriptSegmentOut,
    TranscriptWordOut,
)
from app.services import job as job_service
from app.services import queue
from app.services.project.service import (
    create_project,
    delete_project,
    duplicate_project,
    get_project,
    get_storage_key,
    list_projects,
    update_project,
)
from app.services.storage import get_storage
from app.services.video import run_analysis_pipeline
from shared.utils import safe_filename

router = APIRouter()
log = get_logger(__name__)


# =============================================================================
# Helpers
# =============================================================================
def _project_to_out(p: Project) -> ProjectOut:
    return ProjectOut.model_validate(p)


async def _ensure_owner(project: Project, user: User) -> None:
    if project.owner_id != user.id and not user.is_admin:
        raise HTTPException(status_code=403, detail="Not your project")


# =============================================================================
# CRUD
# =============================================================================
@router.post("", response_model=ProjectOut, status_code=201)
async def create(
    payload: ProjectCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectOut:
    project = await create_project(db, owner_id=user.id, payload=payload)
    return _project_to_out(project)


@router.get("", response_model=ProjectListOut)
async def list_(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    archived: bool = False,
) -> ProjectListOut:
    owner_id = user.id if not user.is_admin else None
    items, total = await list_projects(
        db,
        owner_id=owner_id,
        page=page,
        page_size=page_size,
        search=search,
        status=status_filter,
        archived=archived,
    )
    return ProjectListOut(items=[_project_to_out(p) for p in items], total=total, page=page, page_size=page_size)


@router.get("/{project_id}", response_model=ProjectDetailOut)
async def get(
    project_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectDetailOut:
    project = await get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    await _ensure_owner(project, user)
    # Eager load clips
    clips = (await db.execute(select(Clip).where(Clip.project_id == project_id).order_by(Clip.sort_order))).scalars().all()
    segs = (await db.execute(
        select(TSegment).where(TSegment.project_id == project_id).order_by(TSegment.start_sec)
    )).scalars().all()
    jobs = (await db.execute(
        select(Job).where(Job.project_id == project_id).order_by(Job.created_at.desc()).limit(50)
    )).scalars().all()
    from app.schemas.clip import ClipOut
    from app.schemas.job import JobOut

    transcript = None
    if segs:
        first = segs[0]
        typed = [
            TranscriptSegmentOut(
                id=s.id,
                idx=s.idx,
                start_sec=s.start_sec,
                end_sec=s.end_sec,
                text=s.text,
                speaker=s.speaker,
                confidence=s.confidence,
                words=[TranscriptWordOut(**w) for w in (json.loads(s.words_json) if s.words_json else [])],
            )
            for s in segs
        ]
        transcript = TranscriptOut.from_segments(typed, first.language or "en", first.provider or "demo")

    # Convert JSON-string fields into proper lists for the response.
    from app.schemas.clip import ClipOut
    from app.schemas.job import JobOut

    clip_outs: list[ClipOut] = []
    for c in clips:
        co = ClipOut.model_validate(c)
        # Pydantic-from-ORM doesn't know our model stores these as JSON strings.
        if isinstance(c.hashtags, str):
            try:
                co.hashtags = json.loads(c.hashtags) if c.hashtags else None
            except json.JSONDecodeError:
                co.hashtags = None
        if isinstance(c.keywords, str):
            try:
                co.keywords = json.loads(c.keywords) if c.keywords else None
            except json.JSONDecodeError:
                co.keywords = None
        if isinstance(c.config, str) and c.config:
            try:
                co.config = json.loads(c.config)
            except json.JSONDecodeError:
                co.config = None
        clip_outs.append(co)

    return ProjectDetailOut(
        id=project.id,
        owner_id=project.owner_id,
        title=project.title,
        description=project.description,
        source_url=project.source_url,
        source_filename=project.source_filename,
        source_size_bytes=project.source_size_bytes,
        source_duration_sec=project.source_duration_sec,
        source_width=project.source_width,
        source_height=project.source_height,
        source_fps=project.source_fps,
        source_codec=project.source_codec,
        source_thumbnail_url=project.source_thumbnail_url,
        status=project.status,
        language=project.language,
        error=project.error,
        created_at=project.created_at,
        updated_at=project.updated_at,
        clips=clip_outs,
        transcript=transcript,
        jobs=[JobOut.model_validate(j) for j in jobs],
    )


@router.patch("/{project_id}", response_model=ProjectOut)
async def update(
    project_id: str,
    payload: ProjectUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectOut:
    project = await get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    await _ensure_owner(project, user)
    project = await update_project(db, project, payload)
    return _project_to_out(project)


@router.delete("/{project_id}", status_code=204)
async def delete(
    project_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    project = await get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    await _ensure_owner(project, user)
    await delete_project(db, project)


@router.post("/{project_id}/duplicate", response_model=ProjectOut)
async def duplicate(
    project_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectOut:
    project = await get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    await _ensure_owner(project, user)
    new = await duplicate_project(db, project)
    return _project_to_out(new)


@router.post("/{project_id}/archive", response_model=ProjectOut)
async def archive(
    project_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectOut:
    project = await get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    await _ensure_owner(project, user)
    project.status = "archived"
    await db.commit()
    await db.refresh(project)
    return _project_to_out(project)


# =============================================================================
# Upload
# =============================================================================
@router.post("/{project_id}/upload", status_code=200)
async def upload(
    project_id: str,
    background: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    file: UploadFile = File(...),
) -> dict:
    project = await get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    await _ensure_owner(project, user)

    # Validation
    if file.content_type and file.content_type not in settings.allowed_video_mime_set:
        raise HTTPException(status_code=415, detail=f"Unsupported content-type: {file.content_type}")
    ext = (file.filename or "").rsplit(".", 1)[-1].lower() if file.filename else ""
    if ext and ext not in settings.allowed_video_ext_set:
        raise HTTPException(status_code=415, detail=f"Unsupported extension: .{ext}")

    safe_name = safe_filename(file.filename or "video.mp4", fallback="video.mp4")
    storage = get_storage()
    key = get_storage_key(project_id, safe_name)
    dest_path = settings.uploads_dir / project_id / safe_name
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    total = 0
    with open(dest_path, "wb") as out:
        while True:
            chunk = await file.read(8 * 1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > settings.max_upload_size_bytes:
                out.close()
                dest_path.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="File too large")
            out.write(chunk)

    # Upload to configured storage backend as well
    try:
        url = await storage.put_file(dest_path, key, content_type=file.content_type, public=True)
    except Exception as exc:
        log.warning("Storage put_file failed (continuing with local path): %s", exc)
        url = f"{settings.storage_public_base_url.rstrip('/')}/{key}"

    project.source_filename = safe_name
    project.source_path = str(dest_path)
    project.source_size_bytes = total
    project.source_url = url
    project.status = "uploaded"
    project.error = None
    await db.commit()
    await db.refresh(project)
    return {
        "project": _project_to_out(project),
        "upload": {
            "key": key,
            "url": url,
            "size_bytes": total,
        },
    }


# =============================================================================
# Analysis
# =============================================================================
@router.post("/{project_id}/analyze", response_model=JobOut, status_code=202)
async def analyze(
    project_id: str,
    background: BackgroundTasks,
    mode: str = Query("full", pattern="^(full|more)$"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JobOut:
    project = await get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    await _ensure_owner(project, user)
    if mode == "full" and not project.source_path:
        raise HTTPException(status_code=400, detail="No source video uploaded yet")
    if mode == "more":
        has_transcript = (
            await db.execute(select(TSegment.id).where(TSegment.project_id == project.id).limit(1))
        ).first()
        if not has_transcript:
            raise HTTPException(status_code=400, detail="Run a full analysis first")

    job = await job_service.create_job(
        db,
        type_="analyze",
        project_id=project.id,
        user_id=user.id,
        payload={"source": project.source_filename, "mode": mode},
    )

    # Chemin normal : le worker Celery prend le job. ffmpeg ne tourne alors
    # jamais dans le processus qui sert l'API.
    task_id = queue.dispatch(
        "worker.tasks.analyze.run",
        kwargs={"project_id": project.id, "user_id": user.id, "job_id": job.id, "mode": mode},
    )
    if task_id:
        job.celery_task_id = task_id
        await db.commit()
        await db.refresh(job)
        return JobOut.model_validate(job)

    async def _runner():
        # Repli sans worker : on exécute dans le processus web (BackgroundTasks
        # démarre après la réponse, d'où la session dédiée).
        from app.db.session import SessionLocal as _SL

        async with _SL() as session:
            try:
                proj = await get_project(session, project.id)
                j = await job_service.get_job(session, job.id)
                if not proj or not j:
                    return
                await job_service.start_job(session, j)

                async def progress(p, msg, stage=None):
                    jj = await job_service.get_job(session, j.id)
                    if jj:
                        await job_service.update_progress(session, jj, percent=p, message=msg, stage=stage)

                await run_analysis_pipeline(session, proj, j, progress, mode=mode)
                jj = await job_service.get_job(session, j.id)
                if jj:
                    await job_service.complete_job(session, jj, message="Analysis complete")
            except Exception as exc:  # noqa: BLE001
                log.exception("Analyze job %s failed", job.id)
                try:
                    j = await job_service.get_job(session, job.id)
                    if j:
                        await job_service.fail_job(session, j, error=str(exc))
                except Exception:
                    pass

    background.add_task(asyncio.create_task, _runner())
    return JobOut.model_validate(job)


@router.post("/{project_id}/analyze/sync", response_model=dict)
async def analyze_sync(
    project_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Synchronous analyze (useful for demo mode + small files)."""
    project = await get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    await _ensure_owner(project, user)
    if not project.source_path:
        raise HTTPException(status_code=400, detail="No source video uploaded yet")

    job = await job_service.create_job(db, type_="analyze", project_id=project.id, user_id=user.id)
    try:
        await job_service.start_job(db, job)
        last_msg = ""

        async def progress(p, msg, stage=None):
            nonlocal last_msg
            last_msg = msg
            await job_service.update_progress(db, job, percent=p, message=msg, stage=stage)

        result = await run_analysis_pipeline(db, project, job, progress)
        await job_service.complete_job(db, job, message="Analysis complete", extra=result)
        return {"ok": True, "job": JobOut.model_validate(job).model_dump(), "result": result, "last_message": last_msg}
    except Exception as exc:  # noqa: BLE001
        log.exception("Sync analyze failed")
        await job_service.fail_job(db, job, error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))


# =============================================================================
# Transcribe
# =============================================================================
@router.get("/{project_id}/transcript", response_model=Optional[TranscriptOut])
async def get_transcript(
    project_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Optional[TranscriptOut]:
    project = await get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    await _ensure_owner(project, user)
    segs = (await db.execute(
        select(TSegment).where(TSegment.project_id == project_id).order_by(TSegment.start_sec)
    )).scalars().all()
    if not segs:
        return None
    typed = [
        TranscriptSegmentOut(
            id=s.id,
            idx=s.idx,
            start_sec=s.start_sec,
            end_sec=s.end_sec,
            text=s.text,
            speaker=s.speaker,
            confidence=s.confidence,
            words=[TranscriptWordOut(**w) for w in (json.loads(s.words_json) if s.words_json else [])],
        )
        for s in segs
    ]
    return TranscriptOut.from_segments(typed, segs[0].language or "en", segs[0].provider or "demo")
