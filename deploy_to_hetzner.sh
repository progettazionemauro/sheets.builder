#!/usr/bin/env bash
set -e

echo "1) Controllo stato locale..."
git status

echo "2) Push su GitHub..."
git push origin main

echo "3) Deploy su Hetzner..."
ssh root@65.21.176.227 <<'EOF'
set -e
cd /opt/sheets.builder
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
systemctl restart sheets-builder
systemctl status sheets-builder --no-pager
curl -I https://builder.sgbh.org/generate.html
EOF

echo "Deploy completato."