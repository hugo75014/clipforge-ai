"""Tests for the AI engine (heuristic scoring)."""

from __future__ import annotations

from ai_engine.scoring import detect_clips
from shared.types import Transcript, TranscriptSegment, TranscriptWord


def _seg(start: float, end: float, text: str) -> TranscriptSegment:
    return TranscriptSegment(
        id=f"s{start}",
        start=start,
        end=end,
        text=text,
        words=[
            TranscriptWord(word=w, start=start + i * 0.2, end=start + (i + 1) * 0.2)
            for i, w in enumerate(text.split())
        ],
    )


def _tr(segs: list[TranscriptSegment]) -> Transcript:
    return Transcript(language="en", duration=max((s.end for s in segs), default=0.0), provider="test", segments=segs)


def test_detect_clips_returns_sorted_by_score():
    segs = [
        _seg(0.0, 20.0, "Stop scrolling! Here's the secret nobody tells you about the real reason behind this."),
        _seg(20.0, 40.0, "Today we will discuss a normal topic with no particular hook or punchline."),
        _seg(40.0, 60.0, "What if I told you that three simple steps could 10x your results? Try it now!"),
    ]
    tr = _tr(segs)
    clips = detect_clips(tr, target_duration=20.0, min_duration=15.0, max_duration=25.0, top_k=5)
    assert len(clips) >= 1
    # Sorted descending by overall
    for a, b in zip(clips, clips[1:]):
        assert a.scores.overall >= b.scores.overall


def test_detect_clips_respects_top_k():
    segs = [_seg(i * 20.0, (i + 1) * 20.0, f"Stop scrolling! Number {i}, the secret trick you need to know.")
            for i in range(8)]
    clips = detect_clips(_tr(segs), top_k=3)
    assert len(clips) <= 3
