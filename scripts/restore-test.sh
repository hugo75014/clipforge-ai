#!/usr/bin/env bash
# Restaure la dernière sauvegarde sur une base jetable et vérifie qu'elle
# contient bien des données. Sans cette étape, « la sauvegarde tourne » ne dit
# rien sur « la sauvegarde est restaurable ».
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

env_get() { grep -E "^$1=" .env 2>/dev/null | head -1 | cut -d= -f2-; }
fail() { echo "$1" >&2; ./scripts/notify.sh "❌ Test de restauration ÉCHOUÉ

$1"; exit 1; }

BACKUP_DIR="${CLIPFORGE_BACKUP_DIR:-/var/backups/clipforge}"
PG_USER="$(env_get POSTGRES_USER)"
TEST_DB="clipforge_restore_test"

LATEST=$(ls -t "$BACKUP_DIR"/clipforge-*.dump 2>/dev/null | head -1)
[ -n "$LATEST" ] || fail "Aucune sauvegarde trouvée dans $BACKUP_DIR."

docker compose exec -T postgres psql -U "$PG_USER" -d postgres -c "DROP DATABASE IF EXISTS $TEST_DB;" > /dev/null
docker compose exec -T postgres psql -U "$PG_USER" -d postgres -c "CREATE DATABASE $TEST_DB;" > /dev/null

if ! docker compose exec -T postgres pg_restore -U "$PG_USER" -d "$TEST_DB" --no-owner < "$LATEST" > /dev/null 2>&1; then
  docker compose exec -T postgres psql -U "$PG_USER" -d postgres -c "DROP DATABASE IF EXISTS $TEST_DB;" > /dev/null
  fail "pg_restore a refusé $LATEST."
fi

TABLES=$(docker compose exec -T postgres psql -U "$PG_USER" -d "$TEST_DB" -tAc \
  "select count(*) from information_schema.tables where table_schema='public';" | tr -d '\r ')
docker compose exec -T postgres psql -U "$PG_USER" -d postgres -c "DROP DATABASE IF EXISTS $TEST_DB;" > /dev/null

[ "${TABLES:-0}" -ge 5 ] || fail "Restauration vide : $TABLES tables dans $LATEST."

echo "Restauration vérifiée : $LATEST, $TABLES tables."
