# 归档 mrrc_ft710 实现计划

> **面向 AI 代理的工作者：** 必需子技能：superpowers:executing-plans。
> 步骤用复选框（`- [ ]`）跟踪。规格：`docs/superpowers/specs/2026-09-12-mrrc-ft710-archive-design.md`

**目标：** 把 `mrrc_ft710` 归档为历史项目——网站 301 到 `/mrrc_modern/`、从 portal 呈现层
彻底移除、仓库只读、服务器目录删除；历史证据层一字不改。

**架构：** nginx `^~` 前缀 301 + portal 呈现层移除 + GitHub 仓库归档。
无构建步骤。测试运行器 `/usr/bin/python3 -m pytest`（`portal/tests/`）。

**红线（规格 §8）：** R1 不改历史事实｜R2 不删仓库｜R3 不删本地安装器｜R4 不动子站仓库｜
R5 服务器删除只允许 `/var/www/vlsc.net/mrrc_ft710/` 一个目录｜R6 R7 nginx 改动不得修改用户的
`/stats/` 部分，且两者共享一次部署。

---

### 任务 1：提交用户待提交的 `/stats/` 修复（R7）

**文件：** 修改 `nginx/vlsc.net.conf`（内容一字不改）

- [ ] **步骤 1：确认 diff 只含 `/stats/` 那段**

```bash
cd /Users/cheenle/HAM/website && git diff nginx/vlsc.net.conf | grep -E "^[+-]" | grep -vE "^(\+\+\+|---)"
```

预期：只有 `location /stats/` → `location ^~ /stats/` 及其注释。

- [ ] **步骤 2：原样提交**

```bash
git add nginx/vlsc.net.conf
git commit -m "fix(nginx): /stats/ 用 ^~ 前缀，避免被正则 location 截走导致 404"
```

---

### 任务 2：nginx 加 FT-710 301

**文件：** 修改 `nginx/vlsc.net.conf:59`（删除）、`:102-106`（替换）

- [ ] **步骤 1：删掉二次跳转行**

删除 `location = /mrrc_ft710/fde.html   { return 301 /mrrc_ft710/agentic.html; }`

- [ ] **步骤 2：替换块**

```nginx
# ── MRRC FT-710: archived 2026-09-12, merged into MRRC Modern ──
# `^~` is load-bearing: without it the regex location `~* \.(css|js|…)$`
# above outranks this prefix, so /mrrc_ft710/css/*.css would be served as a
# static asset instead of redirecting. Same defect class as the /stats/ fix.
location ^~ /mrrc_ft710/ { return 301 /mrrc_modern/; }
```

- [ ] **步骤 3：本地语法自检（无 sudo 时用 docker 或直接看结构）**

```bash
grep -n -A3 "MRRC FT-710: archived" nginx/vlsc.net.conf
grep -c "location /mrrc_ft710/" nginx/vlsc.net.conf     # 期望 0（旧块已删）
grep -c "location \^~ /mrrc_ft710/" nginx/vlsc.net.conf # 期望 1
```

- [ ] **步骤 4：Commit**

```bash
git add nginx/vlsc.net.conf
git commit -m "feat(nginx): /mrrc_ft710/ 301 到 /mrrc_modern/（归档）"
```

---

### 任务 3：sitemap 移除旧站

**文件：** 修改 `portal/make_sitemap.py:75`、重生成 `portal/sitemap.xml`

- [ ] **步骤 1：从 SUBSITES 移除**

`SUBSITES = ['/mrrc/', '/mrrc_ft710/', …]` → 去掉 `'/mrrc_ft710/', `

- [ ] **步骤 2：重生成并验证**

```bash
cd portal && python3 make_sitemap.py
grep -c "mrrc_ft710" sitemap.xml      # 期望 0
grep -c "<loc>" sitemap.xml           # 期望 58（原 60，减 2）
```

- [ ] **步骤 3：跑 sitemap 测试**

```bash
/usr/bin/python3 -m pytest tests/test_sitemap.py -q
```

若 `tests/test_sitemap.py` 断言了 `/mrrc_ft710/`，同步更新该断言（规格 §4.1 已授权）。

- [ ] **步骤 4：Commit**

```bash
git add portal/make_sitemap.py portal/sitemap.xml portal/tests/test_sitemap.py
git commit -m "chore(portal): sitemap 不再收录已归档的 /mrrc_ft710/"
```

---

### 任务 4：portal 呈现层移除 FT-710

**文件（10 个，注意 EN + ZH）：**
`portal/index.html`、`portal/zh/index.html`、`portal/about.html`、`portal/zh/about.html`、
`portal/contact.html`、`portal/zh/contact.html`、`portal/privacy.html`、`portal/zh/privacy.html`、
`portal/blog/index.html`、`portal/js/global-nav.js`

- [ ] **步骤 1：global-nav.js 三处**

删 `else if (/\/mrrc_ft710\//.test(p)) SITE = 'mrrc_ft710';`、
`mrrc_ft710: '/mrrc_ft710/',`、`siteLink('mrrc_ft710', 'FT-710') +`

- [ ] **步骤 2：逐文件删除 FT-710 条目**

`index.html`：产品矩阵 `<tr>` 行、独立产品卡（`<!-- MRRC FT-710 -->` 到该卡 `</div>`）、页脚列表项。
其余文件同理。ZH 版对应删。

- [ ] **步骤 3：验证呈现层已清空**

```bash
cd /Users/cheenle/HAM/website
SITES=(portal/index.html portal/zh/index.html portal/about.html portal/zh/about.html portal/contact.html portal/zh/contact.html portal/privacy.html portal/zh/privacy.html portal/blog/index.html portal/js/global-nav.js)
grep -n "mrrc_ft710" "${SITES[@]}" | grep -v "github.com/cheenle/mrrc_ft710"
```

预期：只剩 GitHub 源码链接（若该条也删则完全无命中）。

- [ ] **步骤 4：跑 portal 测试**

```bash
cd portal && /usr/bin/python3 -m pytest tests/ -q
```

- [ ] **步骤 5：Commit**

```bash
git add portal/
git commit -m "refactor(portal): 呈现层移除已归档的 MRRC FT-710（导航/产品表/页脚，EN+ZH）"
```

---

### 任务 5：博客文章链接改指 Modern

**文件：** 修改 `portal/blog/ft710-usb-remote-control/index.html`

- [ ] **步骤 1：只改那一句**

```html
<a href="/mrrc_ft710/">MRRC FT-710</a> → <a href="/mrrc_modern/">MRRC FT-710</a>
```

- [ ] **步骤 2：验证**

```bash
grep -n "mrrc_ft710\"" portal/blog/ft710-usb-remote-control/index.html   # 期望 0
```

- [ ] **步骤 3：Commit**

```bash
git add portal/blog/ft710-usb-remote-control/index.html
git commit -m "docs(blog): FT-710 USB 文章链接改指 /mrrc_modern/"
```

---

### 任务 6：CLAUDE.md 标注归档

**文件：** 修改 `CLAUDE.md:14`、`CLAUDE.md:182` 附近

- [ ] **步骤 1：改第 14 行子站描述**

把「MRRC FT-710 (`mrrc_ft710/` → …) — Website for …」改为开头加
「**已归档 2026-09-12**，并入 MRRC Modern；仓库只读，网站 301 到 `/mrrc_modern/`。」，
保留原有路径与部署说明作为历史记录（用删除线或「历史」前缀）。

- [ ] **步骤 2：改「## MRRC FT-710-specific (`mrrc_ft710/`)」章节**

标题改为 `## MRRC FT-710-specific (已归档 2026-09-12)`，并在正文首句写明归档口径。

- [ ] **步骤 3：验证**

```bash
grep -n "已归档 2026-09-12" CLAUDE.md | head        # 期望 ≥2
grep -c "mrrc_ft710" CLAUDE.md                       # 仍应有（SITES 数组等保留）
```

- [ ] **步骤 4：Commit**

```bash
git add CLAUDE.md
git commit -m "docs(CLAUDE.md): 标注 mrrc_ft710 已归档（保留历史与 grep 目标）"
```

---

### 任务 7：mrrc_ft710 归档产物

**文件（在 mrrc_ft710 仓）：** 创建 `ARCHIVED.md`；修改 `README.md`、`website/deploy.sh`

- [ ] **步骤 1：写 `ARCHIVED.md`**

内容照抄规格 §6.1。

- [ ] **步骤 2：README.md 顶部插入提示**

在第一个标题之前插入同义段落（GitHub 首屏可见）。

- [ ] **步骤 3：deploy.sh 加守卫**

在 `set -euo pipefail` 之后插入规格 §6.3 的守卫块（`echo … exit 1`）。

- [ ] **步骤 4：验证守卫真的会拦**

```bash
cd /Users/cheenle/HAM/mrrc_ft710 && bash website/deploy.sh; echo "exit=$?"
```

预期：打印归档提示，`exit=1`，**不产生任何 SSH 连接**。

- [ ] **步骤 5：跑 ft710 测试套件（归档前最后确认仓库健康）**

```bash
cd /Users/cheenle/HAM/mrrc_ft710 && .venv/bin/python3 -m pytest -q 2>&1 | tail -3
```

预期：`439 passed`

- [ ] **步骤 6：Commit（在 mrrc_ft710 仓，非 website 仓）**

```bash
cd /Users/cheenle/HAM/mrrc_ft710
git add ARCHIVED.md README.md website/deploy.sh
git commit -m "chore: archive project — merged into MRRC Modern (site 301s, deploy disabled)"
git push origin HEAD
```

---

### 任务 8：GitHub 仓库归档

- [ ] **步骤 1：归档**

```bash
gh repo archive cheenle/mrrc_ft710 --yes
```

- [ ] **步骤 2：验证**

```bash
gh repo view cheenle/mrrc_ft710 --json isArchived
```

预期：`{"isArchived":true}`

---

### 任务 9：服务器目录删除

**红线 R5：只允许这一个目录。**

- [ ] **步骤 1：列出并确认目标**

```bash
ssh cheenle@www.vlsc.net "sudo du -sh /var/www/vlsc.net/mrrc_ft710; ls /var/www/vlsc.net/ | head -20"
```

- [ ] **步骤 2：验证本地副本完整（删前最后一道保险）**

```bash
ls -la /Users/cheenle/HAM/mrrc_ft710/website/downloads/   # 3 个 exe
```

- [ ] **步骤 3：删除（绝对路径写全，不用通配符）**

```bash
ssh cheenle@www.vlsc.net "sudo rm -rf /var/www/vlsc.net/mrrc_ft710 && echo deleted"
```

- [ ] **步骤 4：验证**

```bash
ssh cheenle@www.vlsc.net "ls /var/www/vlsc.net/mrrc_ft710 2>&1 | head -1"
ssh cheenle@www.vlsc.net "ls /var/www/vlsc.net/"
```

预期：前者 `No such file or directory`；后者其余子站**全部健在**。

---

### 任务 10：部署与终检

- [ ] **步骤 1：部署 nginx 配置（含用户 `/stats/` 修复 + FT-710 301）**

```bash
cd /Users/cheenle/HAM/website
scp nginx/vlsc.net.conf cheenle@www.vlsc.net:/tmp/
ssh cheenle@www.vlsc.net "sudo cp /tmp/vlsc.net.conf /etc/nginx/sites-available/vlsc.net && sudo nginx -t && sudo systemctl reload nginx"
```

- [ ] **步骤 2：部署 portal**

```bash
cd portal && echo y | ./deploy.sh
```

- [ ] **步骤 3：运行规格 §7 的全部 11 项验证**

```bash
for u in /mrrc_ft710/ /mrrc_ft710/css/octen.css /mrrc_ft710/sdd/01-executive-summary.html /mrrc_ft710/zh/ /mrrc_ft710/guide.html; do
  printf "%-46s %s\n" "$u" "$(curl -sI --max-time 15 https://www.vlsc.net$u | head -1 | tr -d '\r')"
done
printf "%-46s %s\n" "/mrrc_modern/" "$(curl -sS -o /dev/null -w '%{http_code}' --max-time 15 https://www.vlsc.net/mrrc_modern/)"
printf "%-46s %s\n" "/stats/ (用户修复)" "$(curl -sS -o /dev/null -w '%{http_code}' --max-time 15 https://www.vlsc.net/stats/)"
```

预期：前 5 行均 `301` + `Location: /mrrc_modern/`；后两行 `200`。

- [ ] **步骤 4：证据层未被误伤**

```bash
cd /Users/cheenle/HAM/website/portal
grep -c "FT-710" agentic.html        # 期望 ≈22
grep -c "mrrc_ft710" blog/seven-billion-tokens/ledger/index.html   # 期望 ≥1
```

- [ ] **步骤 5：portal 全量测试**

```bash
/usr/bin/python3 -m pytest tests/ -q
```

- [ ] **步骤 6：push 并汇报**

```bash
cd /Users/cheenle/HAM/website && git push origin main
```
