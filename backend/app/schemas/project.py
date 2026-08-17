"""Project schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    title: str = Field(default="Untitled project", min_length=1, max_length=255)
    description: Optional[str] = None
    source_url: Optional[str] = None
    template_id: Optional[str] = None
    brand_kit_id: Optional[str] = None
    config: Optional[dict[str, Any]] = None


class ProjectUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = None
    config: Optional[dict[str, Any]] = None
    language: Optional[str] = None


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    owner_id: str
    title: str
    description: Optional[str] = None
    source_url: Optional[str] = None
    source_filename: Optional[str] = None
    source_size_bytes: Optional[int] = None
    source_duration_sec: Optional[float] = None
    source_width: Optional[int] = None
    source_height: Optional[int] = None
    source_fps: Optional[float] = None
    source_codec: Optional[str] = None
    source_thumbnail_url: Optional[str] = None
    status: str
    language: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ProjectDetailOut(ProjectOut):
    clips: list["ClipOut"] = Field(default_factory=list)
    transcript: Optional["TranscriptOut"] = None
    jobs: list["JobOut"] = Field(default_factory=list)


class ProjectListOut(BaseModel):
    items: list[ProjectOut]
    total: int
    page: int
    page_size: int


class UploadInitResponse(BaseModel):
    project_id: str
    upload_url: str
    method: str = "POST"
    expires_at: Optional[datetime] = None
    max_size_bytes: int
    accepted_extensions: list[str]
    accepted_mime: list[str]


# Forward refs
from app.schemas.clip import ClipOut  # noqa: E402
from app.schemas.job import JobOut  # noqa: E402
from app.schemas.transcript import TranscriptOut  # noqa: E402

ProjectDetailOut.model_rebuild()
