"""V1 API aggregator."""

from fastapi import APIRouter

from app.api.v1 import (
    admin,
    ai,
    auth,
    brand_kits,
    clips,
    exports,
    health,
    jobs,
    media,
    projects,
    templates,
    users,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(clips.router, prefix="/clips", tags=["clips"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(brand_kits.router, prefix="/brand-kits", tags=["brand kits"])
api_router.include_router(templates.router, prefix="/templates", tags=["templates"])
api_router.include_router(exports.router, prefix="/exports", tags=["exports"])
api_router.include_router(media.router, prefix="/media", tags=["media"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
