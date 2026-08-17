"""Template schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class TemplateBase(BaseModel):
    name: str
    category: str = "custom"
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    is_public: bool = False
    config: dict[str, Any] = {}


class TemplateCreate(TemplateBase):
    pass


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    is_public: Optional[bool] = None
    config: Optional[dict[str, Any]] = None


class TemplateOut(TemplateBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    owner_id: Optional[str] = None
    is_builtin: bool = False
    created_at: datetime
    updated_at: datetime
