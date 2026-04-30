#!/usr/bin/env bash
set -e

echo "=== Djungo Builder Publish ==="

echo ""
echo "=== Step 1 - Rebuild demo files ==="
python pipeline/build_all_from_input.py examples/case_001
python tools/publish_to_docs.py

echo ""
echo "=== Step 2 - Git status ==="
git status

echo ""
read -p "Commit message: " MSG

git add .
git commit -m "$MSG" || true
git push origin main

echo ""
echo "=== Step 3 - Hetzner sync ==="

ssh root@65.21.176.227 <<'EOF'
set -e

cd /opt/sheets.builder

git pull origin main

source venv/bin/activate
pip install -r requirements.txt

systemctl restart sheets-builder
systemctl status sheets-builder --no-pager

echo ""
echo "=== Health check ==="
curl -s https://builder.sgbh.org/health
EOF

echo ""
echo "=== Published successfully ==="