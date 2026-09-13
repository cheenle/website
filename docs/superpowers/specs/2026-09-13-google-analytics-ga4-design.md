# 设计：全站接入 Google Analytics 4（G-JQLSKV1MCT）

日期：2026-09-13
状态：已获用户批准（注入方式 Q1=A 共享脚本注入；范围 Q2=A 6 个在线站点；守卫 Q3=A 域后缀守卫）
范围：`website` 仓（portal + efhw + 隐私政策）、`MRRC` 仓、`mrrc_modern` 仓、`sunsdr` 仓、`ft8` 仓。
**不含**：已归档/已合并的 `mrrc_ft710`、`SunsdrMobile`（nginx 全量 301，页面永不渲染）；
`feedback/`（代理到 127.0.0.1:8021 的 Flask 服务，无自有 HTML 模板）。

---

## 1. 背景与问题

6 个在线站点（122 个 HTML 页）目前**零** GA/gtag 痕迹——2026-09-13 用带尾斜杠的
`grep -Rn "googletagmanager|gtag\(|G-JQLSKV1MCT|google-analytics"` 遍历全部站点目录，
返回空。用户要给全站接入 GA4 属性 `G-JQLSKV1MCT`（官方 gtag.js 片段）。

难点不在片段本身，而在本仓库的三个结构约束：

1. **SDD 页是生成物。** `sunmrrc`/`mrrc_ft8`/`mrrc_modern`/`mrrc_ft710` 各有 `build_sdd.py`，
   `mrrc_modern` 另有 `build_guide.py`。逐页往 HTML 里内联片段，下次 rebuild 会**静默抹掉**
   ——这正是 `portal/tests/test_sitemap.py` 开头记录的同类陷阱（手工编辑生成物，生成器一跑就丢）。
2. **两种共享脚本并存。** 部分站点用 `js/global-nav.js`，部分用 `js/scope.js`，
   且同一份 `global-nav.js` 在不同仓有 5 个互不相同的副本。
3. **`?v=` 缓存参数散落在 122 个页面里。** nginx 对子站 JS 是 `expires 1h`。

## 2. 勘察结论（2026-09-13 实测）

### 2.1 每页至少加载一个共享脚本 —— 100% 覆盖可达

| 站点（仓） | HTML 页数 | `scope.js` | `global-nav.js` | 两者都不加载的页 |
|---|---|---|---|---|
| `portal/`（website, main） | 29 | 0 | 29 | **0** |
| `efhw/`（website, main） | 4 | 0 | 4 | **0** |
| `mrrc/`（MRRC, main） | 25 | 0 | 25 | **0** |
| `mrrc_modern/`（mrrc_modern, main） | 23 | 18 | 5 | **0** |
| `sunmrrc/`（sunsdr, scope-redesign） | 20 | 20 | 0 | **0** |
| `mrrc_ft8/`（ft8, scope-redesign） | 21 | 21 | 0 | **0** |
| **合计** | **122** | 59 | 63 | **0** |

测量注记：`mrrc_ft8` 无尾斜杠 grep 会静默返回 0 命中（BSD grep 不跟随无尾斜杠的符号链接，
CLAUDE.md 已记录该陷阱）；带尾斜杠复测后，其唯一的 "global-nav" 文本命中是
`sdd/14-version-history.html` 里叙述 `global-nav.js` 的散文，**不是** `<script>` 标签，
故该站 `global-nav.js` 引用数实为 0。

### 2.2 副本差异

- **3 份 `scope.js` 逐字节相同**（`shasum` = `99f14c1c7a2ec61c`，mrrc_modern / sunmrrc / mrrc_ft8）
  → 同一段文本插入 3 次即可。
- `global-nav.js` **5 份互不相同**（`md5` 实测五者各异），其中 4 份在本次范围：portal 248 行 /
  efhw 248 行 / mrrc_modern 243 行 / mrrc 333 行（`mrrc` 变体止于 §9 AdSense，无反馈 bootstrap 块；
  portal 与 efhw 的差异在反馈块注释）。第 5 份属归档站 `mrrc_ft710`，不在范围。
  → 插入位置按「IIFE 顶层、末尾 `})();` 之前」统一，不依赖各副本行号。
- `efhw/js/scope.js` 存在但**无任何页面引用**（死副本）——本次不动它。

### 2.3 既有注入模式（本次沿用）

`global-nav.js`（portal 副本 §8/§9）与 `scope.js`（末尾块）已经这样做：

```js
if (location.hostname === 'www.vlsc.net' && !document.querySelector('script[src*="adsbygoogle"]')) { … }
```

AdSense 与反馈系统都是「共享脚本注入 + hostname 守卫 + 防重复检查」。GA 按同一模式实现。

### 2.4 缓存实测

nginx `vlsc.net.conf:69` 的 `expires 1h; Cache-Control "public, max-age=3600"` 只匹配
`^/(mrrc|mrrc_modern|mrrc_ft710|mrrc_ft8|sunmrrc|sunsdrmobile|efhw)/`，**不含 portal 根的
`/js/*.js`**（后者走默认重验证）。故改共享脚本后：子站最坏 1 小时生效，portal 更早。

## 3. 设计

### 3.1 注入代码（7 个文件逐字相同）

标签不带章节号：`scope.js` 本无编号体系，去掉编号才能让 7 份副本逐字节相同（已用 `awk` 抽块 + `shasum`
实测 7 个哈希均为 `4490cfe814e9c3f22c1a35d07e28faf82c5d01ba`）。

```js
  // ── Google Analytics (GA4) ──
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

与官方片段语义等价的两处稳健性改进：

| 官方片段 | 注入版 | 理由 |
|---|---|---|
| `dataLayer` 定义在第二个 `<script>`，与 async 的 gtag.js 存在竞态 | **先**定义 `window.dataLayer` 与 `window.gtag`，**再**挂脚本标签 | gtag.js 运行时读 `window.dataLayer`；注入版无竞态 |
| `function gtag(){dataLayer.push(arguments);}` 函数声明 | `window.gtag = function () { window.dataLayer.push(arguments); };` | 同一个全局函数，等价；变量名 `gaScript` 已确认不与各副本既有的 `adsenseScript`/`ads`/`fbCss`/`fbJs` 冲突 |

守卫正则单测（实现后逐条跑）：`www.vlsc.net` ✅ / `vlsc.net` ✅ / `localhost` ❌ / `''`（`file://`）❌ /
`evil-vlsc.net` ❌（`-` 不是 `.`，无假阳性）/ `vlsc.net.evil.com` ❌（后缀不匹配）。

### 3.2 落点

| 仓（分支） | 文件 | 插入位置 | 覆盖页 |
|---|---|---|---|
| `HAM/website`（main） | `portal/js/global-nav.js` | 末尾 `})();` 前（现止于 §9 反馈） | 29 |
| `HAM/website`（main） | `efhw/js/global-nav.js` | 同上 | 4 |
| `HAM/MRRC`（main） | `mrrc/js/global-nav.js` | 同上（该变体止于 §9 AdSense） | 25 |
| `HAM/mrrc_modern`（main） | `mrrc_modern/js/scope.js` | IIFE 顶层，反馈块之后 | 18 |
| `HAM/mrrc_modern`（main） | `mrrc_modern/js/global-nav.js` | 末尾 `})();` 前 | 5 |
| `HAM/sunsdr`（scope-redesign） | `sunmrrc/js/scope.js` | 同上 | 20 |
| `HAM/ft8`（scope-redesign） | `mrrc_ft8/js/scope.js` | 同上 | 21 |
| | **7 文件 / 5 仓** | | **122** |

既有 `location.hostname === 'www.vlsc.net'` 的 AdSense/反馈块**原样不动**，GA 新块是独立同级
`if`，因此不可能改变现有广告/反馈行为。

### 3.3 不 bump `?v=`

为最坏 1 小时的缓存去改 122 个页面的 `?v=3→4`，与「零 HTML 改动」的初衷相悖。不做。
（若日后需要立即生效：硬刷新即可，或部署后手动改 5 个站点的引用。）

## 4. 连带改动：隐私政策（必须，非可选）

`portal/privacy.html:74-75` 与 `portal/zh/privacy.html:74-75` 目前明文写着：

> **No first-party analytics** — we do not run Google Analytics, Matomo, or any visitor-tracking script of our own.
> **No first-party cookies** — this website itself does not set cookies.

GA4 会在 `vlsc.net` 域下写 `_ga` / `_ga_*` **第一方** Cookie。上线 GA 后这两条即成**假陈述**。
因此本次必须同步：

1. 改写上述两条 bullet（承认存在第一方分析与第一方 Cookie，其余不变）。
2. 在「Third-party advertising — Google AdSense」**之前**新增 `<h2>Analytics — Google Analytics 4</h2>`
   段：测量 ID、加载域名 `googletagmanager.com`、设置的 Cookie、发送的数据、
   **仅用于聚合**、可在浏览器内容拦截器里屏蔽（本站内容不受影响）、
   Google 的 Analytics 退出插件与隐私政策链接。中文镜像同步。
3. 「Last updated」3 处引用中的 2 处（`privacy.html:63,114`；中文 `zh/privacy.html:63,114`）
   改为 2026-09-13。
4. 重新生成 `portal/sitemap.xml`（`python3 make_sitemap.py`，lastmod 取自文件 mtime），
   因为 `portal/tests/test_sitemap.py::test_artifact_matches_generator_output`
   要求提交物等于生成器输出。

**不做同意门（consent gate）。** 本站既有姿态是「AdSense 已设第三方 Cookie 而无同意横幅」，
单独给 GA 加同意门会造成不一致且引入状态管理复杂度（YAGNI）。代价见 §5。

## 5. 已知取舍（用户已知情）

- **6 站共用一个 GA4 属性。** 同域不同路径，报告里用页面路径 `/mrrc/`、`/sunmrrc/`、
  `/mrrc_ft8/`、`/mrrc_modern/`、`/efhw/`、`/` 区分站点即可，无需拆属性或多数据流。
- **会出现两个 hostname 维度。** nginx `server_name www.vlsc.net vlsc.net` 同时服务两者且
  无 www 硬跳转；按 Q3=A 两者都计入。若日后想让 GA 只显示一个 host，需先做 www 规范化跳转。
- **无同意门 → 欧盟访问者会有 Cookie 落下。** GA4 默认不存储 IP（用后即弃），但 `_ga` 仍属
  非必要 Cookie；这是本项目既有的合规姿态延续，若日后要欧盟合规，需另开一条 consent mode 任务。
- **统计口径延迟**：子站脚本 1 小时缓存 → 老访客最多 1 小时后开始被统计。

## 6. 验证（每条都要有实测输出）

1. `node --check` 全部 7 个文件 —— 语法。
2. **守卫正则单测**：§3.1 的 6 个 host 逐条断言。
3. **真·端到端（无头 Chrome）**：`python3 -m http.server` 起本地站 +
   `chrome --headless --host-resolver-rules="MAP www.vlsc.net 127.0.0.1:PORT" --dump-dom`，
   断言 DOM 中出现 `googletagmanager.com/gtag/js?id=G-JQLSKV1MCT`；同一套把 host 换成
   `localhost` 断言**不出现**。6 个站各抽 1 页。
4. **幂等**：同一页同时加载 `scope.js` + `global-nav.js` 时，DOM 里 gtag 标签恰好 1 个。
5. **覆盖率回归**：6 站全部 122 页仍各自引用两脚本之一（带尾斜杠 grep）。
6. `cd portal && python3.11 -m pytest tests/ -q` —— 基线 84 passed（改动前实测），改后不得下降。

## 7. 提交（不在本设计中自动执行）

5 个仓各一个 commit，message 形如 `feat(analytics): inject GA4 (G-JQLSKV1MCT) via shared nav script`，
**只 `git add` 指定文件**：`HAM/website` 现有 8 个、`MRRC` 25 个、`sunsdr` 13 个、`ft8` 4 个
未提交改动，`git add -A` 会把它们卷进来。部署（各站 `deploy.sh`）另行征得用户同意后执行。

## 8. 不做（YAGNI）

- 不做逐页内联（与 §1 的生成物约束冲突）。
- 不做 GA4 事件埋点（点击/下载/外链）——先有 pageview 基线。
- 不做 consent 门、不做 IP 匿名化配置（GA4 默认即不存储 IP）。
- 不碰归档站 `mrrc_ft710/`、`SunsdrMobile/`，不碰 `feedback/`。
- 不清理 `efhw/js/scope.js` 死副本（与本任务无关，避免无关改动混入 diff）。
