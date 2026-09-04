#!/bin/bash
#
# deploy.sh — Deploy EFHW website to www.vlsc.net/efhw/
# Usage: ./deploy.sh [--force]
#
set -e

LOCAL_WEBSITE_DIR="/Users/cheenle/HAM/website/efhw"
REMOTE_HOST="www.vlsc.net"
REMOTE_USER="cheenle"
REMOTE_WEBROOT="/var/www/vlsc.net/efhw"
BACKUP_DIR="/tmp/efhw_backup_$(date +%Y%m%d_%H%M%S)"
TARBALL="/tmp/efhw_site_$(date +%Y%m%d_%H%M%S).tar.gz"

echo "=========================================="
echo "  EFHW Website Deployment"
echo "  Target: ${REMOTE_HOST}:${REMOTE_WEBROOT}"
echo "=========================================="
echo ""

# Check required files
for f in "index.html" "baluns.html" "zh/baluns.html" "css/octen.css" "js/global-nav.js"; do
    if [ ! -f "${LOCAL_WEBSITE_DIR}/${f}" ]; then
        echo "ERROR: Required file not found: ${LOCAL_WEBSITE_DIR}/${f}"
        exit 1
    fi
done
echo "[OK] Required files present."

# Create tarball
echo "[..] Creating tarball..."
cd "$(dirname "${LOCAL_WEBSITE_DIR}")"
tar czf "${TARBALL}" efhw/
echo "[OK] Tarball created: ${TARBALL}"

# Confirm
if [ "$1" != "--force" ]; then
    echo ""
    echo "This will deploy to https://www.vlsc.net/efhw/"
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
    sudo tar xzf /tmp/efhw_site_*.tar.gz -C /var/www/vlsc.net/
    sudo chown -R www-data:www-data ${REMOTE_WEBROOT}
    sudo find ${REMOTE_WEBROOT} -type d -exec chmod 755 {} \;
    sudo find ${REMOTE_WEBROOT} -type f -exec chmod 644 {} \;
    rm -f /tmp/efhw_site_*.tar.gz
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
echo "  URL: https://www.vlsc.net/efhw/"
echo "=========================================="
