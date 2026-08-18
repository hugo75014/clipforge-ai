#!/usr/bin/env bash
# Surveillance : API, front et conteneurs.
#
# N'alerte qu'au DEUXIÈME échec consécutif : une coupure réseau d'une seconde ne
# doit pas réveiller quelqu'un, et un canal qui crie pour rien finit ignoré.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

STATE="/var/lib/clipforge/health.state"
mkdir -p "$(dirname "$STATE")"
PREVIOUS="$(cat "$STATE" 2>/dev/null || echo ok)"
PROBLEMS=""

check_url() {
  code=$(curl -sS --max-time 20 -o /dev/null -w "%{http_code}" "$1" 2>/dev/null)
  [ "$code" = "200" ] || PROBLEMS="$PROBLEMS
• $1 répond $code"
}

check_url "https://clip.viralcuts.live"
check_url "https://api.clip.viralcuts.live/api/v1/health"

for service in postgres redis backend worker; do
  state=$(docker compose ps --format '{{.Service}} {{.State}}' 2>/dev/null | awk -v s="$service" '$1==s {print $2}')
  [ "$state" = "running" ] || PROBLEMS="$PROBLEMS
• conteneur $service : ${state:-absent}"
done

if [ -n "$PROBLEMS" ]; then
  if [ "$PREVIOUS" = "ko" ]; then
    ./scripts/notify.sh "🔴 ClipForge ne répond plus
$PROBLEMS"
  fi
  echo ko > "$STATE"
  echo "PROBLÈME :$PROBLEMS" >&2
  exit 1
fi

# Retour à la normale après une alerte : le dire, sinon on ignore que c'est réparé.
[ "$PREVIOUS" = "ko" ] && ./scripts/notify.sh "🟢 ClipForge est de nouveau en ligne."
echo ok > "$STATE"
echo "Tout répond."
