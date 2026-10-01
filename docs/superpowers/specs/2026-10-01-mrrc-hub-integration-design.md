# MRRC Cloud Hub 接入全站导航与门户 — 设计规格

| 项 | 值 |
| --- | --- |
| 日期 | 2026-10-01 |
| 状态 | 已批准（对话式批准）→ 实施中 |
| 权威边界 | hub 的接入层事实归 `hub/mrrc_hub/SDD/`；门户只写"它是什么、怎么进"，不复制其架构细节 |

## 1. 目标

把新子站 **MRRC Cloud Hub**（`https://www.vlsc.net/mrrc_hub/`）接入 VLSC 站点生态：

1. 六份共享导航脚本都出现 Hub 入口，用户在任何一页都能走到它；
2. hub 本站的 5 个页面拿到同一条全站顶栏（与其它六个站一致），不再"点进去就掉出导航"；
3. 门户站（portal）在选择表、项目卡、生态段、各页 footer 与 sitemap 里把它讲清楚 —— 定位是**接入层**，不是第五种电台接入方式。

## 2. 非目标

- **不改** hub 仓的 `SDD/` 设计章节（本次不动架构，只在版本历史留一条记录）。
- **不改** hub 站的 `css/octen.css`（逐字节上游拷贝，`deploy.sh` 有哈希闸门）。
- **不给** hub 在 `portal/agentic.html` / `portal/engineering.html` 的证据表里记能力或版本 —— 那是产品成熟度账本，hub 处于"架构评审完成、MVP 未实现"，进去只会稀释它。
- **不修** `hub/deploy/*.sh` 与现网的既有漂移（该仓 SDD §6.2 已记录，属独立变更）。
- 不写版本号/测试数到 hub 卡片（可比数字的唯一 owner 是 `/agentic.html#evidence`）。

## 3. 现状事实（2026-10-01 核实）

| 事实 | 值 |
| --- | --- |
| hub 仓 | `/Users/cheenle/HAM/hub/mrrc_hub/`，分支 `feat/hub`，有自己的 SDD guardian |
| hub 站 | 5 页（index/start/use/trouble/design）+ `css/{octen,hub}.css` + `js/hub.js`，中文单语，已 200 上线 |
| live nginx | 已有 `location ^~ /mrrc_hub/`；仓库参考副本 `nginx/vlsc.net.conf` **落后 live 96 行** |
| 工作区软链 | 存在错名软链 `website -> ../hub/mrrc_hub/website`（应为 `mrrc_hub ->`） |
| 共享导航 | 两套实现：`global-nav.js`（portal/mrrc/mrrc_modern/efhw，含 RIG、feedback、AdSense）与 `scope.js`（sunmrrc/mrrc_ft8，类名 `scope-gn`，无 RIG） |
| hub 站 octen.css | 已含全部 `.vlsc-gn` 规则（25 处），顶栏样式随上游走，无需新增 CSS |
| portal 过期文案 | 项目段副标题 `Seven open-source remote control projects`，实际卡片 5 张；`about.html` 项目一览只有 3 张 |

## 4. 改动清单

### 4.1 共享导航（6 份副本，最小改动）

每份只加三处：`PATHS.mrrc_hub = '/mrrc_hub/'`、SITE 检测分支 `/\/mrrc_hub\//`、`siteLink('mrrc_hub', 'Hub')`（置于 `Modern` 之后）。

- `portal/js/global-nav.js`（canonical）、`mrrc/js/global-nav.js`、`mrrc_modern/js/global-nav.js`、`efhw/js/global-nav.js`
- `sunmrrc/js/scope.js`、`mrrc_ft8/js/scope.js`
- 新增 `hub/mrrc_hub/website/js/global-nav.js` = portal 版的逐字节拷贝（含 hub 自身入口），来源记入 hub 站 README

不对既有副本做整份 resync：它们各自带有本站相关的既有差异（SVG 图样式、移动端滚动规则），整份覆盖会把无关改动混进本次提交。

### 4.2 hub 本站 5 页

- `<body>` → `<body data-site="mrrc_hub">`
- 每页 `</body>` 前加 `<script src="js/global-nav.js?v=1" defer></script>`
- 随之获得顶栏、GA4、AdSense、反馈组件（与其它站一致）
- `deploy.sh` 的 `REQUIRED_FILES` 加 `js/global-nav.js`
- `website/README.md` 文件职责表加一行 + 复拷约定（源是 `portal/js/global-nav.js`）
- `SDD/14-version-history.md` 追加一条

### 4.3 portal 内容（EN/ZH 成对）

| 文件 | 改动 |
| --- | --- |
| `index.html`、`zh/index.html` | 副标题数字按实际改；项目卡加 Hub；选择表加「内网 / 无公网 IP」一行；生态段新增 `Cloud Access / 云端接入` 卡；footer 项目列与仓库链接 |
| `about.html`、`zh/about.html` | 项目一览补 Hub、EFHW、MRRC-FT8（现有 3 张 → 6 张） |
| `contact.html`、`zh/contact.html` | issue 跟踪器加 `mrrc_hub/issues` 一行；footer 项目列 |
| `privacy.html`、`zh/privacy.html` | footer 项目列 |
| `make_sitemap.py` | `SUBSITES` 加 `'/mrrc_hub/'`，重生成 `sitemap.xml` |
| `tests/test_analytics_coverage.py` | `SCRIPTS` 加 `mrrc_hub/js/global-nav.js`；`SITES` 加 `mrrc_hub`；`MIN_PAGES` 120 → 125（122+5=127） |
| `tests/test_sitemap.py` | 金丝雀 24 → 29 |

### 4.4 环境与配置

- 软链改名：`/Users/cheenle/HAM/website/website` → `mrrc_hub`
- `nginx/vlsc.net.conf`：整份与 live 同步（含 `^~ /mrrc_hub/`、`= /mrrc_hub` 与 `mrrc_modern/BG1SB` 边缘段），使其重新成为可信参考副本
- `CLAUDE.md`：站点清单、软链列表、跨站 grep 的 `SITES` 数组加入 `mrrc_hub/`

## 5. 验收判据

| # | 判据 | 怎么验 |
| --- | --- | --- |
| AC-1 | 六份共享脚本都含 `mrrc_hub` 入口，且 GA 块未被破坏 | `grep -c mrrc_hub` 六份 = 3；`pytest portal/tests/test_analytics_coverage.py` 全绿 |
| AC-2 | hub 5 页都加载 `global-nav.js` 且 `data-site="mrrc_hub"` | `grep` 逐页；本地 `http.server` 目视顶栏高亮 Hub |
| AC-3 | portal 的 EN/ZH 页 Hub 入口一致（选择表、项目卡、生态卡、footer） | 逐页 grep `/mrrc_hub/` 计数对齐 |
| AC-4 | sitemap 收录 `/mrrc_hub/` 与 5 个页面 | `python3 make_sitemap.py` + `pytest portal/tests/test_sitemap.py` |
| AC-5 | hub 仓闸门 clean | `sdd_context.py check --staged` = clean；`deploy.sh` 的 grep + octen.css 哈希闸门通过 |
| AC-6 | 线上可达 | `curl` 逐页 200：portal 各页、hub 5 页 |
| AC-7 | 触屏宽度无横向溢出、顶栏不出错位 | 320 / 768 / 960 断点目视 |

## 6. 风险

| 风险 | 缓解 |
| --- | --- |
| hub 仓有在途改动（9 个 M 文件、HEAD 在会话中被推进） | 只 `git add` 本次触碰的文件；不 `git add -A` |
| 给 hub 站注入 GA/AdSense 是行为变化 | 已在设计里明示；与其它六个站一致 |
| 门户文案把预 MVP 项目写成已交付 | 卡片只写能力与"设计评审完成 · MVP 未实现" |
| nginx 参考副本整份同步带入无关 diff | 内容逐段对照 live；该文件不被任何脚本自动部署，风险限于人工 scp |
