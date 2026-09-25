#!/bin/bash
#
# deploy.sh — Deploy 易占 to www.vlsc.net/yijing/
# Usage: ./deploy.sh [--force]
#
set -e

LOCAL_WEBSITE_DIR="/Users/cheenle/HAM/website/yijing"
REMOTE_HOST="www.vlsc.net"
REMOTE_USER="cheenle"
REMOTE_WEBROOT="/var/www/vlsc.net/yijing"
BACKUP_DIR="/tmp/yijing_backup_$(date +%Y%m%d_%H%M%S)"
TARBALL="/tmp/yijing_site_$(date +%Y%m%d_%H%M%S).tar.gz"

echo "=========================================="
echo "  易占 Deployment"
echo "  Target: ${REMOTE_HOST}:${REMOTE_WEBROOT}"
echo "=========================================="
echo ""

# Data validation gate — 64 卦数据不全不准上线。
# env -u：批次撰写期若 shell 里导出过 ALLOW_PARTIAL，不得渗进部署门。
echo "[..] Running check_hexagrams.py (strict)..."
env -u ALLOW_PARTIAL /usr/bin/python3 "${LOCAL_WEBSITE_DIR}/check_hexagrams.py"

# Check required files
for f in "index.html" "css/yijing.css" "js/app.js" "js/cast.js" "js/gua.js" "js/data/trigrams.js" "js/data/hexagrams.js" "server/llm_proxy.py"; do
    if [ ! -f "${LOCAL_WEBSITE_DIR}/${f}" ]; then
        echo "ERROR: Required file not found: ${LOCAL_WEBSITE_DIR}/${f}"
        exit 1
    fi
done
echo "[OK] Required files present."

# Create tarball（工具脚本与测试不进 webroot）
echo "[..] Creating tarball..."
cd "$(dirname "${LOCAL_WEBSITE_DIR}")"
tar czf "${TARBALL}" \
    --exclude='yijing/check_hexagrams.py' \
    --exclude='yijing/deploy.sh' \
    --exclude='yijing/tests' \
    --exclude='yijing/server/llm.env.example' \
    --exclude='yijing/.DS_Store' \
    yijing/
echo "[OK] Tarball created: ${TARBALL}"

# Confirm
if [ "$1" != "--force" ]; then
    echo ""
    echo "This will deploy to https://www.vlsc.net/yijing/"
    read -p "Proceed? (y/N) " -r CONFIRM
    if [[ ! "${CONFIRM}" =~ ^[Yy]$ ]]; then
        echo "Aborted."
        rm -f "${TARBALL}"
        exit 0
    fi
fi

# Backup current site
echo "[..] Backing up current site..."
ssh "${REMOTE_USER}@${REMOTE_HOST}" "
    if [ -d ${REMOTE_WEBROOT} ]; then
        sudo mkdir -p ${BACKUP_DIR} && sudo cp -a ${REMOTE_WEBROOT}/* ${BACKUP_DIR}/ 2>/dev/null || true
        echo 'Backup: ${BACKUP_DIR}'
    else
        echo 'No existing site to back up.'
    fi
"

# Upload
echo "[..] Uploading..."
scp "${TARBALL}" "${REMOTE_USER}@${REMOTE_HOST}:/tmp/"

# Extract and set permissions
echo "[..] Extracting and setting permissions..."
ssh "${REMOTE_USER}@${REMOTE_HOST}" "
    sudo rm -rf ${REMOTE_WEBROOT}/* 2>/dev/null || true
    sudo mkdir -p ${REMOTE_WEBROOT}
    sudo tar xzf /tmp/yijing_site_*.tar.gz -C /var/www/vlsc.net/
    sudo chown -R www-data:www-data ${REMOTE_WEBROOT}
    sudo find ${REMOTE_WEBROOT} -type d -exec chmod 755 {} \;
    sudo find ${REMOTE_WEBROOT} -type f -exec chmod 644 {} \;
    rm -f /tmp/yijing_site_*.tar.gz
    echo '[OK] Files extracted to ${REMOTE_WEBROOT}'
"

# Reload nginx
echo "[..] Reloading nginx..."
ssh "${REMOTE_USER}@${REMOTE_HOST}" "sudo nginx -t && sudo systemctl reload nginx"
echo "[OK] nginx reloaded."

# Cleanup
rm -f "${TARBALL}"

echo ""
echo "=========================================="
echo "  Deployment Complete!"
echo "  URL: https://www.vlsc.net/yijing/"
echo "=========================================="
