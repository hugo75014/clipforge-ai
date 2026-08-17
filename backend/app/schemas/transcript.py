"""Transcript schemas."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TranscriptWordOut(BaseModel):
    word: str
    start: float
    end: float
    confidence: float = 1.0
    speaker: Optional[str] = None


class TranscriptSegmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    idx: int
    start_sec: float
    end_sec: float
    text: str
    speaker: Optional[str] = None
    confidence: Optional[float] = None
    words: list[TranscriptWordOut] = Field(default_factory=list)


class TranscriptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    language: str = "en"
    duration: float = 0.0
    provider: str = "demo"
    segments: list[TranscriptSegmentOut] = Field(default_factory=list)

    @classmethod
    def from_segments(cls, segments: list[TranscriptSegmentOut], language: str, provider: str) -> "TranscriptOut":
        duration = max((s.end_sec for s in segments), default=0.0)
        return cls(language=language, provider=provider, duration=duration, segments=segments)
