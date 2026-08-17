"""Clip schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ClipScores(BaseModel):
    hook: float = 0.0
    emotion: float = 0.0
    information: float = 0.0
    story: float = 0.0
    curiosity: float = 0.0
    shareability: float = 0.0
    completion: float = 0.0
    overall: float = 0.0


class DetectedClipOut(BaseModel):
    start: float
    end: float
    title: str
    hook: str
    description: str
    hashtags: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    reason: str = ""
    transcript: str = ""
    scores: ClipScores


class ClipOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    start_sec: float
    end_sec: float
    edit_start_sec: Optional[float] = None
    edit_end_sec: Optional[float] = None
    title: Optional[str] = None
    hook: Optional[str] = None
    description: Optional[str] = None
    hashtags: Optional[list[str]] = None
    keywords: Optional[list[str]] = None
    reason: Optional[str] = None
    transcript: Optional[str] = None
    score_hook: float = 0.0
    score_emotion: float = 0.0
    score_information: float = 0.0
    score_story: float = 0.0
    score_curiosity: float = 0.0
    score_shareability: float = 0.0
    score_completion: float = 0.0
    score_overall: float = 0.0
    status: str
    selected: bool = True
    sort_order: int = 0
    render_path: Optional[str] = None
    render_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    render_duration_sec: Optional[float] = None
    render_size_bytes: Optional[int] = None
    render_error: Optional[str] = None
    config: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    @property
    def duration_sec(self) -> float:
        s = self.edit_start_sec if self.edit_start_sec is not None else self.start_sec
        e = self.edit_end_sec if self.edit_end_sec is not None else self.end_sec
        return max(0.0, e - s)


class ClipUpdate(BaseModel):
    start_sec: Optional[float] = Field(default=None, ge=0)
    end_sec: Optional[float] = Field(default=None, ge=0)
    edit_start_sec: Optional[float] = Field(default=None, ge=0)
    edit_end_sec: Optional[float] = Field(default=None, ge=0)
    title: Optional[str] = None
    hook: Optional[str] = None
    description: Optional[str] = None
    hashtags: Optional[list[str]] = None
    keywords: Optional[list[str]] = None
    selected: Optional[bool] = None
    sort_order: Optional[int] = None
    config: Optional[dict[str, Any]] = None
    status: Optional[str] = None

    @model_validator(mode="after")
    def _check_window(self):
        if self.start_sec is not None and self.end_sec is not None and self.end_sec <= self.start_sec:
            raise ValueError("end_sec must be greater than start_sec")
        if self.edit_start_sec is not None and self.edit_end_sec is not None and self.edit_end_sec <= self.edit_start_sec:
            raise ValueError("edit_end_sec must be greater than edit_start_sec")
        return self


class ClipReorderItem(BaseModel):
    id: str
    sort_order: int
    selected: Optional[bool] = None
