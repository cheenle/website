# GA4 全站接入 — Implementation Plan

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 让 www.vlsc.net 全部 6 个在线站点（122 页）向 GA4 属性 `G-JQLSKV1MCT` 上报 pageview，且不逐页改 HTML、不让生成物把改动抹掉。

**架构：** gtag.js 由两种既有共享脚本（`js/global-nav.js`、`js/scope.js`）在运行时注入，共 7 个副本（5 个仓）。守卫用 `vlsc.net` 域后缀正则，幂等用 `!window.dataLayer`。隐私政策同步披露 GA4 的第一方 Cookie。

**技术栈：** 原生 JS（无构建、无 npm）、nginx、Python 3.11 + pytest 7.4.3（既有 `portal/tests/`）、无头 Google Chrome（端到端验证）。

## Global Constraints

- 纯静态，无构建步骤，无 npm，无框架。
- 每页必须至少加载 `js/scope.js` 或 `js/global-nav.js` 之一（本次改动的覆盖前提）。
- **生成物不得手改**：`sdd/*.html` 由 `build_sdd.py` 产出；本次不碰任何生成物，也不碰 builder —— 注入点在共享脚本，生成页天然继承。
- 既有 `location.hostname === 'www.vlsc.net'` 的 AdSense / 反馈块**不得改动**（GA 新块是独立同级 `if`）。
- 归档站（`mrrc_ft710/`、`SunsdrMobile/`）与 `feedback/` 不在范围。
- 全站 grep **必须带尾斜杠**（BSD grep 不跟随无尾斜杠的符号链接，静默 0 命中）。
- commit **只 `git add` 指定文件**：`HAM/website` 8 个、`MRRC` 25 个、`sunsdr` 13 个、`ft8` 4 个未提交改动必须保持未提交。
- pytest 解释器：`/opt/homebrew/bin/python3.11`（`python3` 是 3.14 且无 pytest）。

---

## 文件结构

```
website/                                  # 仓根 = /Users/cheenle/HAM/website
├── portal/
│   ├── js/global-nav.js                  # 修改：注入 GA（覆盖 portal 29 页）
│   ├── privacy.html                      # 修改：披露 GA4（§74-75 两条 bullet + 新增章节 + Last updated）
│   ├── zh/privacy.html                   # 修改：中文镜像同上
│   ├── sitemap.xml                       # 重新生成（lastmod）
│   └── tests/test_analytics_coverage.py  # 新增：GA 契约测试（先写，必须失败）
├── efhw/js/global-nav.js                 # 修改：注入 GA（覆盖 efhw 4 页）
├── docs/superpowers/…                    # 本规格与计划（已提交）
├── mrrc/js/global-nav.js                 # → /Users/cheenle/HAM/MRRC/website
├── mrrc_modern/js/{scope.js,global-nav.js}
├── sunmrrc/js/scope.js                   # → /Users/cheenle/HAM/sunsdr/sunmrrc/website
└── mrrc_ft8/js/scope.js                  # → /Users/cheenle/HAM/ft8/website
```

---

### Task 1：GA 契约测试（先写，运行确认失败）

**文件：**
- 创建：`portal/tests/test_analytics_coverage.py`
- 测试：自身

**Interfaces：**
- Consumes：`REPO` 常量、7 个共享脚本路径、6 个站点目录、常量 `G-JQLSKV1MCT`。
- Produces：`SCRIPTS` / `SITES` 列表与 `_guard_regex()`，供后续任务反复运行；断言「7 个副本都带 GA 块」「守卫正则只放行 vlsc 域」「每页都加载共享脚本」。

- [ ] **Step 1：写失败测试**

```python
"""GA4 injection contract tests.

Why this file exists: the analytics snippet ships inside a shared script
(scope.js / global-nav.js), not pasted into 122 pages. Two failures are
possible and neither looks broken in a browser:

  1. one shared-script copy loses the block (a rebuild, a hand-edit), and an
     entire site silently stops reporting;
  2. a new page ships without either shared script, so it is never counted.

Both are green-tree failures. These tests pin them.
"""
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GA_ID = "G-JQLSKV1MCT"

# The 7 shared-script copies carrying the snippet, across 5 repositories.
SCRIPTS = [
    "portal/js/global-nav.js",
    "efhw/js/global-nav.js",
    "mrrc/js/global-nav.js",
    "mrrc_modern/js/scope.js",
    "mrrc_modern/js/global-nav.js",
    "sunmrrc/js/scope.js",
    "mrrc_ft8/js/scope.js",
]

# Every HTML page under these sites must load one of the shared scripts.
SITES = ["portal", "efhw", "mrrc", "mrrc_modern", "sunmrrc", "mrrc_ft8"]
SHARED = ("scope.js", "global-nav.js")

# Canary, calibrated 2026-09-13: 29+4+25+23+20+21 = 122 pages. Retiring a
# sub-site legitimately lowers this; do not lower it to make a walk failure pass.
MIN_PAGES = 120


def _read(rel):
    with open(os.path.join(REPO, rel), encoding="utf-8") as f:
        return f.read()


def _html_pages(site):
    for dirpath, _, filenames in os.walk(os.path.join(REPO, site)):
        for fn in sorted(filenames):
            if fn.endswith(".html"):
                yield os.path.join(dirpath, fn)


def _guard_regex(text):
    """Lift the shipped host guard out of the file: test the artifact, not a copy."""
    m = re.search(
        r"if \(/(.+?)/\.test\(location\.hostname\) && !window\.dataLayer\)", text)
    assert m, "GA 守卫语句缺失"
    return re.compile(m.group(1))


def test_every_shared_script_carries_the_ga_block():
    for rel in SCRIPTS:
        text = _read(rel)
        assert GA_ID in text, f"{rel} 缺 GA 测量 ID"
        assert f"googletagmanager.com/gtag/js?id={GA_ID}" in text, f"{rel} 缺 gtag.js 地址"
        assert f"window.gtag('config', '{GA_ID}')" in text, f"{rel} 缺 config 调用"
        assert f"window.gtag('js', new Date())" in text, f"{rel} 缺 js 调用"
        # dataLayer 必须先于 gtag.js 挂载定义，否则与 async 加载竞态。
        assert text.index("window.dataLayer = window.dataLayer || []") < text.index(
            f"googletagmanager.com/gtag/js?id={GA_ID}"), f"{rel} dataLayer 定义晚于脚本挂载"


def test_guard_regex_accepts_only_vlsc_hosts():
    for rel in SCRIPTS:
        guard = _guard_regex(_read(rel))
        assert guard.search("www.vlsc.net"), f"{rel} 未放行 www.vlsc.net"
        assert guard.search("vlsc.net"), f"{rel} 未放行 vlsc.net"
        for host in ("localhost", "", "127.0.0.1", "evil-vlsc.net", "vlsc.net.evil.com"):
            assert not guard.search(host), f"{rel} 误放行 {host!r}"


def test_ga_block_is_idempotent_by_construction():
    for rel in SCRIPTS:
        assert "!window.dataLayer" in _read(rel), f"{rel} 缺幂等守卫"


def test_every_page_loads_a_shared_script():
    orphans, total = [], 0
    for site in SITES:
        for page in _html_pages(site):
            total += 1
            with open(page, encoding="utf-8", errors="replace") as f:
                text = f.read()
            if not any(s in text for s in SHARED):
                orphans.append(os.path.relpath(page, REPO))
    assert total >= MIN_PAGES, f"只遍历到 {total} 页，目录遍历可能失效"
    assert not orphans, "未加载共享脚本（将不被统计）: " + ", ".join(sorted(orphans))
```

- [ ] **Step 2：运行测试确认失败**

运行：`cd /Users/cheenle/HAM/website/portal && /opt/homebrew/bin/python3.11 -m pytest tests/test_analytics_coverage.py -q`
预期：**FAIL** —— `test_every_shared_script_carries_the_ga_block` 报 "缺 GA 测量 ID"；
`test_guard_regex_accepts_only_vlsc_hosts` 报 "GA 守卫语句缺失"。
`test_every_page_loads_a_shared_script` 预期 **PASS**（覆盖前提本就成立，共 122 页）。

---

### Task 2：portal + efhw 注入（`HAM/website` 仓）

**文件：**
- 修改：`portal/js/global-nav.js`（末尾 `})();` 之前）
- 修改：`efhw/js/global-nav.js`（同上）

- [ ] **Step 1：在两个文件末尾插入同一段代码**

```js
  // ── 10. Google Analytics (GA4) ──
  // 注入而非逐页内联：SDD 页由 build_sdd.py 生成，改 HTML 会在下次 rebuild 时静默丢失。
  // vlsc.net 后缀守卫使 file:// / localhost / 其他域名不上报；dataLayer 存在性检查
  // 兼作幂等守卫（同页同时加载 scope.js + global-nav.js 时只注入一次），并保证
  // 将来某页若内联官方片段，这里自动让位、不会重复计数。
  if (/(^|\.)vlsc\.net$/.test(location.hostname) && !window.dataLayer) {
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { window.dataLayer.push(arguments); };
    var gaScript = document.createElement('script');
    gaScript.async = true;
    gaScript.src = 'https://www.googletagmanager.com/gtag/js?id=G-JQLSKV1MCT';
    document.head.appendChild(gaScript);
    window.gtag('js', new Date());
    window.gtag('config', 'G-JQLSKV1MCT');
  }
```

插入锚点：两个文件最后的 `})();`。`portal` 副本的最后一个块是反馈 bootstrap（`document.body.appendChild(fbJs); }`），`efhw` 相同。

- [ ] **Step 2：验证语法与注入**

运行：`node --check portal/js/global-nav.js && node --check efhw/js/global-nav.js && echo OK`
预期：`OK`（无语法错误输出）

- [ ] **Step 3：跑契约测试（部分应转绿）**

运行：`cd portal && /opt/homebrew/bin/python3.11 -m pytest tests/test_analytics_coverage.py -q`
预期：4 项中 2 项 PASS（上述两文件已带 GA 块），其余 5 个副本仍 FAIL

---

### Task 3：mrrc 注入（`HAM/MRRC` 仓）

**文件：**
- 修改：`mrrc/js/global-nav.js`（333 行版，止于 §9 AdSense）

- [ ] **Step 1：在末尾 `})();` 之前插入 Task 2 Step 1 的同一段代码**（该副本无反馈块，插入点紧接 AdSense 块之后）

- [ ] **Step 2：语法检查** — `node --check mrrc/js/global-nav.js` → 无输出

---

### Task 4：mrrc_modern 注入（`HAM/mrrc_modern` 仓）

**文件：**
- 修改：`mrrc_modern/js/scope.js`（IIFE 顶层，末尾反馈块之后、`})();` 之前）
- 修改：`mrrc_modern/js/global-nav.js`（末尾 `})();` 之前）

注意：Grep 显示站内 18 页加载 `scope.js`、5 页加载 `global-nav.js`，两组不重叠 → **两个文件都要改**，否则 5 页不被统计。

- [ ] **Step 1：注入同一段代码到两个文件**
- [ ] **Step 2：语法检查** — `node --check mrrc_modern/js/scope.js && node --check mrrc_modern/js/global-nav.js`

---

### Task 5：sunmrrc + mrrc_ft8 注入（`HAM/sunsdr`、`HAM/ft8` 仓）

**文件：**
- 修改：`sunmrrc/js/scope.js`（20 页）
- 修改：`mrrc_ft8/js/scope.js`（21 页）

这两个文件与 `mrrc_modern/js/scope.js` 逐字节相同（`99f14c1c7a2ec61c`），插入点同为「IIFE 顶层，`if (location.hostname === 'www.vlsc.net') { … }` 块之后、`})();` 之前」。

- [ ] **Step 1：注入同一段代码到两个文件**
- [ ] **Step 2：语法检查** — `node --check sunmrrc/js/scope.js && node --check mrrc_ft8/js/scope.js`
- [ ] **Step 3：确认 7 个副本全部通过契约测试**

运行：`cd portal && /opt/homebrew/bin/python3.11 -m pytest tests/test_analytics_coverage.py -q && /opt/homebrew/bin/python3.11 -m pytest tests/ -q`
预期：Task 1 的 4 项全 PASS；全套 **88 passed**（基线 84 + 新增 4）

---

### Task 6：隐私政策披露 GA4（`HAM/website` 仓）

**文件：**
- 修改：`portal/privacy.html:74-75`、`portal/privacy.html:63`、`portal/privacy.html:114`
- 修改：`portal/zh/privacy.html:74-75`、`portal/zh/privacy.html:63`、`portal/zh/privacy.html:114`

理由：现有文本明文否认第一方分析与第一方 Cookie，GA4 上线后即假陈述。

- [ ] **Step 1：替换 EN 的两条 bullet**

原：
```html
        <li><strong>No first-party analytics</strong> — we do not run Google Analytics, Matomo, or any visitor-tracking script of our own.</li>
        <li><strong>No first-party cookies</strong> — this website itself does not set cookies.</li>
```

新：
```html
        <li><strong>One first-party analytics script</strong> — we run <strong>Google Analytics 4</strong> (measurement ID <code>G-JQLSKV1MCT</code>) on the <code>vlsc.net</code> pages, to see which pages and projects are actually read. It is disclosed in full under <em>Analytics</em> below.</li>
        <li><strong>No cookies for anything else</strong> — beyond the cookies Google Analytics sets, this site sets none of its own: no account cookie, no session cookie, and no advertising cookie of ours.</li>
```

- [ ] **Step 2：在 `<h2>Third-party advertising — Google AdSense</h2>` 之前插入新章节**

```html
    <h2>Analytics — Google Analytics 4</h2>
    <p>We use <strong>Google Analytics 4</strong> (measurement ID <code>G-JQLSKV1MCT</code>) to understand which pages and which projects are actually used. The script loads from <code>googletagmanager.com</code>, sets <strong>first-party cookies</strong> on this domain — principally <code>_ga</code> and <code>_ga_*</code>, with the lifetimes Google specifies by default — and sends a page-view record to Google: the page URL, the referring page, an approximate location derived from your IP address, and your browser and device strings.</p>
    <ul>
        <li><strong>Aggregate only</strong> — we read Analytics as aggregate statistics. We do not use it to identify you, and we cannot connect it to an account, because this site has no accounts.</li>
        <li><strong>IP addresses</strong> — Google states that Analytics 4 does not log or store IP addresses; the address is used to derive approximate location and then discarded.</li>
        <li><strong>Opting out</strong> — any content blocker (uBlock Origin, Brave Shields, Privacy Badger, …) that blocks <code>googletagmanager.com</code> stops it completely; the site works identically with Analytics blocked. Google also offers an <a href="https://tools.google.com/dlpage/gaoptout" target="_blank" rel="noopener" style="color:var(--accent);">Analytics opt-out browser add-on</a>.</li>
        <li><strong>Google's Privacy Policy</strong> — <a href="https://policies.google.com/privacy" target="_blank" rel="noopener" style="color:var(--accent);">policies.google.com/privacy</a>.</li>
    </ul>
```

- [ ] **Step 3：更新两处 Last updated（`privacy.html:63` 与 `:114`）** 为 `September 13, 2026`

- [ ] **Step 4：中文镜像 `portal/zh/privacy.html` 同步三步**

新 bullet：
```html
        <li><strong>一个第一方分析脚本</strong> —— 我们在 <code>vlsc.net</code> 页面上运行 <strong>Google Analytics 4</strong>（衡量 ID <code>G-JQLSKV1MCT</code>），用于了解哪些页面、哪些项目真的被阅读。完整说明见下方「分析」一节。</li>
        <li><strong>除此之外不设 Cookie</strong> —— 除 Google Analytics 设置的 Cookie 外，本网站自己不设置任何 Cookie：没有账户 Cookie、没有会话 Cookie、也没有我们自己的广告 Cookie。</li>
```

新章节（插在「第三方广告 —— Google AdSense」之前）：
```html
    <h2>分析 —— Google Analytics 4</h2>
    <p>我们使用 <strong>Google Analytics 4</strong>（衡量 ID <code>G-JQLSKV1MCT</code>）来了解哪些页面、哪些项目真的被使用。该脚本从 <code>googletagmanager.com</code> 加载，在本域设置<strong>第一方 Cookie</strong>——主要是 <code>_ga</code> 与 <code>_ga_*</code>，有效期采用 Google 的默认设定——并向 Google 发送一条网页浏览记录：页面 URL、来源页面、由你的 IP 地址推导出的粗略位置，以及浏览器与设备字符串。</p>
    <ul>
        <li><strong>仅作聚合统计</strong> —— 我们只以聚合统计的形式查看 Analytics。我们不使用它来识别你，也无法把它与任何账户关联，因为本站没有账户。</li>
        <li><strong>IP 地址</strong> —— Google 声明 Analytics 4 不记录也不存储 IP 地址；该地址仅用于推导粗略位置，随后即被丢弃。</li>
        <li><strong>如何退出</strong> —— 任何拦截 <code>googletagmanager.com</code> 的内容拦截器（uBlock Origin、Brave Shields、Privacy Badger 等）都能完全阻止它；屏蔽后本站功能完全一致。Google 也提供 <a href="https://tools.google.com/dlpage/gaoptout" target="_blank" rel="noopener" style="color:var(--accent);">Analytics 退出浏览器插件</a>。</li>
        <li><strong>Google 隐私政策</strong> —— <a href="https://policies.google.com/privacy" target="_blank" rel="noopener" style="color:var(--accent);">policies.google.com/privacy</a>。</li>
    </ul>
```

Last updated 两处改为 `2026 年 9 月 13 日`。

- [ ] **Step 5：验证两页无残留假陈述**

运行：`grep -n "No first-party analytics\|无第一方分析\|No first-party cookies\|无第一方 Cookie" portal/privacy.html portal/zh/privacy.html`
预期：无输出（旧断言已全部替换）

---

### Task 7：重生成 sitemap + 全套测试

**文件：**
- 修改（生成）：`portal/sitemap.xml`

- [ ] **Step 1：重生成**

运行：`cd /Users/cheenle/HAM/website/portal && python3 make_sitemap.py`
预期：无报错；`sitemap.xml` 的 privacy 两条 `lastmod` 变为 `2026-09-13`

- [ ] **Step 2：全套测试**

运行：`cd /Users/cheenle/HAM/website/portal && /opt/homebrew/bin/python3.11 -m pytest tests/ -q`
预期：**88 passed**（不得低于基线 84）

---

### Task 8：端到端验证（无头 Chrome，真注入真渲染）

**文件：** 无（只读验证）。临时文件写在 `/tmp`，不落仓。

- [ ] **Step 1：起本地静态服务器**

运行：`cd /Users/cheenle/HAM/website && (python3 -m http.server 8791 >/tmp/ga_srv.log 2>&1 &) && sleep 1 && curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8791/portal/index.html`
预期：`200`

- [ ] **Step 2：把 www.vlsc.net 映射到本地，断言 gtag 被注入**

**同时把 `*.googletagmanager.com` 黑洞到 127.0.0.1**：DOM 断言只需要那个 `<script>` 元素存在，
而让 gtag.js 真的加载成功会向全新属性灌入 6 条来自 `/portal/index.html` 的测试 pageview。

运行（对 6 个站各抽 1 页）：
```bash
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
MAP="MAP www.vlsc.net 127.0.0.1:8791, MAP *.googletagmanager.com 127.0.0.1"
for p in portal/index.html mrrc/index.html mrrc_modern/index.html sunmrrc/index.html mrrc_ft8/index.html efhw/index.html; do
  n=$("$CHROME" --headless=new --disable-gpu --no-sandbox \
      --host-resolver-rules="$MAP" \
      --virtual-time-budget=4000 --dump-dom "http://www.vlsc.net/$p" 2>/dev/null \
      | grep -c 'googletagmanager.com/gtag/js?id=G-JQLSKV1MCT')
  echo "$p → gtag 标签数=$n"
done
```
预期：每行 `gtag 标签数=1`（六行共 6）

- [ ] **Step 3：守卫反证 —— 非 vlsc.net host 不得注入**

运行：同 Step 2 但把 `MAP www.vlsc.net …` 换成不映射、直接访问 `http://127.0.0.1:8791/portal/index.html`
预期：`gtag 标签数=0`（hostname 是 `127.0.0.1`）

- [ ] **Step 4：幂等反证 —— 同页加载两脚本时只注入一次**

把两个脚本复制到 `/tmp` 下的独立服务目录（不往仓里加文件），再用第二个端口与第二组 MAP：

运行：
```bash
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
mkdir -p /tmp/ga_idem/js
cp /Users/cheenle/HAM/website/mrrc_modern/js/scope.js \
   /Users/cheenle/HAM/website/mrrc_modern/js/global-nav.js /tmp/ga_idem/js/
cat > /tmp/ga_idem/index.html <<'EOF'
<!DOCTYPE html><html><body>
<script src="js/scope.js"></script>
<script src="js/global-nav.js"></script>
</body></html>
EOF
(cd /tmp/ga_idem && python3 -m http.server 8792 >/tmp/ga_srv2.log 2>&1 &)
sleep 1
"$CHROME" --headless=new --disable-gpu --no-sandbox \
  --host-resolver-rules="MAP www.vlsc.net 127.0.0.1:8792, MAP *.googletagmanager.com 127.0.0.1" \
  --virtual-time-budget=4000 --dump-dom "http://www.vlsc.net/index.html" 2>/dev/null \
  | grep -c 'googletagmanager.com/gtag/js'
```
预期：**`1`** —— 两个脚本都执行了，但第二个被 `!window.dataLayer` 挡住。若看到 `2`，说明幂等守卫失效。

- [ ] **Step 5：覆盖率回归（带尾斜杠）**

运行：
```bash
cd /Users/cheenle/HAM/website && SITES=(portal/ efhw/ mrrc/ mrrc_modern/ sunmrrc/ mrrc_ft8/) && for s in "${SITES[@]}"; do
  echo "$s total=$(find -L $s -name '*.html' | wc -l | tr -d ' ') shared=$(grep -Rl 'scope\.js\|global-nav\.js' $s --include='*.html' | wc -l | tr -d ' ')"
done
```
预期：每站 `total == shared`，合计 122

- [ ] **Step 6：关掉本地服务器** — `pkill -f "http.server 879" || true`

---

### Task 9：提交（5 个仓，只加指定文件）

**文件：** 无新增。仅 `git add` 本次触碰的文件。

- [ ] **Step 1：`HAM/website`**（仓根 `/Users/cheenle/HAM/website`）

```bash
cd /Users/cheenle/HAM/website
git add portal/js/global-nav.js efhw/js/global-nav.js portal/privacy.html portal/zh/privacy.html \
        portal/sitemap.xml portal/tests/test_analytics_coverage.py \
        docs/superpowers/specs/2026-09-13-google-analytics-ga4-design.md \
        docs/superpowers/plans/2026-09-13-google-analytics-ga4.md
git status --porcelain   # 确认只暂存上述 8 个文件，其余 8 个既有改动仍未暂存
git commit -m "feat(analytics): inject GA4 (G-JQLSKV1MCT) site-wide via shared nav script

- portal/efhw global-nav.js: inject gtag.js, guarded to the vlsc.net domain,
  idempotent via the dataLayer presence check
- privacy policy (EN + zh): disclose first-party GA4 cookies -- the previous
  text claimed 'no first-party analytics' and 'no first-party cookies'
- sitemap.xml regenerated (make_sitemap.py)
- portal/tests/test_analytics_coverage.py: pins the 7 script copies, the host
  guard, and the 122-page shared-script coverage"
```

- [ ] **Step 2：`HAM/MRRC`** — `git add website/js/global-nav.js`（先 `git -C /Users/cheenle/HAM/MRRC status --porcelain` 确认路径形态）→ commit `feat(analytics): inject GA4 via js/global-nav.js`
- [ ] **Step 3：`HAM/mrrc_modern`** — `git add website/js/scope.js website/js/global-nav.js` → commit 同上
- [ ] **Step 4：`HAM/sunsdr`** — `git add sunmrrc/website/js/scope.js` → commit 同上
- [ ] **Step 5：`HAM/ft8`** — `git add website/js/scope.js` → commit 同上
- [ ] **Step 6：确认 5 个仓的 diff 都只含 GA 相关改动**

运行：`for r in /Users/cheenle/HAM/website /Users/cheenle/HAM/MRRC /Users/cheenle/HAM/mrrc_modern /Users/cheenle/HAM/sunsdr /Users/cheenle/HAM/ft8; do echo "── $r"; git -C $r show --stat HEAD | tail -5; done`
预期：每个 HEAD 只含本次文件

---

### Task 10：部署（**需用户另行同意**，不在本计划自动执行）

各站 `deploy.sh`：`portal`（含 efhw，因同仓）、`mrrc`、`mrrc_modern`、`sunmrrc`、`mrrc_ft8`（`ft8` 站用 `website/deploy.sh`）。
也可用仓根统一脚本：`cd /Users/cheenle/HAM/website && ./deploy.sh --list` 后按站点名部署。
部署后验证：`curl -s https://www.vlsc.net/portal/js/global-nav.js | grep -c G-JQLSKV1MCT`（`portal` 根路径即 `/js/global-nav.js`）。
