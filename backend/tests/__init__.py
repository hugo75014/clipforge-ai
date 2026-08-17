"""Pytest configuration."""

from __future__ import annotations

import asyncio
import os
import sys
import tempfile
from pathlib import Path
from typing import AsyncIterator

# Add the project root to sys.path so `app.*`, `shared.*`, `video_engine.*`,
# `ai_engine.*` resolve when pytest runs from `backend/`.
_ROOT = Path(__file__).resolve().parents[2]
for p in (str(_ROOT), str(_ROOT / "backend")):
    if p not in sys.path:
        sys.path.insert(0, p)

# Force a SQLite + temp data dir for the test session.
_TMP_DATA = tempfile.mkdtemp(prefix="clipforge-test-")
os.environ["APP_ENV"] = "test"
os.environ["DEMO_MODE"] = "true"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["STORAGE_BACKEND"] = "local"
os.environ["STORAGE_LOCAL_ROOT"] = _TMP_DATA
os.environ["SECRET_KEY"] = "test-secret"
os.environ["JWT_SECRET"] = "test-jwt"
os.environ["TRANSCRIPTION_PROVIDER"] = "demo"
os.environ["AI_PROVIDER"] = "demo"
os.environ["LOG_LEVEL"] = "WARNING"
