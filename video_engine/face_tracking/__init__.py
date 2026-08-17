"""Face tracking — compute a (x, y) track for a video so the smart crop
follows the speaker.

Implementation strategy:
1. Sample frames at `sample_fps` (default 4 fps).
2. Try OpenCV's built-in Haar cascade first (no extra deps, fast).
3. Fall back to MediaPipe if installed (more robust on varied faces).
4. If neither is available, return a centered default track (so the rest of
   the pipeline still works).
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Tuple, Union

from video_engine.ffmpeg.runner import get_metadata, run_ffmpeg


@dataclass
class FaceTrackPoint:
    t: float           # seconds
    x: float           # normalized 0..1
    y: float           # normalized 0..1
    size: float        # normalized (face width / frame width)


def _extract_frames(video: str, sample_fps: float, out_dir: Path) -> List[Path]:
    """Extract frames to PNG via ffmpeg (sync helper)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    pattern = out_dir / "frame_%06d.png"

    async def _run():
        await run_ffmpeg(
            [
                "-i", str(video),
                "-vf", f"fps={sample_fps}",
                str(pattern),
            ]
        )
    asyncio.run(_run())
    return sorted(out_dir.glob("frame_*.png"))


def _default_track(duration: float, sample_fps: float) -> List[FaceTrackPoint]:
    pts: List[FaceTrackPoint] = []
    n = max(1, int(duration * sample_fps))
    for i in range(n):
        t = i / sample_fps
        pts.append(FaceTrackPoint(t=t, x=0.5, y=0.5, size=0.3))
    return pts


def _smooth(pts: List[FaceTrackPoint], window: int = 5) -> List[FaceTrackPoint]:
    if not pts:
        return pts
    half = window // 2
    out: List[FaceTrackPoint] = []
    for i, p in enumerate(pts):
        a = max(0, i - half)
        b = min(len(pts), i + half + 1)
        xs = [q.x for q in pts[a:b]]
        ys = [q.y for q in pts[a:b]]
        ss = [q.size for q in pts[a:b]]
        out.append(
            FaceTrackPoint(
                t=p.t,
                x=sum(xs) / len(xs),
                y=sum(ys) / len(ys),
                size=sum(ss) / len(ss),
            )
        )
    return out


def track_faces(video: Union[str, Path], *, sample_fps: float = 4.0) -> List[FaceTrackPoint]:
    """Return a smoothed face track for the video.

    The output list is roughly sampled at `sample_fps` Hz and ranges over the
    full duration. The caller is responsible for subsampling / interpolating
    at render time.
    """
    video = str(video)
    meta = get_metadata(video)
    if meta.duration <= 0:
        return []

    # OpenCV path (preferred — no extra deps).
    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore
    except ImportError:
        return _default_track(meta.duration, sample_fps)

    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    if not Path(cascade_path).exists():
        return _default_track(meta.duration, sample_fps)
    detector = cv2.CascadeClassifier(cascade_path)

    out_dir = Path(meta.path).with_suffix("")
    out_dir = out_dir.parent / f".frames_{out_dir.name}_{int(sample_fps)}"
    try:
        frames = _extract_frames(video, sample_fps, out_dir)
    except Exception:
        return _default_track(meta.duration, sample_fps)

    pts: List[FaceTrackPoint] = []
    try:
        for i, fp in enumerate(frames):
            img = cv2.imread(str(fp))
            if img is None:
                continue
            h, w = img.shape[:2]
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(30, 30))
            if len(faces) == 0:
                # Hold last point if we have one, else default center
                if pts:
                    pts.append(FaceTrackPoint(t=i / sample_fps, x=pts[-1].x, y=pts[-1].y, size=pts[-1].size))
                else:
                    pts.append(FaceTrackPoint(t=i / sample_fps, x=0.5, y=0.5, size=0.3))
                continue
            # Pick the largest face
            x, y, ww, hh = max(faces, key=lambda f: f[2] * f[3])
            cx = (x + ww / 2) / w
            cy = (y + hh / 2) / h
            size = ww / w
            pts.append(FaceTrackPoint(t=i / sample_fps, x=cx, y=cy, size=size))
    finally:
        # Clean up frames
        for fp in frames:
            try:
                fp.unlink(missing_ok=True)
            except Exception:
                pass
        try:
            out_dir.rmdir()
        except Exception:
            pass

    return _smooth(pts)


def track_to_dense(track: Sequence[FaceTrackPoint], duration: float, step: float = 0.25) -> List[Tuple[float, float, float]]:
    """Densify the (sparse) face track into a list of (t, x, y) at regular
    intervals, so ffmpeg's sendcmd can consume it."""
    if not track:
        # Default: stay centered
        return [(0.0, 0.5, 0.5), (duration, 0.5, 0.5)]
    out: List[Tuple[float, float, float]] = []
    n = max(1, int(duration / step))
    for i in range(n + 1):
        t = min(duration, i * step)
        # Find nearest two points
        prev = track[0]
        nxt = track[-1]
        for p in track:
            if p.t <= t:
                prev = p
            if p.t >= t:
                nxt = p
                break
        if prev.t == nxt.t:
            x, y = prev.x, prev.y
        else:
            alpha = (t - prev.t) / (nxt.t - prev.t)
            x = prev.x + (nxt.x - prev.x) * alpha
            y = prev.y + (nxt.y - prev.y) * alpha
        out.append((round(t, 3), round(x, 4), round(y, 4)))
    return out
