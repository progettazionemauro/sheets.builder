#!/usr/bin/env bash
set -e

echo "=== Djungo Publish ==="

git status

echo ""
read -p "Commit message: " MSG

git add .
git commit -m "$MSG" || true
git push origin main

ssh root@65.21.176.227 <<'EOF'
set -e

cd /opt/sheets.builder

git clean -f
git pull origin main

source venv/bin/activate
pip install -r requirements.txt

systemctl restart sheets-builder
systemctl status sheets-builder --no-pager

curl -s https://builder.sgbh.org/health
EOF

echo ""
echo "=== Published successfully ==="