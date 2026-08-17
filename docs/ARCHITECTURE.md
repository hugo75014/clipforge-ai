# Architecture

ClipForge AI is a modular monorepo. Each top-level package has a single
responsibility and a tiny public surface, which is what lets the platform
scale from a single-box demo to thousands of concurrent renders without
rewriting the core.

```
┌────────────────────────────────────────────────────────────────────────────┐
│                              Frontend (React)                              │
│   Vite · TS · Tailwind · Framer Motion · Zustand · React Query · Axios     │
│                                                                            │
│   Pages ─► Pages (Dashboard, Project, Clip Editor, Admin, …)               │
│   Stores ─► Auth, UI                                                       │
└────────────────────────────────┬───────────────────────────────────────────┘
                                 │ HTTPS (JWT)
                                 ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                          Backend (FastAPI · async)                          │
│   SQLAlchemy 2 · Pydantic v2 · Alembic · python-jose · boto3 · minio       │
│                                                                            │
│   API v1 ─► /auth /projects /clips /jobs /brand-kits /templates /exports   │
│           ─► /ai /media /admin /users /health                               │
│   Services ─► project, clip, job, storage, AI, video pipeline               │
│   Providers ─► AIProvider {demo, openai, anthropic, gemini, openrouter, …} │
│             ─► TranscriptionProvider {demo, whisper, whisperx}             │
│             ─► StorageProvider {local, s3, minio, r2}                      │
└────────┬───────────────────────────────────────────┬───────────────────────┘
         │ Async jobs (Celery)                        │ Direct (sync)
         ▼                                            ▼
┌──────────────────────────┐                ┌──────────────────────────────┐
│       Worker (Celery)    │                │      Video / AI Engine       │
│  analyze · render · …    │                │  FFmpeg · OpenCV · Whisper   │
└────────┬─────────────────┘                └────────┬─────────────────────┘
         │                                           │
         └─────────────►   PostgreSQL   ◄────────────┘
                          Redis
                          Local FS / S3 / R2 / MinIO
```

## Layered responsibilities

| Layer | Responsibility | Location |
| --- | --- | --- |
| **AI Engine** | Transcription, content analysis, hook detection, scoring, titles, descriptions, hashtags, virality prediction | `ai_engine/` + `backend/app/providers/ai/` |
| **Video Engine** | Cut, reframe, render, subtitles, animations, transitions, export | `video_engine/` + `backend/app/services/video/pipeline.py` |
| **Job Engine** | All heavy work is async (Celery + Redis). Resumable, observable, retriable. | `backend/app/services/job.py` + `workers/` |
| **Storage** | Backend-agnostic abstraction over local / S3 / R2 / MinIO | `backend/app/services/storage/` + `backend/app/providers/storage/` |
| **Auth & API** | JWT-based auth, RBAC, rate-limited REST API, OpenAPI docs | `backend/app/core/security.py` + `backend/app/api/v1/` |

## Why a "provider" abstraction?

A `Provider` is a tiny protocol with a few methods. The rest of the app
**only** talks to that protocol. That gives us:

- **Swappable models.** `AI_PROVIDER=openai` ↔ `AI_PROVIDER=demo` is a single
  env-var change, no code change.
- **Demo Mode by default.** The whole pipeline works offline so the user
  can explore the product without setting up keys.
- **Pluggable storage.** `STORAGE_BACKEND=local` in dev, `=s3` in
  production. Files flow through the same `Storage.put_file(...)` API.
- **Independent scaling.** A new transcription provider (AssemblyAI,
  Deepgram, …) is a single file that implements `TranscriptionProvider`.

## Data model (relational)

- **users** — auth + RBAC
- **projects** — one source video + meta
- **clips** — candidates inside a project (scores, window, render info)
- **transcript_segments** — speech turns (words, speakers, timing)
- **jobs** — every async operation (analyze, render, …) with progress
- **brand_kits** — reusable brand assets per user
- **templates** — built-in & user-created editing presets
- **exports** — every shipped file (history & audit)

## Synchronous vs asynchronous work

The frontend offers **two ways** to run heavy operations:

1. **`/analyze/sync`** — runs inline inside the request, blocks until done.
   Best for demo mode and small files; the UI shows a real progress bar.
2. **`/analyze`** (no `/sync`) — creates a `Job` row, dispatches to Celery,
   and returns immediately. The frontend polls `/api/v1/jobs/{id}` to render
   the progress bar and re-fetches the project when it completes.

Both paths share the same `run_analysis_pipeline` so the result is identical
no matter which one you pick.

## Smart Crop (face-aware)

The video engine can run a face-tracking pass on the source video using
OpenCV's Haar cascade (no extra model downloads). The detected face
centers are interpolated into a dense `(t, x, y)` track, which is then
fed to ffmpeg's `sendcmd` filter to drive a keyframed `crop=…` expression.
If no face is detected the crop falls back to a centered static window.

## Demo Mode

`DEMO_MODE=true` (the default) makes the entire pipeline runnable without
any external dependency. The demo provider:

- returns deterministic but realistic JSON shaped to match a real LLM,
- streams a believable job progress,
- keeps the exact same code path as production.

When you set `AI_PROVIDER=openai` (etc.) the rest of the app does **not**
change. The demo provider simply isn't used anymore.

## Security

- JWT auth (access + refresh), bcrypt password hashing
- Role-based access control (`admin` / `editor` / `viewer`)
- File upload validation (extension, MIME, size)
- Per-route rate limiting (configurable)
- All secrets in env vars — never in code or front-end bundle
- CORS allow-list
- Local backend-mounted `/media` only available when `STORAGE_BACKEND=local`

See [SECURITY.md](SECURITY.md) for the full list.
