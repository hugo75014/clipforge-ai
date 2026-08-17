"""BrandKit model — reusable brand assets per user."""

from __future__ import annotations

import json
from typing import Any, Optional

from sqlalchemy import Boolean, ForeignKey, String, Text, TypeDecorator
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class _JSONDict(TypeDecorator):
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, _dialect):
        if value is None:
            return None
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            return json.dumps(value, ensure_ascii=False)
        return None

    def process_result_value(self, value, _dialect):
        if value is None:
            return None
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, dict) else None
            except (json.JSONDecodeError, TypeError):
                return None
        if isinstance(value, dict):
            return value
        return None


class BrandKit(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "brand_kits"

    owner_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    logo_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    primary_color: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    secondary_color: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    accent_color: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    font_family: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    caption_style: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    intro_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    outro_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    watermark_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    music_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    # JSON blob with extras (lower-thirds, …)
    extras: Mapped[Optional[dict[str, Any]]] = mapped_column(_JSONDict, nullable=True)
