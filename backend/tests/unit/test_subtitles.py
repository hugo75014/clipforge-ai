"""Tests for the video engine: subtitles."""

from __future__ import annotations

from pathlib import Path

from shared.types import Transcript, TranscriptSegment
from video_engine.subtitles import clip_transcript, write_srt, write_vtt


def _make_transcript() -> Transcript:
    return Transcript(
        language="en",
        duration=60.0,
        provider="test",
        segments=[
            TranscriptSegment(id="a", start=2.0, end=10.0, text="Hello world."),
            TranscriptSegment(id="b", start=12.0, end=18.0, text="Second segment here."),
        ],
    )


def test_write_srt(tmp_path: Path):
    out = tmp_path / "out.srt"
    write_srt(_make_transcript().segments, out)
    content = out.read_text(encoding="utf-8")
    assert "00:00:02,000 --> 00:00:10,000" in content
    assert "Hello world." in content


def test_write_vtt(tmp_path: Path):
    out = tmp_path / "out.vtt"
    write_vtt(_make_transcript().segments, out)
    content = out.read_text(encoding="utf-8")
    assert content.startswith("WEBVTT")


def test_clip_transcript_window():
    tr = _make_transcript()
    segs = clip_transcript(tr, start=5.0, end=15.0)
    # First segment (2-10) is partially inside, second (12-18) is fully inside
    assert len(segs) >= 1
    assert all(0.0 <= s.start for s in segs)
    assert all(s.end <= 10.0 for s in segs)
