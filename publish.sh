#!/usr/bin/env bash
set -euo pipefail

BRANCH="level-b-persistent-backend"
HOST="root@65.21.176.227"
REMOTE_DIR="/opt/sheets.builder"

MODE="${1:-}"

if [[ $# -ne 1 || ( "$MODE" != "--dry-run" && "$MODE" != "--staging" ) ]]; then
    echo "Uso: ./publish.sh --dry-run | --staging"
    exit 2
fi

cd "$(dirname "$0")"

echo "=== DJUNGO — $MODE ==="

test "$(git branch --show-current)" = "$BRANCH" || {
    echo "STOP: branch locale non corretto"
    exit 1
}

git fetch origin "$BRANCH"

LOCAL="$(git rev-parse HEAD)"
GITHUB="$(git rev-parse "origin/$BRANCH")"

test "$LOCAL" = "$GITHUB" || {
    echo "STOP: Ubuntu e GitHub non allineati"
    exit 1
}

echo "Commit autorizzato: $LOCAL"

ssh "$HOST" bash -s -- "$MODE" "$BRANCH" "$REMOTE_DIR" "$GITHUB" <<'REMOTE'
set -euo pipefail

MODE="$1"
BRANCH="$2"
REMOTE_DIR="$3"
EXPECTED="$4"

cd "$REMOTE_DIR"

test "$(git branch --show-current)" = "$BRANCH" || {
    echo "STOP: branch staging errato"
    exit 1
}

git fetch origin "$BRANCH"

test "$(git rev-parse "origin/$BRANCH")" = "$EXPECTED" || {
    echo "STOP: GitHub cambiato durante la procedura"
    exit 1
}

git merge-base --is-ancestor HEAD "$EXPECTED" || {
    echo "STOP: aggiornamento non fast-forward"
    exit 1
}

echo
echo "=== Analisi file del commit ==="

mapfile -d '' -t CHANGED < <(
    git diff --name-only -z --no-renames HEAD "$EXPECTED"
)

mapfile -d '' -t LOCAL_MODIFIED < <(
    git diff --name-only -z HEAD
)

mapfile -d '' -t STAGED_MODIFIED < <(
    git diff --cached --name-only -z
)

mapfile -d '' -t UNTRACKED < <(
    git ls-files --others --exclude-standard -z
)

is_protected() {
    case "$1" in
        data/*|output/*|output_project/*|workdir/*|\
        backup_layout_before_cleanup/*|\
        codice.gs|*.gs|google/*|\
        docs/index.html|docs/viewer.html|\
        index.html|viewer.html)
            return 0 ;;
        *)
            return 1 ;;
    esac
}

for file in "${CHANGED[@]}"; do
    echo "Aggiornamento previsto: $file"

    if is_protected "$file"; then
        echo "STOP: percorso protetto nel commit: $file"
        exit 1
    fi

    for modified in "${LOCAL_MODIFIED[@]}" "${STAGED_MODIFIED[@]}"; do
        if [[ "$file" = "$modified" ]]; then
            echo "STOP: modifiche locali sul file: $file"
            exit 1
        fi
    done

    for untracked in "${UNTRACKED[@]}"; do
        if [[ "$file" = "$untracked" || "$file" = "$untracked/"* || "$untracked" = "$file/"* ]]; then
            echo "STOP: conflitto con file non tracciato: $untracked"
            exit 1
        fi
    done
done

echo
echo "Controlli preliminari: OK"
echo "File da aggiornare: ${#CHANGED[@]}"

if [[ "$MODE" = "--dry-run" ]]; then
    echo "DRY RUN: nessun deployment eseguito"
    exit 0
fi

echo
echo "=== Deployment staging ==="

if [[ "$(git rev-parse HEAD)" = "$EXPECTED" ]]; then
    echo "STAGING GIÀ ALLINEATO: nessun merge o riavvio necessario"
    exit 0
fi

git merge --ff-only "$EXPECTED"

test "$(git rev-parse HEAD)" = "$EXPECTED"

systemctl restart sheets-builder
systemctl is-active --quiet sheets-builder

curl -fsS -o /dev/null https://builder.sgbh.org/generate.html

echo "STAGING AGGIORNATO: $(git rev-parse --short HEAD)"
REMOTE
