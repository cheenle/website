# 设计：归档 mrrc_ft710（并入 MRRC Modern）

日期：2026-09-12
状态：已获用户批准（逐节确认 §1–§4）
范围：`website` 仓（portal + nginx + CLAUDE.md）、`mrrc_ft710` 仓（归档产物）、服务器 `/var/www/vlsc.net/mrrc_ft710/`、GitHub 仓库状态。

---

## 1. 背景与问题

`mrrc_ft710` 与 `mrrc_modern` 共享同一个根提交（`9403e2e`），实际是同一系统的先后两代。
`mrrc_modern` 已成长为严格超集：它驱动 FT-710 **以及** IC-7300 / IC-7300MK2，通过可插拔
`RadioBackend`。继续把 `mrrc_ft710` 作为并列的在售产品呈现，会让读者面对两个几乎相同的
产品页，并让维护面无谓翻倍。

用户决定：**归档 mrrc_ft710，网站 301 到 MRRC Modern，旧安装包下线。**

## 2. 勘察结论（本次实测，2026-09-12）

### 2.1 代码层面：ft710 零独有模块

| 维度 | mrrc_ft710 | mrrc_modern | 结论 |
|---|---|---|---|
| Python 模块名 | 39 个 | **含全部 39 个 + 27 个额外** | ft710 无独有模块 |
| 额外模块（仅 modern） | — | `backend.py` `base.py` `civ_codec.py` `civ_controller.py` `civ_scope.py` `config_ft710.py` `config_ic7300.py` `ft710_power.py` `scope_producer.py` `first_run.py` `firstboot_wrapper.py` 等 | modern 是超集 |
| iOS 客户端 | 40 个 swift | 40 个 swift | 相同 |
| Android 客户端 | 有 | 有 | 相同 |
| SDD | 17 个 md（15 章 + 2 附录） | 17 个 md（同名同结构） | 相同 |
| Windows 安装器 | `packaging/windows/MRRC-FT710.iss` | `MRRC-Modern.iss` | 仅改名 |
| macOS / pyinstaller | `ft710_{launcher,server}.spec` | `mrrc_modern_{launcher,server}.spec` | 仅改名 |
| website 目录结构 | — | **逐文件相同**（只差 `mrrc_ft710.scope.css` → `mrrc_modern.scope.css`） | 相同 |
| website 内容 | index 817 行 / guide 1012 行 | **index 986 行 / guide 1491 行** | modern 是超集 |
| FT-710 的 USB 故事 | FT4222 ×14 | FT4222 ×12、SCU-LAN10 ×5、21 fps、48 kHz | modern 已讲述 |

### 2.2 ft710 独有的 13 个提交：全部是 website/docs，零源码

逐提交核对 `mrrc_ft710` 各分支相对 `mrrc_modern/main` 的独有提交：

| 分支 | 独有提交数 |
|---|---|
| `scope-redesign`（当前 HEAD，`9c353a1`） | **13** |
| `main`（`5028b05`） | 4（是上面 13 个的子集） |
| `fix/ios-ptt-safety` | 0 |
| `tx-stability-wakelock` | 0 |

13 个提交触碰的文件路径经检查**全部落在 `website/` 与 `docs/`**，唯一非 website 文件是
`docs/OPERATION_GUIDE.md`（被 `5028b05` 改，内容是把部署实例地址改成
`radio.vlsc.net:3388`）。**没有任何 `.py` / `.swift` / 产品源码改动。**

这 13 个提交的内容类别：
- ft710 专属网站视觉落地（Scope.css 应用到 SDD 与 docs 页、首页重建）
- 移动端响应式修复（导航换行防重叠、堆叠卡片表格）
- `fde.html → agentic.html` 改名与 FDE → Agentic 术语迁移
- 部署脚本加固（备份瘦身+轮转）—— **modern 已有对应提交**

### 2.3 三个关键事实

1. **`radio.vlsc.net:3388` 已死**（HTTP 000）——没有在线实例需要处理。
2. **服务器目录 139M**，其中 106M 是 3 个安装器；磁盘 67% 使用、4.5G 可用。
3. **安装器本地逐字节存在**：`mrrc_ft710/website/downloads/` 有 3 个 exe
   （`MRRC-FT710-Setup.exe`、`-v1.7.8-Windows-x64-Setup.exe`、`-v1.8.0-Windows-x64-Setup.exe`），
   `.gitignore:43` 忽略 `website/downloads/*.exe` 因而会长期留在本地。
   服务器副本与本地大小/日期一致。**删除服务器目录不丢任何东西。**

### 2.4 现有 nginx 配置

```nginx
59:    location = /mrrc_ft710/fde.html   { return 301 /mrrc_ft710/agentic.html; }
67:    location ~* ^/(mrrc|mrrc_modern|mrrc_ft710|mrrc_ft8|sunmrrc|sunsdrmobile|efhw)/.*\.(css|js|jpg|jpeg|png|gif|svg|ico|woff2?)$ { ... }
102:    # ── MRRC FT-710 website (/mrrc_ft710/) ──
103:    location /mrrc_ft710/ { try_files $uri $uri/ =404; autoindex off; }
```

## 3. 已确认的决策

| # | 决策点 | 结论 |
|---|---|---|
| D1 | 归档范围 | **C：仓库归档 + 网站 301 + 旧安装包下线 + 从导航/产品表彻底移除** |
| D2 | 证据层 | **不改**（血统图、账本表、时间线、事故链、约束计数） |
| D3 | 博客文章 | **保留** `ft710-usb-remote-control`，仅将其 1 处 `/mrrc_ft710/` 链接改指 `/mrrc_modern/` |
| D4 | 服务器目录 | **B：全部删除**（139M）；安装器本地已有副本，可随时重新上传 |
| D5 | 工作区符号链接 | **A：保留** `website/mrrc_ft710 →`；`deploy.sh` 加守卫防误部署 |

## 4. 范围边界

### 4.1 会改（呈现层：不再作为当前可选产品出现）

| 位置 | 现状 | 改为 |
|---|---|---|
| `nginx/vlsc.net.conf:102-106` | `location /mrrc_ft710/ { try_files … }` | `location ^~ /mrrc_ft710/ { return 301 /mrrc_modern/; }` |
| `nginx/vlsc.net.conf:59` | `location = /mrrc_ft710/fde.html` 二次跳转 | 删除（被上面的 301 覆盖） |
| `portal/make_sitemap.py:75` | `SUBSITES` 含 `/mrrc_ft710/` | 移除该项 |
| `portal/js/global-nav.js` | SITE 正则 + `PATHS.mrrc_ft710` + `siteLink('mrrc_ft710','FT-710')` | 三处全删 |
| `portal/index.html` | 产品矩阵 Yaesu FT-710 行 + 独立产品卡 + 页脚列表 | 删除 |
| `portal/zh/index.html` | 同上 | 删除 |
| `portal/{about,contact,privacy}.html` + `zh/` | 各自的产品族条目与卡片 | 删除 FT-710 条目 |
| `portal/blog/index.html` | 页脚站点列表含 FT-710 | 删除 |
| `portal/blog/ft710-usb-remote-control/index.html` | 正文 1 处 `href="/mrrc_ft710/"` | → `/mrrc_modern/` |
| `portal/deploy.sh:5` | 注释里的子站列表 | 去掉 `mrrc_ft710/` |
| `CLAUDE.md:14, 182-190` | 当作活跃子站描述 | 标注「已归档 2026-09-12，并入 MRRC Modern」 |
| GitHub `cheenle/mrrc_ft710` | 活跃 | **Archive（只读）** |
| `mrrc_ft710/website/deploy.sh` | 可部署 | 加禁用守卫后 `exit 1` |

### 4.2 不改（证据层：历史事实，改了即篡改）

| 位置 | 为什么 |
|---|---|
| `portal/agentic.html` + `zh/`（22 处 FT-710 引用） | 血统图与「MRRC FT-710 proves a direct USB vertical slice; MRRC Modern generalizes **it**」——FT-710 是主语的宾语，删掉即抹掉论证起点 |
| `portal/engineering.html` + `zh/` | 产品族证据表：`FT-710 vertical validation → Modern platform`、`FT-710: 439 tests`（仍是有效声明） |
| 博客系列账本表 `mrrc_ft710 162 commits / v1.8.0` | 2026-09-12 普查事实 |
| 博客系列时间线 `ft710 起步即重写 SDD（87297d1）` | 方法长成的关键节点 |
| 博客系列事故链 `cat-no-dn / AD-014 / DN; / 2498ec2` | 方法有效性最硬的证据 |
| 约束注册表 `ft710 17 / modern 21 / ft8 14 = 52` | 三仓门禁之一，删除会破坏整条论证 |
| `portal/blog/ft710-usb-remote-control/` 文章本体 | 技术史，Modern 的起源故事 |
| `website/mrrc_ft710` 符号链接 | D5：保留为历史入口与跨站 grep 目标 |
| `mrrc_ft710` 仓库本体与全部分支 | 归档 ≠ 删除 |

**判断依据**：一个引用是「呈现为当前可选产品」还是「作为证据出现」——前者删，后者留。
`agentic.html` 里 FT-710 出现在 `MRRC FT-710 inspired-by → MRRC Modern` 这类血统句中，
不是货架条目。

## 5. 执行顺序（每步可独立回滚）

| # | 步骤 | 回滚方式 |
|---|---|---|
| 1 | `nginx/vlsc.net.conf` 加 `^~` 301、删二次跳转；`nginx -t`；reload → **受 R7 约束，需先解决并发编辑** | 删掉那几行并 reload |
| 2 | `make_sitemap.py` 去 `/mrrc_ft710/`；重生成 `sitemap.xml` | `git revert` |
| 3 | portal 呈现层去 FT-710（10 个文件 × 2 语言） | `git revert` |
| 4 | 博客文章链接改指 `/mrrc_modern/` | `git revert` |
| 5 | `CLAUDE.md` 标注归档 | `git revert` |
| 6 | `mrrc_ft710` 仓加 `ARCHIVED.md`、`README.md` 顶部提示、`deploy.sh` 守卫；push | 删文件 / `git revert` |
| 7 | GitHub 归档：`gh repo archive cheenle/mrrc_ft710` | `gh repo unarchive` |
| 8 | 删服务器目录 `/var/www/vlsc.net/mrrc_ft710/`（139M）。**不建服务器快照**：安装器本地逐字节存在（§2.3），HTML 在已归档仓库里，恢复路径完整 | 从本地重新上传 `website/downloads/` + `website/` |
| 9 | 部署 portal（`portal/deploy.sh`） | 部署回滚 |

**顺序理由**：仓库归档放在第 7 步，晚于所有 portal 改动 —— 前面任一步出错时仓库仍可写，
可以立刻补修 `ARCHIVED.md` 或守卫再归档。服务器目录删除放在第 8 步、部署之后，因为
301 生效后该目录已不可达，删除不影响访问。

### 5.1 nginx 用 `^~` 而不是普通前缀（必须）

`vlsc.net.conf:67` 存在静态资源正则 location：
`location ~* ^/(mrrc|mrrc_modern|mrrc_ft710|…)/.*\.(css|js|jpg|…)$`。
nginx 的匹配顺序是「最长前缀匹配 → 若有匹配的正则则正则胜出」，因此普通写法下
`/mrrc_ft710/css/x.css` 会被那个正则截走而**不会 301**。`^~` 跳过正则匹配。

这与用户 2026-09-12 在 `/stats/` 上修的是同一类缺陷（见 `nginx/vlsc.net.conf` 内注释）。

## 6. 归档产物

### 6.1 `mrrc_ft710/ARCHIVED.md`

```markdown
# Archived — 2026-09-12

This project has been merged into **MRRC Modern**, which is a strict superset:
it drives the FT-710 *and* the IC-7300 / IC-7300MK2 through a pluggable backend.

- Successor: https://github.com/cheenle/mrrc_modern
- Live site: https://www.vlsc.net/mrrc_modern/
  (https://www.vlsc.net/mrrc_ft710/ 301-redirects here)

Everything in this repository remains valid as a historical record. In particular
`.agents/skills/sdd-guardian/` holds 17 machine-readable constraints and is one of
the three gated repositories cited by the VLSC evidence ledger; it is frozen, not
withdrawn.
```

### 6.2 `mrrc_ft710/README.md`

顶部插入一段同义提示（GitHub 首屏可见），原内容不动。

### 6.3 `mrrc_ft710/website/deploy.sh`

在 `set -euo pipefail` 之后插入：

```bash
echo "This project is archived (2026-09-12) and merged into MRRC Modern."
echo "  Successor: https://github.com/cheenle/mrrc_modern"
echo "  Live site: https://www.vlsc.net/mrrc_modern/"
echo ""
echo "Deployment is disabled. To ship an emergency hotfix, comment out this guard."
exit 1
```

## 7. 验证

| 检查 | 命令 / 方式 | 期望 |
|---|---|---|
| nginx 语法 | `sudo nginx -t` | ok |
| 301 生效（含静态资源路径） | `curl -sI https://www.vlsc.net/mrrc_ft710/` | `301` + `Location: /mrrc_modern/` |
| 静态资源不被截走 | `curl -sI https://www.vlsc.net/mrrc_ft710/css/octen.css` | `301`（不是 200） |
| 子路径同样跳转 | `curl -sI .../mrrc_ft710/sdd/01-executive-summary.html` | `301` |
| 后继站仍正常 | `curl -sI https://www.vlsc.net/mrrc_modern/` | `200` |
| sitemap 不含旧站 | `grep -c mrrc_ft710 portal/sitemap.xml` | `0` |
| portal 呈现层无旧站链接 | 跨站 grep（数组写法，见 CLAUDE.md） | 0 命中 |
| 证据层未被误删 | `grep -c "FT-710" portal/agentic.html` | 仍为 22 左右 |
| portal 测试全绿 | `/usr/bin/python3 -m pytest tests/ -q` | 全过 |
| 服务器目录已删 | `ssh … "ls /var/www/vlsc.net/mrrc_ft710"` | 不存在 |
| 仓库已归档 | `gh repo view cheenle/mrrc_ft710 --json isArchived` | `true` |

## 8. 红线

- **R1** 不得修改任何历史事实：财本表、时间线、事故链、约束计数、`agentic.html` 的血统叙述。
- **R2** 不得删除 `mrrc_ft710` 仓库或其任何分支（归档 ≠ 删除）。
- **R3** 不得删除本地 `mrrc_ft710/website/downloads/` 的安装器。
- **R4** 不得改动任何子站仓库（`mrrc/`、`mrrc_modern/`、`sunmrrc/`、`SunsdrMobile/`、`mrrc_ft8/`、`efhw/`）。
- **R5** 服务器上的删除只允许针对 `/var/www/vlsc.net/mrrc_ft710/` 这一个目录。**绝不允许 `rm -rf` DocumentRoot 或任何其他子站目录。** 删除前必须先列出目标清单并逐条确认全部以 `/var/www/vlsc.net/mrrc_ft710/` 开头。
- **R7** **nginx 部署前置条件（已满足）**：用户 2026-09-12 的 `/stats/` `^~` 修复已获准一起上线。实现期必须把它**原样**先提交为独立 commit（内容一字不改），再在其上加 FT-710 的 301；两次改动共享一次部署。**禁止修改用户那部分内容。**
- **R6** portal 的既有未提交改动（用户并行的 `nginx/vlsc.net.conf` 修改）不得被本次提交卷入或覆盖；**本次对 nginx 的修改必须与用户已保存的 `/stats/` 改动共存**。

## 9. 明确不做

- 不删除 `mrrc_ft710` 的本地仓库或 GitHub 仓库
- 不改 `agentic.html` / `engineering.html` 的 FT-710 叙述
- 不改博客系列的任何历史数字
- 不迁移 ft710 网站的 13 个独有提交的内容到 modern（modern 网站已是超集）
- 不处理 `radio.vlsc.net:3388`（已下线，无在线实例）

## 10. 风险

| 风险 | 处置 |
|---|---|
| 用户并行修改的 `nginx/vlsc.net.conf` 与本次改动冲突 | 提交前 `git diff` 逐行确认；只加不删用户那部分 |
| 301 断开历史外部外链 | 301 本身即保留链接权重；`demo`/`downloads` 直达链接会跳到 Modern 首页，可接受 |
| 备份目录 `/var/www/backups/` 无轮转 | 本次只多一份 139M 快照；删目录后主磁盘反而释放 139M |
| 归档后仍需热修 | `deploy.sh` 守卫注释即恢复；`gh repo unarchive` 可逆 |

## 11. 未决项

| 项 | 状态 |
|---|---|
| 服务器快照文件名 | **已定：不建快照**（见 §5 步骤 8） |
| `CLAUDE.md` 归档章节的措辞 | 已定：与 §6.1 口径一致，措辞为「已归档 2026-09-12，并入 MRRC Modern；仓库只读，网站 301 到 `/mrrc_modern/`」 |
| 博客文章是否加归档提示 | 用户已定：不加（D3 仅改链接） |
| **nginx 并发编辑（R7）** | **已解决（用户选 B）**：用户未提交的 `/stats/` 修复与本次 FT-710 301 **一起上线**。实现期分两个 commit（先用户修复、后 FT-710 301）以便各自回滚，但只做一次部署。 |
