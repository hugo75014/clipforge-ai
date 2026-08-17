"""Transcription provider factory."""

from __future__ import annotations

from functools import lru_cache

from app.core import settings
from app.providers.transcription.base import TranscriptionProvider, TranscriptionRequest


@lru_cache(maxsize=1)
def get_transcription_provider() -> TranscriptionProvider:
    name = (settings.transcription_provider or "demo").lower()

    if name in ("demo", "offline"):
        from app.providers.transcription.demo import DemoTranscriptionProvider
        return DemoTranscriptionProvider()

    if name in ("whisper", "faster-whisper", "whisperx"):
        from app.providers.transcription.whisper import WhisperProvider
        return WhisperProvider(
            model_size=settings.whisper_model,
            device=settings.whisper_device,
            compute_type=settings.whisper_compute_type,
            language=settings.whisper_language,
        )

    # Unknown → demo
    from app.providers.transcription.demo import DemoTranscriptionProvider
    return DemoTranscriptionProvider()


__all__ = ["TranscriptionProvider", "TranscriptionRequest", "get_transcription_provider"]
