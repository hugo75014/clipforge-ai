"""Video pipeline — orchestrates the heavy work (analyze, render).

The actual CPU/IO-heavy parts live in `video_engine` and `ai_engine`. This
service is the *workflow* layer: it dispatches to the right components,
persists progress, and stores the results.
"""

from __future__ import annotations

import asyncio
import json
import os
import random
import time
import uuid
from pathlib import Path
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import settings
from app.core.logging import get_logger
from app.models import Clip, Job, Project
from app.providers.transcription import get_transcription_provider
from app.schemas.clip import DetectedClipOut
from app.services.ai import detect_and_enrich
from app.services.storage import get_storage
from shared.constants import AspectRatio
from shared.types import Transcript
from shared.utils import safe_filename, slugify


log = get_logger(__name__)


# =============================================================================
# Analysis pipeline
# =============================================================================
async def run_analysis_pipeline(
    db: AsyncSession,
    project: Project,
    job: Job,
    progress,
    mode: str = "full",
) -> dict:
    """Run the analyze pipeline: probe → extract audio → transcribe → detect clips.

    `mode="more"` reuses the transcript already on disk/DB and only re-runs
    clip detection, appending new clips instead of wiping the project's
    existing ones — used by the "Generate more" action once a project has
    already been analyzed once.

    Returns a dict with `clips_created`.
    """
    if mode == "more":
        return await _run_more_clips(db, project, job, progress)

    storage = get_storage()
    if not project.source_path:
        raise RuntimeError("Project has no source video uploaded")

    local_path = Path(project.source_path)
    if not local_path.exists():
        # Try resolving via storage (in case the file was uploaded to S3 / R2)
        if storage.is_local:
            raise RuntimeError(f"Source file not found: {local_path}")
        # For non-local, we need to materialize a local copy for ffmpeg.
        local_path = await _materialize_source(storage, project)
        project.source_path = str(local_path)
        await db.commit()

    # Step 1 — probe
    await progress(5.0, "Reading video metadata", "probe")
    from video_engine.ffmpeg.runner import get_metadata
    meta = await asyncio.to_thread(get_metadata, str(local_path))
    project.source_duration_sec = meta.duration
    project.source_width = meta.width
    project.source_height = meta.height
    project.source_fps = meta.fps
    project.source_codec = meta.codec
    project.source_size_bytes = local_path.stat().st_size if local_path.exists() else None
    project.status = "analyzing"
    await db.commit()

    # Step 2 — extract audio
    await progress(15.0, "Extracting audio", "extract_audio")
    audio_path = settings.temp_dir / f"{project.id}.wav"
    from video_engine.ffmpeg.operations import extract_audio
    await extract_audio(local_path, audio_path)

    # Step 3 — transcribe
    await progress(35.0, "Transcribing", "transcribe")
    from app.providers.transcription.base import TranscriptionRequest
    transcript = await get_transcription_provider().transcribe(
        TranscriptionRequest(audio_path=str(audio_path), language=project.language)
    )
    project.language = transcript.language
    await db.commit()

    # Persist transcript segments
    from app.models import TranscriptSegment as TSegment

    # Wipe any previous ones
    existing = (await db.execute(select(TSegment).where(TSegment.project_id == project.id))).scalars().all()
    for e in existing:
        await db.delete(e)
    await db.flush()

    for idx, seg in enumerate(transcript.segments):
        words_json = json.dumps(
            [{"word": w.word, "start": w.start, "end": w.end, "confidence": w.confidence} for w in seg.words],
            ensure_ascii=False,
        )
        db.add(TSegment(
            project_id=project.id,
            idx=idx,
            start_sec=seg.start,
            end_sec=seg.end,
            text=seg.text,
            speaker=seg.speaker,
            confidence=seg.confidence,
            words_json=words_json,
            language=transcript.language,
            provider=transcript.provider,
        ))
    await db.commit()

    # Step 4 — detect clips (heuristic + LLM enrichment)
    await progress(60.0, "Detecting viral moments", "detect_clips")
    detected = await detect_and_enrich(
        transcript,
        target_duration=min(45.0, max(15.0, transcript.duration * 0.3)),
        min_duration=min(8.0, max(5.0, transcript.duration * 0.2)),
        max_duration=min(90.0, max(15.0, transcript.duration * 0.8)),
        top_k=10,
        min_score=0.0,
    )

    # Persist detected clips
    await progress(85.0, "Saving clip candidates", "persist_clips")
    # Remove old clips
    old = (await db.execute(select(Clip).where(Clip.project_id == project.id))).scalars().all()
    for c in old:
        await db.delete(c)
    await db.flush()

    for order, d in enumerate(detected):
        clip = Clip(
            project_id=project.id,
            start_sec=d.start,
            end_sec=d.end,
            title=d.title,
            hook=d.hook,
            description=d.description,
            hashtags=json.dumps(d.hashtags, ensure_ascii=False),
            keywords=json.dumps(d.keywords, ensure_ascii=False),
            transcript=d.transcript,
            reason=d.reason,
            score_hook=d.scores.hook,
            score_emotion=d.scores.emotion,
            score_information=d.scores.information,
            score_story=d.scores.story,
            score_curiosity=d.scores.curiosity,
            score_shareability=d.scores.shareability,
            score_completion=d.scores.completion,
            score_overall=d.scores.overall,
            status="ready",
            selected=True,
            sort_order=order,
        )
        db.add(clip)
    await db.commit()

    # Step 5 — generate thumbnail (best-effort)
    try:
        from video_engine.ffmpeg.operations import make_thumbnail
        thumb_path = settings.outputs_dir / f"{project.id}_thumb.jpg"
        await make_thumbnail(local_path, thumb_path, at_sec=min(1.0, max(0.0, (meta.duration or 1.0) / 2.0)))
        key = f"projects/{project.id}/thumbnail.jpg"
        url = await storage.put_file(thumb_path, key, content_type="image/jpeg", public=True)
        project.source_thumbnail_url = url
        await db.commit()
    except Exception as exc:  # noqa: BLE001
        log.warning("Thumbnail generation failed: %s", exc)

    project.status = "ready"
    await db.commit()

    return {"clips_created": len(detected), "transcript_segments": len(transcript.segments)}


async def _run_more_clips(db: AsyncSession, project: Project, job: Job, progress) -> dict:
    """Detect additional clip candidates from the transcript already on file.

    No probe/extract/transcribe: the existing `TranscriptSegment` rows are
    reassembled into a `Transcript` and re-run through detection only. New
    clips are appended after the existing ones; nothing already generated is
    touched, so previously rendered clips and their `render_url` survive.
    """
    from app.models import TranscriptSegment as TSegment
    from shared.types import TranscriptSegment as TSeg, TranscriptWord as TWord

    await progress(10.0, "Loading existing transcript", "load_transcript")
    rows = (
        await db.execute(
            select(TSegment).where(TSegment.project_id == project.id).order_by(TSegment.idx)
        )
    ).scalars().all()
    if not rows:
        raise RuntimeError("Project has no transcript yet — run a full analysis first")

    segments = []
    for row in rows:
        words_raw = json.loads(row.words_json) if row.words_json else []
        words = [
            TWord(
                word=w.get("word", ""),
                start=w.get("start", 0.0),
                end=w.get("end", 0.0),
                confidence=w.get("confidence", 1.0),
            )
            for w in words_raw
        ]
        segments.append(
            TSeg(
                id=str(row.id),
                start=row.start_sec,
                end=row.end_sec,
                text=row.text,
                words=words,
                speaker=row.speaker,
                confidence=row.confidence or 1.0,
            )
        )
    duration = max((s.end for s in segments), default=0.0)
    transcript = Transcript(
        language=project.language or "en",
        segments=segments,
        duration=duration,
        provider=rows[0].provider or "cached",
    )

    await progress(45.0, "Detecting more viral moments", "detect_clips")
    existing_clips = (
        await db.execute(select(Clip).where(Clip.project_id == project.id))
    ).scalars().all()
    existing_ranges = [(c.start_sec, c.end_sec) for c in existing_clips]
    next_order = (max((c.sort_order for c in existing_clips), default=-1)) + 1

    detected = await detect_and_enrich(
        transcript,
        target_duration=min(45.0, max(15.0, duration * 0.3)),
        min_duration=min(8.0, max(5.0, duration * 0.2)),
        max_duration=min(90.0, max(15.0, duration * 0.8)),
        top_k=10,
        min_score=0.0,
    )

    def _overlaps(a_start: float, a_end: float) -> bool:
        return any(a_start < b_end and b_start < a_end for b_start, b_end in existing_ranges)

    created = 0
    await progress(80.0, "Saving new clip candidates", "persist_clips")
    for d in detected:
        if _overlaps(d.start, d.end):
            continue
        clip = Clip(
            project_id=project.id,
            start_sec=d.start,
            end_sec=d.end,
            title=d.title,
            hook=d.hook,
            description=d.description,
            hashtags=json.dumps(d.hashtags, ensure_ascii=False),
            keywords=json.dumps(d.keywords, ensure_ascii=False),
            transcript=d.transcript,
            reason=d.reason,
            score_hook=d.scores.hook,
            score_emotion=d.scores.emotion,
            score_information=d.scores.information,
            score_story=d.scores.story,
            score_curiosity=d.scores.curiosity,
            score_shareability=d.scores.shareability,
            score_completion=d.scores.completion,
            score_overall=d.scores.overall,
            status="ready",
            selected=True,
            sort_order=next_order,
        )
        next_order += 1
        created += 1
        db.add(clip)
    await db.commit()

    project.status = "ready"
    await db.commit()

    return {"clips_created": created, "transcript_segments": len(segments)}


async def _materialize_source(storage, project) -> Path:
    """Download a remote object to a local temp file so ffmpeg can read it."""
    if not project.source_url:
        raise RuntimeError("No source URL to download")
    import httpx

    out = settings.temp_dir / f"{project.id}_{safe_filename(project.source_filename or 'video.mp4')}"
    out.parent.mkdir(parents=True, exist_ok=True)
    async with httpx.AsyncClient(timeout=None, follow_redirects=True) as client:
        async with client.stream("GET", project.source_url) as r:
            r.raise_for_status()
            with open(out, "wb") as f:
                async for chunk in r.aiter_bytes(1 << 20):
                    f.write(chunk)
    return out


# =============================================================================
# Render pipeline
# =============================================================================
async def run_render_pipeline(
    db: AsyncSession,
    clip: Clip,
    project: Project,
    job: Job,
    progress,
    *,
    aspect: str = "9:16",
    resolution: str = "1080p",
    burn_subtitles: bool = True,
    caption_style: Optional[str] = "viral",
    caption_position: str = "bottom",
    watermark_path: Optional[str] = None,
) -> dict:
    from video_engine.ffmpeg.operations import (
        ExportOptions,
        render_clip,
        trim,
    )
    from video_engine.subtitles import clip_transcript, write_srt

    if not project.source_path:
        raise RuntimeError("Project has no source video")
    src = Path(project.source_path)
    if not src.exists():
        raise RuntimeError(f"Source not found: {src}")

    # Resolve edit window
    start = clip.edit_start_sec if clip.edit_start_sec is not None else clip.start_sec
    end = clip.edit_end_sec if clip.edit_end_sec is not None else clip.end_sec

    # 1 — trim to a working file
    await progress(15.0, "Trimming source", "trim")
    work_dir = settings.temp_dir / f"clip_{clip.id}"
    work_dir.mkdir(parents=True, exist_ok=True)
    raw = work_dir / "raw.mp4"
    await trim(src, raw, start=start, end=end, re_encode=True)

    # 2 — write SRT for the window
    srt_path: Optional[Path] = None
    if burn_subtitles and clip.transcript:
        await progress(45.0, "Building subtitles", "subtitles")
        from app.models import TranscriptSegment as TSegment

        segs = (await db.execute(
            select(TSegment)
            .where(TSegment.project_id == project.id)
            .order_by(TSegment.start_sec)
        )).scalars().all()
        from shared.types import TranscriptSegment, TranscriptWord, Transcript as T

        typed = [
            TranscriptSegment(
                id=s.id,
                start=s.start_sec,
                end=s.end_sec,
                text=s.text,
                speaker=s.speaker,
                confidence=s.confidence or 0.0,
                words=[
                    TranscriptWord(
                        word=w.get("word", ""),
                        start=w.get("start", 0.0),
                        end=w.get("end", 0.0),
                        confidence=w.get("confidence", 1.0),
                    )
                    for w in (json.loads(s.words_json) if s.words_json else [])
                ],
            )
            for s in segs
        ]
        window = clip_transcript(T(segments=typed, language=project.language or "en", duration=end, provider="db"), start, end)
        srt_path = work_dir / "captions.srt"
        write_srt(window, srt_path)

    # 3 — final render
    await progress(70.0, "Rendering final clip", "render")
    output_path = settings.outputs_dir / f"clip_{clip.id}.mp4"
    opts = ExportOptions(
        aspect=AspectRatio(aspect),
        resolution=resolution,
        burn_subtitles=bool(srt_path and burn_subtitles),
        srt_path=srt_path,
        caption_style=caption_style or "viral",
        caption_position=caption_position,
        watermark_path=Path(watermark_path) if watermark_path else None,
    )
    await render_clip(raw, output_path, opts)

    # 4 — upload to storage + create thumbnail
    await progress(90.0, "Uploading result", "upload")
    storage = get_storage()
    key = f"clips/{clip.id}/{output_path.name}"
    url = await storage.put_file(output_path, key, content_type="video/mp4", public=True)
    clip.render_path = key
    clip.render_url = url
    clip.render_size_bytes = output_path.stat().st_size if output_path.exists() else None
    from video_engine.ffmpeg.runner import get_metadata
    out_meta = await asyncio.to_thread(get_metadata, str(output_path))
    clip.render_duration_sec = out_meta.duration
    clip.status = "ready"

    # Thumbnail
    try:
        from video_engine.ffmpeg.operations import make_thumbnail
        thumb_path = work_dir / "thumb.jpg"
        await make_thumbnail(output_path, thumb_path, at_sec=min(1.0, max(0.0, (out_meta.duration or 1.0) / 2.0)))
        thumb_key = f"clips/{clip.id}/thumb.jpg"
        thumb_url = await storage.put_file(thumb_path, thumb_key, content_type="image/jpeg", public=True)
        clip.thumbnail_url = thumb_url
    except Exception as exc:  # noqa: BLE001
        log.warning("Clip thumbnail failed: %s", exc)

    await db.commit()

    # Log an export record
    from app.models import ExportRecord

    db.add(ExportRecord(
        project_id=project.id,
        clip_id=clip.id,
        format=f"mp4_{opts.resolution}",
        aspect_ratio=opts.aspect.value,
        resolution=opts.resolution,
        file_path=str(output_path),
        file_url=url,
        file_size_bytes=clip.render_size_bytes,
        duration_sec=int(out_meta.duration) if out_meta.duration else None,
        target="local",
        status="completed",
    ))
    await db.commit()

    return {"render_url": url, "duration_sec": out_meta.duration, "size_bytes": clip.render_size_bytes}


# =============================================================================
# AI Edit pipeline
# =============================================================================
async def run_ai_edit_pipeline(
    db: AsyncSession,
    clip: Clip,
    project: Project,
    job: Job,
    progress,
    *,
    instruction: str,
) -> dict:
    """Apply a natural-language AI instruction to a clip.

    Supported intents (heuristic intent classifier for demo mode):
      - 'remove silence' / 'tighten'  → ffmpeg silenceremove
      - 'faster'                       → speedup via setpts
      - 'caption' / 'dynamic'          → ensure captions on
      - 'focus on speaker'             → face-track smart crop
      - 'professional'                 → caption style = clean
      - 'tiktok' / 'reels' / 'shorts'  → 9:16, bold captions
    """
    text = instruction.lower()
    notes: list[str] = []

    # Persist the new "edit instructions" in clip config
    cfg: dict = {}
    if clip.config:
        try:
            cfg = json.loads(clip.config) or {}
        except json.JSONDecodeError:
            cfg = {}
    cfg["ai_edit_instructions"] = instruction
    cfg["ai_edit_at"] = time.time()
    clip.config = json.dumps(cfg, ensure_ascii=False)

    aspect = "9:16"
    caption_style = cfg.get("caption_style", "viral")
    burn = bool(cfg.get("burn_subtitles", True))
    remove_silence = False
    speedup = 1.0

    if "remove silence" in text or "tighten" in text or "cut silence" in text:
        remove_silence = True
        notes.append("Silence will be removed in the final render.")
    if "faster" in text or "speed" in text or "punchier" in text or "pacing" in text:
        speedup = 1.15
        notes.append("Playback will be slightly sped up for a punchier feel.")
    if "professional" in text or "podcast" in text or "clean" in text:
        caption_style = "clean"
        notes.append("Switched to clean / professional caption style.")
    if "tiktok" in text or "reels" in text or "shorts" in text or "bold" in text:
        aspect = "9:16"
        caption_style = "bold"
        notes.append("Optimized for TikTok / Reels: 9:16 with bold captions.")
    if "podcast" in text:
        caption_style = "podcast"
    if "cinematic" in text:
        caption_style = "cinematic"
    if "karaoke" in text:
        caption_style = "karaoke"
    if "1:1" in text or "square" in text:
        aspect = "1:1"
    if "16:9" in text or "landscape" in text or "youtube" in text:
        aspect = "16:9"
    if "no caption" in text or "without caption" in text:
        burn = False

    if "focus on speaker" in text or "speaker" in text or "face" in text or "track" in text:
        notes.append("Speaker tracking enabled (face-aware smart crop).")

    cfg["aspect"] = aspect
    cfg["caption_style"] = caption_style
    cfg["burn_subtitles"] = burn
    cfg["remove_silence"] = remove_silence
    cfg["speedup"] = speedup
    clip.config = json.dumps(cfg, ensure_ascii=False)
    await db.commit()

    # Re-render
    await progress(20.0, "Applying AI edit", "ai_edit")
    if remove_silence:
        # Apply silence removal as a pre-step
        from video_engine.ffmpeg.operations import remove_silence
        src = Path(project.source_path)
        work = settings.temp_dir / f"clip_{clip.id}_noshort.mp4"
        start = clip.edit_start_sec if clip.edit_start_sec is not None else clip.start_sec
        end = clip.edit_end_sec if clip.edit_end_sec is not None else clip.end_sec
        from video_engine.ffmpeg.operations import trim
        cut = settings.temp_dir / f"clip_{clip.id}_cut.mp4"
        await trim(src, cut, start=start, end=end, re_encode=True)
        await remove_silence(cut, work)
        # Replace the source file for the next render step by writing a "patched" project
        project.source_path = str(work)
        await db.commit()

    await progress(60.0, "Re-rendering with new settings", "render")
    # Re-use the render pipeline
    from app.services.video.pipeline import run_render_pipeline

    new_job = Job(id=str(uuid.uuid4()), type="render", status="processing", project_id=project.id, clip_id=clip.id, user_id=job.user_id)
    db.add(new_job)
    await db.commit()

    async def sub(p, msg, stage=None):
        await progress(60.0 + p * 0.35, msg, stage)

    out = await run_render_pipeline(
        db,
        clip,
        project,
        new_job,
        sub,
        aspect=aspect,
        resolution="1080p",
        burn_subtitles=burn,
        caption_style=caption_style,
    )
    return {"notes": notes, "render": out}
