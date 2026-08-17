"""Transcription provider interface."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from shared.types import Transcript


@dataclass
class TranscriptionRequest:
    audio_path: str
    language: str | None = None
    word_level: bool = True
    speaker_diarization: bool = False
    model: str | None = None


class TranscriptionProvider(Protocol):
    name: str

    async def transcribe(self, request: TranscriptionRequest) -> Transcript: ...
