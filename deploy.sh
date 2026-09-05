#!/bin/bash
# ════════════════════════════════════════════════════════════════════
# VLSC Unified Deploy — deploys all HAM-radio project sites to www.vlsc.net
#
# Usage:
#   ./deploy.sh                 # deploy all 7 sites (prompt to confirm)
#   ./deploy.sh portal          # deploy only named site(s)
#   ./deploy.sh mrrc sunmrrc    # deploy several
#   ./deploy.sh --yes           # skip confirmation prompt
#   ./deploy.sh --list          # list configured sites and exit
#
# Server: nginx on www.vlsc.net (HTTPS via Let's Encrypt).
# Each site is backed up before overwrite. Reloads nginx once at the end.
# ════════════════════════════════════════════════════════════════════
set -euo pipefail

# ── Config ──────────────────────────────────────────────────────────
REMOTE_HOST="www.vlsc.net"
REMOTE_USER="cheenle"
REMOTE_ROOT="/var/www/vlsc.net" # nginx DocumentRoot
BACKUP_BASE="/var/www/backups"

# Each site: key | local dir | remote subdir (under REMOTE_ROOT) | URL
SITES=(
	"portal|/Users/cheenle/HAM/website/portal||https://$REMOTE_HOST/"
	"mrrc|/Users/cheenle/HAM/MRRC/website|mrrc|https://$REMOTE_HOST/mrrc/"
	"mrrc_ft710|/Users/cheenle/HAM/mrrc_ft710/website|mrrc_ft710|https://$REMOTE_HOST/mrrc_ft710/"
	"mrrc_ft8|/Users/cheenle/HAM/ft8/website|mrrc_ft8|https://$REMOTE_HOST/mrrc_ft8/"
	"sunmrrc|/Users/cheenle/HAM/sunsdr/sunmrrc/website|sunmrrc|https://$REMOTE_HOST/sunmrrc/"
	"sunsdrmobile|/Users/cheenle/HAM/sunsdr/SunsdrMobile/website|sunsdrmobile|https://$REMOTE_HOST/sunsdrmobile/"
	"efhw|/Users/cheenle/HAM/website/efhw|efhw|https://$REMOTE_HOST/efhw/"
)

# Files/dirs to exclude from every site's tarball
EXCLUDES=(
	--exclude='deploy.sh'
	--exclude='.DS_Store'
	--exclude='.claude'
	--exclude='.iflow_logs'
	--exclude='stats'
	--exclude='logs'
	--exclude='node_modules'
	--exclude='*.tar.gz'
)

# ── Colors ──────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ── Functions ──────────────────────────────────────────────────────
usage() {
	sed -n '2,16p' "$0"
	echo
	echo "Available sites:"
	list_sites
}

list_sites() {
	for s in "${SITES[@]}"; do
		IFS='|' read -r key ldir rsub url <<<"$s"
		printf "  ${CYAN}%-14s${NC} %s\n" "$key" "$url"
	done
}

# ── Args ────────────────────────────────────────────────────────────
ASSUME_YES=0
ONLY=()
for arg in "$@"; do
	case "$arg" in
	--yes | -y) ASSUME_YES=1 ;;
	--list)
		list_sites
		exit 0
		;;
	-h | --help)
		usage
		exit 0
		;;
	*) ONLY+=("$arg") ;;
	esac
done

# Resolve which sites to deploy
DEPLOY_KEYS=()
for s in "${SITES[@]}"; do
	IFS='|' read -r key _ _ _ <<<"$s"
	if [ ${#ONLY[@]} -eq 0 ]; then
		DEPLOY_KEYS+=("$key")
	else
		for o in "${ONLY[@]}"; do
			[ "$o" = "$key" ] && DEPLOY_KEYS+=("$key")
		done
	fi
done

if [ ${#DEPLOY_KEYS[@]} -eq 0 ]; then
	echo -e "${RED}No matching sites.${NC} Known:"
	list_sites
	exit 1
fi

# ── Header ──────────────────────────────────────────────────────────
echo -e "${BOLD}══════════════════════════════════════════════════════════════"
echo -e "  VLSC Unified Deploy → $REMOTE_HOST (nginx)"
echo -e "══════════════════════════════════════════════════════════════${NC}"
echo -e "Sites to deploy:"
for k in "${DEPLOY_KEYS[@]}"; do
	for s in "${SITES[@]}"; do
		IFS='|' read -r key ldir rsub url <<<"$s"
		[ "$key" = "$k" ] && printf "  ${GREEN}•${NC} %-12s %s\n" "$key" "$url"
	done
done
echo

# ── Pre-flight: verify local dirs + required files ──────────────────
echo -e "${YELLOW}Pre-flight checks…${NC}"
for k in "${DEPLOY_KEYS[@]}"; do
	for s in "${SITES[@]}"; do
		IFS='|' read -r key ldir rsub url <<<"$s"
		[ "$key" = "$k" ] || continue
		if [ ! -d "$ldir" ]; then
			echo -e "  ${RED}✗ $key: local dir missing: $ldir${NC}"
			exit 1
		fi
		ok=1
		for f in index.html css/octen.css; do
			[ -f "$ldir/$f" ] || {
				echo -e "  ${RED}✗ $key: missing $f${NC}"
				ok=0
			}
		done
		[ -f "$ldir/js/global-nav.js" ] || {
			echo -e "  ${RED}✗ $key: missing js/global-nav.js${NC}"
			ok=0
		}
		[ $ok -eq 1 ] && echo -e "  ${GREEN}✓ $key${NC} ($ldir)"
	done
done
echo

# ── Confirm ─────────────────────────────────────────────────────────
if [ $ASSUME_YES -ne 1 ]; then
	read -rp "Deploy these ${#DEPLOY_KEYS[@]} site(s) to $REMOTE_HOST? [y/N] " confirm
	[[ "$confirm" =~ ^[yY]$ ]] || {
		echo "Cancelled."
		exit 0
	}
fi

TS="$(date +%Y%m%d_%H%M%S)"

# ── Deploy each site ───────────────────────────────────────────────
deploy_one() {
	local key="$1"
	local ldir rsub url remote_dir
	for s in "${SITES[@]}"; do
		IFS='|' read -r k ldir rsub url <<<"$s"
		[ "$k" = "$key" ] && break
	done
	remote_dir="$REMOTE_ROOT${rsub:+/$rsub}"
	local pkg="/tmp/vlsc_${key}_${TS}.tar.gz"
	local backup="${BACKUP_BASE}/${key}_${TS}"

	echo -e "${BOLD}▼ [$key]${NC} $url"
	echo -e "  local : $ldir"
	echo -e "  remote: $remote_dir"

	# 1. Package
	tar -czf "$pkg" "${EXCLUDES[@]}" -C "$ldir" .
	echo -e "  ${GREEN}✓${NC} packaged $(du -h "$pkg" | cut -f1)"

	# 2. Remote: backup + prep + extract + perms (single SSH round-trip)
	scp -q "$pkg" "$REMOTE_USER@$REMOTE_HOST:/tmp/"
	ssh "$REMOTE_USER@$REMOTE_HOST" bash -s "$key" "$remote_dir" "$backup" "$pkg" <<'REMOTE'
    set -e
    KEY="$1"; REMOTE_DIR="$2"; BACKUP="$3"; PKG="$4"

    # Backup current site if non-empty
    if [ -d "$REMOTE_DIR" ] && [ "$(ls -A "$REMOTE_DIR" 2>/dev/null)" ]; then
      sudo mkdir -p /var/www/backups
      sudo cp -r "$REMOTE_DIR" "$BACKUP"
      echo "  • backed up → $BACKUP"
    else
      echo "  • remote empty, skipped backup"
    fi

    sudo mkdir -p "$REMOTE_DIR"
    sudo tar -xzf "$PKG" -C "$REMOTE_DIR" --overwrite
    sudo chown -R www-data:www-data "$REMOTE_DIR"
    sudo chmod -R 755 "$REMOTE_DIR"
    sudo find "$REMOTE_DIR" -type f \( -name '*.html' -o -name '*.css' -o -name '*.js' \) -exec chmod 644 {} \;
    rm -f "$PKG"
    echo "  • extracted + permissions set"
REMOTE
	rm -f "$pkg"
	echo -e "  ${GREEN}✓ [$key] done${NC}"
	echo
}

for k in "${DEPLOY_KEYS[@]}"; do
	deploy_one "$k"
done

# ── Reload nginx once ───────────────────────────────────────────────
echo -e "${YELLOW}Reloading nginx…${NC}"
ssh "$REMOTE_USER@$REMOTE_HOST" 'sudo nginx -t && sudo systemctl reload nginx' &&
	echo -e "${GREEN}✓ nginx reloaded${NC}" ||
	echo -e "${RED}✗ nginx reload failed — check config${NC}"

# ── Summary ────────────────────────────────────────────────────────
echo
echo -e "${BOLD}══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Deployment complete${NC}"
echo -e "${BOLD}══════════════════════════════════════════════════════════════${NC}"
for k in "${DEPLOY_KEYS[@]}"; do
	for s in "${SITES[@]}"; do
		IFS='|' read -r key ldir rsub url <<<"$s"
		[ "$key" = "$k" ] && echo -e "  $url"
	done
done
echo
echo "Rollback: ssh $REMOTE_USER@$REMOTE_HOST"
echo "  sudo rm -rf <remote_dir> && sudo cp -r /var/www/backups/<key>_${TS} <remote_dir>"
