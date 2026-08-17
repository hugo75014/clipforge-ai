"""Clip model — a candidate segment inside a project."""

from __future__ import annotations

import json
from typing import Any, Optional

from sqlalchemy import Float, ForeignKey, Integer, String, Text, TypeDecorator
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class _JSONList(TypeDecorator):
    """Stores a list[str] as a JSON string in the DB, transparently."""
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, _dialect):
        if value is None:
            return None
        if isinstance(value, str):
            # Already a string — try to parse and re-serialize to validate.
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return value
            except (json.JSONDecodeError, TypeError):
                return None
        if isinstance(value, list):
            return json.dumps(value, ensure_ascii=False)
        return None

    def process_result_value(self, value, _dialect):
        if value is None:
            return None
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else None
            except (json.JSONDecodeError, TypeError):
                return None
        if isinstance(value, list):
            return value
        return None


class _JSONDict(TypeDecorator):
    """Stores a dict as a JSON string in the DB, transparently."""
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, _dialect):
        if value is None:
            return None
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, dict):
                    return value
            except (json.JSONDecodeError, TypeError):
                return None
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


class Clip(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "clips"

    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False
    )

    # Source window in the original video (seconds)
    start_sec: Mapped[float] = mapped_column(Float, nullable=False)
    end_sec: Mapped[float] = mapped_column(Float, nullable=False)

    # Editable offset (e.g. user dragged the handles)
    edit_start_sec: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    edit_end_sec: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # AI metadata
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    hook: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hashtags: Mapped[Optional[list[str]]] = mapped_column(_JSONList, nullable=True)
    keywords: Mapped[Optional[list[str]]] = mapped_column(_JSONList, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)    # Why AI picked this
    transcript: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Scores (0-100)
    score_hook: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    score_emotion: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    score_information: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    score_story: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    score_curiosity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    score_shareability: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    score_completion: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    score_overall: Mapped[float] = mapped_column(Float, default=0.0, nullable=False, index=True)

    # Editable config (JSON): crop, captions, music, brand, text overlays
    config: Mapped[Optional[dict[str, Any]]] = mapped_column(_JSONDict, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True, nullable=False)
    selected: Mapped[bool] = mapped_column(default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Rendered output
    render_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    render_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    render_duration_sec: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    render_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    render_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relation
    project: Mapped["Project"] = relationship("Project", back_populates="clips")  # noqa: F821

    @property
    def duration_sec(self) -> float:
        s = self.edit_start_sec if self.edit_start_sec is not None else self.start_sec
        e = self.edit_end_sec if self.edit_end_sec is not None else self.end_sec
        return max(0.0, e - s)
