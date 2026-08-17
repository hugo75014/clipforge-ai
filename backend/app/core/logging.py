"""Structured logging setup."""

from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path
from typing import Any

from app.core import settings


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": int(time.time() * 1000),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for k, v in record.__dict__.items():
            if k.startswith("_") or k in payload:
                continue
            if k in ("args", "msg", "name", "levelno", "levelname", "pathname", "filename",
                     "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
                     "created", "msecs", "relativeCreated", "thread", "threadName",
                     "processName", "process", "message", "asctime"):
                continue
            try:
                json.dumps(v)
                payload[k] = v
            except TypeError:
                payload[k] = str(v)
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


class _TextFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        ts = self.formatTime(record, "%Y-%m-%d %H:%M:%S")
        msg = record.getMessage()
        base = f"{ts} [{record.levelname:<7}] {record.name}: {msg}"
        if record.exc_info:
            base += "\n" + self.formatException(record.exc_info)
        return base


def setup_logging() -> None:
    """Idempotent logger setup."""
    root = logging.getLogger()
    if getattr(root, "_clipforge_configured", False):
        return

    # Clear existing handlers (re-init in tests, reload, etc.)
    for h in list(root.handlers):
        root.removeHandler(h)

    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    root.setLevel(level)

    formatter = (
        _JsonFormatter() if settings.log_format.lower() == "json" else _TextFormatter()
    )

    # Console
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    root.addHandler(console)

    # File (best-effort, only if dir is writable)
    try:
        settings.logs_dir.mkdir(parents=True, exist_ok=True)
        fileh = logging.FileHandler(settings.logs_dir / "clipforge.log", encoding="utf-8")
        fileh.setFormatter(formatter)
        root.addHandler(fileh)
    except OSError:
        # In a sandboxed test env we may not be able to write — just skip.
        pass

    # Quiet down noisy libs
    logging.getLogger("multipart").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    root._clipforge_configured = True  # type: ignore[attr-defined]


def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)


# Bind contextual fields to a logger (job_id, project_id, …)
class ContextFilter(logging.Filter):
    def __init__(self, **fields: Any) -> None:
        super().__init__()
        self.fields = fields

    def filter(self, record: logging.LogRecord) -> bool:
        for k, v in self.fields.items():
            if not hasattr(record, k):
                setattr(record, k, v)
        return True
