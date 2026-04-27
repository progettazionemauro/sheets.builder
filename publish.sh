#!/usr/bin/env bash
set -e

echo "=== GitHub push + Hetzner sync ==="

git push origin main

ssh root@65.21.176.227 <<'EOF'
set -e

cd /opt/sheets.builder
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
systemctl restart sheets-builder
systemctl status sheets-builder --no-pager
EOF

echo "=== Published successfully ==="