"""Job schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class JobProgressOut(BaseModel):
    step: int = 0
    total_steps: int = 1
    percent: float = 0.0
    message: str = ""
    current_stage: Optional[str] = None
    error: Optional[str] = None
    extra: dict[str, Any] = Field(default_factory=dict)


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: str
    status: str
    project_id: Optional[str] = None
    clip_id: Optional[str] = None
    user_id: Optional[str] = None
    progress: float = 0.0
    current_stage: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None
    celery_task_id: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    duration_ms: Optional[int] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    estimated_cost_usd: Optional[float] = None
    created_at: datetime
    updated_at: datetime


class JobCreate(BaseModel):
    type: str
    project_id: Optional[str] = None
    clip_id: Optional[str] = None
    payload: dict[str, Any] = Field(default_factory=dict)
