"""Thin async wrapper around the ffmpeg / ffprobe CLI."""

from __future__ import annotations

import asyncio
import json
import os
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping, Optional, Sequence, Union

from shared.types import VideoMetadata


# =============================================================================
# Discovery
# =============================================================================
def find_ffmpeg() -> str:
    """Locate the ffmpeg binary. Honours `FFMPEG_PATH` env, then PATH."""
    override = os.getenv("FFMPEG_PATH")
    if override and os.path.isfile(override) and os.access(override, os.X_OK):
        return override
    found = shutil.which("ffmpeg")
    if not found:
        raise RuntimeError(
            "ffmpeg binary not found. Install it (https://ffmpeg.org/download.html) "
            "or set FFMPEG_PATH."
        )
    return found


def find_ffprobe() -> str:
    override = os.getenv("FFPROBE_PATH")
    if override and os.path.isfile(override) and os.access(override, os.X_OK):
        return override
    found = shutil.which("ffprobe")
    if not found:
        raise RuntimeError("ffprobe binary not found. Install ffmpeg/ffprobe.")
    return found


# =============================================================================
# Run
# =============================================================================
@dataclass
class FFmpegResult:
    returncode: int
    stdout: str
    stderr: str
    cmd: list[str] = field(default_factory=list)
    duration_sec: float = 0.0


async def run_ffmpeg(
    args: Sequence[Union[str, Path]],
    *,
    input_data: Optional[bytes] = None,
    timeout: Optional[float] = None,
    env: Optional[Mapping[str, str]] = None,
    cwd: Optional[Union[str, Path]] = None,
    log_stderr: bool = False,
) -> FFmpegResult:
    """Run ffmpeg asynchronously. Returns parsed result."""
    ffmpeg = find_ffmpeg()
    cmd = [str(ffmpeg), "-y", *[str(a) for a in args]]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE if input_data else None,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env={**os.environ, **(env or {})},
        cwd=str(cwd) if cwd else None,
    )
    try:
        stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(input_data), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise

    stdout = stdout_b.decode("utf-8", "replace")
    stderr = stderr_b.decode("utf-8", "replace")
    if log_stderr and stderr:
        sys.stderr.write(f"[ffmpeg] {stderr[-2000:]}\n")

    # Parse "time=HH:MM:SS.xx" from progress if available
    duration = _parse_last_time(stderr)

    return FFmpegResult(
        returncode=proc.returncode or 0,
        stdout=stdout,
        stderr=stderr,
        cmd=cmd,
        duration_sec=duration,
    )


def run_ffmpeg_sync(args: Sequence[Union[str, Path]], **kwargs) -> FFmpegResult:
    return asyncio.run(run_ffmpeg(args, **kwargs))


# =============================================================================
# Probe
# =============================================================================
async def probe(path: Union[str, Path]) -> dict:
    ffprobe = find_ffprobe()
    cmd = [
        ffprobe,
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out_b, err_b = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {err_b.decode('utf-8', 'replace')[:500]}")
    return json.loads(out_b.decode("utf-8") or "{}")


def get_metadata(path: Union[str, Path]) -> VideoMetadata:
    """Sync helper, safe to call from anywhere.

    If we're already in a running event loop, offload the probe to a
    dedicated thread and bridge back to the loop to await it.
    """
    data = _run_probe_sync(path)
    fmt = data.get("format", {})
    streams = data.get("streams", [])
    v_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
    a_stream = next((s for s in streams if s.get("codec_type") == "audio"), {})

    fps = 0.0
    if v_stream.get("avg_frame_rate"):
        try:
            num, den = v_stream["avg_frame_rate"].split("/")
            fps = float(num) / float(den) if float(den) else 0.0
        except (ValueError, ZeroDivisionError):
            fps = 0.0

    duration = float(fmt.get("duration", 0.0) or 0.0)
    size = int(fmt.get("size", 0) or 0)
    bitrate = int(fmt.get("bit_rate", 0) or 0) or None

    return VideoMetadata(
        path=str(path),
        duration=duration,
        width=int(v_stream.get("width", 0) or 0),
        height=int(v_stream.get("height", 0) or 0),
        fps=fps,
        codec=v_stream.get("codec_name", "") or "",
        bitrate=bitrate,
        has_audio=bool(a_stream),
        size_bytes=size,
    )


def get_duration(path: Union[str, Path]) -> float:
    return get_metadata(path).duration


def _run_probe_sync(path):
    """Run the async `probe` from a sync context, even when there's a running loop."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        # No running loop — asyncio.run() is safe.
        return asyncio.run(probe(path))

    # There's a running loop. Run probe in a worker thread + bridge.
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        future = ex.submit(lambda: asyncio.run(probe(path)))
        return future.result()


# =============================================================================
# Internal helpers
# =============================================================================
import re

_TIME_RE = re.compile(r"time=(\d+):(\d+):(\d+\.?\d*)")


def _parse_last_time(stderr: str) -> float:
    m = None
    for line in stderr.splitlines():
        found = _TIME_RE.search(line)
        if found:
            m = found
    if not m:
        return 0.0
    h, mn, s = m.groups()
    return int(h) * 3600 + int(mn) * 60 + float(s)
