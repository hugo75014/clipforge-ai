"""Shared dataclasses and TypedDicts used across services.

These mirror the Pydantic schemas on the backend and the TypeScript types in
`frontend/src/types`. The goal is a single canonical shape for things like
"clip", "job", "project" so the video/AI engines can speak to the API and the
worker without re-defining them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from shared.constants import JobStatus, JobType


# =============================================================================
# Jobs
# =============================================================================
@dataclass
class JobProgress:
    step: int = 0
    total_steps: int = 1
    percent: float = 0.0
    message: str = ""
    current_stage: Optional[str] = None
    error: Optional[str] = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class JobInfo:
    id: str
    type: JobType
    status: JobStatus
    progress: JobProgress
    project_id: Optional[str] = None
    clip_id: Optional[str] = None
    user_id: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    error: Optional[str] = None
    payload: dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Transcript / analysis
# =============================================================================
@dataclass
class TranscriptWord:
    word: str
    start: float          # seconds from start of media
    end: float
    confidence: float = 1.0
    speaker: Optional[str] = None


@dataclass
class TranscriptSegment:
    id: str
    start: float
    end: float
    text: str
    words: list[TranscriptWord] = field(default_factory=list)
    speaker: Optional[str] = None
    confidence: float = 1.0


@dataclass
class Transcript:
    language: str
    segments: list[TranscriptSegment]
    duration: float
    provider: str


# =============================================================================
# Clips
# =============================================================================
@dataclass
class ClipScores:
    hook: float = 0.0
    emotion: float = 0.0
    information: float = 0.0
    story: float = 0.0
    curiosity: float = 0.0
    shareability: float = 0.0
    completion: float = 0.0

    @property
    def overall(self) -> float:
        # Weighted average — hook & emotion matter more for short-form.
        weights = {
            "hook": 0.25,
            "emotion": 0.20,
            "curiosity": 0.15,
            "shareability": 0.15,
            "completion": 0.10,
            "information": 0.08,
            "story": 0.07,
        }
        score = (
            self.hook * weights["hook"]
            + self.emotion * weights["emotion"]
            + self.curiosity * weights["curiosity"]
            + self.shareability * weights["shareability"]
            + self.completion * weights["completion"]
            + self.information * weights["information"]
            + self.story * weights["story"]
        )
        return round(max(0.0, min(100.0, score)), 1)

    def to_dict(self) -> dict[str, float]:
        return {
            "hook": self.hook,
            "emotion": self.emotion,
            "information": self.information,
            "story": self.story,
            "curiosity": self.curiosity,
            "shareability": self.shareability,
            "completion": self.completion,
            "overall": self.overall,
        }


@dataclass
class DetectedClip:
    start: float
    end: float
    title: str
    hook: str
    description: str
    hashtags: list[str]
    scores: ClipScores
    transcript: str = ""
    reason: str = ""             # Why the AI picked this segment
    keywords: list[str] = field(default_factory=list)

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)


# =============================================================================
# Video metadata
# =============================================================================
@dataclass
class VideoMetadata:
    path: str
    duration: float
    width: int
    height: int
    fps: float
    codec: str
    bitrate: Optional[int] = None
    has_audio: bool = True
    size_bytes: int = 0
