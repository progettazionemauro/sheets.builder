#!/usr/bin/env bash
set -euo pipefail

BRANCH="level-b-persistent-backend"
HOST="root@65.21.176.227"
REMOTE_DIR="/opt/sheets.builder"

if [[ "${1:-}" != "--dry-run" || $# -ne 1 ]]; then
    echo "Uso: ./publish.sh --dry-run"
    echo "Questa versione non esegue pubblicazioni."
    exit 2
fi

echo "=== DJUNGO — TRISYNC DRY RUN ==="

echo
echo "=== 1. Repository locale ==="
test "$(git branch --show-current)" = "$BRANCH" || {
    echo "STOP: branch locale non corretto."
    exit 1
}

git log -1 --oneline
git status --short

echo
echo "=== 2. File sorgente modificati ==="
git diff --name-only -- \
    . \
    ':!data/' \
    ':!output/' \
    ':!docs/index.html' \
    ':!docs/viewer.html' \
    ':!docs/codice.gs' \
    ':!codice.gs'

echo
echo "=== 3. GitHub ==="
git fetch origin "$BRANCH"
LOCAL_COMMIT="$(git rev-parse HEAD)"
GITHUB_COMMIT="$(git rev-parse "origin/$BRANCH")"

echo "Locale: $LOCAL_COMMIT"
echo "GitHub: $GITHUB_COMMIT"

echo
echo "=== 4. Hetzner staging ==="
ssh "$HOST" "cd '$REMOTE_DIR' && \
    echo 'Commit:' && git log -1 --oneline && \
    echo 'Modifiche operative:' && git status --short"

echo
echo "=== 5. Documentazione ==="
git status --short -- README.md HANDOVER.md docs/MANUALE_TECNICO.md

echo
echo "=== DRY RUN COMPLETATO ==="
echo "Nessun commit, push o deployment eseguito."
