"""Cross-cutting constants and enums.

Keep this file pure-Python and dependency-free. The frontend mirrors these
constants in `frontend/src/lib/constants.ts`.
"""

from __future__ import annotations

from enum import Enum


# =============================================================================
# App identity
# =============================================================================
APP_NAME = "ClipForge AI"
APP_TAGLINE = "AI video clipping studio"


# =============================================================================
# Job lifecycle
# =============================================================================
class JobStatus(str, Enum):
    """Lifecycle of any async job in the system."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, Enum):
    UPLOAD = "upload"
    EXTRACT_AUDIO = "extract_audio"
    TRANSCRIBE = "transcribe"
    ANALYZE = "analyze"
    DETECT_SCENES = "detect_scenes"
    DETECT_FACES = "detect_faces"
    SCORE_CLIPS = "score_clips"
    RENDER = "render"
    EXPORT = "export"
    THUMBNAIL = "thumbnail"
    AI_EDIT = "ai_edit"


# =============================================================================
# Project / clip
# =============================================================================
class ProjectStatus(str, Enum):
    DRAFT = "draft"
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    ANALYZING = "analyzing"
    READY = "ready"
    EDITING = "editing"
    RENDERING = "rendering"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    FAILED = "failed"


class ClipStatus(str, Enum):
    DRAFT = "draft"
    SELECTED = "selected"
    RENDERING = "rendering"
    READY = "ready"
    EXPORTED = "exported"
    FAILED = "failed"


class AspectRatio(str, Enum):
    VERTICAL = "9:16"      # 1080x1920 — TikTok / Reels / Shorts
    SQUARE = "1:1"         # 1080x1080 — Instagram feed
    HORIZONTAL = "16:9"    # 1920x1080 — YouTube

    @property
    def width(self) -> int:
        return {
            AspectRatio.VERTICAL: 1080,
            AspectRatio.SQUARE: 1080,
            AspectRatio.HORIZONTAL: 1920,
        }[self]

    @property
    def height(self) -> int:
        return {
            AspectRatio.VERTICAL: 1920,
            AspectRatio.SQUARE: 1080,
            AspectRatio.HORIZONTAL: 1080,
        }[self]


class ExportFormat(str, Enum):
    MP4_H264_1080P = "mp4_h264_1080p"
    MP4_H264_720P = "mp4_h264_720p"
    MP4_H264_480P = "mp4_h264_480p"


# =============================================================================
# Captions
# =============================================================================
class CaptionStyle(str, Enum):
    VIRAL = "viral"           # Big, dynamic, word-by-word highlight
    CLEAN = "clean"           # Minimalist white on dark
    PODCAST = "podcast"       # Centered, two-line max
    CINEMATIC = "cinematic"   # Letterboxed premium
    BOLD = "bold"             # Heavy weight, high contrast (TikTok/Reels)
    KARAOKE = "karaoke"       # Color sweep per word


class CaptionPosition(str, Enum):
    TOP = "top"
    CENTER = "center"
    BOTTOM = "bottom"


# =============================================================================
# AI
# =============================================================================
class AIProviderName(str, Enum):
    DEMO = "demo"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OPENROUTER = "openrouter"
    LOCAL = "local"


class TranscriptionProviderName(str, Enum):
    DEMO = "demo"
    WHISPER = "whisper"
    WHISPERX = "whisperx"


# =============================================================================
# Templates
# =============================================================================
class TemplateCategory(str, Enum):
    PODCAST = "podcast"
    INTERVIEW = "interview"
    BUSINESS = "business"
    MOTIVATION = "motivation"
    NEWS = "news"
    EDUCATION = "education"
    GAMING = "gaming"
    STORYTELLING = "storytelling"
    CUSTOM = "custom"


# =============================================================================
# Storage
# =============================================================================
class StorageBackend(str, Enum):
    LOCAL = "local"
    S3 = "s3"
    MINIO = "minio"
    R2 = "r2"


# =============================================================================
# User / Auth
# =============================================================================
class UserRole(str, Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


# =============================================================================
# Scoring (viral moment detection)
# =============================================================================
class ScoreAxis(str, Enum):
    HOOK = "hook"
    EMOTION = "emotion"
    INFORMATION = "information"
    STORY = "story"
    CURIOSITY = "curiosity"
    SHAREABILITY = "shareability"
    COMPLETION = "completion"
    OVERALL = "overall"


# =============================================================================
# Defaults
# =============================================================================
DEFAULT_CLIP_TARGET_DURATION_SEC = 45.0
DEFAULT_CLIP_MIN_DURATION_SEC = 15.0
DEFAULT_CLIP_MAX_DURATION_SEC = 90.0
DEFAULT_CONTEXT_PADDING_SEC = 1.5
DEFAULT_MAX_CLIPS_PER_PROJECT = 30
DEFAULT_TOP_K_CLIPS = 10

# Score thresholds
MIN_CLIP_VIRAL_SCORE = 55      # Below this we keep the clip only if it's a "soft" pick
STRONG_CLIP_VIRAL_SCORE = 80

# Upload limits
DEFAULT_MAX_UPLOAD_MB = 2048
ALLOWED_VIDEO_EXT = {"mp4", "mov", "mkv", "webm"}
ALLOWED_VIDEO_MIME = {
    "video/mp4",
    "video/quicktime",
    "video/x-matroska",
    "video/webm",
    "application/octet-stream",  # some browsers send this for mkv
}

# CORS
DEFAULT_CORS_ORIGINS = [
    "http://localhost",
    "http://localhost:80",
    "http://localhost:5173",
    "http://localhost:8000",
]
