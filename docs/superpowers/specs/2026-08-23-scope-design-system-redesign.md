# VLSC Website Holistic Redesign — Scope.css Design System

## Goal

Rebuild the entire VLSC web presence around a new shared design system (`Scope.css` / `Scope.js`) that:

1. Makes the 7-project ecosystem immediately understandable.
2. Delivers a cohesive, premium hardware-lab / oscilloscope-green visual identity.
3. Works flawlessly on mobile, including the global top nav and dense sub-site navbars.
4. Elevates MRRC Modern as the newest, recommended route while keeping all projects discoverable.
5. Unifies every page — portal landing pages, sub-site home pages, SDD pages, and docs — under one visual language.

## Scope

**In scope:**

- Portal (`/Users/cheenle/HAM/website/portal/`): all EN/ZH pages, blog index, blog articles, FDE.
- Sub-sites (home pages + zh home pages):
  - `/Users/cheenle/UHRR/MRRC/website/`
  - `/Users/cheenle/HAM/website/efhw/`
  - `/Users/cheenle/HAM/mrrc_ft710/website/`
  - `/Users/cheenle/HAM/mrrc_modern/website/`
  - `/Users/cheenle/HAM/ft8/website/`
  - `/Users/cheenle/HAM/sunsdr/sunmrrc/website/`
  - `/Users/cheenle/HAM/sunsdr/SunsdrMobile/website/`
- Sub-site SDD and docs pages: apply base typography, code blocks, tables, and navigation chrome from the new system without rewriting content.
- Shared navigation (`global-nav.js`) and shared utilities (scroll progress, back-to-top, mobile menu).

**Out of scope (for this phase):**

- Rewriting the technical content of SDDs or docs (only visual/structural unification).
- Adding new interactive features unrelated to the redesign.
- Changing backend/feedback service logic.

## Design System: Scope.css

### Visual Identity

The new identity is inspired by vintage oscilloscopes and lab-grade test equipment:

- **Background:** deep black-green `#050a08`.
- **Primary accent:** phosphor green `#00ff41` with soft glow.
- **Secondary accent:** dim green `#00b830`.
- **Surface:** `#0a1510` on top of background, bordered with `#1a3322`.
- **Text:**
  - Primary: `#e8f5e9` (near-white with green tint).
  - Secondary: `#a8c5b5`.
  - Muted: `#5c7a6a`.
- **Grid texture:** subtle 20px green grid overlaid on surfaces.
- **Effects:** horizontal scanlines, phosphor text glow, tick-mark borders on cards.

### Typography

- **Headings / labels:** `JetBrains Mono`, 600–700 weight, all-caps labels for sections.
- **Body:** `Inter`, 400–500 weight.
- **Code / diagrams:** `JetBrains Mono`, 14px.

### Shared Components

All components live in `Scope.css` and are reused by every site:

- `.scope-btn` — primary/secondary/outline buttons with green border and glow.
- `.scope-card` — bordered surface card with optional tick marks and scanline header.
- `.scope-section` — vertical rhythm, section label, heading, subtitle.
- `.scope-table` — data table with green header border and alternating row tint.
- `.scope-code` — inline and block code with dark surface and green tint.
- `.scope-hero` — full-width hero with grid background, glow headline, CTA row.
- `.scope-nav` — global top nav (replaces `vlsc-gn`).
- `.scope-site-nav` — per-site navbar pattern.
- `.scope-qr` — WeChat group QR section.
- `.scope-footer` — shared footer with project links and status.

### Effects

Effects are implemented as CSS utilities so they can be toggled per element:

- `.fx-scanlines` — repeating linear gradient overlay.
- `.fx-glow` — text-shadow / box-shadow green glow.
- `.fx-grid` — background grid texture.
- `.fx-ticks` — pseudo-element tick marks on card corners.

### JavaScript: Scope.js

A single shared behavior layer that replaces `global-nav.js`:

- Injects global top nav with all 7 projects.
- Active project highlighting.
- Mobile menu toggle.
- Scroll progress bar.
- Back-to-top button.
- Scroll-reveal animations.
- Feedback widget bootstrap (preserves existing feedback system integration).
- AdSense bootstrap (preserves existing AdSense integration).

## Information Architecture: Portal

### New Portal Homepage Structure

1. **Global top nav** — 7 projects + FDE + Blog + GitHub.
2. **Hero** — oscilloscope-grid background, large phosphor-green headline, one-line value prop, two CTAs (`Find Your Project`, `Join WeChat Group`).
3. **Project selector (radio table)** — radio/hardware on the left, recommended project on the right, with a highlighted default row for MRRC Modern.
4. **MRRC Modern spotlight** — full-width feature card explaining why it is the newest / recommended route for FT-710 and IC-7300 users.
5. **7-project grid** — equal cards for all projects, each with icon, one-line description, hardware tags, and links.
6. **Comparison matrix** — concise table comparing MRRC / FT-710 / Modern / SunMRRC / FT8 / EFHW / SunsdrMobile across radio, backend, audio, use-case.
7. **Community QR section** — join WeChat group.
8. **Footer** — project links, language switch, GitHub, status.

### Portal Sub-Pages

- **About:** rewrite as "About the Ecosystem" with the 7-project grid and architecture diagram.
- **Contact:** keep form/links but use new card styling.
- **Privacy:** keep content, apply new typography and layout.
- **FDE:** apply new chrome, keep existing content.
- **Blog index & articles:** apply new listing cards and article typography.

## Sub-Site Unification

Each sub-site keeps its own content but adopts:

- `Scope.css` as the base stylesheet.
- `Scope.js` for global nav and utilities.
- A site-specific override file (e.g., `mrrc.scope.css`) only for accent color if needed (default is phosphor green for all; sub-sites may keep subtle accents but the primary identity is now shared green).
- Common homepage structure:
  1. Global top nav.
  2. Site navbar.
  3. Hero with project tagline + version/status.
  4. Feature highlights in `.scope-card` grid.
  5. Community QR section.
  6. Shared footer.

SDD and docs pages receive:

- New typography (headings, paragraphs, lists).
- New code block styling.
- New table styling.
- New sidebar/nav chrome (if present) without rewriting content.

## Migration Strategy

### Phase 1: Build Scope.css / Scope.js

- Create `/Users/cheenle/HAM/website/portal/css/scope.css` and `/Users/cheenle/HAM/website/portal/js/scope.js` as the canonical versions.
- Include all variables, components, utilities, and responsive rules.
- Copy to every sub-site's `css/` and `js/` directories during deployment.

### Phase 2: Rebuild Portal Pages

- Update all Portal EN/ZH HTML to use `scope.css` and `scope.js`.
- Rewrite homepage structure per IA above.
- Update blog index and articles to use new cards.

### Phase 3: Rebuild Sub-Site Home Pages

- Update each sub-site's `index.html` and `zh/index.html`.
- Apply common homepage structure while preserving project-specific content.
- Add/update QR code sections where missing.

### Phase 4: SDD & Docs Styling

- Add `scope.css` to all SDD and docs templates/HTML.
- Verify tables, code blocks, diagrams render correctly.
- Update `build_sdd.py` templates if used so future SDD pages inherit the style.

### Phase 5: Cleanup & Deploy

- Remove or deprecate old `octen.css` / `sunsdrmobile.css` references after verifying no page still needs them.
- Bump cache-buster versions.
- Deploy all sites (using `rsync --rsync-path="sudo rsync"` for speed and reliability).

## Responsive Behavior

- **Desktop (>1024px):** full grid layouts, global nav single row.
- **Tablet (768–1024px):** 2-column grids, global nav single row with tighter gaps.
- **Mobile (<768px):**
  - Global nav wraps to two rows (brand + GitHub on top, project links below).
  - Site nav collapses to hamburger or wraps if few links.
  - Hero font scales down.
  - Project grid becomes single column.
  - QR card full width.

## Testing & Quality

- Verify every page loads without 404 CSS/JS.
- Verify global nav appears and links correctly on all 8 sites.
- Verify mobile wrap CSS works (use browser devtools or curl-check media queries).
- Verify QR code images load on all sub-sites.
- Verify AdSense and feedback widgets still inject on `www.vlsc.net`.
- Check that old `octen.css`/`global-nav.js` references are gone or mapped to new files.

## Deployment

Use the same rsync approach proven in the MRRC Modern integration:

```bash
rsync -avz --delete --rsync-path="sudo rsync" \
  --exclude='.DS_Store' --exclude='deploy.sh' --exclude='__pycache__' \
  local-website/ cheenle@www.vlsc.net:/var/www/vlsc.net/<site>/
```

Follow with SSH for permissions and nginx reload:

```bash
ssh cheenle@www.vlsc.net 'sudo chown -R www-data:www-data /var/www/vlsc.net/<site> && sudo chmod -R 755 /var/www/vlsc.net/<site> && sudo nginx -t && sudo systemctl reload nginx'
```

## Success Criteria

- [ ] All Portal pages render with the new oscilloscope-green design system.
- [ ] All 7 sub-site home pages render with the new design system.
- [ ] All SDD/docs pages have unified typography and components.
- [ ] Global nav links to all 7 projects and wraps correctly on mobile.
- [ ] Project selector on Portal makes it obvious which project to choose.
- [ ] MRRC Modern is visually highlighted as the newest/recommended route.
- [ ] QR code community section appears on all sub-sites.
- [ ] Zero 404s for CSS/JS/image assets.
- [ ] All sites deployed and live on `www.vlsc.net`.

## Open Questions / Decisions

1. Should sub-sites keep any per-project accent color, or go all-in on phosphor green? (Recommendation: all-in green, minimal per-site tint only if needed for differentiation.)
2. Should the blog move to the new design system now or in a follow-up? (Recommendation: include now since it is part of Portal.)
3. Do we keep the current `fde.html` content-heavy layout or redesign it as a simpler feature page? (Recommendation: restyle but keep content.)
