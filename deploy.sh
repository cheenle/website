#!/bin/bash
# ════════════════════════════════════════════════════════════════════
# VLSC Unified Deploy — dispatches to each site's own deploy.sh
#
# Usage:
#   ./deploy.sh                  # every site below, one confirmation each
#   ./deploy.sh portal mrrc      # only the named sites
#   ./deploy.sh --yes            # auto-confirm (answers each prompt with "y")
#   ./deploy.sh --list           # list configured sites and exit
#
# This script used to package, back up, set ownership and print rollback hints
# itself — a second implementation of what every site's own deploy.sh already
# does. The two copies drifted, and every drift was a live hazard (measured
# 2026-09-13):
#   • the table listed /mrrc_ft710/ and /sunsdrmobile/, which nginx 301-redirects
#     and whose server directories are gone — a bare `./deploy.sh` would have
#     resurrected both dead sites — and it omitted mrrc_modern entirely;
#   • the pre-flight demanded js/global-nav.js, which sunmrrc and mrrc_ft8 do not
#     ship (they load js/scope.js), so those two could never be deployed here;
#   • the package excluded nothing, so mrrc_modern's 363MB downloads/ crossed the
#     wire on every release, and the remote backup was a plain `cp -r` of it —
#     the accumulation CLAUDE.md records as filling a volume to 100%;
#   • ownership ran `chown -R` on the site directory, which for the portal IS
#     /var/www/vlsc.net, the DocumentRoot shared with every sub-site;
#   • the rollback hint printed `sudo rm -rf <remote_dir>` — for the portal,
#     "delete the DocumentRoot and restore the landing page".
# CLAUDE.md forbids all five. Rather than maintain a corrected second copy, this
# script now runs each site's own deploy.sh, which owns packaging, backups,
# permissions, rollback text and the nginx reload in one place per site.
# ════════════════════════════════════════════════════════════════════
set -euo pipefail

REMOTE_HOST="www.vlsc.net"
REMOTE_USER="cheenle"

# key | directory containing that site's deploy.sh | URL
# Archived sub-sites (/mrrc_ft710/, /sunsdrmobile/) are deliberately absent:
# nginx 301-redirects them, their server directories are deleted, and their own
# deploy.sh scripts refuse to run. Deploying them would recreate directories
# that nothing links to.
SITES=(
	"portal|/Users/cheenle/HAM/website/portal|https://$REMOTE_HOST/"
	"efhw|/Users/cheenle/HAM/website/efhw|https://$REMOTE_HOST/efhw/"
	"mrrc|/Users/cheenle/HAM/MRRC/website|https://$REMOTE_HOST/mrrc/"
	"mrrc_modern|/Users/cheenle/HAM/mrrc_modern/website|https://$REMOTE_HOST/mrrc_modern/"
	"mrrc_ft8|/Users/cheenle/HAM/ft8/website|https://$REMOTE_HOST/mrrc_ft8/"
	"sunmrrc|/Users/cheenle/HAM/sunsdr/sunmrrc/website|https://$REMOTE_HOST/sunmrrc/"
)

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ── Functions ──────────────────────────────────────────────────────
list_sites() {
	for s in "${SITES[@]}"; do
		IFS='|' read -r key ldir url <<<"$s"
		printf "  ${CYAN}%-14s${NC} %s\n" "$key" "$url"
	done
}

usage() {
	cat <<'USAGE'
Usage:
  ./deploy.sh                  deploy every configured site (one prompt each)
  ./deploy.sh portal mrrc      deploy only the named sites
  ./deploy.sh --yes            auto-confirm each site's prompt
  ./deploy.sh --list           list configured sites and exit
USAGE
	echo
	echo "Available sites:"
	list_sites
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

DEPLOY_KEYS=()
for s in "${SITES[@]}"; do
	IFS='|' read -r key _ _ <<<"$s"
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
echo -e "  VLSC Unified Deploy → $REMOTE_HOST (each site's own deploy.sh)"
echo -e "══════════════════════════════════════════════════════════════${NC}"
echo -e "Sites to deploy:"
for k in "${DEPLOY_KEYS[@]}"; do
	for s in "${SITES[@]}"; do
		IFS='|' read -r key ldir url <<<"$s"
		[ "$key" = "$k" ] && printf "  ${GREEN}•${NC} %-12s %s\n" "$key" "$url"
	done
done
echo

# ── Pre-flight: every selected site must own a runnable deploy.sh ───
echo -e "${YELLOW}Pre-flight checks…${NC}"
for k in "${DEPLOY_KEYS[@]}"; do
	for s in "${SITES[@]}"; do
		IFS='|' read -r key ldir url <<<"$s"
		[ "$key" = "$k" ] || continue
		if [ ! -x "$ldir/deploy.sh" ]; then
			echo -e "  ${RED}✗ $key: no executable deploy.sh in $ldir${NC}"
			exit 1
		fi
		echo -e "  ${GREEN}✓ $key${NC} ($ldir/deploy.sh)"
	done
done
echo

# ── Deploy each site via its own script ─────────────────────────────
# The site script owns packaging, backup + retention, ownership, rollback text
# and reloading nginx — all of it scoped to that site's own directory.
deploy_one() {
	local key="$1" ldir url
	for s in "${SITES[@]}"; do
		IFS='|' read -r k ldir url <<<"$s"
		[ "$k" = "$key" ] && break
	done

	echo -e "${BOLD}▼ [$key]${NC} $url"
	if [ "$ASSUME_YES" -eq 1 ]; then
		( cd "$ldir" && yes y | ./deploy.sh )
	else
		( cd "$ldir" && ./deploy.sh )
	fi
	echo -e "  ${GREEN}✓ [$key] done${NC}"
	echo
}

FAILED=()
for k in "${DEPLOY_KEYS[@]}"; do
	deploy_one "$k" || FAILED+=("$k")
done

# ── Verify nginx once (each site's script has already reloaded it) ──
echo -e "${YELLOW}Verifying nginx…${NC}"
if ssh "$REMOTE_USER@$REMOTE_HOST" 'sudo nginx -t && sudo systemctl reload nginx'; then
	echo -e "${GREEN}✓ nginx healthy${NC}"
else
	echo -e "${RED}✗ nginx check failed — inspect the config before serving again${NC}"
	FAILED+=("nginx")
fi

# ── Summary ─────────────────────────────────────────────────────────
echo
echo -e "${BOLD}══════════════════════════════════════════════════════════════${NC}"
if [ ${#FAILED[@]} -eq 0 ]; then
	echo -e "${GREEN}  Deployment complete${NC}"
else
	echo -e "${RED}  Finished with failures: ${FAILED[*]}${NC}"
fi
echo -e "${BOLD}══════════════════════════════════════════════════════════════${NC}"
for k in "${DEPLOY_KEYS[@]}"; do
	for s in "${SITES[@]}"; do
		IFS='|' read -r key ldir url <<<"$s"
		[ "$key" = "$k" ] && echo -e "  $url"
	done
done
echo
echo "Rollback: each site's deploy.sh prints its own backup path and a restore"
echo "command scoped to that site alone. Never 'rm -rf /var/www/vlsc.net/*':"
echo "the sub-sites share that DocumentRoot and are not in the portal's backup."
echo
echo "Verify the deployed files: curl -s https://$REMOTE_HOST/<site>/ | head -1"

[ ${#FAILED[@]} -eq 0 ]
