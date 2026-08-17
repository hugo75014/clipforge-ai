"""Media routes — serve local files when STORAGE_BACKEND=local.

In production with S3 / R2 / MinIO, files are served directly by the bucket
and these routes are only used for thumbnails/waveforms previews.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response

from app.core import settings
from app.services.storage import get_storage

router = APIRouter()


_SAFE_KEY = re.compile(r"^[A-Za-z0-9._/\-]+$")


@router.get("/{key:path}")
async def serve(key: str) -> Response:
    storage = get_storage()
    if not storage.is_local:
        raise HTTPException(status_code=404, detail="Direct media is only available with STORAGE_BACKEND=local")
    if not _SAFE_KEY.match(key):
        raise HTTPException(status_code=400, detail="Invalid key")
    local = storage.local_path(key)
    if local is None or not local.exists() or not local.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(local)


@router.get("/_info/{key:path}")
async def info(key: str) -> dict:
    storage = get_storage()
    if not storage.is_local:
        return {"backend": storage.backend, "key": key}
    local = storage.local_path(key)
    return {
        "backend": storage.backend,
        "key": key,
        "exists": local is not None and local.exists(),
        "size": local.stat().st_size if local and local.exists() else 0,
    }
