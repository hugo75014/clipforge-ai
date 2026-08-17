# Deployment

## One-command dev stack

```bash
git clone <your-repo> clipforge && cd clipforge
cp .env.example .env
# Edit .env: set SECRET_KEY, JWT_SECRET, POSTGRES_PASSWORD

docker compose up -d --build
```

Open:
- Frontend: <http://localhost>
- API: <http://localhost:8000>
- API docs: <http://localhost:8000/docs>

## Default admin

| Field | Value |
| --- | --- |
| Email | `admin@clipforge.local` |
| Password | `admin_change_me` |

**Change these in `.env` before going to production** (`ADMIN_EMAIL` /
`ADMIN_PASSWORD`). If the admin already exists at first boot, the bootstrap
is a no-op — use `/api/v1/users/{id}` (admin-only) to change it.

## Production hardening

This is a *checklist*. None of these are on by default because they all
involve a real-world trade-off (cost, complexity, vendor lock-in).

### Must-do

- [ ] Replace `SECRET_KEY` and `JWT_SECRET` with strong random values:
  ```bash
  openssl rand -hex 32
  ```
- [ ] Change `ADMIN_EMAIL` / `ADMIN_PASSWORD` and the password of the
  bootstrap admin.
- [ ] Set `APP_ENV=production`, `APP_DEBUG=false`.
- [ ] Front the app with HTTPS (Caddy, nginx, Cloudflare, …).
- [ ] Restrict `CORS_ALLOW_ORIGINS` to your real domain.
- [ ] Set `DEMO_MODE=false` once you have a real AI provider configured.
- [ ] Set `STORAGE_BACKEND=s3` (or `r2`, `minio`) and configure credentials.
- [ ] Make sure the database is on a private network.
- [ ] Backups: enable PITR on Postgres, snapshot the storage bucket.

### Recommended

- [ ] Configure a real AI provider (`OPENAI_API_KEY` or similar).
- [ ] Configure a real transcription provider (`TRANSCRIPTION_PROVIDER=whisper`).
- [ ] Run **multiple worker replicas** to scale renders:
  ```bash
  docker compose up -d --scale worker=4
  ```
- [ ] Mount a GPU on worker hosts and set `WHISPER_DEVICE=cuda`.
- [ ] Wire `SENTRY_DSN` for error reporting.
- [ ] Set up log shipping (the app emits structured JSON when
  `LOG_FORMAT=json`).
- [ ] Add rate limiting at the load-balancer layer (the app has a basic
  in-process rate limiter but real production needs the LB).

### Optional

- [ ] Wire publish targets (YouTube, TikTok, Instagram, Facebook). Each
  one is a single file under `backend/app/services/export/` implementing
  the same interface. No UI work needed.
- [ ] Switch to a managed Postgres (RDS, Cloud SQL, Neon, Supabase).
- [ ] Move the workers to a separate VM/cluster.

## Single-VM production (no k8s)

This is the simplest "real" deploy. The `docker-compose.yml` is enough:

```bash
# On the server
git clone <your-repo> clipforge && cd clipforge
cp .env.example .env
# … edit .env …
docker compose up -d --build
# Set up HTTPS with Caddy in front:
sudo caddy reverse-proxy --from clipforge.example.com --to localhost:80
```

## Kubernetes

The Dockerfiles are multi-stage and minimal — they work on any container
runtime. Recommended layout:

```text
clipforge-frontend   →  Deployment + Service (ClusterIP)
clipforge-backend    →  Deployment + Service (ClusterIP)
clipforge-worker     →  Deployment (N replicas)  — no Service
postgres             →  StatefulSet (or managed)
redis                →  StatefulSet (or managed)
```

Use a `HorizontalPodAutoscaler` on the worker Deployment, driven by
`redis_queue_length` (Celery exposes this in its stats).

## Backup & restore

### Postgres

```bash
# Backup
docker compose exec -T postgres pg_dump -U clipforge clipforge > backup.sql
# Restore
cat backup.sql | docker compose exec -T postgres psql -U clipforge clipforge
```

### Storage

For S3 / R2 use the provider's native snapshotting. For local storage,
`tar czf data-$(date +%F).tgz data/`.

## Health & monitoring

- `GET /api/v1/health` — fast liveness probe.
- `GET /api/v1/health/deep` — DB, storage, ffmpeg, redis, AI, transcription.
- `GET /api/v1/admin/health-deep` — same, admin-gated, with provider info.
- The app logs structured JSON to `data/logs/clipforge.log` and stdout.
- Set `SENTRY_DSN` to forward errors to Sentry.

## Performance tips

- **Render throughput** is bounded by FFmpeg. Scale workers horizontally.
- **Transcription throughput** depends on `WHISPER_MODEL`. `tiny` is 32×
  faster than `large` at the cost of accuracy.
- **Database** is mostly read-heavy; add a connection pooler (PgBouncer) if
  you see "too many connections".
- **Frontend** is a static SPA — serve it from a CDN in production.
