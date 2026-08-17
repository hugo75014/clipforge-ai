"""AI Edit task — runs the AI Edit pipeline in a worker."""

from __future__ import annotations

from worker.celery_app import celery_app
from worker.tasks._common import _sync_loop
from app.core.logging import get_logger

log = get_logger(__name__)


@celery_app.task(name="worker.tasks.ai_edit.run", bind=True, max_retries=1)
def run_ai_edit(self, clip_id: str, instruction: str, user_id: str | None = None) -> dict:
    from app.db.session import SessionLocal
    from app.models import Clip, Project
    from app.services import job as job_service
    from app.services.video import run_ai_edit_pipeline

    with _sync_loop() as loop:
        async def _run():
            async with SessionLocal() as db:
                clip = await db.get(Clip, clip_id)
                if clip is None:
                    return {"ok": False, "error": "clip not found"}
                project = await db.get(Project, clip.project_id)
                if project is None:
                    return {"ok": False, "error": "project not found"}
                job = await job_service.create_job(
                    db, type_="ai_edit", project_id=project.id, clip_id=clip.id, user_id=user_id
                )
                try:
                    await job_service.start_job(db, job, worker_id=self.request.id)

                    async def progress(p, msg, stage=None):
                        await job_service.update_progress(db, job, percent=p, message=msg, stage=stage)

                    result = await run_ai_edit_pipeline(db, clip, project, job, progress, instruction=instruction)
                    await job_service.complete_job(db, job, message="AI edit applied", extra=result)
                    return {"ok": True, "job_id": job.id, "result": result}
                except Exception as exc:  # noqa: BLE001
                    log.exception("Worker AI edit failed")
                    await job_service.fail_job(db, job, error=str(exc))
                    return {"ok": False, "job_id": job.id, "error": str(exc)}

        return loop.run_until_complete(_run())
