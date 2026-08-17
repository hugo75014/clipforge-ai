"""Small, dependency-free utilities used across the monorepo."""

from __future__ import annotations

import hashlib
import re
import time
import unicodedata
import uuid
from pathlib import Path
from typing import Iterable, Optional

# =============================================================================
# Identifiers
# =============================================================================
def short_id(prefix: str = "", length: int = 12) -> str:
    """Generate a URL-safe short id like `clip_aB3xY9kP2L`."""
    raw = uuid.uuid4().hex[:length]
    return f"{prefix}{raw}" if not prefix else f"{prefix}_{raw}"


def is_uuid(value: str) -> bool:
    if not isinstance(value, str):
        return False
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError):
        return False


# =============================================================================
# Time / formatting
# =============================================================================
def format_duration(seconds: float, *, precision: int = 1) -> str:
    """`42.0` -> `00:42`, `3725.4` -> `01:02:05`."""
    if seconds is None or seconds < 0:
        return "00:00"
    seconds = float(seconds)
    hours, rem = divmod(int(seconds), 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    if precision == 0:
        return f"{minutes:02d}:{secs:02d}"
    fractional = seconds - int(seconds)
    return f"{minutes:02d}:{secs:02d}.{int(fractional * 10 ** precision):0{precision}d}"


def format_timestamp(seconds: float) -> str:
    """SRT/VTT-compatible `HH:MM:SS,mmm`."""
    if seconds is None or seconds < 0:
        seconds = 0.0
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis == 1000:
        seconds += 1
        millis = 0
    h, rem = divmod(int(seconds), 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{millis:03d}"


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


# =============================================================================
# Text
# =============================================================================
_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(text: str, *, fallback: str = "untitled", max_length: int = 80) -> str:
    """`"My Project #1!"` -> `my-project-1`."""
    if not text:
        return fallback
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = _SLUG_RE.sub("-", text).strip("-")
    if not text:
        return fallback
    return text[:max_length].rstrip("-")


_WORD_RE = re.compile(r"\w+", re.UNICODE)


def estimate_words(text: str) -> int:
    if not text:
        return 0
    return len(_WORD_RE.findall(text))


# =============================================================================
# Files
# =============================================================================
def safe_filename(name: str, *, fallback: str = "file", max_length: int = 120) -> str:
    """Strip directory parts, dangerous chars, and clamp length."""
    if not name:
        return fallback
    name = Path(name).name
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._-")
    if not name:
        return fallback
    if len(name) > max_length:
        stem, dot, ext = name.rpartition(".")
        if dot:
            keep = max(1, max_length - len(ext) - 1)
            name = stem[:keep] + "." + ext
        else:
            name = name[:max_length]
    return name or fallback


def sha256_file(path: str | Path, *, chunk_size: int = 1 << 20) -> str:
    """Stream a file and return its hex digest. Handles multi-GB files."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


# =============================================================================
# Timing
# =============================================================================
class Timer:
    """Tiny context manager for timing code blocks."""

    __slots__ = ("_start", "elapsed")

    def __init__(self) -> None:
        self._start = 0.0
        self.elapsed = 0.0

    def __enter__(self) -> "Timer":
        self._start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.elapsed = time.perf_counter() - self._start


# =============================================================================
# Batching
# =============================================================================
def chunked(iterable: Iterable, size: int):
    """Yield successive `size`-sized chunks from an iterable."""
    if size <= 0:
        raise ValueError("chunk size must be > 0")
    chunk: list = []
    for item in iterable:
        chunk.append(item)
        if len(chunk) >= size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


# =============================================================================
# Safe attribute get
# =============================================================================
def dig(payload: Optional[dict], *path, default=None):
    """`dig(d, "a", "b", "c")` -> `d["a"]["b"]["c"]` or default."""
    cur: Any = payload
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur
