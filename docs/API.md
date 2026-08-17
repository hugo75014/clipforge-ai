# API reference

The full live OpenAPI spec is at **`/docs`** on your running instance.
This is a short, hand-curated tour.

## Conventions

- All endpoints are prefixed with `/api/v1`.
- Auth uses `Authorization: Bearer <access_token>`.
- All responses are JSON.
- Errors: `{"detail": "...", "code": 4xx|5xx}`.

## Auth

| Method | Path | Body | Description |
| --- | --- | --- | --- |
| `POST` | `/auth/register` | `{email, password, name?}` | Create a new account (returns access + refresh tokens) |
| `POST` | `/auth/login` | `{email, password}` | Sign in |
| `POST` | `/auth/refresh` | `?refresh_token=…` | Exchange refresh token for a new access token |
| `GET`  | `/auth/me` | — | Current user |

## Projects

| Method | Path | Description |
| --- | --- | --- |
| `GET`   | `/projects?page=1&page_size=20&search=&status=&archived=` | List my projects (admin sees all) |
| `POST`  | `/projects` | Create a new project |
| `GET`   | `/projects/{id}` | Project detail (clips, transcript, recent jobs) |
| `PATCH` | `/projects/{id}` | Update title / description / status / config |
| `DELETE`| `/projects/{id}` | Delete (and all its clips/jobs) |
| `POST`  | `/projects/{id}/duplicate` | Duplicate the project |
| `POST`  | `/projects/{id}/archive` | Archive the project |
| `POST`  | `/projects/{id}/upload` | Multipart upload (`file` field) |
| `POST`  | `/projects/{id}/analyze` | Async analyze (returns a `Job`) |
| `POST`  | `/projects/{id}/analyze/sync` | Sync analyze (returns result directly) |
| `GET`   | `/projects/{id}/transcript` | Just the transcript |

## Clips

| Method | Path | Description |
| --- | --- | --- |
| `GET`   | `/clips/{id}` | Get a clip |
| `PATCH` | `/clips/{id}` | Edit a clip (start/end, title, hook, hashtags, config, …) |
| `DELETE`| `/clips/{id}` | Delete a clip |
| `POST`  | `/clips/reorder` | Bulk update `sort_order` / `selected` |
| `POST`  | `/clips/{id}/render` | Async render (returns a `Job`) |
| `POST`  | `/clips/{id}/render/sync` | Sync render |
| `POST`  | `/clips/{id}/ai-edit` | Natural-language AI edit (`{instruction: "…"}`) |

## Jobs

| Method | Path | Description |
| --- | --- | --- |
| `GET`  | `/jobs/{id}` | Job status, progress, error |
| `POST` | `/jobs/{id}/cancel` | Cancel a running job |

## Brand kits

| Method | Path | Description |
| --- | --- | --- |
| `GET`   | `/brand-kits` | List my kits |
| `POST`  | `/brand-kits` | Create |
| `PATCH` | `/brand-kits/{id}` | Update |
| `DELETE`| `/brand-kits/{id}` | Delete |

## Templates

| Method | Path | Description |
| --- | --- | --- |
| `GET`   | `/templates?category=&include_public=true` | List mine + public + built-in |
| `GET`   | `/templates/{id}` | Detail |
| `POST`  | `/templates` | Create a custom template |
| `PATCH` | `/templates/{id}` | Update |
| `DELETE`| `/templates/{id}` | Delete |

## Exports

| Method | Path | Description |
| --- | --- | --- |
| `GET`   | `/exports?project_id=&limit=` | History |
| `POST`  | `/exports` | Record a new export intent |
| `GET`   | `/exports/providers` | List publish targets & config status |

## AI

| Method | Path | Description |
| --- | --- | --- |
| `GET`  | `/ai/info` | Current provider, model, demo flag |
| `POST` | `/ai/complete` | Raw completion (great for debugging) |

## Users (admin)

| Method | Path | Description |
| --- | --- | --- |
| `GET`   | `/users` | List all users |
| `POST`  | `/users` | Create a user |
| `PATCH` | `/users/{id}` | Update |
| `DELETE`| `/users/{id}` | Delete |

## Admin

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/admin/stats` | Platform-wide KPIs |
| `GET` | `/admin/jobs?status=&type=` | Recent jobs |
| `GET` | `/admin/config` | Effective config (no secrets) |
| `GET` | `/admin/health-deep` | Per-component health check |

## Health

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Liveness |
| `GET` | `/health/deep` | DB, storage, ffmpeg, redis, AI, transcription |
