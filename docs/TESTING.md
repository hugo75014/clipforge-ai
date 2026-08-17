# Testing

```bash
# Backend (Python)
cd backend
pip install -e ".[dev]"
pytest -q

# Frontend
cd frontend
npm install
npm run lint
npm run typecheck
```

## Test layout

```text
backend/tests/
├── conftest.py             # fixtures: db_session, client, user, auth_headers
├── unit/
│   ├── test_shared.py      # shared/utils (formatting, hashing, …)
│   ├── test_ai_engine.py   # AI scoring
│   ├── test_subtitles.py   # SRT/VTT writers, clip_transcript
│   └── test_video_engine.py# FFmpeg probe on a synthetic 1-second video
└── e2e/
    └── test_workflow.py    # register → project → upload → analyze → render
```

## End-to-end

`tests/e2e/test_workflow.py` exercises the **full pipeline**:

1. Register / login
2. Create a project
3. Upload a generated 3-second test video
4. Run the synchronous analyze
5. Verify the project has clips and a transcript
6. Render the first clip
7. Verify a render URL exists

The test is automatically skipped if ffmpeg is not installed.

## Demo-mode in tests

All tests run against `DEMO_MODE=true` and the demo providers. The demo
output is deterministic given the same input — so the assertions are
stable.

## Coverage

```bash
cd backend
pytest --cov=app --cov=video_engine --cov=ai_engine --cov-report=term-missing
```

## Manual smoke test

```bash
# 1. Boot the stack
docker compose up -d --build

# 2. Log in as the bootstrap admin
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@clipforge.local","password":"admin_change_me"}'

# 3. Create a project
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"title":"smoke"}'

# 4. Upload + analyze + render
# … see API.md …
```

## CI suggestions

```yaml
# .github/workflows/ci.yml
name: ci
on: [push, pull_request]
jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: sudo apt-get install -y ffmpeg
      - run: cd backend && pip install -e ".[dev]" && pytest -q
  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: cd frontend && npm install && npm run lint && npm run typecheck
```
