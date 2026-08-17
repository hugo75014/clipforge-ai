"""Template model — reusable editing presets."""

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


class Template(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "templates"

    owner_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False, default="custom")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Full config JSON (crop, captions, music, …)
    config: Mapped[dict[str, Any]] = mapped_column(_JSONDict, nullable=False, default=dict)
