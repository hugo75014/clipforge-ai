"""Core configuration loaded from environment variables."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _split_csv(value: Optional[str], default: List[str]) -> List[str]:
    if not value:
        return default
    out = [v.strip() for v in value.split(",") if v.strip()]
    return out or default


class Settings(BaseSettings):
    """All runtime configuration. Read from env / .env file."""

    model_config = SettingsConfigDict(
        env_file=os.getenv("APP_ENV_FILE", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---------- App ----------
    app_name: str = "ClipForge AI"
    app_env: str = "development"
    app_version: str = "0.1.0"
    app_debug: bool = True
    app_url: str = "http://localhost"
    api_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:5173"

    # ---------- Security ----------
    secret_key: str = "dev-secret-change-me"
    jwt_secret: str = "dev-jwt-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 60
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30

    # ---------- Demo ----------
    demo_mode: bool = True
    demo_progress_min_ms: int = 400
    demo_progress_max_ms: int = 1200

    # ---------- Database ----------
    database_url: str = "postgresql+asyncpg://clipforge:clipforge@postgres:5432/clipforge"
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "clipforge"
    postgres_user: str = "clipforge"
    postgres_password: str = "clipforge"

    # ---------- Redis / Celery ----------
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/1"
    # Quand false, les traitements lourds tournent dans le processus web
    # (utile en dev / sur une machine sans worker).
    use_celery: bool = True

    # ---------- Storage ----------
    storage_backend: str = "local"  # local | s3 | minio | r2
    storage_local_root: str = "/app/data"
    storage_public_base_url: str = "http://localhost:8000/media"

    s3_endpoint: Optional[str] = None
    s3_region: str = "us-east-1"
    s3_bucket: str = "clipforge"
    s3_access_key: Optional[str] = None
    s3_secret_key: Optional[str] = None
    s3_public_url: Optional[str] = None

    minio_endpoint: Optional[str] = None
    minio_port: int = 9000
    minio_access_key: Optional[str] = None
    minio_secret_key: Optional[str] = None
    minio_bucket: str = "clipforge"
    minio_secure: bool = False

    r2_account_id: Optional[str] = None
    r2_access_key: Optional[str] = None
    r2_secret_key: Optional[str] = None
    r2_bucket: str = "clipforge"

    # ---------- Uploads ----------
    max_upload_size_mb: int = 2048
    allowed_video_mime: str = "video/mp4,video/quicktime,video/x-matroska,video/webm"
    allowed_video_ext: str = "mp4,mov,mkv,webm"

    @property
    def allowed_video_mime_set(self) -> set[str]:
        return {m.strip() for m in self.allowed_video_mime.split(",") if m.strip()}

    @property
    def allowed_video_ext_set(self) -> set[str]:
        return {e.strip().lower().lstrip(".") for e in self.allowed_video_ext.split(",") if e.strip()}

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    # ---------- AI ----------
    ai_provider: str = "demo"
    ai_model: str = "gpt-4o-mini"
    ai_temperature: float = 0.7
    ai_max_tokens: int = 2048
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None

    # ---------- Transcription ----------
    transcription_provider: str = "demo"
    whisper_model: str = "base"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    whisper_language: Optional[str] = None

    # ---------- Video ----------
    ffmpeg_path: str = "ffmpeg"
    ffprobe_path: str = "ffprobe"
    video_threads: int = 4
    default_export_codec: str = "libx264"
    default_export_preset: str = "medium"
    default_export_crf: int = 23

    # ---------- CORS ----------
    cors_allow_origins: str = "http://localhost,http://localhost:5173,http://localhost:8000"

    @property
    def cors_origins_list(self) -> List[str]:
        return _split_csv(self.cors_allow_origins, ["http://localhost"])

    # ---------- Rate limit ----------
    rate_limit_per_minute: int = 120
    upload_rate_limit_per_hour: int = 20

    # ---------- Logging ----------
    log_level: str = "INFO"
    log_format: str = "text"  # json | text
    sentry_dsn: Optional[str] = None

    # ---------- Admin bootstrap ----------
    admin_email: str = "admin@clipforge.local"
    admin_password: str = "admin_change_me"
    admin_name: str = "Administrator"

    # ---------- Convenience paths ----------
    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parents[3]

    @property
    def data_dir(self) -> Path:
        """Racine des fichiers (uploads, rendus, temporaires).

        Doit suivre STORAGE_LOCAL_ROOT : dans l'image Docker, `project_root`
        remonte à « / » et les vidéos atterrissaient dans /data, à côté du
        volume monté sur /app/data. Résultat : fichiers perdus au rebuild, et
        worker et API qui ne voyaient pas les mêmes fichiers.
        """
        root = (self.storage_local_root or "").strip()
        if root:
            return Path(root)
        return self.project_root / "data"

    @property
    def uploads_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def temp_dir(self) -> Path:
        return self.data_dir / "temp"

    @property
    def outputs_dir(self) -> Path:
        return self.data_dir / "outputs"

    @property
    def logs_dir(self) -> Path:
        return self.data_dir / "logs"

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in ("production", "prod")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
