"""Whisper / faster-whisper provider.

Real model is loaded lazily so the rest of the app stays responsive when
`TRANSCRIPTION_PROVIDER=demo` (default).
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import asdict

from app.providers.transcription.base import TranscriptionProvider, TranscriptionRequest
from shared.types import Transcript, TranscriptSegment, TranscriptWord


class WhisperProvider:
    name = "whisper"

    def __init__(
        self,
        *,
        model_size: str | None = None,
        device: str | None = None,
        compute_type: str | None = None,
        language: str | None = None,
    ) -> None:
        self.model_size = model_size or os.getenv("WHISPER_MODEL", "base")
        self.device = device or os.getenv("WHISPER_DEVICE", "cpu")
        self.compute_type = compute_type or os.getenv("WHISPER_COMPUTE_TYPE", "int8")
        self.language = language or os.getenv("WHISPER_LANGUAGE") or None
        self._model = None

    def _ensure_model(self):
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
            except ImportError as exc:  # pragma: no cover
                raise RuntimeError(
                    "faster-whisper not installed. pip install faster-whisper"
                ) from exc
            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
            )
        return self._model

    async def transcribe(self, request: TranscriptionRequest) -> Transcript:
        model = self._ensure_model()
        language = request.language or self.language
        # faster-whisper is sync + CPU-bound — run in a thread.
        segments_iter, info = await asyncio.to_thread(
            model.transcribe,
            request.audio_path,
            language=language,
            word_timestamps=request.word_level,
            vad_filter=True,
        )
        segments: list[TranscriptSegment] = []
        # Materialize the iterator inside the thread so we don't block the loop.
        material = await asyncio.to_thread(list, segments_iter)
        for idx, seg in enumerate(material):
            words: list[TranscriptWord] = []
            if getattr(seg, "words", None):
                for w in seg.words:
                    words.append(
                        TranscriptWord(
                            word=w.word,
                            start=float(w.start or 0.0),
                            end=float(w.end or 0.0),
                            confidence=float(getattr(w, "probability", 1.0) or 1.0),
                        )
                    )
            segments.append(
                TranscriptSegment(
                    id=f"seg_{idx:04d}",
                    start=float(seg.start),
                    end=float(seg.end),
                    text=seg.text.strip(),
                    words=words,
                    confidence=float(getattr(seg, "avg_logprob", 0.0) or 0.0),
                )
            )
        return Transcript(
            language=info.language or "en",
            duration=float(info.duration or 0.0),
            provider=self.name,
            segments=segments,
        )
