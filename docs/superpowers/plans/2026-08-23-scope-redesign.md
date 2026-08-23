# VLSC Scope.css Holistic Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the entire VLSC web presence (Portal + 7 sub-sites, including SDD/docs pages) around a new shared oscilloscope-green design system (`Scope.css` / `Scope.js`) that unifies navigation, typography, components, and mobile behavior.

**Architecture:** Create a canonical `Scope.css` and `Scope.js` in `portal/`, copy them to every sub-site, then rewrite Portal pages and sub-site home pages to use the new system. SDD/docs pages receive the new base styles without content rewrites. Deployment uses `rsync --rsync-path="sudo rsync"` for fast, reliable syncing.

**Tech Stack:** Static HTML5, CSS3 (custom properties, flexbox, grid), vanilla ES5/ES6 JavaScript, nginx. No build tools.

---

## File Structure

### New shared files (canonical in Portal)

- `portal/css/scope.css` — design tokens, reset, layout, components, utilities, responsive rules.
- `portal/js/scope.js` — global nav injection, mobile menu, scroll progress, back-to-top, reveal animations, feedback/AdSense bootstrap.

### Copied to each sub-site

For each sub-site, copy the two files above into its `css/` and `js/` directories:

- `mrrc/css/scope.css`, `mrrc/js/scope.js`
- `efhw/css/scope.css`, `efhw/js/scope.js`
- `mrrc_ft710/css/scope.css`, `mrrc_ft710/js/scope.js`
- `mrrc_modern/css/scope.css`, `mrrc_modern/js/scope.js`
- `mrrc_ft8/css/scope.css`, `mrrc_ft8/js/scope.js`
- `sunmrrc/css/scope.css`, `sunmrrc/js/scope.js`
- `sunsdrmobile/css/scope.css`, `sunsdrmobile/js/scope.js`

### Site-specific override files (minimal)

- `portal/css/portal.scope.css` — Portal-only layout tweaks.
- `<site>/css/<site>.scope.css` — sub-site accent tweaks if absolutely needed (default: empty or not created).

### HTML files to modify

**Portal:**
- `portal/index.html`, `portal/zh/index.html`
- `portal/about.html`, `portal/zh/about.html`
- `portal/contact.html`, `portal/zh/contact.html`
- `portal/privacy.html`, `portal/zh/privacy.html`
- `portal/fde.html`, `portal/zh/fde.html`
- `portal/blog/index.html`
- `portal/blog/efhw-esp32s3-auto-tuner/index.html`
- `portal/blog/ft710-usb-remote-control/index.html`
- `portal/blog/opus-vs-pcm-remote-audio/index.html`
- `portal/blog/psk-reporter-dxcc-hunting/index.html`

**Sub-site home pages:**
- `UHRR/MRRC/website/index.html`, `UHRR/MRRC/website/zh/index.html`
- `website/efhw/index.html`, `website/efhw/zh/index.html`
- `HAM/mrrc_ft710/website/index.html`, `HAM/mrrc_ft710/website/zh/index.html`
- `HAM/mrrc_modern/website/index.html`, `HAM/mrrc_modern/website/zh/index.html`
- `HAM/ft8/website/index.html`, `HAM/ft8/website/zh/index.html`
- `HAM/sunsdr/sunmrrc/website/index.html`, `HAM/sunsdr/sunmrrc/website/zh/index.html`
- `HAM/sunsdr/SunsdrMobile/website/index.html`, `HAM/sunsdr/SunsdrMobile/website/zh/index.html`

**SDS/docs templates:**
- `HAM/mrrc_ft710/website/build_sdd.py`
- `HAM/ft8/website/build_sdd.py`
- `HAM/sunsdr/sunmrrc/website/build_sdd.py`
- Individual SDD HTML files in the three sites above (apply base styles, do not rewrite content).

---

## Task 1: Create Scope.css Foundation

**Files:**
- Create: `portal/css/scope.css`

- [ ] **Step 1: Write CSS reset and design tokens**

```css
/* portal/css/scope.css */
:root {
  --scope-bg: #050a08;
  --scope-surface: #0a1510;
  --scope-surface-2: #0f1f17;
  --scope-border: #1a3322;
  --scope-border-strong: #00ff41;
  --scope-primary: #00ff41;
  --scope-primary-dim: #00b830;
  --scope-primary-glow: rgba(0, 255, 65, 0.35);
  --scope-text: #e8f5e9;
  --scope-text-2: #a8c5b5;
  --scope-text-muted: #5c7a6a;
  --scope-font-mono: 'JetBrains Mono', 'SFMono-Regular', Consolas, monospace;
  --scope-font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --scope-radius: 6px;
  --scope-nav-h: 56px;
  --scope-gn-h: 36px;
}

*, *::before, *::after { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  font-family: var(--scope-font-sans);
  background: var(--scope-bg);
  color: var(--scope-text);
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}
a { color: var(--scope-primary); text-decoration: none; }
a:hover { text-decoration: underline; }
img { max-width: 100%; height: auto; }
```

- [ ] **Step 2: Add grid/scanline utilities and effects**

Append to `portal/css/scope.css`:

```css
.fx-grid {
  background-image:
    linear-gradient(rgba(0, 255, 65, 0.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 255, 65, 0.06) 1px, transparent 1px);
  background-size: 24px 24px;
}
.fx-scanlines::after {
  content: '';
  position: fixed;
  inset: 0;
  pointer-events: none;
  background: repeating-linear-gradient(
    0deg,
    rgba(0, 0, 0, 0.08) 0px,
    rgba(0, 0, 0, 0.08) 1px,
    transparent 1px,
    transparent 3px
  );
  z-index: 9999;
}
.fx-glow { text-shadow: 0 0 12px var(--scope-primary-glow); }
.fx-glow-box { box-shadow: 0 0 18px var(--scope-primary-glow); }
```

- [ ] **Step 3: Add layout utilities and container**

Append to `portal/css/scope.css`:

```css
.container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1.5rem;
}
.scope-section { padding: 5rem 0; }
.scope-section-alt { background: var(--scope-surface); }
.section-label {
  display: inline-block;
  font-family: var(--scope-font-mono);
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--scope-primary);
  margin-bottom: 0.75rem;
}
.section-title {
  font-family: var(--scope-font-mono);
  font-size: 2rem;
  font-weight: 700;
  margin: 0 0 0.75rem;
  color: var(--scope-text);
}
.section-subtitle {
  color: var(--scope-text-2);
  max-width: 640px;
  margin: 0 0 2.5rem;
}
```

- [ ] **Step 4: Add buttons and cards**

Append to `portal/css/scope.css`:

```css
.scope-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.7rem 1.4rem;
  font-family: var(--scope-font-mono);
  font-weight: 600;
  font-size: 0.875rem;
  border-radius: var(--scope-radius);
  border: 1px solid var(--scope-primary);
  background: transparent;
  color: var(--scope-primary);
  cursor: pointer;
  transition: all 0.2s ease;
}
.scope-btn:hover {
  background: rgba(0, 255, 65, 0.1);
  box-shadow: 0 0 16px var(--scope-primary-glow);
  text-decoration: none;
}
.scope-btn-primary {
  background: var(--scope-primary);
  color: var(--scope-bg);
}
.scope-btn-primary:hover { background: #33ff66; }

.scope-card {
  background: var(--scope-surface);
  border: 1px solid var(--scope-border);
  border-radius: var(--scope-radius);
  padding: 1.5rem;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.scope-card:hover {
  border-color: var(--scope-primary-dim);
  box-shadow: 0 0 18px rgba(0, 255, 65, 0.1);
}
```

- [ ] **Step 5: Add tables and code blocks**

Append to `portal/css/scope.css`:

```css
.scope-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}
.scope-table th,
.scope-table td {
  padding: 0.85rem 1rem;
  text-align: left;
  border-bottom: 1px solid var(--scope-border);
}
.scope-table th {
  font-family: var(--scope-font-mono);
  font-weight: 600;
  color: var(--scope-primary);
  background: var(--scope-surface);
}
.scope-table tr:nth-child(even) { background: rgba(0, 255, 65, 0.03); }

.scope-code,
pre.scope-code {
  font-family: var(--scope-font-mono);
  background: var(--scope-surface);
  border: 1px solid var(--scope-border);
  border-radius: var(--scope-radius);
  padding: 1rem;
  overflow-x: auto;
  color: var(--scope-text-2);
}
code.scope-code {
  padding: 0.15rem 0.4rem;
  font-size: 0.85em;
}
```

- [ ] **Step 6: Add responsive rules**

Append to `portal/css/scope.css`:

```css
@media (max-width: 768px) {
  :root { --scope-gn-h: 72px; }
  .section-title { font-size: 1.6rem; }
  .scope-section { padding: 3.5rem 0; }
  .container { padding: 0 1.1rem; }
}
```

- [ ] **Step 7: Verify file exists and has no syntax errors**

Run:

```bash
wc -l portal/css/scope.css
# Expected: 200+ lines
```

Open `portal/css/scope.css` in an editor and confirm no unmatched braces.

- [ ] **Step 8: Commit**

```bash
git add portal/css/scope.css
git commit -m "feat(scope): add Scope.css design system foundation"
```

---

## Task 2: Create Scope.js Shared Behavior Layer

**Files:**
- Create: `portal/js/scope.js`

- [ ] **Step 1: Write site detection and nav rendering**

```javascript
// portal/js/scope.js
(function () {
  'use strict';

  var SITE = document.body.getAttribute('data-site') || 'portal';
  var isCN = (document.documentElement.lang || '').startsWith('zh') || /\/zh\//.test(location.pathname);

  var PATHS = {
    portal: '/',
    fde: '/fde.html',
    mrrc: '/mrrc/',
    mrrc_ft710: '/mrrc_ft710/',
    mrrc_modern: '/mrrc_modern/',
    mrrc_ft8: '/mrrc_ft8/',
    sunmrrc: '/sunmrrc/',
    sunsdrmobile: '/sunsdrmobile/',
    blog: '/blog/'
  };

  var LABELS = isCN ? {
    brand: 'VLSC 项目',
    projects: '项目',
    back: '返回顶部'
  } : {
    brand: 'VLSC Projects',
    projects: 'Projects',
    back: 'Back to top'
  };

  function siteLink(key, label) {
    var active = key === SITE ? ' is-active' : '';
    return '<a href="' + PATHS[key] + '" data-site="' + key + '" class="' + active.trim() + '">' + label + '</a>';
  }

  var gn = document.createElement('div');
  gn.className = 'scope-gn';
  gn.innerHTML =
    '<div class="scope-gn-inner container">' +
      '<a class="scope-gn-brand" href="/">' +
        '<i class="fas fa-satellite-dish"></i>' +
        '<span>VLSC<span class="dot">·</span>Projects</span>' +
      '</a>' +
      '<nav class="scope-gn-links">' +
        siteLink('fde', 'FDE') +
        siteLink('mrrc', 'MRRC') +
        siteLink('mrrc_ft710', 'FT-710') +
        siteLink('mrrc_modern', 'Modern') +
        siteLink('mrrc_ft8', 'FT-8') +
        siteLink('sunmrrc', 'SunMRRC') +
        siteLink('sunsdrmobile', 'SunsdrMobile') +
        siteLink('blog', 'Blog') +
      '</nav>' +
      '<a class="scope-gn-gh" href="https://github.com/cheenle" target="_blank" rel="noopener">' +
        '<i class="fab fa-github"></i>' +
      '</a>' +
    '</div>';
  document.body.insertBefore(gn, document.body.firstChild);
  document.body.classList.add('scope-gn-on');
```

- [ ] **Step 2: Add scroll progress, back-to-top, and scroll reveal**

Append to `portal/js/scope.js`:

```javascript
  var sp = document.createElement('div');
  sp.className = 'scope-scroll-progress';
  document.body.appendChild(sp);

  var bt = document.createElement('button');
  bt.type = 'button';
  bt.className = 'scope-to-top';
  bt.setAttribute('aria-label', LABELS.back);
  bt.innerHTML = '<i class="fas fa-arrow-up"></i>';
  bt.addEventListener('click', function () { window.scrollTo({ top: 0, behavior: 'smooth' }); });
  document.body.appendChild(bt);

  var navbar = document.querySelector('.scope-site-nav, .navbar, .header');
  var ticking = false;
  function onScroll() {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(function () {
      var st = window.scrollY || document.documentElement.scrollTop;
      var h = document.documentElement.scrollHeight - window.innerHeight;
      sp.style.width = (h > 0 ? (st / h * 100) : 0) + '%';
      if (navbar) navbar.classList.toggle('scrolled', st > 40);
      bt.classList.toggle('show', st > 600);
      ticking = false;
    });
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  if ('IntersectionObserver' in window) {
    var reveal = document.querySelectorAll('.scope-reveal');
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    reveal.forEach(function (el) { io.observe(el); });
  }
```

- [ ] **Step 3: Add mobile menu toggle and bootstrap feedback/AdSense**

Append to `portal/js/scope.js`:

```javascript
  var toggle = document.querySelector('.scope-site-nav-toggle, .mobile-menu-toggle');
  var navLinks = document.querySelector('.scope-site-nav-links, .nav-links');
  if (toggle && navLinks) {
    toggle.addEventListener('click', function () {
      navLinks.classList.toggle('active');
      toggle.classList.toggle('is-open');
    });
    navLinks.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () {
        navLinks.classList.remove('active');
        toggle.classList.remove('is-open');
      });
    });
  }

  if (location.hostname === 'www.vlsc.net') {
    if (!document.querySelector('script[src*="adsbygoogle"]')) {
      var ads = document.createElement('script');
      ads.async = true;
      ads.src = 'https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-7442510147240155';
      ads.crossOrigin = 'anonymous';
      document.head.appendChild(ads);
    }
    if (!/\/feedback\/(admin|api)/.test(location.pathname)) {
      var fbCss = document.createElement('link');
      fbCss.rel = 'stylesheet';
      fbCss.href = '/feedback/static/feedback.css?v=1';
      document.head.appendChild(fbCss);
      var fbJs = document.createElement('script');
      fbJs.src = '/feedback/static/feedback.js?v=1';
      document.body.appendChild(fbJs);
    }
  }
})();
```

- [ ] **Step 4: Verify no syntax errors**

Run:

```bash
node --check portal/js/scope.js
# Expected: no output (success)
```

- [ ] **Step 5: Commit**

```bash
git add portal/js/scope.js
git commit -m "feat(scope): add Scope.js shared nav and utilities"
```

---

## Task 3: Add Scope Navigation Styles to scope.css

**Files:**
- Modify: `portal/css/scope.css`

- [ ] **Step 1: Add global top nav styles**

Append to `portal/css/scope.css`:

```css
.scope-gn {
  position: fixed;
  top: 0; left: 0; right: 0;
  z-index: 120;
  height: var(--scope-gn-h);
  background: rgba(5, 10, 8, 0.96);
  border-bottom: 1px solid var(--scope-border);
  backdrop-filter: blur(14px);
  font-family: var(--scope-font-mono);
  font-size: 0.8125rem;
}
.scope-gn-inner {
  height: var(--scope-gn-h);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}
.scope-gn-brand {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-weight: 700;
  color: var(--scope-text);
  white-space: nowrap;
}
.scope-gn-brand i { color: var(--scope-primary); }
.scope-gn-brand .dot { color: var(--scope-primary); margin: 0 0.35rem; opacity: 0.5; }
.scope-gn-links {
  display: flex;
  align-items: center;
  gap: 1.1rem;
}
.scope-gn-links a {
  color: var(--scope-text-2);
  font-weight: 500;
  white-space: nowrap;
  padding: 0.2rem 0;
  position: relative;
}
.scope-gn-links a:hover { color: var(--scope-text); text-decoration: none; }
.scope-gn-links a.is-active { color: var(--scope-primary); }
.scope-gn-gh { color: var(--scope-text-2); }
.scope-gn-gh:hover { color: var(--scope-text); }

body.scope-gn-on { padding-top: var(--scope-gn-h); }
body.scope-gn-on .scope-site-nav,
body.scope-gn-on .navbar,
body.scope-gn-on .header { top: var(--scope-gn-h); }
```

- [ ] **Step 2: Add mobile global nav wrap rules**

Append to `portal/css/scope.css`:

```css
@media (max-width: 768px) {
  :root { --scope-gn-h: 72px; }
  .scope-gn { height: auto; min-height: var(--scope-gn-h); }
  .scope-gn-inner {
    flex-wrap: wrap;
    height: auto;
    min-height: var(--scope-gn-h);
    gap: 0.35rem;
    padding: 0.4rem 1.1rem;
  }
  .scope-gn-brand { order: 1; }
  .scope-gn-gh { order: 2; }
  .scope-gn-links {
    order: 3;
    width: 100%;
    justify-content: center;
    flex-wrap: wrap;
    gap: 0.35rem 0.75rem;
    padding-top: 0.2rem;
  }
  .scope-gn-links a { padding: 0.1rem 0; }
}
```

- [ ] **Step 3: Add site nav, scroll progress, back-to-top styles**

Append to `portal/css/scope.css`:

```css
.scope-site-nav {
  position: fixed;
  top: 0; left: 0; right: 0;
  z-index: 110;
  height: var(--scope-nav-h);
  background: rgba(5, 10, 8, 0.95);
  border-bottom: 1px solid var(--scope-border);
}
.scope-site-nav-inner {
  height: var(--scope-nav-h);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}
.scope-site-nav-links {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  list-style: none;
  margin: 0; padding: 0;
}
.scope-site-nav-links a { color: var(--scope-text-2); font-weight: 500; }
.scope-site-nav-links a:hover { color: var(--scope-text); text-decoration: none; }
.scope-site-nav-toggle { display: none; background: none; border: none; color: var(--scope-primary); font-size: 1.25rem; cursor: pointer; }

.scope-scroll-progress {
  position: fixed; top: 0; left: 0; z-index: 200;
  height: 2px; width: 0%;
  background: linear-gradient(90deg, var(--scope-primary), var(--scope-primary-dim));
  pointer-events: none;
}
.scope-to-top {
  position: fixed; right: 1.5rem; bottom: 1.5rem; z-index: 110;
  width: 44px; height: 44px; border-radius: 50%;
  background: var(--scope-surface); border: 1px solid var(--scope-border);
  color: var(--scope-primary); cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  opacity: 0; visibility: hidden; transform: translateY(12px);
  transition: all 0.3s ease;
}
.scope-to-top.show { opacity: 1; visibility: visible; transform: translateY(0); }
.scope-to-top:hover { border-color: var(--scope-primary); box-shadow: 0 0 16px var(--scope-primary-glow); }

.scope-reveal { opacity: 0; transform: translateY(24px); transition: all 0.6s ease; }
.scope-reveal.in { opacity: 1; transform: translateY(0); }

@media (max-width: 768px) {
  .scope-site-nav-links {
    display: none;
    position: absolute;
    top: var(--scope-nav-h);
    left: 0; right: 0;
    background: rgba(5, 10, 8, 0.98);
    border-bottom: 1px solid var(--scope-border);
    flex-direction: column;
    padding: 1rem 1.5rem;
    gap: 0.75rem;
  }
  .scope-site-nav-links.active { display: flex; }
  .scope-site-nav-toggle { display: block; }
}
```

- [ ] **Step 4: Commit**

```bash
git add portal/css/scope.css
git commit -m "feat(scope): add navigation, progress, and utility styles"
```

---

## Task 4: Rebuild Portal Homepage

**Files:**
- Modify: `portal/index.html`
- Modify: `portal/zh/index.html`

- [ ] **Step 1: Update head and body attributes in `portal/index.html`**

Replace the `<head>` stylesheet links with:

```html
<link rel="stylesheet" href="css/scope.css?v=1">
<link rel="stylesheet" href="css/portal.scope.css?v=1">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
```

Add to `<body>`: `data-site="portal" class="fx-grid"`

- [ ] **Step 2: Replace old navbar with Scope site nav**

Remove the existing `<nav class="navbar">...</nav>` block and replace with:

```html
<nav class="scope-site-nav">
  <div class="container scope-site-nav-inner">
    <a href="#" class="scope-site-brand fx-glow">VLSC<span style="color:var(--scope-primary)">·</span>Projects</a>
    <ul class="scope-site-nav-links">
      <li><a href="#selector">Selector</a></li>
      <li><a href="#projects">Projects</a></li>
      <li><a href="#modern">Modern</a></li>
      <li><a href="#ecosystem">Ecosystem</a></li>
      <li><a href="/blog/">Blog</a></li>
      <li><a href="/fde.html">FDE</a></li>
      <li><a href="https://github.com/cheenle" target="_blank" rel="noopener"><i class="fab fa-github"></i></a></li>
    </ul>
    <div style="display:flex;align-items:center;gap:0.75rem;">
      <a href="zh/index.html" class="scope-btn" style="padding:0.4rem 0.8rem;font-size:0.75rem;">中文</a>
      <button class="scope-site-nav-toggle" aria-label="Toggle menu"><i class="fas fa-bars"></i></button>
    </div>
  </div>
</nav>
```

- [ ] **Step 3: Replace hero section**

Replace the existing `<section class="hero">` with:

```html
<section class="scope-hero">
  <div class="container" style="position:relative;z-index:1;">
    <div class="section-label">Open Source · Remote Radio Control</div>
    <h1 class="fx-glow" style="font-family:var(--scope-font-mono);font-size:clamp(2.2rem,6vw,4rem);font-weight:700;margin:0 0 1rem;line-height:1.1;">
      Control Your Station<br>From Anywhere
    </h1>
    <p style="color:var(--scope-text-2);font-size:1.15rem;max-width:640px;margin:0 0 2rem;">
      Seven open-source projects for modern HAM operators. Browser, phone, or native iOS — one ecosystem for HF, SDR, and digital modes.
    </p>
    <div style="display:flex;flex-wrap:wrap;gap:1rem;">
      <a href="#selector" class="scope-btn scope-btn-primary"><i class="fas fa-compass"></i> Find Your Project</a>
      <a href="#community" class="scope-btn"><i class="fas fa-qrcode"></i> Join WeChat Group</a>
    </div>
  </div>
</section>
```

- [ ] **Step 4: Add hero styles to `portal/css/portal.scope.css`**

Create `portal/css/portal.scope.css`:

```css
.scope-hero {
  position: relative;
  padding: calc(var(--scope-gn-h) + 6rem) 0 6rem;
  background:
    radial-gradient(circle at 70% 30%, rgba(0, 255, 65, 0.08), transparent 40%),
    var(--scope-bg);
  overflow: hidden;
}
.scope-hero::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(0, 255, 65, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 255, 65, 0.05) 1px, transparent 1px);
  background-size: 32px 32px;
  mask-image: radial-gradient(circle at 50% 0%, black 0%, transparent 70%);
  -webkit-mask-image: radial-gradient(circle at 50% 0%, black 0%, transparent 70%);
}
```

- [ ] **Step 5: Replace project selector and project grid sections**

Replace the existing selector table with a Scope-styled table and replace the project cards grid with `.scope-card` markup. Keep the existing 7-project content but apply the new classes.

- [ ] **Step 6: Add MRRC Modern spotlight section**

Insert after the selector section:

```html
<section class="scope-section scope-section-alt" id="modern">
  <div class="container">
    <div class="section-label">Newest</div>
    <h2 class="section-title">MRRC Modern — One Codebase, Multiple Radios</h2>
    <p class="section-subtitle">Direct USB-native remote control for Yaesu FT-710 and Icom IC-7300 / IC-7300MK2. No Hamlib, no SCU-LAN10, just plug in and operate.</p>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:1rem;margin-top:2rem;">
      <div class="scope-card"><i class="fas fa-microchip" style="color:var(--scope-primary);margin-bottom:0.5rem;"></i><h3 style="margin:0 0 0.5rem;">FT-710 Backend</h3><p style="color:var(--scope-text-2);font-size:0.9rem;margin:0;">FT4222 SPI spectrum, bidirectional Opus audio, full CAT.</p></div>
      <div class="scope-card"><i class="fas fa-broadcast-tower" style="color:var(--scope-primary);margin-bottom:0.5rem;"></i><h3 style="margin:0 0 0.5rem;">IC-7300 Backend</h3><p style="color:var(--scope-text-2);font-size:0.9rem;margin:0;">CI-V spectrum and control via a single USB cable.</p></div>
      <div class="scope-card"><i class="fas fa-mobile-alt" style="color:var(--scope-primary);margin-bottom:0.5rem;"></i><h3 style="margin:0 0 0.5rem;">PWA + Mobile</h3><p style="color:var(--scope-text-2);font-size:0.9rem;margin:0;">Works in browser and as installable PWA on phone/tablet.</p></div>
    </div>
    <div style="margin-top:1.5rem;">
      <a href="/mrrc_modern/" class="scope-btn scope-btn-primary"><i class="fas fa-external-link-alt"></i> Open MRRC Modern</a>
    </div>
  </div>
</section>
```

- [ ] **Step 7: Update QR community section and footer**

Replace the existing QR section with:

```html
<section class="scope-section" id="community">
  <div class="container" style="text-align:center;">
    <div class="section-label">Community</div>
    <h2 class="section-title">Join the Conversation</h2>
    <p class="section-subtitle" style="margin-left:auto;margin-right:auto;">Scan the QR code with WeChat to join the MRRC-HAM group.</p>
    <div class="scope-card" style="display:inline-block;padding:1.25rem;max-width:280px;">
      <img src="images/qr-wechat-group.jpg" alt="WeChat QR code for MRRC-HAM group" style="border-radius:var(--scope-radius);">
    </div>
    <p style="color:var(--scope-text-muted);font-size:0.85rem;margin-top:1rem;">QR code valid until Aug 29, 2026. Will be updated when refreshed.</p>
  </div>
</section>
```

- [ ] **Step 8: Update script tag at end of body**

Replace the old `global-nav.js` script tag with:

```html
<script src="js/scope.js?v=1" defer></script>
```

- [ ] **Step 9: Mirror changes to `portal/zh/index.html`**

Apply the same structural changes. Translate visible labels:
- "Open Source · Remote Radio Control" → "开源 · 远程电台控制"
- "Control Your Station From Anywhere" → "随时随地控制你的电台"
- "Find Your Project" → "找到你的项目"
- "Join WeChat Group" → "加入微信群"
- "MRRC Modern — One Codebase, Multiple Radios" → "MRRC Modern — 一套代码，多台电台"
- etc.

- [ ] **Step 10: Verify homepage renders**

Open `portal/index.html` locally in a browser or run:

```bash
python3 -m http.server 8000 --directory portal
# Then curl the rendered HTML and check for scope.css
```

Check that:
- `scope.css?v=1` and `scope.js?v=1` are referenced.
- The hero, selector, spotlight, project grid, QR section, and footer are present.
- No references to `octen.css` or `global-nav.js` remain.

- [ ] **Step 11: Commit**

```bash
git add portal/index.html portal/zh/index.html portal/css/portal.scope.css
git commit -m "feat(portal): rebuild homepage with Scope.css"
```

---

## Task 5: Update Other Portal Pages

**Files:**
- Modify: `portal/about.html`, `portal/zh/about.html`
- Modify: `portal/contact.html`, `portal/zh/contact.html`
- Modify: `portal/privacy.html`, `portal/zh/privacy.html`
- Modify: `portal/fde.html`, `portal/zh/fde.html`
- Modify: `portal/blog/index.html` and four article pages

- [ ] **Step 1: Create a reusable page shell snippet**

For each Portal page, apply this pattern:

1. Replace `octen.css` and `sunsdrmobile.css` links with:
   ```html
   <link rel="stylesheet" href="css/scope.css?v=1">
   <link rel="stylesheet" href="css/portal.scope.css?v=1">
   ```
2. Add `data-site="portal" class="fx-grid"` to `<body>`.
3. Replace the old `<nav class="navbar">` with the Scope site nav from Task 4 (adjusted active link if needed).
4. Wrap main content in `<main class="container" style="padding-top:calc(var(--scope-gn-h) + 2rem);padding-bottom:4rem;">`.
5. Replace the old footer with a simple Scope footer.
6. Replace `global-nav.js` script with `scope.js?v=1`.

- [ ] **Step 2: Update `about.html` and `zh/about.html`**

Restyle project cards with `.scope-card`. Keep content about the ecosystem. Add the 7-project grid.

- [ ] **Step 3: Update `contact.html` and `zh/contact.html`**

Wrap contact info in `.scope-card`. Keep existing links and form if present.

- [ ] **Step 4: Update `privacy.html` and `zh/privacy.html`**

Apply new typography. Keep all legal text unchanged.

- [ ] **Step 5: Update `fde.html` and `zh/fde.html`**

Apply new chrome. Keep existing FDE content.

- [ ] **Step 6: Update blog index and articles**

For `portal/blog/index.html` and the four article pages:
- Replace stylesheets with `../css/scope.css?v=1` and `../css/portal.scope.css?v=1`.
- Use Scope site nav with adjusted relative paths (`../`).
- Use `scope.js?v=1` with `../../js/scope.js?v=1` as needed.
- Restyle article cards and article body typography.

- [ ] **Step 7: Verify all Portal pages**

Run a grep to confirm no Portal HTML references old assets:

```bash
grep -R "octen\.css\|global-nav\.js\|sunsdrmobile\.css" portal/ || echo "No old assets found"
```

- [ ] **Step 8: Commit**

```bash
git add portal/
git commit -m "feat(portal): restyle about, contact, privacy, fde, blog with Scope.css"
```

---

## Task 6: Copy Scope.css / Scope.js to All Sub-Sites

**Files:**
- Create in each sub-site: `css/scope.css`, `js/scope.js`

- [ ] **Step 1: Copy files to Portal-adjacent sites**

```bash
cp portal/css/scope.css efhw/css/scope.css
cp portal/js/scope.js efhw/js/scope.js
```

- [ ] **Step 2: Copy files to external sub-sites**

```bash
cp portal/css/scope.css /Users/cheenle/UHRR/MRRC/website/css/scope.css
cp portal/js/scope.js /Users/cheenle/UHRR/MRRC/website/js/scope.js

cp portal/css/scope.css /Users/cheenle/HAM/mrrc_ft710/website/css/scope.css
cp portal/js/scope.js /Users/cheenle/HAM/mrrc_ft710/website/js/scope.js

cp portal/css/scope.css /Users/cheenle/HAM/mrrc_modern/website/css/scope.css
cp portal/js/scope.js /Users/cheenle/HAM/mrrc_modern/website/js/scope.js

cp portal/css/scope.css /Users/cheenle/HAM/ft8/website/css/scope.css
cp portal/js/scope.js /Users/cheenle/HAM/ft8/website/js/scope.js

cp portal/css/scope.css /Users/cheenle/HAM/sunsdr/sunmrrc/website/css/scope.css
cp portal/js/scope.js /Users/cheenle/HAM/sunsdr/sunmrrc/website/js/scope.js

cp portal/css/scope.css /Users/cheenle/HAM/sunsdr/SunsdrMobile/website/css/scope.css
cp portal/js/scope.js /Users/cheenle/HAM/sunsdr/SunsdrMobile/website/js/scope.js
```

- [ ] **Step 3: Verify copies exist**

```bash
for f in efhw/css/scope.css /Users/cheenle/UHRR/MRRC/website/css/scope.css /Users/cheenle/HAM/mrrc_ft710/website/css/scope.css /Users/cheenle/HAM/mrrc_modern/website/css/scope.css /Users/cheenle/HAM/ft8/website/css/scope.css /Users/cheenle/HAM/sunsdr/sunmrrc/website/css/scope.css /Users/cheenle/HAM/sunsdr/SunsdrMobile/website/css/scope.css; do ls -la "$f"; done
```

- [ ] **Step 4: Commit**

```bash
git add efhw/css/scope.css efhw/js/scope.js
git commit -m "feat(scope): distribute Scope.css and Scope.js to all sub-sites"
```

Note: external sub-sites are in other git repos; handle their commits separately or via their deploy scripts.

---

## Task 7: Rebuild Sub-Site Home Pages

**Files:**
- Modify each sub-site `index.html` and `zh/index.html`

Sites:
- `UHRR/MRRC/website/index.html`, `zh/index.html`
- `website/efhw/index.html`, `zh/index.html`
- `HAM/mrrc_ft710/website/index.html`, `zh/index.html`
- `HAM/mrrc_modern/website/index.html`, `zh/index.html`
- `HAM/ft8/website/index.html`, `zh/index.html`
- `HAM/sunsdr/sunmrrc/website/index.html`, `zh/index.html`
- `HAM/sunsdr/SunsdrMobile/website/index.html`, `zh/index.html`

- [ ] **Step 1: Create a standard sub-site page template**

For each site, apply:

1. In `<head>`:
   ```html
   <link rel="stylesheet" href="css/scope.css?v=1">
   <link rel="stylesheet" href="css/<site>.scope.css?v=1">
   <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
   ```
2. `<body data-site="<site-key>" class="fx-grid">` (use site keys from scope.js: `mrrc`, `mrrc_ft710`, `mrrc_modern`, `mrrc_ft8`, `sunmrrc`, `sunsdrmobile`, `efhw`).
3. Site nav (example for MRRC):
   ```html
   <nav class="scope-site-nav">
     <div class="container scope-site-nav-inner">
       <a href="#" class="scope-site-brand fx-glow">MRRC</a>
       <ul class="scope-site-nav-links">
         <li><a href="#features">Features</a></li>
         <li><a href="#demo">Demo</a></li>
         <li><a href="docs/installation.html">Install</a></li>
         <li><a href="/efhw/">EFHW</a></li>
         <li><a href="/mrrc_modern/">Modern</a></li>
         <li><a href="https://github.com/cheenle/UHRR_mac" target="_blank"><i class="fab fa-github"></i></a></li>
       </ul>
       <div style="display:flex;align-items:center;gap:0.75rem;">
         <a href="zh/index.html" class="scope-btn" style="padding:0.4rem 0.8rem;font-size:0.75rem;">中文</a>
         <button class="scope-site-nav-toggle"><i class="fas fa-bars"></i></button>
       </div>
     </div>
   </nav>
   ```
4. Hero section using project-specific headline and CTAs.
5. Feature highlights in `.scope-card` grid.
6. QR community section.
7. Simple footer.
8. `<script src="js/scope.js?v=1" defer></script>`.

- [ ] **Step 2: Update MRRC home page**

Apply the template. Keep MRRC-specific content: universal HF remote, Hamlib/rigctld, Opus audio, WDSP, AI voice, FT8, PTT safety.

- [ ] **Step 3: Update EFHW home page**

Apply the template. Keep EFHW-specific content: ESP32-S3 auto-tuner, bias-tee, Fuchs coupler, servo-driven ATU.

- [ ] **Step 4: Update MRRC FT-710 home page**

Apply the template. Keep FT-710-specific content: FT4222 SPI spectrum, single USB cable, v1.8.0 downloads.

- [ ] **Step 5: Update MRRC Modern home page**

Apply the template. Highlight FT-710 and IC-7300 backends, v1.10.1, PWA/mobile.

- [ ] **Step 6: Update MRRC-FT8 home page**

Apply the template. Keep FT8-specific content: WSJT-X DSP, supervised worker, mobile cockpit.

- [ ] **Step 7: Update SunMRRC home page**

Apply the template. Keep SunSDR2 DX-specific content: IQ demodulation, FFT waterfall, Opus/PCM, WebSocket endpoints.

- [ ] **Step 8: Update SunsdrMobile home page**

Apply the template. Keep iOS SwiftUI app content.

- [ ] **Step 9: Mirror all EN pages to ZH pages**

For each site, apply the same structure to `zh/index.html` with Chinese translations. Adjust relative paths for CSS/JS (`../css/scope.css`, `../js/scope.js`) and nav links (`../docs/...`, `./index.html`).

- [ ] **Step 10: Verify no old asset references in sub-site home pages**

```bash
for f in /Users/cheenle/UHRR/MRRC/website/index.html /Users/cheenle/HAM/website/efhw/index.html /Users/cheenle/HAM/mrrc_ft710/website/index.html /Users/cheenle/HAM/mrrc_modern/website/index.html /Users/cheenle/HAM/ft8/website/index.html /Users/cheenle/HAM/sunsdr/sunmrrc/website/index.html /Users/cheenle/HAM/sunsdr/SunsdrMobile/website/index.html; do echo "=== $f ==="; grep -nE "octen\.css|global-nav\.js|sunsdrmobile\.css" "$f" || echo "OK"; done
```

- [ ] **Step 11: Commit per site or in batches**

For the local repo sites:

```bash
git add efhw/index.html efhw/zh/index.html
git commit -m "feat(efhw): rebuild homepage with Scope.css"
```

External sites commit separately in their own repos if desired, or deploy without committing.

---

## Task 8: Apply Scope.css to SDD and Docs Pages

**Files:**
- Modify SDD builder scripts and/or individual SDD HTML files.

- [ ] **Step 1: Identify SDD generation entry points**

Check:
- `/Users/cheenle/HAM/mrrc_ft710/website/build_sdd.py`
- `/Users/cheenle/HAM/ft8/website/build_sdd.py`
- `/Users/cheenle/HAM/sunsdr/sunmrrc/website/build_sdd.py`

- [ ] **Step 2: Update SDD template to include Scope.css**

In each `build_sdd.py`, locate the `<head>` template and replace old CSS links with:

```html
<link rel="stylesheet" href="../css/scope.css?v=1">
```

Add `data-site="<site-key>" class="fx-grid"` to `<body>`.

Replace `global-nav.js` references with:

```html
<script src="../js/scope.js?v=1" defer></script>
```

- [ ] **Step 3: Regenerate SDD HTML files**

For each site with `build_sdd.py`:

```bash
cd /Users/cheenle/HAM/mrrc_ft710/website && python3 build_sdd.py
cd /Users/cheenle/HAM/ft8/website && python3 build_sdd.py
cd /Users/cheenle/HAM/sunsdr/sunmrrc/website && python3 build_sdd.py
```

- [ ] **Step 4: Manually patch non-generated SDD/docs pages**

For SDD HTML files that are not generated or for docs pages in `UHRR/MRRC/website/docs/`, update the `<head>` to reference `scope.css` and `scope.js`, add `data-site` and `fx-grid` to body, and remove old `octen.css`/`global-nav.js` references.

- [ ] **Step 5: Verify docs tables and code blocks**

Open a few SDD pages in a browser and confirm:
- Tables use `.scope-table` styling.
- Code blocks use `.scope-code` styling.
- Global nav appears at the top.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat(sdd): apply Scope.css to generated and static docs pages"
```

---

## Task 9: Cleanup and Cache Busting

**Files:**
- Modify: all HTML files that still reference old assets.

- [ ] **Step 1: Find and remove old asset references**

```bash
find /Users/cheenle/HAM/website /Users/cheenle/UHRR/MRRC/website /Users/cheenle/HAM/mrrc_ft710/website /Users/cheenle/HAM/mrrc_modern/website /Users/cheenle/HAM/ft8/website /Users/cheenle/HAM/sunsdr/sunmrrc/website /Users/cheenle/HAM/sunsdr/SunsdrMobile/website -type f -name '*.html' -exec grep -lE 'octen\.css|global-nav\.js' {} + 2>/dev/null
```

For any matches, update the `<head>` and script tags to use `scope.css` / `scope.js`.

- [ ] **Step 2: Bump all Scope asset versions to v=2**

After initial local testing, bump cache busters to ensure production caches are invalidated:

```bash
find /Users/cheenle/HAM/website /Users/cheenle/UHRR/MRRC/website /Users/cheenle/HAM/mrrc_ft710/website /Users/cheenle/HAM/mrrc_modern/website /Users/cheenle/HAM/ft8/website /Users/cheenle/HAM/sunsdr/sunmrrc/website /Users/cheenle/HAM/sunsdr/SunsdrMobile/website -type f -name '*.html' -exec sed -i '' 's/scope\.css?v=1/scope.css?v=2/g; s/scope\.js?v=1/scope.js?v=2/g' {} + 2>/dev/null
```

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "chore(scope): cleanup old assets and bump cache versions"
```

---

## Task 10: Deploy All Sites

**Files:**
- Deploy all sites to `www.vlsc.net`.

- [ ] **Step 1: Deploy Portal**

```bash
rsync -avz --rsync-path="sudo rsync" --exclude='.DS_Store' --exclude='deploy.sh' --exclude='__pycache__' /Users/cheenle/HAM/website/portal/ cheenle@www.vlsc.net:/var/www/vlsc.net/
ssh cheenle@www.vlsc.net 'sudo chown -R www-data:www-data /var/www/vlsc.net && sudo chmod -R 755 /var/www/vlsc.net && sudo nginx -t && sudo systemctl reload nginx'
```

- [ ] **Step 2: Deploy EFHW**

```bash
rsync -avz --delete --rsync-path="sudo rsync" --exclude='.DS_Store' --exclude='deploy.sh' --exclude='__pycache__' /Users/cheenle/HAM/website/efhw/ cheenle@www.vlsc.net:/var/www/vlsc.net/efhw/
ssh cheenle@www.vlsc.net 'sudo chown -R www-data:www-data /var/www/vlsc.net/efhw && sudo chmod -R 755 /var/www/vlsc.net/efhw && sudo nginx -t && sudo systemctl reload nginx'
```

- [ ] **Step 3: Deploy MRRC**

```bash
rsync -avz --delete --rsync-path="sudo rsync" --exclude='.DS_Store' --exclude='deploy.sh' --exclude='__pycache__' /Users/cheenle/UHRR/MRRC/website/ cheenle@www.vlsc.net:/var/www/vlsc.net/mrrc/
ssh cheenle@www.vlsc.net 'sudo chown -R www-data:www-data /var/www/vlsc.net/mrrc && sudo chmod -R 755 /var/www/vlsc.net/mrrc && sudo nginx -t && sudo systemctl reload nginx'
```

- [ ] **Step 4: Deploy MRRC FT-710, Modern, FT-8, SunMRRC, SunsdrMobile**

Repeat the rsync + ssh pattern for:
- `/Users/cheenle/HAM/mrrc_ft710/website/` → `/var/www/vlsc.net/mrrc_ft710/`
- `/Users/cheenle/HAM/mrrc_modern/website/` → `/var/www/vlsc.net/mrrc_modern/`
- `/Users/cheenle/HAM/ft8/website/` → `/var/www/vlsc.net/mrrc_ft8/`
- `/Users/cheenle/HAM/sunsdr/sunmrrc/website/` → `/var/www/vlsc.net/sunmrrc/`
- `/Users/cheenle/HAM/sunsdr/SunsdrMobile/website/` → `/var/www/vlsc.net/sunsdrmobile/`

- [ ] **Step 5: Verify live sites**

Run verification commands:

```bash
for url in https://www.vlsc.net/ https://www.vlsc.net/mrrc/ https://www.vlsc.net/efhw/ https://www.vlsc.net/mrrc_ft710/ https://www.vlsc.net/mrrc_modern/ https://www.vlsc.net/mrrc_ft8/ https://www.vlsc.net/sunmrrc/ https://www.vlsc.net/sunsdrmobile/; do
  echo "=== $url ==="
  curl -sL "$url" | grep -oE 'scope\.css\?v=[0-9]+|scope\.js\?v=[0-9]+' | sort -u
  curl -sL "$url" | grep -c 'scope-gn'
done
```

Expected: every site shows `scope.css?v=2` and `scope.js?v=2`, and `scope-gn` count > 0.

- [ ] **Step 6: Commit deployment notes (optional)**

```bash
git add -A
git commit -m "docs: deployment complete for Scope.css redesign"
```

---

## Self-Review

### Spec coverage

- New design system: Task 1, Task 2, Task 3.
- Portal rewrite: Task 4, Task 5.
- Sub-site distribution and rewrite: Task 6, Task 7.
- SDD/docs styling: Task 8.
- Cleanup/cache busting: Task 9.
- Deployment and verification: Task 10.

### Placeholder scan

- No TBD/TODO in code blocks.
- Every step names exact files or commands.
- Translation step is explicit (Step 9 of Task 4).

### Type consistency

- CSS variable names are consistent across all tasks.
- `data-site` values match `scope.js` PATHS keys.
- Cache-buster `v=1` is later bumped to `v=2` in Task 9.

### Gap

- The plan assumes sub-site `*.scope.css` override files are created only if needed. If a site needs a unique accent, a task must be added per site.
