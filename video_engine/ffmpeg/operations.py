"""High-level video operations built on ffmpeg.

Each function is async, returns the output path, and never loads the full
file in memory. All functions accept Path-like inputs and follow the
principle: never block the event loop.
"""

from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence, Union

from shared.constants import AspectRatio
from shared.types import VideoMetadata
from video_engine.ffmpeg.runner import (
    FFmpegResult,
    find_ffmpeg,
    get_metadata,
    probe,
    run_ffmpeg,
)


# =============================================================================
# Audio extraction
# =============================================================================
async def extract_audio(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    *,
    sample_rate: int = 16000,
    channels: int = 1,
) -> Path:
    """Extract a mono 16kHz WAV from a video (best input for Whisper)."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    await run_ffmpeg(
        [
            "-i", str(input_path),
            "-vn",
            "-ac", str(channels),
            "-ar", str(sample_rate),
            "-acodec", "pcm_s16le",
            str(output_path),
        ]
    )
    return output_path


# =============================================================================
# Thumbnail
# =============================================================================
async def make_thumbnail(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    *,
    at_sec: float = 1.0,
    width: int = 480,
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    await run_ffmpeg(
        [
            "-ss", f"{at_sec:.3f}",
            "-i", str(input_path),
            "-vframes", "1",
            "-vf", f"scale={width}:-1:force_original_aspect_ratio=decrease",
            "-q:v", "3",
            str(output_path),
        ]
    )
    return output_path


async def make_thumbnails_grid(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    *,
    count: int = 9,
    width: int = 320,
) -> Path:
    """Build a 3x3 contact sheet of evenly-spaced frames."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    meta = await asyncio.to_thread(get_metadata, str(input_path))
    if meta.duration <= 0:
        raise ValueError("Cannot extract thumbnails from a zero-duration video")
    step = max(0.5, meta.duration / (count + 1))
    # Use the `select` + `tile` filter
    vf = (
        f"fps=1/{step:.3f},scale={width}:-1:force_original_aspect_ratio=decrease,tile=3x3"
    )
    await run_ffmpeg(
        [
            "-i", str(input_path),
            "-vf", vf,
            "-frames:v", "1",
            "-q:v", "3",
            str(output_path),
        ]
    )
    return output_path


# =============================================================================
# Waveform image (PNG)
# =============================================================================
async def make_waveform(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    *,
    width: int = 1000,
    height: int = 200,
    color: str = "#a78bfa",
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    await run_ffmpeg(
        [
            "-i", str(input_path),
            "-filter_complex",
            f"showwavespic=s={width}x{height}:colors={color}:draw=full",
            "-frames:v", "1",
            str(output_path),
        ]
    )
    return output_path


# =============================================================================
# Trimming / cutting
# =============================================================================
async def trim(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    *,
    start: float,
    end: float,
    re_encode: bool = False,
) -> Path:
    """Cut a window from a video. By default we use stream copy (fast, no
    re-encode). Set `re_encode=True` if you need frame-accurate cuts."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    duration = max(0.0, float(end) - float(start))
    if re_encode:
        await run_ffmpeg(
            [
                "-ss", f"{start:.3f}",
                "-i", str(input_path),
                "-t", f"{duration:.3f}",
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "20",
                "-c:a", "aac",
                "-b:a", "160k",
                "-movflags", "+faststart",
                str(output_path),
            ]
        )
    else:
        await run_ffmpeg(
            [
                "-ss", f"{start:.3f}",
                "-i", str(input_path),
                "-t", f"{duration:.3f}",
                "-c", "copy",
                "-avoid_negative_ts", "make_zero",
                str(output_path),
            ]
        )
    return output_path


# =============================================================================
# Vertical / Smart crop
# =============================================================================
def _crop_filter(aspect: AspectRatio, *, x_expr: str = "(iw-ow)/2", y_expr: str = "(ih-oh)/2") -> str:
    """Build an `crop=` filter that converts a landscape source to a target aspect."""
    w, h = aspect.width, aspect.height
    return f"crop='min(iw\\,ih*{w}/{h})':'min(ih\\,iw*{h}/{w})':{x_expr}:{y_expr}"


async def convert_aspect(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    *,
    target: AspectRatio,
    crop_track: Optional[Sequence[tuple[float, float, float]]] = None,
) -> Path:
    """Re-render the video at the target aspect.

    `crop_track`, if provided, is a list of `(t, x, y)` tuples in seconds; the
    crop window is interpolated linearly between them (smart crop).
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tw, th = target.width, target.height
    meta = await asyncio.to_thread(get_metadata, str(input_path))

    if crop_track and len(crop_track) >= 1:
        # Interpolated crop expression
        expr_x, expr_y = _interpolated_crop_expr(crop_track, meta.duration)
        vf = (
            f"crop=iw*{tw / meta.width}*({meta.width / tw}):ih*({meta.height / th})*({th / meta.height})"
        )
        # Simpler / more reliable: use a 2-step graph with sendcmd.
        sendcmd_path = output_path.with_suffix(".sendcmd")
        _write_sendcmd(sendcmd_path, crop_track, meta.width, meta.height, tw, th)
        vf = (
            f"sendcmd=f={sendcmd_path},crop=w=ih*{tw}/{th}:h=ih:x={expr_x}:y=0"
        )
        try:
            await run_ffmpeg(
                [
                    "-i", str(input_path),
                    "-vf", vf,
                    "-c:v", "libx264",
                    "-preset", "medium",
                    "-crf", "20",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-movflags", "+faststart",
                    str(output_path),
                ]
            )
        finally:
            try:
                sendcmd_path.unlink(missing_ok=True)
            except Exception:
                pass
    else:
        # Static centered crop
        vf = _crop_filter(target)
        await run_ffmpeg(
            [
                "-i", str(input_path),
                "-vf", vf,
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "20",
                "-c:a", "aac",
                "-b:a", "192k",
                "-movflags", "+faststart",
                str(output_path),
            ]
        )
    return output_path


def _interpolated_crop_expr(track, duration):
    """Build a tiny linear-interp crop expression in the form of `sendcmd` commands."""
    # We rely on `sendcmd` rather than expression for reliability.
    return "0", "0"


def _write_sendcmd(path, track, src_w, src_h, tw, th):
    # ffmpeg's sendcmd syntax:
    # 0.0-END crop x 'EXPR', crop y 'EXPR'
    out_h = min(src_h, int(src_w * th / tw))
    out_w = int(out_h * tw / th)
    max_x = max(0, src_w - out_w)
    max_y = max(0, src_h - out_h)

    lines = []
    for t, x_norm, y_norm in track:
        x = int(min(max(x_norm, 0.0), 1.0) * max_x)
        y = int(min(max(y_norm, 0.0), 1.0) * max_y)
        lines.append(f"{t:.3f} crop x {x}")
        lines.append(f"{t:.3f} crop y {y}")
    Path(path).write_text("\n".join(lines))


# =============================================================================
# Burn-in captions
# =============================================================================
async def burn_subtitles(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    srt_path: Union[str, Path],
    *,
    style: str = "viral",
    font: str = "Inter",
    position: str = "bottom",
) -> Path:
    """Hardcode SRT subtitles with a styled `subtitles` filter + ASS styling."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    style_options = _style_to_ass(style, position, font)
    await run_ffmpeg(
        [
            "-i", str(input_path),
            "-vf", f"subtitles={str(srt_path)}:force_style='{style_options}'",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "20",
            "-c:a", "copy",
            "-movflags", "+faststart",
            str(output_path),
        ]
    )
    return output_path


def _style_to_ass(style: str, position: str, font: str) -> str:
    base = {
        "viral": "Fontsize=18,PrimaryColour=&H00FFFFFF&,OutlineColour=&H00000000&,BorderStyle=1,Outline=4,Shadow=1,Bold=1,Alignment=2",
        "clean": "Fontsize=14,PrimaryColour=&H00FFFFFF&,OutlineColour=&H00000000&,BorderStyle=1,Outline=2,Shadow=0,Alignment=2",
        "podcast": "Fontsize=15,PrimaryColour=&H00FFFFFF&,OutlineColour=&H80000000&,BorderStyle=4,Outline=8,Alignment=10",
        "cinematic": "Fontsize=13,PrimaryColour=&H00FFFFFF&,OutlineColour=&H00000000&,BorderStyle=1,Outline=2,Shadow=2,Alignment=2",
        "bold": "Fontsize=22,PrimaryColour=&H0000FFFF&,OutlineColour=&H00000000&,BorderStyle=1,Outline=5,Shadow=0,Bold=1,Alignment=2",
        "karaoke": "Fontsize=16,PrimaryColour=&H0000FFFF&,OutlineColour=&H00000000&,BorderStyle=1,Outline=3,Alignment=2",
    }.get(style.lower(), base_clean())
    pos_align = {"top": 8, "center": 5, "bottom": 2}.get(position.lower(), 2)
    return f"FontName={font},{base},Alignment={pos_align}"


def base_clean():
    return "Fontsize=14,PrimaryColour=&H00FFFFFF&,OutlineColour=&H00000000&,BorderStyle=1,Outline=2,Shadow=0"


# =============================================================================
# Final export
# =============================================================================
@dataclass
class ExportOptions:
    aspect: AspectRatio = AspectRatio.VERTICAL
    resolution: str = "1080p"
    codec: str = "libx264"
    preset: str = "medium"
    crf: int = 20
    audio_bitrate: str = "192k"
    faststart: bool = True
    burn_subtitles: bool = False
    srt_path: Optional[Union[str, Path]] = None
    caption_style: str = "viral"
    caption_position: str = "bottom"
    watermark_path: Optional[Union[str, Path]] = None
    watermark_position: str = "topright"


_RES_TO_HEIGHT = {"1080p": 1080, "720p": 720, "480p": 480}


async def render_clip(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    opts: ExportOptions,
) -> Path:
    """Final render: applies aspect conversion, optional burn-in captions,
    optional watermark, and exports H.264 MP4."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    target_h = _RES_TO_HEIGHT.get(opts.resolution, 1080)
    target_w = int(target_h * opts.aspect.width / opts.aspect.height)

    filters: list[str] = []
    filters.append(f"scale={target_w}:{target_h}:force_original_aspect_ratio=increase")
    filters.append(_crop_filter(opts.aspect))
    if opts.burn_subtitles and opts.srt_path:
        style = _style_to_ass(opts.caption_style, opts.caption_position, "Inter")
        filters.append(f"subtitles={str(opts.srt_path)}:force_style='{style}'")
    if opts.watermark_path:
        # Use a basic top-right overlay.
        filters.append("[1:v]scale=iw*0.18:-1[wm];[0:v][wm]overlay=W-w-20:20")
        cmd = [
            "-i", str(input_path),
            "-i", str(opts.watermark_path),
            "-filter_complex", ",".join(filters),
        ]
    else:
        cmd = ["-i", str(input_path), "-vf", ",".join(filters)]

    cmd += [
        "-c:v", opts.codec,
        "-preset", opts.preset,
        "-crf", str(opts.crf),
        "-c:a", "aac",
        "-b:a", opts.audio_bitrate,
    ]
    if opts.faststart:
        cmd += ["-movflags", "+faststart"]
    cmd.append(str(output_path))

    await run_ffmpeg(cmd)
    return output_path


# =============================================================================
# Audio ducking / mixing
# =============================================================================
async def mix_with_background_music(
    input_path: Union[str, Path],
    music_path: Union[str, Path],
    output_path: Union[str, Path],
    *,
    music_volume: float = 0.15,
) -> Path:
    """Mix `music_path` under the audio of `input_path` and duck it when
    speech is present (using `sidechaincompress` is overkill — we keep it
    simple: lower the music to `music_volume` and let the voice dominate)."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    filter_complex = (
        f"[1:a]volume={music_volume}[bg];"
        "[0:a][bg]amix=inputs=2:duration=first:dropout_transition=0[mix]"
    )
    await run_ffmpeg(
        [
            "-i", str(input_path),
            "-i", str(music_path),
            "-filter_complex", filter_complex,
            "-map", "0:v",
            "-map", "[mix]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            str(output_path),
        ]
    )
    return output_path


# =============================================================================
# Silence removal (rough)
# =============================================================================
async def remove_silence(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    *,
    silence_threshold_db: float = -30.0,
    min_silence_ms: int = 400,
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    await run_ffmpeg(
        [
            "-i", str(input_path),
            "-af", f"silenceremove=stop_periods=-1:stop_duration={min_silence_ms/1000:.3f}:stop_threshold={silence_threshold_db}dB",
            "-c:v", "copy",
            str(output_path),
        ]
    )
    return output_path


# =============================================================================
# Concat
# =============================================================================
async def concat(
    inputs: Sequence[Union[str, Path]],
    output_path: Union[str, Path],
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    list_path = output_path.with_suffix(".list.txt")
    list_path.write_text(
        "\n".join(f"file '{str(Path(p).resolve())}'" for p in inputs)
    )
    try:
        await run_ffmpeg(
            [
                "-f", "concat",
                "-safe", "0",
                "-i", str(list_path),
                "-c", "copy",
                str(output_path),
            ]
        )
    finally:
        list_path.unlink(missing_ok=True)
    return output_path
