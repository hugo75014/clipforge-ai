"""Render task — runs the clip render pipeline in a worker."""

from __future__ import annotations

from worker.celery_app import celery_app
from worker.tasks._common import _sync_loop
from app.core.logging import get_logger

log = get_logger(__name__)


@celery_app.task(name="worker.tasks.render.run", bind=True, max_retries=1)
def run_render(
    self,
    clip_id: str,
    *,
    aspect: str = "9:16",
    resolution: str = "1080p",
    burn_subtitles: bool = True,
    caption_style: str = "viral",
    caption_position: str = "bottom",
    user_id: str | None = None,
    job_id: str | None = None,
) -> dict:
    from app.db.session import SessionLocal
    from app.models import Clip, Project
    from app.services import job as job_service
    from app.services.video import run_render_pipeline

    with _sync_loop() as loop:
        async def _run():
            async with SessionLocal() as db:
                clip = await db.get(Clip, clip_id)
                if clip is None:
                    return {"ok": False, "error": "clip not found"}
                project = await db.get(Project, clip.project_id)
                if project is None:
                    return {"ok": False, "error": "project not found"}
                # Idem analyze : réutiliser le Job créé par l'API.
                job = await job_service.get_job(db, job_id) if job_id else None
                if job is None:
                    job = await job_service.create_job(
                        db, type_="render", project_id=project.id, clip_id=clip.id, user_id=user_id
                    )
                try:
                    await job_service.start_job(db, job, worker_id=self.request.id)

                    async def progress(p, msg, stage=None):
                        await job_service.update_progress(db, job, percent=p, message=msg, stage=stage)

                    result = await run_render_pipeline(
                        db, clip, project, job, progress,
                        aspect=aspect, resolution=resolution,
                        burn_subtitles=burn_subtitles,
                        caption_style=caption_style,
                        caption_position=caption_position,
                    )
                    await job_service.complete_job(db, job, message="Render complete", extra=result)
                    return {"ok": True, "job_id": job.id, "result": result}
                except Exception as exc:  # noqa: BLE001
                    log.exception("Worker render failed")
                    await job_service.fail_job(db, job, error=str(exc))
                    return {"ok": False, "job_id": job.id, "error": str(exc)}

        return loop.run_until_complete(_run())
