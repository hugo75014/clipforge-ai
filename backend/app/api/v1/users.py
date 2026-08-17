"""User management routes (admin)."""

from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, hash_password, require_admin
from app.db.session import get_db
from app.models import User
from app.schemas.auth import UserCreate, UserOut, UserUpdate


router = APIRouter()


@router.get("", response_model=list[UserOut])
async def list_users(
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[UserOut]:
    res = await db.execute(select(User).order_by(User.created_at.desc()))
    return [UserOut.model_validate(u) for u in res.scalars().all()]


@router.post("", response_model=UserOut, status_code=201)
async def create_user(
    payload: UserCreate,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    if (await db.execute(select(User).where(User.email == payload.email.lower()))).scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Email already exists")
    user = User(
        email=payload.email.lower(),
        name=payload.name,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        is_active=payload.is_active,
        avatar_url=payload.avatar_url,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserOut.model_validate(user)


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: str,
    payload: UserUpdate,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    if current.id != user_id and not current.is_admin:
        raise HTTPException(status_code=403, detail="Cannot edit other users")
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.name is not None:
        user.name = payload.name
    if payload.avatar_url is not None:
        user.avatar_url = payload.avatar_url
    if payload.password:
        user.hashed_password = hash_password(payload.password)
    if payload.role is not None and current.is_admin:
        user.role = payload.role
    if payload.is_active is not None and current.is_admin:
        user.is_active = payload.is_active
    if payload.preferences is not None:
        user.preferences = payload.preferences
    await db.commit()
    await db.refresh(user)
    return UserOut.model_validate(user)


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: str,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_admin:
        # Don't allow deleting the last admin
        admins = (await db.execute(select(User).where(User.role == "admin"))).scalars().all()
        if len(admins) <= 1:
            raise HTTPException(status_code=400, detail="Cannot delete the only admin")
    await db.delete(user)
    await db.commit()
