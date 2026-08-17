"""FastAPI app entry point."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1 import api_router
from app.core import settings
from app.core.logging import get_logger, setup_logging
from app.db.session import SessionLocal, init_db


setup_logging()
log = get_logger(__name__)


# =============================================================================
# Background tasks
# =============================================================================
async def _bootstrap_admin() -> None:
    """Ensure a default admin user exists (idempotent)."""
    from app.core.security import hash_password
    from app.models import Template, User
    from sqlalchemy import select

    try:
        async with SessionLocal() as db:
            existing = (await db.execute(select(User).where(User.email == settings.admin_email))).scalar_one_or_none()
            if existing is None:
                admin = User(
                    email=settings.admin_email,
                    name=settings.admin_name,
                    hashed_password=hash_password(settings.admin_password),
                    role="admin",
                    is_active=True,
                )
                db.add(admin)
                await db.commit()
                log.info("Bootstrapped admin user %s", settings.admin_email)
            await _seed_builtin_templates(db)
    except Exception as exc:  # noqa: BLE001
        log.warning("Bootstrap admin skipped: %s", exc)


async def _seed_builtin_templates(db) -> None:
    """Insert built-in templates on first boot."""
    import json

    from sqlalchemy import select
    from app.models import Template

    builtins = [
        {
            "name": "Podcast",
            "category": "podcast",
            "description": "Centered captions, clean transitions, lower-third name.",
            "config": {
                "aspect": "9:16",
                "caption_style": "podcast",
                "caption_position": "center",
                "burn_subtitles": True,
                "intro": None,
            },
        },
        {
            "name": "Interview",
            "category": "interview",
            "description": "Two-speaker layout with smart crop, side-by-side when needed.",
            "config": {
                "aspect": "9:16",
                "caption_style": "clean",
                "caption_position": "bottom",
                "burn_subtitles": True,
            },
        },
        {
            "name": "Business",
            "category": "business",
            "description": "Polished look, cinematic captions, subtle zoom.",
            "config": {
                "aspect": "9:16",
                "caption_style": "cinematic",
                "caption_position": "bottom",
                "burn_subtitles": True,
            },
        },
        {
            "name": "Motivation",
            "category": "motivation",
            "description": "Big bold captions, dramatic pacing, speaker zoom.",
            "config": {
                "aspect": "9:16",
                "caption_style": "bold",
                "caption_position": "bottom",
                "burn_subtitles": True,
                "dynamic_zoom": True,
            },
        },
        {
            "name": "News",
            "category": "news",
            "description": "Lower-third with topic, clean captions, fast cuts.",
            "config": {
                "aspect": "9:16",
                "caption_style": "clean",
                "caption_position": "bottom",
                "burn_subtitles": True,
            },
        },
        {
            "name": "Education",
            "category": "education",
            "description": "Step-by-step list overlay, clean captions, slow zoom.",
            "config": {
                "aspect": "9:16",
                "caption_style": "clean",
                "caption_position": "bottom",
                "burn_subtitles": True,
            },
        },
        {
            "name": "Gaming",
            "category": "gaming",
            "description": "Colorful karaoke captions, fast zooms, SFX-friendly.",
            "config": {
                "aspect": "9:16",
                "caption_style": "karaoke",
                "caption_position": "bottom",
                "burn_subtitles": True,
                "dynamic_zoom": True,
            },
        },
        {
            "name": "Storytelling",
            "category": "storytelling",
            "description": "Cinematic letterbox, soft transitions, gentle zooms.",
            "config": {
                "aspect": "9:16",
                "caption_style": "cinematic",
                "caption_position": "bottom",
                "burn_subtitles": True,
            },
        },
    ]
    existing = {(t.name, t.category) for t in (await db.execute(select(Template))).scalars().all()}
    for spec in builtins:
        if (spec["name"], spec["category"]) in existing:
            continue
        db.add(Template(
            owner_id=None,
            name=spec["name"],
            category=spec["category"],
            description=spec["description"],
            config=json.dumps(spec["config"], ensure_ascii=False),
            is_builtin=True,
            is_public=True,
        ))
    await db.commit()


# =============================================================================
# Lifespan
# =============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Best-effort: try to create tables (idempotent). In production, prefer Alembic.
    try:
        await init_db()
    except Exception as exc:  # noqa: BLE001
        log.warning("init_db failed (DB may be unreachable at startup): %s", exc)
    try:
        await _bootstrap_admin()
    except Exception as exc:  # noqa: BLE001
        log.warning("Bootstrap failed: %s", exc)

    # Make sure data dirs exist
    for d in (settings.uploads_dir, settings.temp_dir, settings.outputs_dir, settings.logs_dir):
        d.mkdir(parents=True, exist_ok=True)

    log.info("%s started (env=%s, version=%s)", settings.app_name, settings.app_env, settings.app_version)
    yield
    log.info("Shutting down %s", settings.app_name)


# =============================================================================
# App factory
# =============================================================================
app = FastAPI(
    title=settings.app_name,
    description=(
        "ClipForge AI — turn long videos into viral Shorts / Reels / TikTok "
        "with AI-powered clip detection, smart cropping, dynamic captions, "
        "and a pluggable provider layer."
    ),
    version=settings.app_version,
    lifespan=lifespan,
    debug=settings.app_debug,
)


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "X-Job-Id", "X-Project-Id"],
)


# Error handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "code": exc.status_code},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    log.exception("Unhandled error at %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "code": 500, "error": str(exc)[:500]},
    )


# API routes
app.include_router(api_router)


# Static files (frontend build OR local data dir for direct access)
_frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if _frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="frontend")
else:
    # Fallback: serve the data dir so /media works in dev
    if settings.uploads_dir.exists():
        app.mount("/uploads", StaticFiles(directory=str(settings.uploads_dir)), name="uploads")
    if settings.outputs_dir.exists():
        app.mount("/outputs", StaticFiles(directory=str(settings.outputs_dir)), name="outputs")
    if settings.data_dir.exists():
        # Mirror everything in /media
        app.mount("/media", StaticFiles(directory=str(settings.data_dir)), name="media")
