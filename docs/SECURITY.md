# Security

This document lists the security mechanisms ClipForge AI ships with and the
operational practices we recommend.

## Authentication

- **JWT** with HS256, access (1h) + refresh (30d) tokens.
- **bcrypt** password hashing (cost 12).
- Stateless sessions — there is no session table.
- Logout is client-side (`localStorage.clear()`). If you need real
  revocation, add a denylist in Redis.

## Authorization

- Role-based access control with three roles: `admin`, `editor`, `viewer`.
- The default bootstrap account is `admin`.
- Routes that mutate other users' resources (`/users/{id}`, `/admin/*`) are
  admin-only.

## Input validation

- All Pydantic schemas validate types, lengths, and ranges at the boundary.
- File uploads are validated by **extension**, **MIME type**, and **size**.
- CORS is allow-list based (`CORS_ALLOW_ORIGINS`).
- SQL injection is prevented by SQLAlchemy 2 parameter binding.
- `safe_filename` strips dangerous characters and `..` from any user input
  that touches the filesystem.

## Rate limiting

- Per-user and per-IP limits via `app.core.security` + a `slowapi`-style
  dependency (configurable in `.env`).
- For real production, put a rate-limiter at the load-balancer layer.

## Secrets

- All secrets live in environment variables (`.env`, never in code).
- The frontend never receives a key — it only ever talks to the backend.
- AI provider keys are read **only** inside `app/providers/ai/*`.
- The `.env` file is `.gitignore`d.

## File handling

- Uploaded files are written to `data/uploads/<project_id>/<filename>` and
  never served from there directly — the API serves them through a
  sanitized `/media` mount.
- The local storage provider sanitizes keys, blocks `..` traversal, and
  resolves all paths before any I/O.
- Temporary files live in `data/temp/` and are cleaned up by the worker
  at the end of each render.

## Production hardening checklist

See [DEPLOYMENT.md](DEPLOYMENT.md#production-hardening) for the full list.
Highlights:

- [ ] Replace `SECRET_KEY` and `JWT_SECRET` with strong random values.
- [ ] Change `ADMIN_PASSWORD` from the default.
- [ ] Set `APP_DEBUG=false`, `APP_ENV=production`.
- [ ] Front with HTTPS.
- [ ] Restrict `CORS_ALLOW_ORIGINS` to your real domain(s).
- [ ] Run database and storage on a private network.
- [ ] Enable Postgres backups (PITR preferred).
- [ ] Set `SENTRY_DSN` for error tracking.

## What we **don't** do

- No password reset via email out of the box (the admin can issue a new
  password through `/users/{id}` PATCH).
- No 2FA. If you need it, add a TOTP layer on top of the JWT auth.
- No CSRF tokens. We're stateless + JWT + JSON APIs — CSRF doesn't apply
  as long as the front-end doesn't share cookies cross-origin.

## Reporting vulnerabilities

Open a GitHub issue with the `security` label, or email
<security@clipforge.ai>. Please do **not** open a public PR with a fix
before we coordinate a release.
