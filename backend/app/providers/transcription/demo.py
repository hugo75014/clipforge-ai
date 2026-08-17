"""Demo transcription provider — returns a believable transcript.

Uses the source video's duration and a deterministic split of "fake but
realistic" speech segments. Real transcription (Whisper) is wired in
`app.providers.transcription.whisper` and selected via
`TRANSCRIPTION_PROVIDER=whisper` in .env.
"""

from __future__ import annotations

import asyncio
import hashlib
import random
from typing import Iterable

from app.providers.transcription.base import TranscriptionProvider, TranscriptionRequest
from shared.types import Transcript, TranscriptSegment, TranscriptWord


_DEMO_LINES = [
    "Welcome back to the channel, today we're going to talk about something that completely changed the way I think about this topic.",
    "Most people get this wrong, and honestly I used to get it wrong too until I discovered this one trick.",
    "Here's the thing — and this is the part nobody tells you — the real reason this works is not what you think.",
    "Let me give you an example. Imagine you've been working on this for years, and suddenly everything clicks.",
    "So the three rules I want you to remember are these. First, focus on the outcome. Second, ignore the noise. Third, ship fast.",
    "The mistake I see over and over is people waiting for the perfect moment. There is no perfect moment.",
    "If you take one thing away from this video, let it be this: clarity beats motivation every single time.",
    "The data doesn't lie. Look at the chart — the curve goes up, then it explodes. That explosion is what you want.",
    "Now here's the part where it gets interesting. I was skeptical at first, but the results speak for themselves.",
    "Stop scrolling — this is the part of the video that will save you the next six months of trial and error.",
    "And honestly, the simplest way to explain it is this: attention is the only currency that matters in 2025.",
    "If you're new here, hit subscribe. We drop two of these a week and they get sharper every time.",
    "The biggest unlock for me was realising that the audience doesn't want perfection, they want progress.",
    "So let me show you exactly how I do it, step by step, with the actual tools I use every single day.",
    "By the end of this clip you'll have a framework you can apply tonight, and that's a promise, not a hook.",
]


def _seeded_rng(audio_path: str) -> random.Random:
    seed = int(hashlib.sha256(audio_path.encode("utf-8")).hexdigest()[:8], 16)
    return random.Random(seed)


def _build_demo_transcript(audio_path: str, duration: float) -> Transcript:
    rng = _seeded_rng(audio_path)
    segments: list[TranscriptSegment] = []
    cursor = 1.0
    idx = 0
    # Choose a segment size that gives us at least 2 segments for short videos
    # and up to ~30 for long ones. Each segment is between 1.5 and 10 seconds.
    seg_dur_target = max(1.5, min(8.0, duration / 4.0))
    while cursor < max(duration - 1.0, 5.0):
        line = _rng_pick(rng, _DEMO_LINES)
        seg_dur = max(1.5, seg_dur_target + (rng.random() - 0.5) * 3.0)
        if cursor + seg_dur > duration:
            seg_dur = max(1.5, duration - cursor)
        if seg_dur < 1.5:
            break
        words = _split_words(line)
        if not words:
            break
        per = seg_dur / max(1, len(words))
        words_data: list[TranscriptWord] = []
        for i, w in enumerate(words):
            words_data.append(
                TranscriptWord(
                    word=w,
                    start=round(cursor + i * per, 3),
                    end=round(cursor + (i + 1) * per, 3),
                    confidence=round(0.85 + rng.random() * 0.14, 3),
                )
            )
        segments.append(
            TranscriptSegment(
                id=f"seg_{idx:04d}",
                start=round(cursor, 3),
                end=round(cursor + seg_dur, 3),
                text=line,
                words=words_data,
                confidence=round(0.88 + rng.random() * 0.10, 3),
            )
        )
        cursor += seg_dur + 0.2
        idx += 1

    return Transcript(
        language="en",
        duration=duration,
        provider="demo",
        segments=segments,
    )


def _rng_pick(rng: random.Random, items: list[str]) -> str:
    return items[rng.randrange(len(items))]


def _split_words(s: str) -> list[str]:
    out: list[str] = []
    cur = []
    for ch in s:
        if ch.isspace():
            if cur:
                out.append("".join(cur))
                cur = []
        else:
            cur.append(ch)
    if cur:
        out.append("".join(cur))
    return out


class DemoTranscriptionProvider:
    name = "demo"

    async def transcribe(self, request: TranscriptionRequest) -> Transcript:
        # Tiny pause to mimic API latency.
        await asyncio.sleep(0.05)
        duration = _probe_duration(request.audio_path)
        return _build_demo_transcript(request.audio_path, duration)


def _probe_duration(path: str) -> float:
    """Use ffprobe if available, otherwise fall back to 600s."""
    try:
        from video_engine.ffmpeg.probe import get_duration  # type: ignore

        # `probe` is async; get_duration is sync — call it directly.
        return get_duration(path)
    except Exception:
        return 600.0
