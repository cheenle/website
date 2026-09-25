# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a workspace grouping HAM radio project websites. All are pure static HTML/CSS/JS — no frameworks, no build tools, no npm.

**Landing page:**
- **portal/** — Unified landing page at `https://www.vlsc.net/` introducing all five projects and their ecosystem relationship. Deploys to the DocumentRoot (`/var/www/vlsc.net/`). Uses octen.css cyan/teal theme.

**Project sub-sites (symlinks):**
- **MRRC** (`mrrc/` → `/Users/cheenle/UHRR/MRRC/website/`) — Website for the MRRC (Mobile Remote Radio Control) project. Deployed to `https://www.vlsc.net/mrrc/`.
- **MRRC FT-710** (`mrrc_ft710/` → `/Users/cheenle/HAM/mrrc_ft710/website/`) — **已归档 2026-09-12，并入 MRRC Modern。** 仓库只读（GitHub archived），网站 `/mrrc_ft710/` 已 301 到 `/mrrc_modern/`，`website/deploy.sh` 已加禁用守卫。 `mrrc_modern` 是严格超集（同一根提交 `9403e2e`，ft710 零独有代码模块），因此该目录仍保留作为历史入口与跨站 grep 目标。以下描述为归档前状态：Website for the MRRC FT-710 (Software SCU-LAN10 replacement for Yaesu FT-710). Uses octen.css with amber (`#f0a030`) brand overrides in `css/ft710.css`.
- **SunMRRC** (`sunmrrc/` → `/Users/cheenle/HAM/sunsdr/sunmrrc/website/`) — Website for the SunMRRC (SunSDR2 DX Mobile Radio Control) project. Deployed to `https://www.vlsc.net/sunmrrc/`.
- **SunsdrMobile** (`SunsdrMobile/` → `/Users/cheenle/HAM/sunsdr/SunsdrMobile/website/`) — **已合并入 SunMRRC 2026-09-12。** 它不是独立产品，而是 SunMRRC 服务的**原生 iOS 客户端**（打开浏览器所用的同四条 WebSocket 连接）。网站 `/sunsdrmobile/` 已 301 到 `/sunmrrc/ios/`，仓库只读（GitHub archived），其 9 个提交已用 `git subtree` 导入 `sunsdr` 仓。以下描述为合并前状态：Promotional website for the SunsdrMobile native iOS app for SunSDR2 DX.
- **EFHW** (`efhw/`) — Product website for the EFHW Fuchs ATU V3.0 and EFHW antenna knowledge ecosystem. Deployed to `https://www.vlsc.net/efhw/`. Uses octen.css with emerald green (`#10b981`) brand overrides in `css/efhw.css`.
- **易占** (`yijing/`) — I Ching divination app（易经占卜）. Deployed to `https://www.vlsc.net/yijing/`. Pure static HTML/CSS/JS, Chinese-only UI, 水墨宣纸 theme in `css/yijing.css` (cinnabar `#9e2b25` accent). Data lives in `js/data/hexagrams.js` (64 hexagrams: received text of 卦辞/彖/象/爻辞/小象 + vernacular readings + per-topic advice) and `js/data/trigrams.js`; `check_hexagrams.py` is the pre-deploy data gate (run `ALLOW_PARTIAL=1` while authoring batches). Logic: `cast.js` (three-coin casting), `gua.js` (本卦/之卦/互卦 + Zhu Xi 断法 in `duanCi`), `app.js` (DOM/state). Node tests in `yijing/tests/` (`cd yijing && node --test`), excluded from the deploy tarball along with `check_hexagrams.py` and `deploy.sh`.

**Infrastructure:**
- **nginx/** — nginx server block config (`vlsc.net.conf`) replacing the old Apache vhost.

All sites are bilingual (EN/CN), share the same Octen dark theme design system (`css/octen.css`), and deploy to nginx on `www.vlsc.net`.

## Site-wide editorial rules

### Agentic Engineering is the umbrella; FDE is one loop inside it

`/agentic.html` is the thesis page (EN + `zh/`). `/engineering.html` is the mechanism volume.
Forward Deployed Engineering (Echo → Delta → Product) stays documented inside §03 Lineage as the
predecessor that produced the contracts agents now load. Do not re-promote FDE as the top-level
brand, and do not delete it. Chinese term: 智能体工程 (never 代理式工程); FDE 中文统一为「前沿部署工程」.

### Facts have one owner

The portal Evidence section (`/agentic.html#evidence`) is the single source of truth for
cross-project comparable numbers: versions, test counts, release status, known defects.
Sub-sites keep their own architecture, module tables and protocol detail — they must not
self-report comparable numbers. Link to the ledger instead.

Never claim a product family was built by AI or agents. Process evidence (constraint registry,
spec trail, hooks, verified blocks) is graded separately from product maturity and never
promotes it. Repositories without `.agents/skills/sdd-guardian/` must not describe a pre-edit gate.

### Cross-site checks

Sub-site directories under `website/` are symlinks into other git repositories
(`mrrc/`, `mrrc_modern/`, `mrrc_ft710/`, `sunmrrc/`, `SunsdrMobile/`, `mrrc_ft8/`, `ft8/`);
`portal/`, `efhw/`, `yijing/` and `nginx/` are real directories.

**Site-wide greps must list the site directories explicitly — as a shell ARRAY, never as a
string variable.** Two independent traps here, both verified 2026-09-05 against this
machine's actual tooling (`grep` resolves to **ugrep 7.5.0**, not BSD grep; the shell is
**zsh 5.9**):

1. `-r` / `-R` will not descend into symlinked sub-directories when searching from `.`, so
   `grep -R pattern .` reports a clean tree while every sub-site hit stays invisible.
   Measured: 0 hits under `./mrrc_ft710/` and `./mrrc/` for a string that occurs in both.
2. **zsh does not word-split unquoted parameter expansions.** Assigning the list to a string
   and expanding `$SITES` passes all eight directories as ONE nonexistent path. ugrep prints
   `warning: … No such file or directory`, exits 2, and produces no matches — which at a
   prompt is indistinguishable from "clean tree". This is a silent false green across every
   sub-site, produced by the very pattern meant to prevent one.

```zsh
SITES=(portal/ mrrc/ mrrc_ft710/ mrrc_modern/ sunmrrc/ SunsdrMobile/ mrrc_ft8/ efhw/)
grep -Rn "pattern" $SITES       # correct: array expands to 8 args  → 8 hits measured
grep -Rn "pattern" .            # WRONG: misses all symlinked sub-sites → 0 hits
```

```zsh
SITES="portal/ mrrc/ … efhw/"   # WRONG under zsh — string, not array
grep -Rn "pattern" $SITES       # → 1 bogus arg, exit 2, 0 hits, looks like a clean tree
```

If a script must stay POSIX/bash-compatible, use `bash -c` with the array, or pass the
directories as literal arguments.

**The trailing slash IS load-bearing — re-measured 2026-09-12.** This section has now been
wrong in *both* directions, so here is the measurement rather than a claim. On this machine
`grep` is **BSD grep 2.6.0-FreeBSD** (`grep --version`) — *not* ugrep, as an earlier revision
of this file stated. `-R` does **not** follow a symlink named without a trailing slash, and
fails **silently**:

```
grep -Rn mrrc_modern mrrc/ --include='*.html'   →   2 hits   ✅
grep -Rn mrrc_modern mrrc  --include='*.html'   →   0 hits   ❌  same directory, silently empty
```

(Measured 2026-09-12 with `mrrc/` → `/Users/cheenle/HAM/MRRC/website`. `--include` does not
change the outcome: without it the same pair reads 3 vs 0. A bare-form false green is
indistinguishable from a clean tree, which is exactly the failure this whole section exists to
prevent. **Always write the trailing slash** — not for readability, but because without it the
search reads nothing.

Note the pattern has to still exist to be a valid test: an earlier draft of this paragraph
used `mrrc_ft710`, which returned 5/0 — until that sub-site was archived the same day and both
sides legitimately became 0. Verify with `grep --version` too: the tool here has changed at
least once, and an earlier "correction" in this file was itself wrong.

`find` needs the same care: use `find -L` to follow symlinks. Grepping `.` is only safe
after `cd` into a sub-site's real repository directory (e.g. `/Users/cheenle/HAM/MRRC/website`).
Commits go to the owning repository, not this one.

**`portal/images/` and `efhw/images/` are deliberately NOT tracked.** They hold the WeChat
group QR code, which expires and is regenerated roughly weekly; committing it would mean a
churn commit every week. The tracked HTML references those paths, so a fresh clone renders a
broken image until the files are placed on disk. Deployment ships them from the working tree
(`portal/deploy.sh` tars the directory, not the git index), so production is unaffected. If
you add a tracked asset under those directories, say so explicitly — the default is disk-only.

## Common patterns across all five sites

- **Design**: `css/octen.css` — dark theme with cyan/teal accent (`#22d3ee`), Inter + JetBrains Mono fonts, responsive. Font Awesome 6.4 for icons. Embedded SVG favicons.
- **i18n**: Chinese translations live in `zh/` mirroring the EN file structure. MRRC uses `js/i18n.js` for runtime language switching; SunMRRC has separate `zh/index.html`.
- **Deployment**: Each site has a `deploy.sh` that `tar` + `scp` to `www.vlsc.net`, extracts under `/var/www/vlsc.net/<project>/`, sets `www-data` ownership, then reloads nginx. Requires SSH access. Scripts ask for confirmation before deploying and auto-create backups.
- **No build step**: Edit HTML/CSS/JS directly. The exception is SunMRRC's SDD docs (see below).

## MRRC-specific (`mrrc/`)

```
mrrc/
├── index.html           # Landing page (EN)
├── fde.html             # FDE product page
├── aladdin-v2.html      # Aladdin V2 product page
├── css/
│   ├── octen.css        # Shared dark theme
│   ├── style.css        # MRRC-specific styles
│   ├── modern.css       # Additional styles
│   └── docs.css         # Documentation page styles
├── js/
│   ├── main.js          # Site-wide JS
│   └── i18n.js          # Runtime EN↔CN translation strings
├── docs/                # Documentation & design pages
│   └── design/          # Architecture design docs (HTML)
├── efhw/                # EFHW antenna product sub-site
├── images/              # Site images
├── stats/               # Apache log analyzer (Python)
│   ├── analyze.py       # Parses Apache logs → SQLite → HTML dashboard
│   └── stats.db         # SQLite database
├── logs/ALL/            # ADIF log files
├── zh/                  # Chinese translations (mirrors EN structure)
├── deploy.sh            # Deploy to www.vlsc.net/mrrc/
└── vlsc.net.conf        # Reference Apache vhost config
```

### Stats analyzer (`stats/analyze_nginx.py`)

Python script that parses nginx access logs from `/var/log/nginx/access.log`, stores hits in SQLite (`stats_nginx.db`), and generates an HTML dashboard. Uses GeoLite2 for country lookup. Run directly: `python3 stats/analyze_nginx.py`.

The old Apache-based `stats/analyze.py` (MRRC-specific) is kept for reference but no longer used since the migration to nginx.

Deploy to server:
```bash
scp stats/analyze_nginx.py cheenle@www.vlsc.net:/home/cheenle/stats/
ssh cheenle@www.vlsc.net "sudo mkdir -p /home/cheenle/stats && sudo python3 /home/cheenle/stats/analyze_nginx.py"
```

Set up cron (every 30 min):
```bash
# On server: crontab -e
*/30 * * * * cd /home/cheenle/stats && python3 analyze_nginx.py
```

Stats dashboard: `https://www.vlsc.net/stats/` (HTTP basic auth protected).

### AdSense

Google AdSense (publisher ID `ca-pub-7442510147240155`) is injected on all pages across all project sites via `js/global-nav.js`. The script dynamically creates the AdSense `<script>` tag on `www.vlsc.net` only, with a duplicate-prevention check to avoid double-loading on pages that already have the script inline (e.g., MRRC docs).

Pages that do not load `global-nav.js` (e.g., `mrrc_ft710/sdd/`, `sunmrrc/sdd/`) get AdSense via the `build_sdd.py` template. After editing `build_sdd.py`, rebuild SDD pages with `python3 build_sdd.py`.

## SunMRRC-specific (`sunmrrc/`)

```
sunmrrc/
├── index.html           # Landing page (EN)
├── css/
│   └── octen.css        # Shared dark theme
├── sdd/                 # Software Design Document (generated HTML)
│   ├── index.html       # SDD overview
│   ├── 01-executive-summary.html ... 15-ptt-safety-architecture.html
│   └── diagrams/        # SVG architecture diagrams
├── zh/
│   └── index.html       # Chinese landing page
├── build_sdd.py         # SDD builder: markdown → styled HTML
└── deploy.sh            # Deploy to www.vlsc.net/sunmrrc/
```

### SDD build system (`build_sdd.py`)

Converts markdown files from `/Users/cheenle/HAM/sunsdr/SDD/` into styled HTML pages with a sidebar navigation. Requires **pandoc** installed. Run:

```bash
cd /Users/cheenle/HAM/sunsdr/sunmrrc/website
python3 build_sdd.py
```

This regenerates all files in `sdd/`. Each output page embeds the SunMRRC navbar, a sticky sidebar with all 15 SDD chapters, and footer. The script defines the file mapping and nav structure as Python lists near the top — edit those to add/remove chapters.

## MRRC FT-710-specific (`mrrc_ft710/`) — 已归档 2026-09-12

> **归档说明**：本项目已并入 **MRRC Modern**，仓库设为只读（GitHub archived），
> 网站 `https://www.vlsc.net/mrrc_ft710/` 全量 **301 到 `/mrrc_modern/`**（nginx `location ^~`，
> 必须用 `^~`——普通前缀会被 `~*\.(css|js|…)$` 正则截走），服务器目录已删除，
> `website/deploy.sh` 已加禁用守卫。
>
> **不得**把 `mrrc_ft710` 从导航/产品表重新加回 portal（那是已完成的归档工作）。
> **但**血统与证据层必须保留：`portal/agentic.html`（血统图、`MRRC FT-710 inspired-by → MRRC Modern`）、
> `portal/engineering.html`（产品族证据表、`FT-710: 439 tests`）、博客系列账本表/时间线/事故链/
> 约束计数（17/21/14 = 52）。删这些等于抹掉论证起点。
>
> 归档时仓库 HEAD 在 `scope-redesign` 分支（`9c353a1`），另 13 个独有提交全在 `website/` 与
> `docs/`，零源码差异。

```
mrrc_ft710/ (→ /Users/cheenle/HAM/mrrc_ft710/website/)
├── index.html              # Landing page (EN)
├── sdd.html                # SDD overview page
├── css/
│   ├── octen.css           # Shared dark theme
│   ├── sunsdrmobile.css    # Shared component styles
│   └── ft710.css           # Amber (#f0a030) brand overrides
├── js/
│   └── global-nav.js       # Shared navigation JS
├── sdd/                    # Software Design Document (generated HTML)
│   ├── index.html          # SDD overview (from README.md)
│   ├── 01-executive-summary.html ... 15-ptt-safety-architecture.html
│   └── diagrams/           # SVG architecture diagrams
├── zh/
│   ├── index.html          # Chinese landing page
│   └── sdd.html            # Chinese SDD overview
├── build_sdd.py            # SDD builder: markdown → styled HTML
└── deploy.sh               # Deploy to www.vlsc.net/mrrc_ft710/
```

### SDD build system (`build_sdd.py`)

Converts markdown files from `/Users/cheenle/HAM/mrrc_ft710/SDD/` into styled HTML pages with FT-710 branding. Requires **pandoc** installed. Run:

```bash
cd /Users/cheenle/HAM/mrrc_ft710/website
python3 build_sdd.py
```

This regenerates all files in `sdd/`. Each output page embeds the FT-710 navbar, a sticky sidebar with all 16 SDD entries, and footer.

## SunsdrMobile-specific (`SunsdrMobile/`) — 已合并入 SunMRRC 2026-09-12

> **合并说明**：`SunsdrMobile` 不是独立产品，而是 **SunMRRC 的原生 iOS 客户端**
> （`ConnectionManager.swift` 注释："Manages the 4 WebSocket connections to sunmrrc"；
> 默认服务器 `radio.vlsc.net:8889`）。合并后：
>
> - 代码与 **9 个提交的完整历史**经 `git subtree` 进入 `sunsdr` 仓的 `SunsdrMobile/`
> - 网站页并入 `sunmrrc/website/ios/`（+`zh/ios/`），`/sunsdrmobile/` 全量
>   **301 到 `/sunmrrc/ios/`**（nginx `location ^~`，必须用 `^~`——普通前缀会被
>   `~*\.(css|js|…)$` 正则截走）；服务器目录已删除
> - `SunsdrMobile` 的 GitHub 仓已归档只读，`website/deploy.sh` 已加禁用守卫
> - portal 呈现层不再单列：产品矩阵/产品卡合并为一个 SunMRRC 条目
>
> **不得**把 SunsdrMobile 从导航/产品表重新加回 portal。
> **但**证据层必须保留：`portal/agentic.html`（已用正确框架：*"SunMRRC is the station
> system; Web and SunsdrMobile are clients"*）、`portal/engineering.html` 产品族表、
> 博客系列账本表（`sunsdr 67+9 commits`）。
>
> **注意**：`portal/css/sunsdrmobile.css` 是 **portal 自己的共享样式表**（12 个 portal
> 页面依赖 `.gradient`/`.btn-primary`/`.section-label` 等），文件名只是继承来源，**不得删除**。

```
SunsdrMobile/
├── index.html              # Landing page (EN)
├── css/
│   ├── octen.css           # Shared dark theme (copied from SunMRRC)
│   └── sunsdrmobile.css    # Amber/orange accent overrides + site components
├── zh/
│   └── index.html          # Chinese landing page
└── deploy.sh               # Deploy to www.vlsc.net/sunsdrmobile/
```

Pure static HTML/CSS, no JS framework. Uses amber/orange accent (`#f39c12`) — site-specific overrides in `sunsdrmobile.css` that redefine CSS custom properties from the shared `octen.css`. Follows the same navbar/footer/section patterns as MRRC and SunMRRC. Uses Font Awesome 6.4 icons (no emoji). i18n mirrors SunMRRC's separate `zh/index.html` approach. The pages include inline SVG architecture diagrams and a UI phone mockup.

### Design system

SunsdrMobile preserves its amber/orange brand identity by loading `octen.css` first, then overriding CSS custom properties in `sunsdrmobile.css`:
- `--accent: #f39c12` (amber instead of cyan)
- `--bg-primary: #0a0e14` (dark blue-gray instead of pure black)
- Additional site-specific component classes for feature cards, performance metrics, step counters, and architecture endpoint cards.

## EFHW-specific (`efhw/`)

```
efhw/
├── index.html              # Landing page (EN)
├── css/
│   ├── octen.css           # Shared dark theme (copied from SunsdrMobile)
│   └── efhw.css            # Emerald green (#10b981) brand overrides
├── js/
│   └── global-nav.js       # Shared navigation JS
├── images/                 # Product images
├── zh/
│   └── index.html          # Chinese landing page
└── deploy.sh               # Deploy to www.vlsc.net/efhw/
```

Pure static HTML/CSS/JS, no framework. Uses emerald green accent (`#10b981`) for its outdoor/antenna theme, distinguishing it from cyan (MRRC/Portal) and amber (FT-710/SunsdrMobile). Site covers the EFHW Fuchs ATU V3.0 product — ESP32-S3 servo-driven auto-tuner — and links to MRRC's deep research pages for in-depth antenna theory.

### Design system

EFHW preserves its emerald green brand identity by loading `octen.css` first, then overriding CSS custom properties in `efhw.css`:
- `--accent: #10b981` (emerald green instead of cyan)
- `--bg-primary: #0a0e14` (dark blue-gray)
- `.gradient` override: `linear-gradient(135deg, #10b981, #059669)`

### Relationship with MRRC EFHW pages

MRRC contains complementary EFHW deep research pages at `/mrrc/efhw/` (Tailwind CSS, 17-chapter research synthesis). The EFHW product site links to these for deep-dive content; the research pages link back via a "Product Site" nav item. Both are preserved — they serve different audiences (product overview vs. engineering deep-dive).

## Portal — Unified Landing Page (`portal/`)

```
portal/
├── index.html           # EN landing page (root /)
├── css/
│   └── octen.css        # Shared dark theme (copied from SunMRRC)
├── zh/
│   └── index.html       # CN landing page
└── deploy.sh            # Deploy to /var/www/vlsc.net/ (DocumentRoot)
```

The portal is the unified entry point at `https://www.vlsc.net/`. It introduces all three projects and explains the two-track ecosystem:
- **Track A** — MRRC: Universal HF remote control for any radio via Hamlib/rigctld
- **Track B** — SunSDR: SunSDR2 DX-specific client-server pair (SunMRRC + SunsdrMobile)

Uses the standard octen.css cyan/teal accent as the parent "VLSC Projects" brand color. Four project cards link to each sub-site and GitHub repo.

## nginx Configuration (`nginx/`)

The server migrated from Apache to nginx. The config at `nginx/vlsc.net.conf` is the reference copy of the server block deployed to `/etc/nginx/sites-enabled/vlsc.net` on the server.

Key design:
- HTTP (port 80) → HTTPS redirect
- SSL certs reused from `/etc/apache2/ssl/` (Let's Encrypt)
- `root /var/www/vlsc.net` serves the portal landing page
- `location /mrrc/`, `/mrrc_ft710/`, `/sunmrrc/`, `/sunsdrmobile/` use `alias` to their respective directories
- Static asset caching (7d) for CSS/JS/images
- Security headers (X-Frame-Options, X-Content-Type-Options)
- Hidden files denied

To deploy nginx config changes:
```bash
scp nginx/vlsc.net.conf cheenle@www.vlsc.net:/tmp/
ssh cheenle@www.vlsc.net "sudo cp /tmp/vlsc.net.conf /etc/nginx/sites-available/vlsc.net && sudo nginx -t && sudo systemctl reload nginx"
```

## Deploying

Each site deploys independently via its own script:

```bash
# Portal (unified landing page at /)
cd /Users/cheenle/HAM/website/portal
./deploy.sh

# MRRC
cd /Users/cheenle/UHRR/MRRC/website
./deploy.sh

# SunMRRC
cd /Users/cheenle/HAM/sunsdr/sunmrrc/website
./deploy.sh

# SunsdrMobile
cd /Users/cheenle/HAM/sunsdr/SunsdrMobile/website
./deploy.sh

# MRRC FT-710
cd /Users/cheenle/HAM/mrrc_ft710/website
./deploy.sh

# EFHW
cd /Users/cheenle/HAM/website/efhw
./deploy.sh
```

All deploy scripts: (1) validate required files exist, (2) create a tarball, (3) SSH to `www.vlsc.net` to back up the current site, (4) `scp` the tarball, (5) extract and set permissions, (6) reload nginx. They prompt for confirmation before the remote steps.

Rollback: each script prints the backup path on the server. Restore **only that backup, into the paths it covers** — `portal/deploy.sh` backs up exactly the files its package writes.

### Deploy scripts must stay scoped to their own site

`/var/www/vlsc.net` is a **shared DocumentRoot**: the portal owns the loose files at its root, each sub-site owns its own directory (nginx `alias`). Therefore no deploy script may ever `rm -rf`, `chown -R` or `chmod -R` the DocumentRoot as a whole — that hits every other site. `portal/deploy.sh` drives backup, ownership and rollback off the package's own file list for this reason.

Two rules when editing any `deploy.sh`:

- **Remote heredocs must be quoted** (`<<'REMOTE'`), with variables passed on the `ssh` command line. An unquoted `<< EOF` lets the local macOS shell expand `$(...)`/`$VAR` first, which once made `portal/deploy.sh` skip its backup silently on every single run while still printing a backup path that did not exist.
- **`tar -x` never deletes.** Excluding a file from the package does not remove a copy already published by an earlier run, so retiring shipped tooling (`tests/`, `make_sitemap.py`, `check_baluns.py`) needs an explicit remote delete. Build-time tooling must not be in the package at all — the DocumentRoot is world-readable.
- **Backups are per-site, lean, and rotated.** Never `cp -r` a whole deployed site:
  `downloads/` and `videos/` are server-managed binaries no HTML deploy touches, and
  they are ~120-140MB of each site — that is how `/var/tmp` reached 3.7G (1.7G from 13
  `mrrc_ft710` copies, 2.0G from 18 `mrrc_ft8` copies) on a volume that once filled to
  100%. Use `rsync -a --exclude='downloads' --exclude='videos' <site>/ <backup>/` and
  keep only the 3 newest backups per site (append `|| true` to the prune pipeline: on
  a first deploy none exist, and the remote blocks run under `set -e`).
- **A rollback hint may only restore one site's own directory.** Three scripts used to
  print `sudo rm -rf $REMOTE_WEBROOT && sudo cp -r /var/tmp/<site>_backup_* $REMOTE_WEBROOT`,
  which deletes the whole DocumentRoot and puts back a single sub-site. Restore with
  `sudo rsync -a $B/ $REMOTE_WEBROOT/<site>/` (merge, so `downloads/` survives).
## nginx server

All sites are served by nginx on `www.vlsc.net` (HTTPS via Let's Encrypt). The server block config is at `nginx/vlsc.net.conf`. The landing page is served from the DocumentRoot (`/var/www/vlsc.net/`). Sub-sites use `alias` directives: `/mrrc/` → `/var/www/vlsc.net/mrrc/`, `/mrrc_ft710/` → `/var/www/vlsc.net/mrrc_ft710/`, `/sunmrrc/` → `/var/www/vlsc.net/sunmrrc/`, `/sunsdrmobile/` → `/var/www/vlsc.net/sunsdrmobile/`, `/efhw/` → `/var/www/vlsc.net/efhw/`, `/yijing/` → `/var/www/vlsc.net/yijing/`. SSL certs at `/etc/letsencrypt/live/www.vlsc.net/`.
