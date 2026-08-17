"""Seed built-in templates + default admin user.

Usage:
    cd backend
    python -m database.seeders.seed
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from sqlalchemy import select

from app.core import settings
from app.core.security import hash_password
from app.db.session import Base, SessionLocal, engine, init_db
from app.models import Template, User


BUILTIN_TEMPLATES = [
    ("Podcast", "podcast", "Centered captions, clean transitions, lower-third name.", {"aspect": "9:16", "caption_style": "podcast", "caption_position": "center", "burn_subtitles": True}),
    ("Interview", "interview", "Two-speaker layout, smart crop, side-by-side when needed.", {"aspect": "9:16", "caption_style": "clean", "caption_position": "bottom", "burn_subtitles": True}),
    ("Business", "business", "Polished look, cinematic captions, subtle zoom.", {"aspect": "9:16", "caption_style": "cinematic", "caption_position": "bottom", "burn_subtitles": True}),
    ("Motivation", "motivation", "Big bold captions, dramatic pacing, speaker zoom.", {"aspect": "9:16", "caption_style": "bold", "caption_position": "bottom", "burn_subtitles": True, "dynamic_zoom": True}),
    ("News", "news", "Lower-third with topic, clean captions, fast cuts.", {"aspect": "9:16", "caption_style": "clean", "caption_position": "bottom", "burn_subtitles": True}),
    ("Education", "education", "Step-by-step list overlay, clean captions, slow zoom.", {"aspect": "9:16", "caption_style": "clean", "caption_position": "bottom", "burn_subtitles": True}),
    ("Gaming", "gaming", "Colorful karaoke captions, fast zooms, SFX-friendly.", {"aspect": "9:16", "caption_style": "karaoke", "caption_position": "bottom", "burn_subtitles": True, "dynamic_zoom": True}),
    ("Storytelling", "storytelling", "Cinematic letterbox, soft transitions, gentle zooms.", {"aspect": "9:16", "caption_style": "cinematic", "caption_position": "bottom", "burn_subtitles": True}),
]


async def seed_admin() -> None:
    async with SessionLocal() as db:
        existing = (await db.execute(select(User).where(User.email == settings.admin_email))).scalar_one_or_none()
        if existing is None:
            db.add(User(
                email=settings.admin_email,
                name=settings.admin_name,
                hashed_password=hash_password(settings.admin_password),
                role="admin",
                is_active=True,
            ))
            print(f"[seed] created admin user: {settings.admin_email}")
        else:
            print(f"[seed] admin user already exists: {settings.admin_email}")
        await db.commit()


async def seed_templates() -> None:
    async with SessionLocal() as db:
        existing = {(t.name, t.category) for t in (await db.execute(select(Template))).scalars().all()}
        created = 0
        for name, category, desc, config in BUILTIN_TEMPLATES:
            if (name, category) in existing:
                continue
            db.add(Template(
                owner_id=None,
                name=name,
                category=category,
                description=desc,
                config=json.dumps(config, ensure_ascii=False),
                is_builtin=True,
                is_public=True,
            ))
            created += 1
        await db.commit()
        print(f"[seed] inserted {created} built-in templates")


async def main() -> None:
    try:
        await init_db()
    except Exception as exc:
        print(f"[seed] init_db failed (DB may be unreachable): {exc}")
        return
    await seed_admin()
    await seed_templates()
    await engine.dispose()


if __name__ == "__main__":  # pragma: no cover
    asyncio.run(main())
