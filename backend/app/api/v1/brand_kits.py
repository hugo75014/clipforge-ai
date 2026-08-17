"""Brand kit routes."""

from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, require_editor
from app.db.session import get_db
from app.models import BrandKit, User
from app.schemas.brand_kit import BrandKitCreate, BrandKitOut, BrandKitUpdate


router = APIRouter()


@router.get("", response_model=list[BrandKitOut])
async def list_brand_kits(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[BrandKitOut]:
    stmt = select(BrandKit).where(BrandKit.owner_id == user.id).order_by(BrandKit.created_at.desc())
    res = await db.execute(stmt)
    return [BrandKitOut.model_validate(b) for b in res.scalars().all()]


@router.post("", response_model=BrandKitOut, status_code=201)
async def create_brand_kit(
    payload: BrandKitCreate,
    user: User = Depends(require_editor),
    db: AsyncSession = Depends(get_db),
) -> BrandKitOut:
    if payload.is_default:
        existing = (await db.execute(
            select(BrandKit).where(BrandKit.owner_id == user.id, BrandKit.is_default.is_(True))
        )).scalars().all()
        for b in existing:
            b.is_default = False
    b = BrandKit(owner_id=user.id, **payload.model_dump())
    db.add(b)
    await db.commit()
    await db.refresh(b)
    return BrandKitOut.model_validate(b)


@router.patch("/{brand_kit_id}", response_model=BrandKitOut)
async def update_brand_kit(
    brand_kit_id: str,
    payload: BrandKitUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BrandKitOut:
    b = await db.get(BrandKit, brand_kit_id)
    if b is None or b.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Brand kit not found")
    data = payload.model_dump(exclude_unset=True)
    if data.get("is_default") is True:
        existing = (await db.execute(
            select(BrandKit).where(BrandKit.owner_id == user.id, BrandKit.is_default.is_(True), BrandKit.id != brand_kit_id)
        )).scalars().all()
        for e in existing:
            e.is_default = False
    for k, v in data.items():
        setattr(b, k, v)
    await db.commit()
    await db.refresh(b)
    return BrandKitOut.model_validate(b)


@router.delete("/{brand_kit_id}", status_code=204)
async def delete_brand_kit(
    brand_kit_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    b = await db.get(BrandKit, brand_kit_id)
    if b is None or b.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Brand kit not found")
    await db.delete(b)
    await db.commit()
