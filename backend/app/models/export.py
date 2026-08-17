"""ExportRecord — every shipped file is logged for history & audit."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class ExportRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "exports"

    project_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=True
    )
    clip_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("clips.id", ondelete="CASCADE"), index=True, nullable=True
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )

    format: Mapped[str] = mapped_column(String(64), nullable=False)
    aspect_ratio: Mapped[str] = mapped_column(String(16), nullable=False, default="9:16")
    resolution: Mapped[str] = mapped_column(String(16), nullable=False, default="1080p")
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration_sec: Mapped[Optional[float]] = mapped_column(Integer, nullable=True)

    target: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # youtube/tiktok/...
    external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    external_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="completed", nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
