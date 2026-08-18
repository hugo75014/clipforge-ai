#!/usr/bin/env bash
# Envoi d'un message sur le canal Telegram partagé « Système Agentique ».
#
#   ./scripts/notify.sh "texte"
#
# Ne fait jamais échouer l'appelant : une alerte perdue ne doit pas transformer
# une sauvegarde réussie en échec.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Lecture ciblée : le .env contient des valeurs avec espaces, un `source` les
# exécuterait comme des commandes.
env_get() { grep -E "^$1=" "$ROOT/.env" 2>/dev/null | head -1 | cut -d= -f2-; }

TOKEN="$(env_get TELEGRAM_BOT_TOKEN)"
CHAT="$(env_get TELEGRAM_CHAT_ID)"
SOURCE="$(env_get TELEGRAM_SOURCE)"
MESSAGE="${1:-}"

[ -z "$TOKEN" ] || [ -z "$CHAT" ] || [ -z "$MESSAGE" ] && { echo "notify: configuration incomplète, message non envoyé" >&2; exit 0; }

curl -sS --max-time 15 -X POST \
  "https://api.telegram.org/bot${TOKEN}/sendMessage" \
  -d "chat_id=${CHAT}" \
  -d "parse_mode=HTML" \
  --data-urlencode "text=<b>[${SOURCE}]</b>
${MESSAGE}" > /dev/null || echo "notify: envoi échoué" >&2
exit 0
