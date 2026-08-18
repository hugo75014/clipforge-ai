#!/usr/bin/env bash
# Sauvegarde quotidienne de la base ClipForge.
#
# Une sauvegarde jamais restaurée ne vaut rien : voir restore-test.sh, qui
# restaure réellement sur une base vierge. Tout échec part sur Telegram — une
# sauvegarde morte en silence est le pire des cas.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

env_get() { grep -E "^$1=" .env 2>/dev/null | head -1 | cut -d= -f2-; }
fail() { echo "$1" >&2; ./scripts/notify.sh "❌ Sauvegarde base de données ÉCHOUÉE

$1"; exit 1; }

BACKUP_DIR="${CLIPFORGE_BACKUP_DIR:-/var/backups/clipforge}"
KEEP_DAYS="${CLIPFORGE_BACKUP_KEEP_DAYS:-14}"
PG_USER="$(env_get POSTGRES_USER)"
PG_DB="$(env_get POSTGRES_DB)"
STAMP="$(date +%Y%m%d-%H%M%S)"
TARGET="$BACKUP_DIR/clipforge-$STAMP.dump"

mkdir -p "$BACKUP_DIR"

# Format personnalisé : compressé et restaurable table par table.
if ! docker compose exec -T postgres pg_dump -U "$PG_USER" -d "$PG_DB" -Fc > "$TARGET" 2>/tmp/clipforge-backup.err; then
  fail "pg_dump a échoué : $(tail -3 /tmp/clipforge-backup.err | tr '\n' ' ')"
fi

SIZE=$(stat -c%s "$TARGET" 2>/dev/null || echo 0)
if [ "$SIZE" -lt 1024 ]; then
  rm -f "$TARGET"
  fail "Sauvegarde suspecte : $SIZE octets. Fichier supprimé."
fi

find "$BACKUP_DIR" -name 'clipforge-*.dump' -mtime "+$KEEP_DAYS" -delete

echo "Sauvegarde : $TARGET ($((SIZE / 1024)) Kio)"
