#!/usr/bin/env bash
# Purge du stockage et surveillance du disque.
#
# Les fichiers temporaires d'un rendu interrompu ne sont supprimés par personne :
# sans cette purge, le disque se remplit lentement et le serveur tombe un matin
# sans prévenir.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

TEMP_DAYS="${CLIPFORGE_TEMP_KEEP_DAYS:-2}"
DISK_ALERT_PCT="${CLIPFORGE_DISK_ALERT_PCT:-85}"

# Fichiers de travail : rien à conserver au-delà de quelques jours.
docker compose exec -T backend sh -c \
  "find /app/data/temp -type f -mtime +$TEMP_DAYS -delete 2>/dev/null; find /app/data/temp -type d -empty -delete 2>/dev/null" || true

USED=$(df --output=pcent / | tail -1 | tr -dc '0-9')
DATA=$(docker compose exec -T backend sh -c "du -sh /app/data 2>/dev/null | cut -f1" | tr -d '\r')

echo "Disque : ${USED}% utilisé — données ClipForge : ${DATA:-inconnu}"

if [ "${USED:-0}" -ge "$DISK_ALERT_PCT" ]; then
  ./scripts/notify.sh "⚠️ Disque du VPS à ${USED} %

Données ClipForge : ${DATA:-inconnu}. Les rendus et sources s'accumulent dans le volume app-data ; supprimer d'anciens projets libère de la place."
fi
