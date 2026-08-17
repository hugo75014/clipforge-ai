"""Export routes — list & create export records.

Real "push to TikTok / YouTube" wiring is intentionally left as a
`EXTERNAL_PROVIDER_*` abstraction layer; the UI shows the configuration
panel and stores tokens, but no live upload happens until the user wires
the corresponding provider.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models import ExportRecord, User
from app.schemas.export import ExportCreate, ExportOut


router = APIRouter()


@router.get("", response_model=list[ExportOut])
async def list_exports(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    project_id: str | None = None,
    limit: int = 50,
) -> list[ExportOut]:
    stmt = select(ExportRecord).order_by(ExportRecord.created_at.desc()).limit(max(1, min(200, limit)))
    if not user.is_admin:
        stmt = stmt.where(ExportRecord.user_id == user.id)
    if project_id:
        stmt = stmt.where(ExportRecord.project_id == project_id)
    res = await db.execute(stmt)
    return [ExportOut.model_validate(e) for e in res.scalars().all()]


@router.post("", response_model=ExportOut, status_code=201)
async def create_export(
    payload: ExportCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExportOut:
    if not payload.clip_id and not payload.project_id:
        raise HTTPException(status_code=400, detail="clip_id or project_id is required")
    rec = ExportRecord(
        project_id=payload.project_id,
        clip_id=payload.clip_id,
        user_id=user.id,
        format=payload.format,
        aspect_ratio=payload.aspect_ratio,
        resolution=payload.resolution,
        file_path="",  # will be filled when render completes
        file_url="",
        target=payload.target,
        status="queued",
        notes=payload.notes,
    )
    db.add(rec)
    await db.commit()
    await db.refresh(rec)
    return ExportOut.model_validate(rec)


@router.get("/providers")
async def providers(_: User = Depends(get_current_user)) -> list[dict]:
    """List available external publish targets & their config status.

    No live API calls — just the configuration the user has set in .env.
    """
    from app.core import settings

    return [
        {
            "name": "youtube",
            "display": "YouTube Shorts",
            "configured": bool(getattr(settings, "openai_api_key", None)),  # placeholder hook
            "fields": ["channel_id", "oauth_refresh_token"],
        },
        {
            "name": "tiktok",
            "display": "TikTok",
            "configured": False,
            "fields": ["open_id", "access_token"],
        },
        {
            "name": "instagram",
            "display": "Instagram Reels",
            "configured": False,
            "fields": ["ig_user_id", "access_token"],
        },
        {
            "name": "facebook",
            "display": "Facebook Reels",
            "configured": False,
            "fields": ["page_id", "access_token"],
        },
        {
            "name": "local",
            "display": "Download (.mp4)",
            "configured": True,
            "fields": [],
        },
    ]
