#!/usr/bin/env bash
# ClipForge AI — pre-flight audit
# Verifies that the project is internally consistent and ready to ship.

set -uo pipefail
cd "$(dirname "$0")/.."

GREEN="\033[1;32m"
RED="\033[1;31m"
YELLOW="\033[1;33m"
CYAN="\033[1;36m"
NC="\033[0m"

PASS=0
FAIL=0
WARN=0

pass() { echo -e "${GREEN}✓${NC} $1"; PASS=$((PASS + 1)); }
fail() { echo -e "${RED}✗${NC} $1"; FAIL=$((FAIL + 1)); }
warn() { echo -e "${YELLOW}!${NC} $1"; WARN=$((WARN + 1)); }
hdr()  { echo -e "\n${CYAN}── $1 ──${NC}"; }

# =============================================================================
# 1) Project layout
# =============================================================================
hdr "Project layout"
for d in frontend backend workers video_engine ai_engine storage database shared docker docs; do
  if [ -d "$d" ]; then pass "directory $d/ present"; else fail "directory $d/ missing"; fi
done
for f in README.md LICENSE Makefile docker-compose.yml .env.example; do
  if [ -f "$f" ]; then pass "file $f present"; else fail "file $f missing"; fi
done

# =============================================================================
# 2) Python syntax (best-effort — requires python3)
# =============================================================================
hdr "Python syntax"
if command -v python3 >/dev/null 2>&1; then
  if python3 -m compileall -q backend/app backend/alembic video_engine ai_engine shared workers 2>/dev/null; then
    pass "Python sources compile"
  else
    fail "Python sources have syntax errors (run python3 -m compileall backend workers video_engine ai_engine shared for details)"
  fi
else
  warn "python3 not available — skipped Python syntax check"
fi

# =============================================================================
# 3) Frontend syntax (best-effort)
# =============================================================================
hdr "Frontend syntax"
if [ -d frontend/node_modules ]; then
  if (cd frontend && npx --no-install tsc --noEmit) >/dev/null 2>&1; then
    pass "TypeScript compiles cleanly"
  else
    fail "TypeScript has errors (run cd frontend && npx tsc --noEmit)"
  fi
else
  warn "frontend/node_modules not present — skipped TypeScript check (run 'npm install' in frontend/)"
fi

# =============================================================================
# 4) Environment
# =============================================================================
hdr "Environment"
if [ -f .env ]; then
  pass ".env file present"
  for k in SECRET_KEY JWT_SECRET POSTGRES_PASSWORD; do
    if grep -qE "^${k}=" .env; then
      v=$(grep -E "^${k}=" .env | head -1 | cut -d= -f2-)
      if [ -z "$v" ] || [ "$v" = "change-me" ]; then
        warn "$k is set to a placeholder — replace before production"
      else
        pass "$k set"
      fi
    else
      fail "$k missing in .env"
    fi
  done
else
  warn ".env not present — copy .env.example to .env and configure"
fi

# =============================================================================
# 5) FFmpeg / ffprobe
# =============================================================================
hdr "System tools"
if command -v ffmpeg >/dev/null 2>&1; then
  pass "ffmpeg installed: $(ffmpeg -version | head -1)"
else
  fail "ffmpeg not installed"
fi
if command -v ffprobe >/dev/null 2>&1; then
  pass "ffprobe installed"
else
  fail "ffprobe not installed"
fi

# =============================================================================
# 6) Docker
# =============================================================================
hdr "Docker"
if command -v docker >/dev/null 2>&1; then
  pass "docker installed: $(docker --version)"
  if docker compose version >/dev/null 2>&1; then
    pass "docker compose plugin available"
  else
    warn "docker compose plugin not detected — install docker-compose-plugin"
  fi
  if [ -f docker-compose.yml ]; then
    if docker compose config >/dev/null 2>&1; then
      pass "docker-compose.yml is valid"
    else
      fail "docker-compose.yml has errors"
    fi
  fi
else
  warn "docker not installed — required for 'docker compose up'"
fi

# =============================================================================
# 7) Tests
# =============================================================================
hdr "Tests"
for f in backend/tests/unit/test_shared.py backend/tests/unit/test_ai_engine.py backend/tests/unit/test_subtitles.py backend/tests/e2e/test_workflow.py; do
  if [ -f "$f" ]; then pass "test $f present"; else fail "test $f missing"; fi
done

# =============================================================================
# Summary
# =============================================================================
echo
echo -e "${CYAN}══ Summary ══${NC}"
echo -e "  ${GREEN}pass: $PASS${NC}"
echo -e "  ${YELLOW}warn: $WARN${NC}"
echo -e "  ${RED}fail: $FAIL${NC}"
echo

if [ $FAIL -gt 0 ]; then
  echo -e "${RED}Audit failed — fix the items above before going to production.${NC}"
  exit 1
fi
echo -e "${GREEN}Audit passed.${NC}"
