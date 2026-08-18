#!/usr/bin/env bash
# Déploiement complet de ClipForge AI.
#
#   ./scripts/deploy.sh            front + backend
#   ./scripts/deploy.sh front      front seulement (Netlify)
#   ./scripts/deploy.sh backend    backend seulement (Docker sur le VPS)
#
# Les fichiers _redirects et _headers sont regénérés à chaque build : Netlify ne
# lit pas netlify.toml sur un dépôt de fichiers, et sans eux toute route profonde
# renvoie 404.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SITE_ID="307f67b2-a6a2-49df-887e-0d38cbaee502"
API_URL="https://api.clip.viralcuts.live"
TARGET="${1:-all}"

deploy_front() {
  echo "▸ Build du front (VITE_API_URL=$API_URL)"
  cd "$ROOT/frontend"
  npm ci --no-audit --no-fund
  VITE_API_URL="$API_URL" npm run build

  printf '/*  /index.html  200\n' > dist/_redirects
  cat > dist/_headers <<'HEADERS'
/*
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=()
  Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
/assets/*
  Cache-Control: public, max-age=31536000, immutable
/index.html
  Cache-Control: no-cache
/robots.txt
  Cache-Control: public, max-age=3600
/sitemap.xml
  Cache-Control: public, max-age=3600
/og.png
  Cache-Control: public, max-age=86400
HEADERS

  for f in _redirects _headers index.html robots.txt sitemap.xml; do
    [ -f "dist/$f" ] || { echo "✗ dist/$f manquant, déploiement annulé"; exit 1; }
  done

  echo "▸ Envoi sur Netlify"
  netlify deploy --prod --dir dist --site "$SITE_ID" --no-build
}

deploy_backend() {
  echo "▸ Reconstruction des images"
  cd "$ROOT"
  docker compose build backend worker
  docker compose up -d
}

check() {
  echo "▸ Vérification"
  for url in "https://clip.viralcuts.live" "https://clip.viralcuts.live/login" "$API_URL/api/v1/health"; do
    code=$(curl -sS -o /dev/null -w "%{http_code}" "$url")
    printf '  %-45s %s\n' "$url" "$code"
    [ "$code" = "200" ] || { echo "✗ $url répond $code"; exit 1; }
  done
  echo "✓ Déploiement vérifié"
}

case "$TARGET" in
  front)   deploy_front ;;
  backend) deploy_backend ;;
  all)     deploy_backend; deploy_front ;;
  *)       echo "Usage: $0 [all|front|backend]"; exit 1 ;;
esac
check
