"""Heuristic scoring of transcript segments.

We score every segment (and combinations of 1-3 consecutive segments) on
seven axes: hook, emotion, information, story, curiosity, shareability,
completion. Each axis returns 0-100. The final viral score is a weighted
average (see `shared.types.ClipScores.overall`).

The scorer is fully deterministic and runs without any external LLM — it's
the "always works" layer. The LLM provider adds a second pass on top
(re-ranking + titles/hooks/hashtags) but the engine is functional with
just heuristics.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List, Sequence

from shared.constants import (
    DEFAULT_CLIP_MAX_DURATION_SEC,
    DEFAULT_CLIP_MIN_DURATION_SEC,
    DEFAULT_CLIP_TARGET_DURATION_SEC,
    DEFAULT_CONTEXT_PADDING_SEC,
    STRONG_CLIP_VIRAL_SCORE,
)
from shared.types import ClipScores, DetectedClip, Transcript, TranscriptSegment
from shared.utils import estimate_words


# =============================================================================
# Lexicons (small, additive — keep them modest so this stays deterministic)
# =============================================================================
HOOK_PATTERNS = [
    r"^(stop scrolling|wait|listen|here's (?:the|why)|imagine|what if|you (?:won't|will) believe|the truth|everyone is wrong|nobody tells you|the (real|actual) reason)",
    r"\?$",
    r"!$",
]

EMOTION_WORDS = {
    "love", "hate", "fear", "amazing", "shocking", "incredible", "terrible",
    "beautiful", "destroyed", "ruined", "saved", "lost", "won", "die", "kill",
    "cry", "laugh", "secret", "shocked", "heart", "soul", "regret", "hope",
}

CURIOSITY_WORDS = {
    "why", "how", "what", "secret", "trick", "reason", "discover",
    "nobody", "no one", "the truth", "actually", "really", "hidden",
}

STORY_MARKERS = {
    "then", "after", "before", "when i", "i was", "we were", "suddenly",
    "finally", "eventually", "remember", "years ago", "last week",
}

INFORMATION_MARKERS = {
    "step", "first", "second", "third", "rule", "tip", "because",
    "study", "research", "data", "percent", "%", "according to",
}

POWER_WORDS = {
    "free", "instantly", "today", "now", "easy", "simple", "proven",
    "guaranteed", "results", "fast", "best", "worst", "must",
}

NUMERIC_RE = re.compile(r"\b\d+(?:[.,]\d+)?%?\b")
QUESTION_RE = re.compile(r"\?\s*$")
EXCLAM_RE = re.compile(r"!\s*$")
SECOND_PERSON_RE = re.compile(r"\b(you|your|you're|you've|you'll)\b", re.IGNORECASE)


# =============================================================================
# Per-axis scorers (each returns 0-100)
# =============================================================================
def score_hook(text: str) -> float:
    if not text:
        return 0.0
    s = text.lower().strip()
    score = 30.0
    if any(re.search(p, s) for p in HOOK_PATTERNS):
        score += 40
    if QUESTION_RE.search(text):
        score += 15
    if EXCLAM_RE.search(text):
        score += 8
    if SECOND_PERSON_RE.search(text):
        score += 8
    if any(w in s for w in POWER_WORDS):
        score += 5
    if len(text.split()) <= 18:
        score += 6
    return min(100.0, score)


def score_emotion(text: str) -> float:
    if not text:
        return 0.0
    words = set(re.findall(r"\w+", text.lower()))
    hits = len(words & EMOTION_WORDS)
    return min(100.0, 30.0 + hits * 18)


def score_curiosity(text: str) -> float:
    if not text:
        return 0.0
    s = text.lower()
    hits = sum(1 for w in CURIOSITY_WORDS if w in s)
    if QUESTION_RE.search(text):
        hits += 1
    return min(100.0, 35.0 + hits * 16)


def score_story(text: str) -> float:
    if not text:
        return 0.0
    s = text.lower()
    hits = sum(1 for w in STORY_MARKERS if w in s)
    return min(100.0, 25.0 + hits * 15)


def score_information(text: str) -> float:
    if not text:
        return 0.0
    s = text.lower()
    hits = sum(1 for w in INFORMATION_MARKERS if w in s)
    nums = len(NUMERIC_RE.findall(text))
    return min(100.0, 25.0 + hits * 12 + nums * 8)


def score_shareability(text: str) -> float:
    if not text:
        return 0.0
    s = text.lower()
    score = 35.0
    score += min(20.0, sum(1 for w in POWER_WORDS if w in s) * 6)
    if SECOND_PERSON_RE.search(text):
        score += 8
    if NUMERIC_RE.search(text):
        score += 8
    if 8 <= estimate_words(text) <= 30:
        score += 10
    return min(100.0, score)


def score_completion(text: str, duration: float) -> float:
    """Likelihood the viewer watches to the end.

    Shorter + emotionally charged + question-led = high completion."""
    if not text:
        return 0.0
    base = 70.0
    if duration <= 25:
        base += 15
    elif duration <= 45:
        base += 8
    elif duration >= 90:
        base -= 15
    if QUESTION_RE.search(text):
        base += 8
    if any(re.search(p, text.lower()) for p in HOOK_PATTERNS):
        base += 6
    return max(0.0, min(100.0, base))


# =============================================================================
# Sliding-window detection
# =============================================================================
@dataclass
class _Window:
    segments: List[TranscriptSegment]
    text: str
    start: float
    end: float


def _build_windows(
    segments: Sequence[TranscriptSegment],
    *,
    target_duration: float = DEFAULT_CLIP_TARGET_DURATION_SEC,
    min_duration: float = DEFAULT_CLIP_MIN_DURATION_SEC,
    max_duration: float = DEFAULT_CLIP_MAX_DURATION_SEC,
    max_segments: int = 4,
) -> Iterable[_Window]:
    if not segments:
        return
    # Greedy packer: start a new window whenever adding the next segment
    # would exceed max_duration.
    windows: List[_Window] = []
    cur: List[TranscriptSegment] = []
    cur_start = segments[0].start
    for seg in segments:
        prospective_end = seg.end
        if not cur:
            cur = [seg]
            cur_start = seg.start
            continue
        prospective_dur = prospective_end - cur_start
        if prospective_dur > max_duration or len(cur) >= max_segments:
            windows.append(_Window(segments=cur, text=" ".join(s.text for s in cur), start=cur_start, end=cur[-1].end))
            cur = [seg]
            cur_start = seg.start
        else:
            cur.append(seg)
    if cur:
        windows.append(_Window(segments=cur, text=" ".join(s.text for s in cur), start=cur_start, end=cur[-1].end))

    # Drop too-short windows (they'll be merged with neighbours later)
    for w in windows:
        if (w.end - w.start) < min_duration:
            continue
        yield w


def _pad_window(
    w: _Window,
    segments: Sequence[TranscriptSegment],
    padding: float = DEFAULT_CONTEXT_PADDING_SEC,
) -> _Window:
    start = max(0.0, w.start - padding)
    end = w.end + padding
    # Snap to segment boundaries if close
    for seg in segments:
        if abs(seg.start - start) < 0.4:
            start = seg.start
        if abs(seg.end - end) < 0.4:
            end = seg.end
    return _Window(segments=w.segments, text=w.text, start=start, end=end)


def _title_for(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return "Untitled moment"
    # First sentence, capped
    first = re.split(r"(?<=[.!?])\s", text, maxsplit=1)[0]
    first = first.strip().rstrip(".!?")
    words = first.split()
    if len(words) > 9:
        first = " ".join(words[:9]) + "…"
    return first[:80] or "Untitled moment"


def _hook_for(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""
    return text.split(".")[0][:140]


def _hashtags_for(text: str) -> List[str]:
    base = ["#shorts", "#viral", "#clipforge"]
    # Crude keyword extraction — take the most "interesting" nouns via caps ratio
    words = re.findall(r"\b[A-Za-z][A-Za-z\-]{3,}\b", text)
    seen: set[str] = set()
    out: List[str] = []
    for w in words:
        wl = w.lower()
        if wl in seen:
            continue
        if wl in {"this", "that", "with", "from", "have", "your", "what", "when", "they", "them"}:
            continue
        seen.add(wl)
        out.append(f"#{wl}")
        if len(out) >= 6:
            break
    return base + out


def detect_clips(
    transcript: Transcript,
    *,
    target_duration: float = DEFAULT_CLIP_TARGET_DURATION_SEC,
    min_duration: float = DEFAULT_CLIP_MIN_DURATION_SEC,
    max_duration: float = DEFAULT_CLIP_MAX_DURATION_SEC,
    top_k: int = 10,
    min_score: float = 0.0,
) -> List[DetectedClip]:
    """Detect candidate clips using deterministic heuristics."""
    windows = list(_build_windows(
        transcript.segments,
        target_duration=target_duration,
        min_duration=min_duration,
        max_duration=max_duration,
    ))
    candidates: List[DetectedClip] = []
    for w in windows:
        w = _pad_window(w, transcript.segments)
        duration = w.end - w.start
        if duration < min_duration:
            continue
        scores = ClipScores(
            hook=round(score_hook(w.text), 1),
            emotion=round(score_emotion(w.text), 1),
            information=round(score_information(w.text), 1),
            story=round(score_story(w.text), 1),
            curiosity=round(score_curiosity(w.text), 1),
            shareability=round(score_shareability(w.text), 1),
            completion=round(score_completion(w.text, duration), 1),
        )
        overall = scores.overall
        if overall < min_score:
            continue
        candidates.append(
            DetectedClip(
                start=round(w.start, 2),
                end=round(w.end, 2),
                title=_title_for(w.text),
                hook=_hook_for(w.text),
                description=("AI-detected moment — high hook strength and emotional contrast."),
                hashtags=_hashtags_for(w.text),
                scores=scores,
                transcript=w.text,
                reason="Heuristic scoring on hook, emotion, curiosity, shareability.",
                keywords=re.findall(r"\b[A-Za-z][A-Za-z\-]{4,}\b", w.text)[:6],
            )
        )

    candidates.sort(key=lambda c: c.scores.overall, reverse=True)

    # Suppress overlapping windows (greedy NMS by score)
    kept: List[DetectedClip] = []
    for c in candidates:
        if any(_overlaps(c, k) for k in kept):
            continue
        kept.append(c)
        if len(kept) >= top_k:
            break
    return kept


def _overlaps(a: DetectedClip, b: DetectedClip) -> bool:
    inter = max(0.0, min(a.end, b.end) - max(a.start, b.start))
    smaller = min(a.duration, b.duration)
    return smaller > 0 and (inter / smaller) > 0.5
