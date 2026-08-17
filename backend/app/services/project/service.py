"""Project business logic — create, list, update, delete projects.

Pure DB-level helpers; the heavy lifting (upload, analyze, render) lives in
the corresponding services.
"""

from __future__ import annotations

import json
from typing import Optional

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Project
from app.schemas.project import ProjectCreate, ProjectUpdate
from shared.utils import slugify


async def create_project(db: AsyncSession, *, owner_id: str, payload: ProjectCreate) -> Project:
    project = Project(
        owner_id=owner_id,
        title=payload.title.strip() or "Untitled project",
        description=payload.description,
        source_url=payload.source_url,
        status="draft",
    )
    if payload.config is not None:
        project.config = json.dumps(payload.config, ensure_ascii=False)
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


async def get_project(db: AsyncSession, project_id: str, *, owner_id: Optional[str] = None) -> Optional[Project]:
    stmt = select(Project).where(Project.id == project_id)
    if owner_id is not None:
        stmt = stmt.where(Project.owner_id == owner_id)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()


async def list_projects(
    db: AsyncSession,
    *,
    owner_id: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    status: Optional[str] = None,
    archived: bool = False,
) -> tuple[list[Project], int]:
    page = max(1, int(page))
    page_size = max(1, min(100, int(page_size)))

    stmt = select(Project)
    count_stmt = select(func.count()).select_from(Project)
    if owner_id is not None:
        stmt = stmt.where(Project.owner_id == owner_id)
        count_stmt = count_stmt.where(Project.owner_id == owner_id)
    if search:
        like = f"%{search}%"
        stmt = stmt.where(Project.title.ilike(like))
        count_stmt = count_stmt.where(Project.title.ilike(like))
    if status:
        stmt = stmt.where(Project.status == status)
        count_stmt = count_stmt.where(Project.status == status)
    if not archived:
        stmt = stmt.where(Project.status != "archived")

    total = (await db.execute(count_stmt)).scalar_one()
    stmt = stmt.order_by(Project.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)
    res = await db.execute(stmt)
    return list(res.scalars().all()), int(total)


async def update_project(db: AsyncSession, project: Project, payload: ProjectUpdate) -> Project:
    if payload.title is not None:
        project.title = payload.title
    if payload.description is not None:
        project.description = payload.description
    if payload.status is not None:
        project.status = payload.status
    if payload.config is not None:
        project.config = json.dumps(payload.config, ensure_ascii=False)
    if payload.language is not None:
        project.language = payload.language
    await db.commit()
    await db.refresh(project)
    return project


async def delete_project(db: AsyncSession, project: Project) -> None:
    await db.delete(project)
    await db.commit()


async def duplicate_project(db: AsyncSession, project: Project) -> Project:
    new = Project(
        owner_id=project.owner_id,
        title=f"{project.title} (copy)",
        description=project.description,
        source_url=project.source_url,
        source_path=project.source_path,
        source_filename=project.source_filename,
        source_size_bytes=project.source_size_bytes,
        source_duration_sec=project.source_duration_sec,
        source_width=project.source_width,
        source_height=project.source_height,
        source_fps=project.source_fps,
        source_codec=project.source_codec,
        language=project.language,
        config=project.config,
        status="draft",
    )
    db.add(new)
    await db.commit()
    await db.refresh(new)
    return new


def get_storage_key(project_id: str, filename: str) -> str:
    return f"projects/{project_id}/{slugify(filename) or 'video'}"
