# MRRC Modern Portal Integration Design

## Goal
Add the newly-created `mrrc_modern` sub-site to the VLSC portal and every existing sub-site navbar, fix mobile navbar overlap, add the WeChat group QR code to `mrrc_modern`, and deploy all affected sites.

## Background
- `mrrc_modern` lives at `/Users/cheenle/HAM/mrrc_modern/website` and is symlinked as `/Users/cheenle/HAM/website/mrrc_modern`.
- It is a software SCU-LAN10 replacement for Yaesu FT-710 **and** Icom IC-7300/IC-7300MK2, current version v1.10.1.
- It will be served at `https://www.vlsc.net/mrrc_modern/`.

## Changes

### 1. Portal (`/Users/cheenle/HAM/website/portal/`)
Add MRRC Modern as the 7th project in:
- `index.html`: selector table, project cards grid, ecosystem metrics, CTA-adjacent references, footer project list.
- `zh/index.html`: same places, Chinese copy.
- `about.html`: project cards grid and footer project list.
- `contact.html`: project list and footer.
- `privacy.html`: footer project list.
- Copy: "MRRC Modern — FT-710 / IC-7300 Remote" / "MRRC Modern — FT-710 / IC-7300 远程".

### 2. Sub-site navbars
Add a top-navbar link to `mrrc_modern` in:
- `/Users/cheenle/UHRR/MRRC/website/index.html` + `zh/index.html`
- `/Users/cheenle/HAM/mrrc_ft710/website/index.html` + `zh/index.html`
- `/Users/cheenle/HAM/mrrc_modern/website/index.html` + `zh/index.html`
- `/Users/cheenle/HAM/ft8/website/index.html` + `zh/index.html`
- `/Users/cheenle/HAM/sunsdr/sunmrrc/website/index.html` + `zh/index.html`
- `/Users/cheenle/HAM/sunsdr/SunsdrMobile/website/index.html` + `zh/index.html`
- `/Users/cheenle/HAM/website/efhw/index.html` + `zh/index.html`

Use the existing single-link pattern (e.g. `<li><a href="/mrrc_modern/">Modern</a></li>`), keeping changes minimal.

### 3. Mobile navbar overlap fix
Update each site's site-specific CSS (the file loaded after `octen.css`) so that on narrow viewports the navbar links wrap into two centered rows instead of overflowing or overlapping.
Concretely:
- `.navbar-content { flex-wrap: wrap; }`
- `.nav-links { flex-wrap: wrap; justify-content: center; }`
- Adjust `.nav-links li` padding/margins for touch.
- Keep the hamburger toggle behavior unchanged where it already exists.

### 4. QR code on `mrrc_modern`
- Copy `ma.jpg` → `mrrc_modern/website/images/qr-wechat-group.jpg`.
- Append `.qr-section`/`.qr-card`/`.qr-note` styles to the site-specific CSS.
- Insert the Community/社区 QR section after the hero section in `index.html` and `zh/index.html`.

### 5. Deployment
Run each affected site's `deploy.sh`:
- portal, efhw, mrrc, mrrc_ft710, mrrc_modern, mrrc_ft8, sunmrrc, SunsdrMobile.
Use `echo y | ./deploy.sh` (or `--force` where supported) to auto-confirm.

## Success criteria
- Portal selector and project cards list 7 projects including MRRC Modern.
- Every sub-site navbar links to `/mrrc_modern/`.
- On a phone-width viewport, navbar links wrap to two readable rows.
- `mrrc_modern` home pages show the WeChat group QR code.
- All deploy scripts complete and sites are live.
