#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

MODE="${1:---dry-run}"

if [[ ( "$MODE" != "--dry-run" && "$MODE" != "--run" ) || $# -gt 1 ]]; then
    echo "Uso: ./checkpoint.sh --dry-run | --run"
    exit 2
fi

BRANCH="level-b-persistent-backend"

if [[ "$(git branch --show-current)" != "$BRANCH" ]]; then
    echo "STOP: branch non corretto"
    exit 1
fi

allowed_source() {
    case "$1" in
        server.py|wsgi.py|build_from_config.py|requirements.txt|\
        publish.sh|checkpoint.sh|\
        app/*.py|generators/*.py|pipeline/*.py|tools/*.py|\
        docs/app_ready.html|docs/builder.html|\
        docs/generate.html|docs/review.html)
            return 0 ;;
        *)
            return 1 ;;
    esac
}

allowed_docs() {
    case "$1" in
        README.md|HANDOVER.md|PROJECT_STATE_DUMP.md|\
        docs/MANUALE_TECNICO.md)
            return 0 ;;
        *)
            return 1 ;;
    esac
}

gas_source() {
    case "$1" in
        google/*.gs|google/appsscript.json)
            return 0 ;;
        *)
            return 1 ;;
    esac
}

complete_deployment() {
    echo
    echo "=== PREFLIGHT STAGING ==="

    if ! ./publish.sh --dry-run; then
        echo "STOP: preflight staging non superato."
        echo "Il commit GitHub rimane invariato."
        return 1
    fi

    echo
    read -r -p "Scrivi STAGING per verificare/distribuire su Hetzner: " DEPLOY
    if [[ "$DEPLOY" != "STAGING" ]]; then
        echo "Distribuzione staging rinviata."
        return 0
    fi

    ./publish.sh --staging

    echo
    echo "=== CHECKPOINT COMPLETATO ==="
    echo "GitHub e Hetzner staging allineati."
}

echo "=== DJUNGO CHECKPOINT — ANTEPRIMA ==="
echo "Branch: $BRANCH"
echo

if ! git diff --cached --quiet; then
    echo "ATTENZIONE: sono presenti modifiche già in staging Git."
    echo "Il checkpoint operativo dovrà verificarle prima di procedere."
    echo
fi

mapfile -d '' -t FILES < <(
    {
        git diff --name-only -z HEAD
        git ls-files --others --exclude-standard -z
    } | sort -zu
)

SOURCES=0
DOCS=0
GAS=0
EXCLUDED=0

for file in "${FILES[@]}"; do
    if allowed_source "$file"; then
        echo "SORGENTE:       $file"
        ((SOURCES+=1))
    elif allowed_docs "$file"; then
        echo "DOCUMENTAZIONE: $file"
        ((DOCS+=1))
    elif gas_source "$file"; then
        echo "GAS DA VERIFICARE: $file"
        ((GAS+=1))
    else
        echo "ESCLUSO:       $file"
        ((EXCLUDED+=1))
    fi
done

echo
echo "=== RIEPILOGO ==="
echo "Sorgenti:       $SOURCES"
echo "Documentazione: $DOCS"
echo "GAS:           $GAS"
echo "Esclusi:       $EXCLUDED"
echo
if [[ "$MODE" == "--dry-run" ]]; then
    echo "DRY RUN: nessun file modificato o pubblicato."
    exit 0
fi

echo
echo "=== CONTROLLI PRELIMINARI ==="

git fetch origin "$BRANCH"

LOCAL_HEAD="$(git rev-parse HEAD)"
REMOTE_HEAD="$(git rev-parse "origin/$BRANCH")"

if [[ "$LOCAL_HEAD" != "$REMOTE_HEAD" ]]; then
    if ! git merge-base --is-ancestor "$REMOTE_HEAD" "$LOCAL_HEAD"; then
        echo "STOP: GitHub è avanti o la cronologia è divergente."
        echo "Nessun push automatico consentito."
        exit 1
    fi

    echo
    echo "=== CHECKPOINT LOCALE DA COMPLETARE ==="
    git log --oneline "$REMOTE_HEAD..$LOCAL_HEAD"

    echo
    echo "=== VERIFICA FILE DEI COMMIT DA RECUPERARE ==="

    mapfile -t PENDING_COMMITS < <(
        git rev-list --reverse "$REMOTE_HEAD..$LOCAL_HEAD"
    )

    for commit in "${PENDING_COMMITS[@]}"; do
        echo "Verifica commit: $(git rev-parse --short "$commit")"

        PARENTS="$(git rev-list --parents -n 1 "$commit")"
        read -r -a PARENT_ARRAY <<< "$PARENTS"

        if (( ${#PARENT_ARRAY[@]} != 2 )); then
            echo "STOP: commit di merge o senza un unico genitore."
            echo "Richiesta verifica manuale: $commit"
            exit 1
        fi

        mapfile -d '' -t PENDING_FILES < <(
            git diff-tree --root --no-commit-id --name-only                 -r -z --no-renames "$commit"
        )

        for file in "${PENDING_FILES[@]}"; do
            if allowed_source "$file" || allowed_docs "$file"; then
                echo "  AUTORIZZATO: $file"
            else
                echo "STOP: file non autorizzato nel commit $commit: $file"
                exit 1
            fi
        done
    done

    if ! git diff --cached --quiet || [[ -n "$(git ls-files -u)" ]]; then
        echo "STOP: staging Git non vuoto o conflitti presenti."
        exit 1
    fi

    read -r -p "Scrivi RIPRENDI per completare il push: " CONFIRM
    [[ "$CONFIRM" == "RIPRENDI" ]] || exit 0

    git push origin "$BRANCH"
    echo "Push completato."
    complete_deployment
    exit $?
fi

if ! git diff --cached --quiet || [[ -n "$(git ls-files -u)" ]]; then
    echo "STOP: area di staging Git non vuota o conflitti presenti"
    exit 1
fi

SELECTED=()
HAS_CODE=0
HAS_HANDOVER=0
HAS_MANUAL=0

for file in "${FILES[@]}"; do
    if allowed_source "$file"; then
        SELECTED+=("$file")
        HAS_CODE=1
    elif allowed_docs "$file"; then
        SELECTED+=("$file")
        [[ "$file" == "HANDOVER.md" ]] && HAS_HANDOVER=1
        [[ "$file" == "docs/MANUALE_TECNICO.md" ]] && HAS_MANUAL=1
    elif gas_source "$file"; then
        echo "STOP: modifiche GAS da verificare separatamente: $file"
        exit 1
    fi
done

if (( ${#SELECTED[@]} == 0 )); then
    echo "Nessuna nuova modifica autorizzata."
    complete_deployment
    exit $?
fi

if (( HAS_CODE && (!HAS_HANDOVER || !HAS_MANUAL) )); then
    echo "STOP: modifiche al codice senza aggiornamento di entrambi i documenti."
    exit 1
fi

echo
echo "File selezionati:"
printf '  %s\n' "${SELECTED[@]}"

echo
read -r -p "Descrizione del checkpoint: " MESSAGE
[[ -n "$MESSAGE" ]] || {
    echo "STOP: descrizione obbligatoria"
    exit 1
}

echo
echo "Verranno eseguiti commit e push su GitHub."
read -r -p "Scrivi PUBBLICA per confermare: " CONFIRM
[[ "$CONFIRM" == "PUBBLICA" ]] || {
    echo "Operazione annullata"
    exit 0
}

echo
echo "=== VERIFICA FINALE DEI FILE ==="

mapfile -d '' -t CURRENT < <(
    {
        git diff --name-only -z HEAD
        git ls-files --others --exclude-standard -z
    } | sort -zu
)

for file in "${SELECTED[@]}"; do
    if [[ ! -f "$file" || -L "$file" ]]; then
        echo "STOP: file assente o collegamento simbolico: $file"
        exit 1
    fi
done

for file in "${CURRENT[@]}"; do
    if allowed_source "$file" || allowed_docs "$file"; then
        FOUND=0
        for selected in "${SELECTED[@]}"; do
            [[ "$file" == "$selected" ]] && FOUND=1
        done
        if [[ "$FOUND" -ne 1 ]]; then
            echo "STOP: selezione cambiata durante il checkpoint: $file"
            exit 1
        fi
    fi
done

git add -- "${SELECTED[@]}"
git diff --cached --check
git commit -m "$MESSAGE"
git push origin "$BRANCH"

echo
echo "=== GITHUB AGGIORNATO ==="
echo "Commit: $(git rev-parse --short HEAD)"

complete_deployment
