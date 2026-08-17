"""Export schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ExportCreate(BaseModel):
    clip_id: Optional[str] = None
    project_id: Optional[str] = None
    format: str = "mp4_h264_1080p"
    aspect_ratio: str = "9:16"
    resolution: str = "1080p"
    target: Optional[str] = None  # youtube / tiktok / instagram / facebook / local
    notes: Optional[str] = None


class ExportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: Optional[str] = None
    clip_id: Optional[str] = None
    user_id: Optional[str] = None
    format: str
    aspect_ratio: str
    resolution: str
    file_path: str
    file_url: str
    file_size_bytes: Optional[int] = None
    duration_sec: Optional[int] = None
    target: Optional[str] = None
    external_id: Optional[str] = None
    external_url: Optional[str] = None
    status: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
