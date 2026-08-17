"""Analysis task — runs the full analyze pipeline inside a Celery worker."""

from __future__ import annotations

from worker.celery_app import celery_app
from worker.tasks._common import _sync_loop
from app.core.logging import get_logger

log = get_logger(__name__)


@celery_app.task(name="worker.tasks.analyze.run", bind=True, max_retries=2)
def run_analyze(self, project_id: str, user_id: str | None = None) -> dict:
    """Run the analyze pipeline for `project_id`.

    Mirrors the inline `analyze_sync` endpoint but in a worker.
    """
    from app.db.session import SessionLocal
    from app.models import Job, Project
    from app.services import job as job_service
    from app.services.video import run_analysis_pipeline

    with _sync_loop() as loop:
        async def _run():
            async with SessionLocal() as db:
                project = await db.get(Project, project_id)
                if project is None:
                    return {"ok": False, "error": "project not found"}
                job = await job_service.create_job(
                    db, type_="analyze", project_id=project.id, user_id=user_id
                )
                try:
                    await job_service.start_job(db, job, worker_id=self.request.id)

                    async def progress(p, msg, stage=None):
                        await job_service.update_progress(db, job, percent=p, message=msg, stage=stage)

                    result = await run_analysis_pipeline(db, project, job, progress)
                    await job_service.complete_job(db, job, message="Analysis complete", extra=result)
                    return {"ok": True, "job_id": job.id, "result": result}
                except Exception as exc:  # noqa: BLE001
                    log.exception("Worker analyze failed")
                    await job_service.fail_job(db, job, error=str(exc))
                    return {"ok": False, "job_id": job.id, "error": str(exc)}

        return loop.run_until_complete(_run())
