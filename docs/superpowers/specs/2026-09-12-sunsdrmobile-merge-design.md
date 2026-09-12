# 设计：把 SunsdrMobile 并入 SunMRRC（仓库 + 网站 + 呈现）

日期：2026-09-12
状态：已获用户批准（§1 逐层确认；Q2 = A 带历史导入）
范围：`sunsdr` 仓、`SunsdrMobile` 仓、`website` 仓（portal + nginx + CLAUDE.md）、
服务器 `/var/www/vlsc.net/sunsdrmobile/`、GitHub 仓库状态。

---

## 1. 背景与问题

`SunsdrMobile` 不是独立产品，而是 **SunMRRC 服务的原生 iOS 客户端**：

| 证据 | 位置 |
|---|---|
| *"Manages the 4 WebSocket connections to **sunmrrc**"* | `SunsdrMobile/Sources/Networking/ConnectionManager.swift:3` |
| 默认服务器 `radio.vlsc.net:8889`（SunMRRC 端口） | `ConnectionManager.swift:7,21` |
| *"a complete mobile replacement for the web frontend"* | `SunsdrMobile/README.md` |
| *"SunMRRC is the station system; Web and SunsdrMobile are [clients]"* | `portal/agentic.html:797` |

**论点页早已用正确框架描述它们**，只有 portal 的产品矩阵/产品卡/导航把 iOS 客户端当成
并列的独立产品。加上 git 层面存在一个未配置完成的嵌套引用，现状是三层不一致。

本生态的既有模式是**客户端与服务器同仓**：`mrrc_modern` 仓内就有 `FT710Mobile/` 与
`FT710Android/`。`SunsdrMobile` 分居是异常。

用户决定：**按 ft710 归档的同一口径处理——合并了就作为同一产品呈现。**

## 2. 勘察结论（2026-09-12 实测）

### 2.1 两个 git 仓库

| | `sunsdr`（SunMRRC） | `SunsdrMobile` |
|---|---|---|
| 路径 | `/Users/cheenle/HAM/sunsdr` | `/Users/cheenle/HAM/sunsdr/SunsdrMobile`（嵌套） |
| 远端 | `git@github.com:cheenle/sunsdr.git` | `https://github.com/cheenle/SunsdrMobile.git` |
| 提交数 | 67 | 9（2026-07-01 → 2026-09-03） |
| 分支 | `scope-redesign`（HEAD） | `main`、`scope-redesign`（HEAD） |
| 跟踪文件 | — | 44（23 个 Swift + 工程文件 + 网站 + 文档） |

### 2.2 git 层面的现状：一个坏引用

```
$ git -C sunsdr ls-files -s SunsdrMobile
160000 f93955ed6a355f7832aca36b27b4f8d20d266c99 0  SunsdrMobile
```

- **mode 160000 = gitlink**（嵌套仓库引用）
- **没有 `.gitmodules`** —— 不是 submodule，是一个未配置完成的悬挂引用
- gitlink 指向 `f93955e`（2026-07-04），而 SunsdrMobile 的 HEAD 是 `c2d51c0`（2026-09-03）——
  **相差 6 个提交**
- 后果：`git status` 在 sunsdr 里**永久显示 ` M SunsdrMobile`**，且克隆者拿不到 app 的代码

### 2.3 移动整棵树是安全的

`SunsdrMobile.xcodeproj` 与 `project.yml`（XcodeGen）全部使用**工程内相对路径**
（`Sources/`、`Resources/`、组路径 `App`/`Audio`/…）。整棵目录树作为单元移动不会破坏构建。
bundle id `com.hamradio.sunsdrmobile`、scheme `SunsdrMobile`、`DEVELOPMENT_TEAM VQ89MM7935`
均不依赖目录位置。

### 2.4 app 尚未上架

`SunsdrMobile/website/index.html:693`：

> *"App Store Release and Real-Device Audio — App Store submission and every audio-path
> judgement on a real handset stay with a human. Simulator output is never presented as
> on-air evidence."*

即**应用未提交上架**。把它作为独立「已发布产品」列在 portal 上是超前的。

### 2.5 `portal/css/sunsdrmobile.css` 是 portal 自己的资产

该文件名源自 SunsdrMobile 设计系统，但实际是 **portal 的共享样式表**：提供 `.logo`、
`.gradient`、`.btn-primary`/`-outline`/`-secondary`、`.section-label`、`.vlsc-scroll-progress`、
`.qr-section`、`.qr-card`，被 **12 个 portal 页面**引用（EN + ZH）。
**不得删除或改名**——与产品移除无关。

### 2.6 服务器与 nginx 现状

- `/var/www/vlsc.net/sunsdrmobile` = **424K**（只有 `css/ images/ js/ index.html zh/ deploy.sh`，
  **无 downloads/ 无 videos/**）
- nginx `:128` 是普通前缀 `location /sunsdrmobile/ { … }`；`:69` 是静态资源正则

## 3. 已确认的决策

| # | 决策点 | 结论 |
|---|---|---|
| D1 | 合并层级 | **C：仓库 + 网站 + 呈现全部合并** |
| D2 | 历史处理 | **A：`git subtree` 带历史导入**（9 个提交进入 sunsdr 仓） |
| D3 | 目录名 | **保持 `SunsdrMobile/`**（bundle id / scheme / 未来 App Store 身份都叫这个） |
| D4 | 网站形态 | iOS 内容并入 `sunmrrc/website/ios/`（+`zh/ios/`），`/sunsdrmobile/` 301 到 `/sunmrrc/ios/` |
| D5 | portal 呈现 | 2 行产品矩阵 → 1 行；2 张产品卡 → 1 张；导航/页脚/子页/sitemap 移除 |
| D6 | 证据层 | **一字不改**（`agentic.html` 的框架本来就是对的） |
| D7 | `portal/css/sunsdrmobile.css` | **保留**（portal 共享样式，12 页依赖） |

## 4. 范围边界

### 4.1 仓库合并

| 位置 | 现状 | 改为 |
|---|---|---|
| `sunsdr/SunsdrMobile` | gitlink（mode 160000 → `f93955e`） | **真实目录**，历史经 subtree 导入 |
| `sunsdr/SunsdrMobile/**` | 嵌套仓，不被 sunsdr 跟踪 | 44 个文件纳入 sunsdr 跟踪 |
| `SunsdrMobile/.git/` | 嵌套仓 | 移出树外（`/tmp/SunsdrMobile.git-archive/`），不删除 |
| `SunsdrMobile` 仓 | 独立仓库 | GitHub **归档只读** + `ARCHIVED.md` + deploy 守卫 |
| sunsdr 导入分支 | — | `scope-redesign`（HEAD，含全部 9 提交） |

### 4.2 网站合并

| 位置 | 改为 |
|---|---|
| `SunsdrMobile/website/index.html` + `zh/index.html` | → `sunmrrc/website/ios/index.html` + `zh/ios/index.html` |
| `SunsdrMobile/website/css/scope.css`、`js/scope.js` | **无需迁移** —— 与 sunmrrc 的同名文件逐字节相同（§11）；iOS 页改用 sunmrrc 的 `css/scope.css?v=2` 与 `js/scope.js?v=2` |
| `sunmrrc/website/index.html` + `zh/` | 增加 iOS 一节 + 导航项 |
| nginx `:128` | `location ^~ /sunsdrmobile/ { return 301 /sunmrrc/ios/; }` |
| 服务器目录 | 删 `/var/www/vlsc.net/sunsdrmobile/`（424K；本地与仓库均有副本） |
| `SunsdrMobile/website/deploy.sh` | 加禁用守卫 |

### 4.3 portal 呈现

| 位置 | 现状 | 改为 |
|---|---|---|
| `index.html` 产品矩阵 | 2 行（SunMRRC / SunsdrMobile） | **1 行**：`SunSDR2 DX` → SunMRRC →「服务端 + Web 前端 + 原生 iOS 客户端」 |
| `index.html` 产品卡 | 2 张 | **1 张**，SunMRRC 卡增加 iOS 条目 |
| `js/global-nav.js` | `siteLink('sunsdrmobile','SunsdrMobile')` + `PATHS` + SITE 正则 | 三处删除 |
| `about/contact/privacy` + `zh/` | 各自的条目 | 删除 |
| `blog/index.html` 页脚 | SunsdrMobile 条目 | 删除 |
| `make_sitemap.py` `SUBSITES` | 含 `/sunsdrmobile/` | 移除 |
| `portal/css/sunsdrmobile.css` | — | **保留**（D7） |
| portal meta description / keywords | 列出 SunsdrMobile | 从产品清单移除（keywords 保留枚举亦无害，实现期一并清） |

### 4.4 证据层（一字不改）

| 位置 | 处数 | 为什么 |
|---|---|---|
| `portal/agentic.html` | 10 | 已写 *"SunMRRC is the station system; Web and SunsdrMobile are clients"* —— 框架正确 |
| `portal/zh/agentic.html` | 10 | 同上 |
| `portal/engineering.html` + `zh/` | 各 2 | 产品族证据表 |
| 博客系列 | 3 | 账本表 `sunsdr 67+9` 等普查事实 |

**判断依据与 ft710 归档一致**：是「货架条目」还是「血统/证据」。前者的框架是错的
（把客户端当独立产品），后者已经是对的。

## 5. 执行顺序（每步可独立回滚）

| # | 步骤 | 回滚 |
|---|---|---|
| 1 | 备份 SunsdrMobile 嵌套 `.git` 到 `/tmp/`，并 `git bundle` 一份完整历史 | 无破坏 |
| 2 | sunsdr：`git rm --cached SunsdrMobile` 移除 gitlink；移走嵌套 `.git` | `git reset` |
| 3 | sunsdr：`git subtree add --prefix=SunsdrMobile <local-path> scope-redesign` | `git reset --hard HEAD~1` |
| 4 | 核验：`git show --stat HEAD` 只含 `SunsdrMobile/**`；用户 14 项未提交改动仍在 | — |
| 5 | 网站合并：iOS 页 → `sunmrrc/website/ios/`；首页加节 | `git revert` |
| 6 | SunsdrMobile 仓：`ARCHIVED.md` + README 横幅 + deploy 守卫；push | 删文件 |
| 7 | GitHub 归档 `cheenle/SunsdrMobile` | `gh repo unarchive` |
| 8 | nginx：`^~` 301；`nginx -t`；reload | 删那几行并 reload |
| 9 | portal 呈现层移除（10 文件 × 2 语言）；`make_sitemap.py` 去项；重生成 | `git revert` |
| 10 | CLAUDE.md 标注归档 | `git revert` |
| 11 | 部署 sunmrrc 站 + portal | 各自 deploy 回滚 |
| 12 | 删除服务器 `/var/www/vlsc.net/sunsdrmobile/` | 从本地重新上传 |

**顺序理由**：仓库历史导入（1–4）先做且立即核验，因为它触及用户未提交的工作区；
GitHub 归档（7）晚于所有内容改动；服务器删除（12）最后，因为 301 生效后该目录已不可达。

## 6. 归档产物

### 6.1 `SunsdrMobile/ARCHIVED.md`

```markdown
# Archived — 2026-09-12

This project has been merged into **SunMRRC** as its native iOS client. The app was never a
standalone product: it opens four WebSocket connections to the SunMRRC server
(`radio.vlsc.net:8889`) and is, in its own README's words, "a complete mobile replacement for
the web frontend".

- Successor repo: https://github.com/cheenle/sunsdr  (the app now lives at `SunsdrMobile/`)
- Successor site: https://www.vlsc.net/sunmrrc/ios/
  (https://www.vlsc.net/sunsdrmobile/ 301-redirects here)

The full 9-commit history of this repository was imported into `cheenle/sunsdr` with
`git subtree`, so nothing is lost by archiving here.

Status note: the app has **not** been submitted to the App Store.
```

### 6.2 `SunsdrMobile/README.md`

顶部插入归档横幅，原内容不动。

### 6.3 `SunsdrMobile/website/deploy.sh`

在 `set -e`（或 `set -euo pipefail`）之后插入守卫块并 `exit 1`，文案指向 `/sunmrrc/ios/`。

## 7. 验证

| 检查 | 命令 | 期望 |
|---|---|---|
| gitlink 已消失 | `git -C sunsdr ls-files -s SunsdrMobile` | 不再是 mode 160000 |
| 历史已导入 | `git -C sunsdr log --oneline -- SunsdrMobile \| wc -l` | ≥ 10（9 + merge） |
| app 代码在 sunsdr 内 | `git -C sunsdr ls-files SunsdrMobile/ \| wc -l` | ≥ 40 |
| 用户未提交改动未被动 | `git -C sunsdr status --short \| wc -l` | 仍为 14（或含本次改动） |
| ` M SunsdrMobile` 消失 | `git -C sunsdr status --short SunsdrMobile` | 空 |
| 301 生效（含静态资源） | `curl -sI .../sunsdrmobile/css/scope.css` | `301` → `/sunmrrc/ios/` |
| 后继页可用 | `curl -sS -o /dev/null -w '%{http_code}' .../sunmrrc/ios/` | `200` |
| `/sunmrrc/` 仍正常 | 同上 | `200` |
| sitemap 不含旧站 | `grep -c sunsdrmobile portal/sitemap.xml` | `0` |
| 呈现层清空 | 跨站 grep（数组写法） | 0 命中 |
| 证据层未动 | `grep -c -i sunsdrmobile portal/agentic.html` | 仍为 10 |
| portal 共享样式未删 | `ls portal/css/sunsdrmobile.css` | 存在 |
| portal 测试全绿 | `/usr/bin/python3 -m pytest tests/ -q` | 全过 |
| 仓库已归档 | `gh repo view cheenle/SunsdrMobile --json isArchived` | `true` |
| 服务器目录已删 | `ls /var/www/vlsc.net/sunsdrmobile` | 不存在 |

## 8. 红线

- **R1** 不得修改证据层：`agentic.html`/`zh/`、`engineering.html`/`zh/`、博客系列里的
  SunsdrMobile 引用。
- **R2** 不得删除 `portal/css/sunsdrmobile.css`（12 个 portal 页面的共享样式）。
- **R3** 不得删除 SunsdrMobile 的本地仓库或其 `.git`（只移出树外 + 归档 GitHub 仓）。
- **R4** **不得扰动 sunsdr 仓的 14 项未提交改动**（`sunmrrc/server.py`、`static/controls.js`、
  `static/index.html`、`static/mobile.js`、`web_control/dsp.py`、`web_control/wdsp_wrapper.py`、
  二维码图片等）。每个 commit 前必须 `git show --stat` 或 `git diff --cached --stat` 确认范围。
- **R5** 不得改动任何其他子站仓库（`mrrc/`、`mrrc_modern/`、`mrrc_ft710/`、`mrrc_ft8/`、`efhw/`）。
- **R6** 服务器删除只允许 `/var/www/vlsc.net/sunsdrmobile/` 这一个目录。
- **R7** 目录名保持 `SunsdrMobile/`，不重命名（bundle id / scheme / App Store 身份一致性）。
- **R8** nginx 必须用 `^~`，否则静态资源会被 `:69` 的正则截走（与 `/stats/`、`/mrrc_ft710/` 同源缺陷）。

## 9. 明确不做

- 不把 app 改名为 "SunMRRC iOS"（bundle id / App Store 身份不变）
- 不改 `sunmrrc/server.py` 或任何服务器代码
- 不改 app 的协议、默认主机或 UI
- 不迁移 `web_control/`、`device/` 或任何服务器侧目录
- 不处理 App Store 上架（未提交上架，本次不涉）

## 10. 风险

| 风险 | 处置 |
|---|---|
| `git subtree add` 在 14 项未提交改动下产生范围外的 commit | 步骤 4 强制核验 `git show --stat HEAD` 只含 `SunsdrMobile/**`；不符则 `git reset --hard HEAD~1` 重做 |
| subtree 导入 `scope-redesign` 而 gitlink 指 `f93955e` | 这是期望：导入让 sunsdr 追上 app 的最新（+6 提交） |
| 移动 `SunsdrMobile/.git` 导致 app 仓不可用 | 先 `git bundle create` 完整备份；远端 GitHub 仓仍在（归档后仍可 clone） |
| iOS 页并入后样式冲突 | **已排查**：两个站的 `scope.css`/`scope.js` 逐字节相同（§11），不存在冲突面 |
| portal 移除条目后 Track B 只剩一项 | 符合决策 C：SunMRRC 就是 Track B 的唯一产品 |

## 11. 未决项

| 项 | 状态 |
|---|---|
| iOS 页的 CSS/JS | **已定：直接复用 sunmrrc 现有副本**。实测 `sunmrrc/website/css/scope.css` 与 `SunsdrMobile/website/css/scope.css` **逐字节相同**（8299 B），`js/scope.js` 亦相同（5453 B）。两个站的 HTML 都引用 `css/scope.css?v=2` —— 所以只需搬运 HTML，样式与脚本零迁移。 |
| iOS 页的二维码图片 | 已定：两个站都用 `images/qr-wechat-group.jpg`（微信群二维码，周级过期）。合并后 iOS 页改指 sunmrrc 的 `images/`，**不新建图片**；该文件按 CLAUDE.md 约定不跟踪（disk-only）。 |
| `sunmrrc/website/index.html` 新增节的具体文案 | 实现期撰写，口径与 portal 产品卡一致（「服务端 + Web 前端 + 原生 iOS 客户端」）。 |
| 服务器快照 | **不建**（424K，本地与仓库均有完整副本）。 |
