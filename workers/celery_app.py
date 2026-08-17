"""Celery application — broker, queues, beat schedule."""

from __future__ import annotations

import os

from celery import Celery

REDIS_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")

celery_app = Celery(
    "clipforge",
    broker=REDIS_URL,
    backend=RESULT_BACKEND,
    include=["worker.tasks.analyze", "worker.tasks.render", "worker.tasks.ai_edit"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_queue="clips",
    task_routes={
        "worker.tasks.analyze.*": {"queue": "ai"},
        "worker.tasks.render.*": {"queue": "video"},
        "worker.tasks.ai_edit.*": {"queue": "ai"},
    },
    broker_connection_retry_on_startup=True,
)
