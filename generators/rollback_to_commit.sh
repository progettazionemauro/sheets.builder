#!/usr/bin/env bash
set -e

if [ -z "$1" ]; then
  echo "Usage: ./rollback_to_commit.sh <commit-hash>"
  exit 1
fi

TARGET="$1"

echo "=== Creating rollback branch from current state ==="
git status
read -p "Continue rollback to $TARGET? Type YES: " CONFIRM

if [ "$CONFIRM" != "YES" ]; then
  echo "Aborted."
  exit 1
fi

echo "=== Reset local working tree to target commit ==="
git reset --hard "$TARGET"

echo "=== Rebuild generated demo files ==="
python pipeline/build_all_from_input.py examples/case_001
python tools/publish_to_docs.py

echo "=== Commit rollback state ==="
git add .
git commit -m "Rollback to stable state $TARGET" || true

echo "=== Push to GitHub ==="
git push origin main --force-with-lease

echo "=== Sync Hetzner ==="
ssh root@65.21.176.227 <<'EOF'
set -e
cd /opt/sheets.builder
git fetch origin
git reset --hard origin/main
source venv/bin/activate
pip install -r requirements.txt
systemctl restart sheets-builder
systemctl status sheets-builder --no-pager
curl -s https://builder.sgbh.org/health
EOF

echo "=== Rollback published successfully ==="