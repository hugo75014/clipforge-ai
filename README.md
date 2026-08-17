# ClipForge AI

> AI-powered video clipping studio. Turn long videos into viral Shorts / Reels / TikTok / YouTube Shorts in minutes.

ClipForge AI is a production-grade SaaS platform that automatically detects the most engaging moments of a long video, generates vertical clips with dynamic captions, smart face tracking, and brand-consistent templates, and lets you edit and export them in a streamlined studio — all powered by a pluggable AI provider layer so you can run fully offline in **Demo Mode** or wire it to OpenAI, Anthropic, Gemini, OpenRouter, or a local model.

---

## ✨ Features

- 🎬 **One-click clipping** — drop a video, get N publish-ready clips
- 🧠 **AI Clip Finder** — multi-axis scoring (Hook, Emotion, Curiosity, Story, Shareability, …)
- 📐 **Smart Crop 9:16 / 1:1 / 16:9** — automatic face & speaker tracking
- 💬 **Dynamic captions** — Viral / Clean / Podcast / Cinematic / Bold presets
- ✨ **Edit with AI** — silence removal, pacing, dynamic zooms, captions
- 🎨 **Brand Kit & Templates** — Podcast, Interview, Business, Motivation, News, …
- ⚙️ **Pluggable AI providers** — OpenAI · Anthropic · Gemini · OpenRouter · Local · Demo
- 📦 **Pluggable storage** — Local · S3 · Cloudflare R2 · MinIO
- 🛡️ **Admin dashboard** — users, projects, jobs, system health, AI cost
- 🐳 **One-command deploy** — `docker compose up -d` locally, or see [DEPLOY.md](DEPLOY.md) for Netlify + Render

---

## 🚀 Quick start (Docker)

```bash
cp .env.example .env
docker compose up -d --build
```

Then open:
- Frontend: `http://localhost`
- API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`

Default admin: `admin@clipforge.local` / `admin_change_me` (change in `.env` before going to production).

---

## ☁️ Production deploy (free tier)

| Component | Host | Cost |
|---|---|---|
| Frontend | **Netlify** | free |
| Backend API | **Render** | free (sleeps after 15 min) |
| Workers | **Render** | free |
| Database | **Neon** | free (0.5 GB) |
| Cache / queue | **Upstash Redis** | free (10k cmd/day) |
| Storage | **Cloudflare R2** | free (10 GB) |
| AI | **OpenAI gpt-4o-mini** | ~$0.15 / 1M input tokens |

Full step-by-step: **[DEPLOY.md](DEPLOY.md)**

---

## 🏗️ Architecture

```text
clipforge-ai/
├── frontend/        React 18 + TS + Vite + Tailwind + Framer Motion + Zustand
├── backend/         Python · FastAPI · SQLAlchemy (async) · Alembic
├── workers/         Celery workers (transcription, render, AI analysis)
├── video_engine/    FFmpeg · OpenCV · face tracking · subtitles
├── ai_engine/       Heuristic scoring + LLM prompts
├── storage/         Pluggable backends (local/S3/MinIO/R2)
├── database/        Migrations + seeders
├── shared/          Types, constants, utils (no framework deps)
├── docker/          Dockerfiles (frontend, backend, worker)
├── docs/            Architecture, API, AI providers, storage, security
├── netlify.toml     Netlify config (frontend)
├── render.yaml      Render Blueprint (backend + worker)
├── docker-compose.yml
├── DEPLOY.md        Production deployment guide
└── scripts/         audit.sh
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full picture.

---

## 📚 Documentation

- [DEPLOY.md](DEPLOY.md) — production deployment (Netlify + Render + Neon + Upstash + R2)
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — system design
- [docs/API.md](docs/API.md) — REST API reference (also at `/docs`)
- [docs/AI_PROVIDERS.md](docs/AI_PROVIDERS.md) — pluggable AI providers
- [docs/STORAGE.md](docs/STORAGE.md) — pluggable storage backends
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) — single-VM & k8s deployment
- [docs/TESTING.md](docs/TESTING.md) — running & writing tests
- [docs/SECURITY.md](docs/SECURITY.md) — security model

---

## 🧪 Tests

```bash
cd backend && pytest -q       # 21 tests
cd frontend && npm run lint && npm run typecheck
bash scripts/audit.sh         # pre-flight
```

---

## 📜 License

MIT — see [LICENSE](LICENSE).
