"""Helpers shared by all worker tasks."""

from __future__ import annotations

import asyncio
import contextlib
import os
import sys
from pathlib import Path

# Make sure the backend + shared + video_engine + ai_engine + workers
# packages are importable when the worker runs from the `workers/` dir.
_ROOT = Path(__file__).resolve().parents[2]
for p in (str(_ROOT), str(_ROOT / "backend"), str(_ROOT / "workers")):
    if p not in sys.path:
        sys.path.insert(0, p)


@contextlib.contextmanager
def _sync_loop():
    """Run a single asyncio event loop synchronously inside a Celery worker."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    yield loop
