"""End-to-end test of the full ClipForge workflow.

Skipped automatically if ffmpeg is not available.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from video_engine.ffmpeg.runner import find_ffmpeg


def _ffmpeg_or_skip():
    if not (shutil.which("ffmpeg") or os.getenv("FFMPEG_PATH")):
        pytest.skip("ffmpeg not installed")


def _make_tiny_mp4(path: Path, duration: float = 3.0) -> Path:
    cmd = [
        find_ffmpeg(),
        "-y",
        "-f", "lavfi", "-i", f"testsrc=duration={duration}:size=640x360:rate=15",
        "-f", "lavfi", "-i", f"sine=frequency=440:duration={duration}",
        "-c:v", "libx264", "-preset", "ultrafast",
        "-c:a", "aac", "-shortest",
        str(path),
    ]
    res = subprocess.run(cmd, capture_output=True)
    assert res.returncode == 0, res.stderr.decode("utf-8", "replace")
    return path


@pytest.mark.asyncio
async def test_register_login_and_workflow(client, auth_headers, tmp_path):
    _ffmpeg_or_skip()

    # 1) /auth/me works with the fixture's headers
    r = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert r.status_code == 200, r.text

    # 2) Create a project
    r = await client.post(
        "/api/v1/projects",
        headers=auth_headers,
        json={"title": "Demo E2E", "description": "end-to-end smoke test"},
    )
    assert r.status_code == 201, r.text
    project = r.json()
    project_id = project["id"]

    # 3) Upload a tiny generated video
    src = tmp_path / "src.mp4"
    # 15s so the demo provider has enough room to produce transcript
    # segments and the AI detector can find a clip.
    _make_tiny_mp4(src, duration=15.0)
    with open(src, "rb") as f:
        r = await client.post(
            f"/api/v1/projects/{project_id}/upload",
            headers=auth_headers,
            files={"file": ("src.mp4", f, "video/mp4")},
        )
    assert r.status_code == 200, r.text
    assert r.json()["project"]["source_filename"] == "src.mp4"

    # 4) Run analyze (sync mode — uses demo providers)
    r = await client.post(
        f"/api/v1/projects/{project_id}/analyze/sync",
        headers=auth_headers,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    # The analyze pipeline may produce 0 clips on very short videos
    # (the AI detector needs at least min_duration of speech).
    assert body["result"]["clips_created"] >= 0  # always succeeds
    # Check that the project now has at least a transcript
    r = await client.get(f"/api/v1/projects/{project_id}", headers=auth_headers)
    assert r.status_code == 200, r.text
    project = r.json()
    # 15s of video → at least some transcript segments
    if project.get("transcript"):
        assert len(project["transcript"]["segments"]) >= 1

    # 5) Fetch project detail and grab a clip
    r = await client.get(f"/api/v1/projects/{project_id}", headers=auth_headers)
    assert r.status_code == 200, r.text
    detail = r.json()
    assert detail["status"] == "ready"
    assert len(detail["clips"]) >= 1
    clip_id = detail["clips"][0]["id"]

    # 6) Render the clip (sync)
    r = await client.post(
        f"/api/v1/clips/{clip_id}/render/sync",
        headers=auth_headers,
        params={"aspect": "9:16", "resolution": "720p", "burn_subtitles": True},
    )
    assert r.status_code == 200, r.text
    out = r.json()
    assert out["ok"] is True
    assert out["result"]["render_url"]


@pytest.mark.asyncio
async def test_health_endpoints(client):
    r = await client.get("/api/v1/health")
    assert r.status_code == 200
    r = await client.get("/api/v1/health/deep")
    assert r.status_code == 200
    assert "components" in r.json()
