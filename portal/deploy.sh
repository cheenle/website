#!/bin/bash
# VLSC Portal — deploy the unified landing page to the DocumentRoot.
#
# Scope: the DocumentRoot is SHARED. Sub-sites (mrrc/, efhw/, sunmrrc/,
# mrrc_ft710/, mrrc_modern/, sunsdrmobile/, mrrc_ft8/) sit beside the portal
# files, served by nginx alias, each owned by its own deploy script. Nothing
# here may touch a path this package does not write.
#
# Two defects this script used to have, both fixed:
#
#  1. The backup never ran. The ssh heredoc was unquoted (<< EOF), so the
#     inner $(ls -A $REMOTE_WEBROOT) was expanded by the *local* macOS shell,
#     where that path does not exist. It produced an empty string, the guard
#     was always false, the copy was silently skipped — and the script still
#     printed a "Backup location" that did not exist. Verified: zero landing_*
#     backups on the server after many deploys. Remote heredocs are now quoted
#     (<<'REMOTE') and variables are passed explicitly on the ssh command line.
#
#  2. The rollback hint was `rm -rf $REMOTE_WEBROOT/*` then restore the landing
#     backup — following it would delete every sub-site, and the (non-existent)
#     backup would not bring them back. /var/www is at 85% with 2.1G free, so a
#     full-DocumentRoot copy per deploy was not viable either. The backup now
#     covers exactly the paths this package writes.
#
# Requires SSH access. Usage: ./deploy.sh [--force]

set -euo pipefail

REMOTE_HOST="www.vlsc.net"
REMOTE_USER="cheenle"
REMOTE_WEBROOT="/var/www/vlsc.net"
STAMP="$(date +%Y%m%d_%H%M%S)"
LOCAL_PORTAL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_TGZ="/var/www/backups/landing_${STAMP}.tgz"
PKG="/tmp/vlsc_landing_${STAMP}.tar.gz"
LIST="/tmp/vlsc_landing_list_${STAMP}.txt"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

FORCE=0
if [ "${1:-}" = "--force" ]; then FORCE=1; fi

echo "=========================================="
echo "VLSC Portal Deployment"
echo "=========================================="
echo "Local:  $LOCAL_PORTAL_DIR"
echo "Remote: $REMOTE_WEBROOT (DocumentRoot, shared with sub-sites)"
echo ""

echo "Checking required files..."
for file in "index.html" "zh/index.html" "css/octen.css" "js/global-nav.js"; do
    if [ ! -f "$LOCAL_PORTAL_DIR/$file" ]; then
        echo -e "${RED}Error: Required file missing: $file${NC}"
        exit 1
    fi
    echo -e "${GREEN}OK${NC} $file"
done

# Build-time tooling must not ship. The old package was "the whole portal
# directory", which published tests/*.py and make_sitemap.py into the webroot:
# they were reachable at https://www.vlsc.net/tests/test_sitemap.py
echo ""
echo "Creating deployment package..."
tar -czf "$PKG" \
    --exclude='./deploy.sh' \
    --exclude='./tests' \
    --exclude='./.pytest_cache' \
    --exclude='./make_sitemap.py' \
    --exclude='./IMG_*' \
    --exclude='.DS_Store' \
    --exclude='__pycache__' \
    -C "$LOCAL_PORTAL_DIR" .

# Relative path of every file the package writes. Drives backup, ownership and
# rollback, so all three stay scoped to portal-owned content.
tar -tzf "$PKG" | sed 's|^\./||' | grep -v -e '^$' -e '/$' > "$LIST"
echo "  files: $(wc -l < "$LIST" | tr -d ' ')  size: $(du -h "$PKG" | cut -f1)"

if [ "$FORCE" -ne 1 ]; then
    echo ""
    echo "This overwrites portal-owned files in $REMOTE_WEBROOT and nothing else."
    read -p "Proceed? (y/N) " -r CONFIRM || true
    if [[ ! "${CONFIRM:-}" =~ ^[Yy]$ ]]; then
        echo "Aborted."
        rm -f "$PKG" "$LIST"
        exit 0
    fi
fi

echo ""
echo "Uploading..."
scp -q "$PKG" "$LIST" "$REMOTE_USER@$REMOTE_HOST:/tmp/"

# Single remote session. Quoted heredoc: nothing here is expanded locally,
# which is what silently killed the backup for the life of this script.
ssh "$REMOTE_USER@$REMOTE_HOST" \
    REMOTE_WEBROOT="$REMOTE_WEBROOT" PKG="$PKG" LIST="$LIST" BACKUP_TGZ="$BACKUP_TGZ" \
    bash -s <<'REMOTE'
set -euo pipefail

echo "Backing up portal-owned files that exist..."
sudo mkdir -p /var/www/backups
cd "$REMOTE_WEBROOT"
EXIST=/tmp/portal_existing.$$
: > "$EXIST"
while IFS= read -r p; do
    if [ -e "$p" ]; then printf '%s\n' "$p" >> "$EXIST"; fi
done < "$LIST"
if [ -s "$EXIST" ]; then
    sudo tar -czf "$BACKUP_TGZ" -T "$EXIST"
    echo "  $(sudo du -h "$BACKUP_TGZ" | cut -f1), $(wc -l < "$EXIST") files -> $BACKUP_TGZ"
else
    echo "  nothing to back up (first write at these paths)"
fi
rm -f "$EXIST"

echo "Extracting..."
sudo tar -xzf "$PKG" -C "$REMOTE_WEBROOT"

echo "Setting ownership (portal-owned top-level entries only)..."
for top in $(cut -d/ -f1 "$LIST" | sort -u); do
    sudo chown -R www-data:www-data "$REMOTE_WEBROOT/$top"
done
# Deliberately NOT chown -R / chmod -R "$REMOTE_WEBROOT": the DocumentRoot also
# holds every sub-site, and chmod -R 755 used to mark all their files executable.
sudo find "$REMOTE_WEBROOT" -maxdepth 1 -type f -exec sudo chmod 644 {} +
for d in css js images blog zh; do
    if [ -d "$REMOTE_WEBROOT/$d" ]; then
        sudo find "$REMOTE_WEBROOT/$d" -type f -exec sudo chmod 644 {} +
        sudo find "$REMOTE_WEBROOT/$d" -type d -exec sudo chmod 755 {} +
    fi
done

echo "Pruning tooling that older versions of this script published..."
sudo rm -rf "$REMOTE_WEBROOT/tests" "$REMOTE_WEBROOT/.pytest_cache"
sudo rm -f "$REMOTE_WEBROOT/make_sitemap.py"

rm -f "$PKG" "$LIST"

echo "Reloading nginx..."
sudo nginx -t
sudo systemctl reload nginx
echo "Portal deployment completed."
REMOTE

rm -f "$PKG" "$LIST"

echo ""
echo "=========================================="
echo -e "${GREEN}Deployment Complete!${NC}"
echo "=========================================="
echo "Landing page: https://$REMOTE_HOST/"
echo "Backup:       $BACKUP_TGZ"
echo ""
echo "To verify:"
echo "  curl -sI https://$REMOTE_HOST/ | head -1"
echo "  curl -s  https://$REMOTE_HOST/sitemap.xml | grep -c '<loc>'"
echo ""
echo -e "${YELLOW}Rollback (restores portal files only):${NC}"
echo "  ssh $REMOTE_USER@$REMOTE_HOST"
echo "  sudo tar -xzf $BACKUP_TGZ -C $REMOTE_WEBROOT"
echo ""
echo -e "${RED}Never 'rm -rf $REMOTE_WEBROOT/*' to roll back:${NC}"
echo "  the sub-sites share this DocumentRoot and are not in this backup."
