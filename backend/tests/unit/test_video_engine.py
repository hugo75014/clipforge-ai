"""Tests for the video engine — check that probe works on a tiny synthetic mp4."""

from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from video_engine.ffmpeg.runner import find_ffmpeg, find_ffprobe, get_duration, get_metadata


def _ffmpeg_or_skip():
    if not (shutil.which("ffmpeg") or os.getenv("FFMPEG_PATH")):
        pytest.skip("ffmpeg not installed")


def test_ffmpeg_and_ffprobe_resolve():
    _ffmpeg_or_skip()
    assert find_ffmpeg()
    assert find_ffprobe()


def test_probe_synthetic_video(tmp_path: Path):
    _ffmpeg_or_skip()
    out = tmp_path / "tiny.mp4"
    # 1-second silent test pattern, 320x240
    cmd = [
        find_ffmpeg(),
        "-y", "-f", "lavfi", "-i", "testsrc=duration=1:size=320x240:rate=15",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
        "-c:v", "libx264", "-preset", "ultrafast", "-t", "1",
        "-c:a", "aac", "-shortest", str(out),
    ]
    res = subprocess.run(cmd, capture_output=True)
    assert res.returncode == 0, res.stderr.decode("utf-8", "replace")
    assert out.exists()
    meta = get_metadata(out)
    assert 0.8 < meta.duration < 1.5
    assert meta.width == 320
    assert meta.height == 240
    assert meta.has_audio
    # The duration reported by ffprobe is exact, so use <= for the upper bound
    assert 0.8 < get_duration(out) <= 1.5
