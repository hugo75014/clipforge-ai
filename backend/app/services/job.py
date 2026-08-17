"""Job service — async work tracking, progress, recovery.

A `Job` row in DB is the source of truth for the UI. The actual work may be
dispatched to Celery (if `CELERY_TASK_ID` is set) or executed inline for the
demo mode (synchronous-ish, in a thread, with progress polling).
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from typing import Any, Awaitable, Callable, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import ContextFilter, get_logger
from app.models import Job


log = get_logger(__name__)


# =============================================================================
# Creation / updates
# =============================================================================
async def create_job(
    db: AsyncSession,
    *,
    type_: str,
    project_id: Optional[str] = None,
    clip_id: Optional[str] = None,
    user_id: Optional[str] = None,
    payload: Optional[dict[str, Any]] = None,
) -> Job:
    job = Job(
        id=str(uuid.uuid4()),
        type=type_,
        status="pending",
        project_id=project_id,
        clip_id=clip_id,
        user_id=user_id,
        message="Queued",
        progress=0.0,
    )
    if payload:
        job.meta = json.dumps(payload, ensure_ascii=False)
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


async def get_job(db: AsyncSession, job_id: str) -> Optional[Job]:
    res = await db.execute(select(Job).where(Job.id == job_id))
    return res.scalar_one_or_none()


async def list_jobs(
    db: AsyncSession,
    *,
    project_id: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = 50,
) -> list[Job]:
    stmt = select(Job).order_by(Job.created_at.desc()).limit(max(1, min(500, limit)))
    if project_id:
        stmt = stmt.where(Job.project_id == project_id)
    if user_id:
        stmt = stmt.where(Job.user_id == user_id)
    res = await db.execute(stmt)
    return list(res.scalars().all())


# =============================================================================
# Status transitions
# =============================================================================
async def start_job(db: AsyncSession, job: Job, *, worker_id: Optional[str] = None) -> None:
    job.status = "processing"
    job.started_at = _now_iso()
    if worker_id:
        job.worker_id = worker_id
    await db.commit()


async def update_progress(
    db: AsyncSession,
    job: Job,
    *,
    percent: float,
    message: Optional[str] = None,
    stage: Optional[str] = None,
    extra: Optional[dict] = None,
) -> None:
    job.progress = max(0.0, min(100.0, float(percent)))
    if message:
        job.message = message[:500]
    if stage:
        job.current_stage = stage[:120]
    if extra:
        existing = {}
        if job.meta:
            try:
                existing = json.loads(job.meta) or {}
            except json.JSONDecodeError:
                existing = {}
        existing.update(extra)
        job.meta = json.dumps(existing, ensure_ascii=False)
    await db.commit()


async def complete_job(
    db: AsyncSession,
    job: Job,
    *,
    message: Optional[str] = None,
    extra: Optional[dict] = None,
) -> None:
    job.status = "completed"
    job.progress = 100.0
    if message:
        job.message = message
    if extra:
        existing = {}
        if job.meta:
            try:
                existing = json.loads(job.meta) or {}
            except json.JSONDecodeError:
                existing = {}
        existing.update(extra)
        job.meta = json.dumps(existing, ensure_ascii=False)
    job.finished_at = _now_iso()
    if job.started_at:
        try:
            t0 = _parse_iso(job.started_at)
            job.duration_ms = int((time.time() - t0) * 1000)
        except Exception:
            pass
    await db.commit()


async def fail_job(
    db: AsyncSession,
    job: Job,
    *,
    error: str,
    extra: Optional[dict] = None,
) -> None:
    job.status = "failed"
    job.error = error[:5000]
    if extra:
        existing = {}
        if job.meta:
            try:
                existing = json.loads(job.meta) or {}
            except json.JSONDecodeError:
                existing = {}
        existing.update(extra)
        job.meta = json.dumps(existing, ensure_ascii=False)
    job.finished_at = _now_iso()
    if job.started_at:
        try:
            t0 = _parse_iso(job.started_at)
            job.duration_ms = int((time.time() - t0) * 1000)
        except Exception:
            pass
    await db.commit()


async def cancel_job(db: AsyncSession, job: Job) -> None:
    job.status = "cancelled"
    job.finished_at = _now_iso()
    await db.commit()


# =============================================================================
# Inline executor (used by demo mode and tests)
# =============================================================================
ProgressCallback = Callable[[float, str, Optional[str]], Awaitable[None]]


async def run_inline(
    db_factory: Callable[[], AsyncSession],
    job: Job,
    steps: list[tuple[str, Callable[[ProgressCallback], Awaitable[Any]]]],
) -> Any:
    """Run a series of async steps inline, updating job progress in DB.

    `steps` is a list of `(stage_name, async_callable)` where the callable
    receives a `progress` callback and returns whatever it wants.
    """
    await start_job(db=db_factory().__class__ is not None and next(_iter_db(db_factory)) or _first(db_factory), job=job)
    total = len(steps)
    result: Any = None
    try:
        for idx, (stage, fn) in enumerate(steps, start=1):
            percent_start = (idx - 1) / total * 100
            percent_end = idx / total * 100

            async def cb(p: float, msg: str = "", stg: Optional[str] = None, _idx=idx, _start=percent_start, _end=percent_end):
                pct = _start + (p / 100.0) * (_end - _start)
                async with db_factory() as db:
                    j = await get_job(db, job.id)
                    if j:
                        await update_progress(db, j, percent=pct, message=msg, stage=stg or stage)

            result = await fn(cb)
        async with db_factory() as db:
            j = await get_job(db, job.id)
            if j:
                await complete_job(db, j, message="Done")
        return result
    except Exception as exc:  # noqa: BLE001
        log.exception("Inline job %s failed", job.id)
        async with db_factory() as db:
            j = await get_job(db, job.id)
            if j:
                await fail_job(db, j, error=str(exc))
        raise


def _iter_db(factory):
    """Tiny helper — yields a session then closes it. Used by `run_inline`."""
    return iter([factory()])  # not actually used; we open fresh sessions per call


def _first(factory):
    # Not actually invoked; left for clarity.
    return factory()


# =============================================================================
# Helpers
# =============================================================================
def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _parse_iso(s: str) -> float:
    return time.mktime(time.strptime(s, "%Y-%m-%dT%H:%M:%SZ"))
