"""Project model — a single imported source video and everything derived from it."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Project(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "projects"

    owner_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Source video
    source_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    source_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    source_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source_duration_sec: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    source_width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source_height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source_fps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    source_codec: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    source_thumbnail_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    source_waveform_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    status: Mapped[str] = mapped_column(String(32), default="draft", index=True, nullable=False)
    language: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)

    # Free-form configuration (caption style, brand kit id, template id, …)
    config: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relations
    clips: Mapped[list["Clip"]] = relationship(  # noqa: F821
        "Clip", back_populates="project", cascade="all, delete-orphan", lazy="selectin"
    )
