"""SRT / VTT / ASS subtitle generation."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from shared.types import Transcript, TranscriptSegment
from shared.utils import format_timestamp


def write_srt(segments: Iterable[TranscriptSegment], path: str | Path) -> Path:
    """Write segments to a SubRip file (`.srt`)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    for idx, seg in enumerate(segments, start=1):
        start = format_timestamp(seg.start)
        end = format_timestamp(seg.end)
        text = _single_line(seg.text)
        lines.append(str(idx))
        lines.append(f"{start} --> {end}")
        lines.append(text)
        lines.append("")
    p.write_text("\n".join(lines), encoding="utf-8")
    return p


def write_vtt(segments: Iterable[TranscriptSegment], path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = ["WEBVTT", ""]
    for idx, seg in enumerate(segments, start=1):
        start = format_timestamp(seg.start).replace(",", ".")
        end = format_timestamp(seg.end).replace(",", ".")
        lines.append(str(idx))
        lines.append(f"{start} --> {end}")
        lines.append(_single_line(seg.text))
        lines.append("")
    p.write_text("\n".join(lines), encoding="utf-8")
    return p


def clip_transcript(transcript: Transcript, start: float, end: float) -> list[TranscriptSegment]:
    """Return only the segments inside [start, end], re-anchored to `start`."""
    out: list[TranscriptSegment] = []
    for seg in transcript.segments:
        if seg.end <= start or seg.start >= end:
            continue
        new_start = max(0.0, seg.start - start)
        new_end = min(end - start, seg.end - start)
        if new_end <= new_start:
            continue
        words = [
            w for w in seg.words if w.end > start and w.start < end
        ]
        # Re-anchor words
        for w in words:
            w.start = max(0.0, w.start - start)
            w.end = max(0.0, w.end - start)
        new_seg = TranscriptSegment(
            id=f"{seg.id}_clip",
            start=round(new_start, 3),
            end=round(new_end, 3),
            text=seg.text,
            words=words,
            speaker=seg.speaker,
            confidence=seg.confidence,
        )
        out.append(new_seg)
    return out


def _single_line(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())
