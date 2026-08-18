"""Celery dispatch — envoie les jobs lourds au worker plutôt qu'au processus web.

Sans ça, ffmpeg tourne dans le conteneur de l'API : un rendu mange le CPU du
serveur web, et un redémarrage en plein rendu perd le job sans laisser de trace.
Si le broker est injoignable, l'appelant retombe sur l'exécution en tâche de
fond du processus web — dégradé, mais l'utilisateur n'est pas bloqué.
"""

from __future__ import annotations

from typing import Any, Optional

from app.core import settings
from app.core.logging import get_logger

log = get_logger(__name__)

_client: Any = None


def _get_client() -> Any:
    """Client Celery paresseux : on ne paie la connexion que si on s'en sert."""
    global _client
    if _client is None:
        from celery import Celery

        _client = Celery(
            "clipforge-api",
            broker=settings.celery_broker_url,
            backend=settings.celery_result_backend,
        )
        # Le routage doit être le miroir exact de workers/celery_app.py :
        # sans lui, l'API poste dans la file « celery » que le worker n'écoute
        # pas, et le job reste `pending` pour toujours.
        _client.conf.update(
            task_serializer="json",
            result_serializer="json",
            accept_content=["json"],
            broker_connection_retry_on_startup=True,
            broker_transport_options={"max_retries": 1},
            task_default_queue="clips",
            task_routes={
                "worker.tasks.analyze.*": {"queue": "ai"},
                "worker.tasks.render.*": {"queue": "video"},
                "worker.tasks.ai_edit.*": {"queue": "ai"},
            },
        )
    return _client


def enabled() -> bool:
    return bool(settings.use_celery)


def dispatch(task_name: str, *, kwargs: dict[str, Any]) -> Optional[str]:
    """Empile une tâche. Renvoie l'id Celery, ou None si l'envoi a échoué.

    On ne laisse jamais remonter l'exception : l'appelant doit pouvoir basculer
    sur son exécution locale sans renvoyer une erreur à l'utilisateur.
    """
    if not enabled():
        return None
    try:
        result = _get_client().send_task(task_name, kwargs=kwargs)
        log.info("Dispatched %s to worker (task_id=%s)", task_name, result.id)
        return result.id
    except Exception as exc:  # noqa: BLE001
        log.warning("Celery dispatch failed for %s (%s) — falling back in-process", task_name, exc)
        return None
