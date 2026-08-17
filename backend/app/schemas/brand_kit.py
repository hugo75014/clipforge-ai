"""Brand kit schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class BrandKitBase(BaseModel):
    name: str
    is_default: bool = False
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    font_family: Optional[str] = None
    caption_style: Optional[str] = None
    intro_url: Optional[str] = None
    outro_url: Optional[str] = None
    watermark_url: Optional[str] = None
    music_url: Optional[str] = None
    extras: Optional[dict[str, Any]] = None


class BrandKitCreate(BrandKitBase):
    pass


class BrandKitUpdate(BaseModel):
    name: Optional[str] = None
    is_default: Optional[bool] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    font_family: Optional[str] = None
    caption_style: Optional[str] = None
    intro_url: Optional[str] = None
    outro_url: Optional[str] = None
    watermark_url: Optional[str] = None
    music_url: Optional[str] = None
    extras: Optional[dict[str, Any]] = None


class BrandKitOut(BrandKitBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    owner_id: str
    created_at: datetime
    updated_at: datetime
