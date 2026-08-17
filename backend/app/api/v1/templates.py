"""Template routes — preset configs for different content types."""

from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, require_editor
from app.db.session import get_db
from app.models import Template, User
from app.schemas.template import TemplateCreate, TemplateOut, TemplateUpdate


router = APIRouter()


def _serialize(t: Template) -> TemplateOut:
    return TemplateOut.model_validate(t)


@router.get("", response_model=list[TemplateOut])
async def list_templates(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    category: Optional[str] = None,
    include_public: bool = True,
) -> list[TemplateOut]:
    stmt = select(Template).where(
        or_(Template.owner_id == user.id, Template.is_public.is_(True) if include_public else False)
    )
    if category:
        stmt = stmt.where(Template.category == category)
    stmt = stmt.order_by(Template.is_builtin.desc(), Template.created_at.desc())
    res = await db.execute(stmt)
    return [_serialize(t) for t in res.scalars().all()]


@router.get("/{template_id}", response_model=TemplateOut)
async def get_template(
    template_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TemplateOut:
    t = await db.get(Template, template_id)
    if t is None:
        raise HTTPException(status_code=404, detail="Template not found")
    if not (t.is_public or t.is_builtin or t.owner_id == user.id):
        raise HTTPException(status_code=403, detail="Not your template")
    return _serialize(t)


@router.post("", response_model=TemplateOut, status_code=201)
async def create_template(
    payload: TemplateCreate,
    user: User = Depends(require_editor),
    db: AsyncSession = Depends(get_db),
) -> TemplateOut:
    t = Template(
        owner_id=user.id,
        name=payload.name,
        category=payload.category,
        description=payload.description,
        thumbnail_url=payload.thumbnail_url,
        is_public=payload.is_public,
        config=payload.config or {},
    )
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return _serialize(t)


@router.patch("/{template_id}", response_model=TemplateOut)
async def update_template(
    template_id: str,
    payload: TemplateUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TemplateOut:
    t = await db.get(Template, template_id)
    if t is None or (t.owner_id != user.id and not user.is_admin):
        raise HTTPException(status_code=404, detail="Template not found")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(t, k, v)
    await db.commit()
    await db.refresh(t)
    return _serialize(t)


@router.delete("/{template_id}", status_code=204)
async def delete_template(
    template_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    t = await db.get(Template, template_id)
    if t is None or (t.owner_id != user.id and not user.is_admin):
        raise HTTPException(status_code=404, detail="Template not found")
    await db.delete(t)
    await db.commit()
