# 把 SunsdrMobile 并入 SunMRRC 实现计划

> **面向 AI 代理的工作者：** 必需子技能：superpowers:executing-plans。
> 步骤用复选框（`- [ ]`）跟踪。规格：`docs/superpowers/specs/2026-09-12-sunsdrmobile-merge-design.md`

**目标：** 把 SunsdrMobile 从独立仓库/独立产品，合并为 SunMRRC 的原生 iOS 客户端——
仓库带历史导入、网站并入 `/sunmrrc/ios/`、portal 呈现合并为一个产品。

**技术栈：** `git subtree`（带历史导入）、纯静态 HTML/CSS、nginx `^~` 301。
无构建步骤。测试运行器 `/usr/bin/python3 -m pytest`（`portal/tests/`）。

**红线（规格 §8）：** R1 证据层不改｜R2 不删 `portal/css/sunsdrmobile.css`｜R3 不删 SunsdrMobile
仓库或其 `.git`｜**R4 不扰动 sunsdr 仓 14 项未提交改动**｜R5 不动其他子站｜R6 服务器删除只允许
`/var/www/vlsc.net/sunsdrmobile/`｜R7 目录名不改｜R8 nginx 必须 `^~`

---

### 任务 1：SunsdrMobile 仓收尾 + 备份

**文件：** `SunsdrMobile/website/{index.html,zh/index.html,images/qr-wechat-group.jpg}`

- [ ] **步骤 1：提交二维码例行更新**

```bash
cd /Users/cheenle/HAM/sunsdr/SunsdrMobile
git add website/index.html website/zh/index.html website/images/qr-wechat-group.jpg
git commit -m "chore(website): 微信群二维码有效期顺延至 Sep 12"
```

- [ ] **步骤 2：两份备份（导入前双保险）**

```bash
git bundle create /tmp/SunsdrMobile-full-$(date +%Y%m%d).bundle --all
git push origin scope-redesign
```

- [ ] **步骤 3：验证工作区干净 + bundle 可用**

```bash
git status --short          # 期望空
git bundle verify /tmp/SunsdrMobile-full-*.bundle | tail -2
```

---

### 任务 2：sunsdr 移除悬挂 gitlink

**文件：** `sunsdr` 仓索引（`SunsdrMobile` 条目）

- [ ] **步骤 1：记录现状（回滚用）**

```bash
cd /Users/cheenle/HAM/sunsdr
git ls-files -s SunsdrMobile            # 记下 160000 <sha>
git rev-parse HEAD                      # 记下当前 HEAD
git status --short | wc -l              # 记下未提交条目数（应为 14）
```

- [ ] **步骤 2：移除 gitlink，把嵌套仓移出树外**

```bash
git rm --cached SunsdrMobile
mv SunsdrMobile /tmp/SunsdrMobile-pretree
ls -d SunsdrMobile 2>&1                 # 期望 "No such file or directory"
```

- [ ] **步骤 3：验证用户的改动未被触动**

```bash
git status --short | grep -v "^D  SunsdrMobile$" | wc -l   # 期望仍为 14
```

---

### 任务 3：带历史导入（`git subtree add`）

- [ ] **步骤 1：导入**

```bash
cd /Users/cheenle/HAM/sunsdr
git subtree add --prefix=SunsdrMobile /tmp/SunsdrMobile-pretree scope-redesign
```

- [ ] **步骤 2：核验提交范围（R4 —— 这一步不通过就回滚）**

```bash
git show --stat HEAD | tail -5
# 期望：只含 SunsdrMobile/** 文件
git show --name-only --format="" HEAD | grep -v "^SunsdrMobile/" | head
# 期望：输出为空
```

若出现范围外文件：`git reset --hard HEAD~1` 并停下报告。

- [ ] **步骤 3：核验历史与文件数**

```bash
printf "历史提交数: %s (期望 ≥10)\n" "$(git log --oneline -- SunsdrMobile | wc -l | tr -d ' ')"
printf "跟踪文件数: %s (期望 ≥40)\n" "$(git ls-files SunsdrMobile/ | wc -l | tr -d ' ')"
git status --short SunsdrMobile          # 期望空（" M SunsdrMobile" 消失）
```

- [ ] **步骤 4：核验用户未提交改动仍在**

```bash
git status --short | grep -E "sunmrrc/server.py|web_control/dsp.py" | wc -l   # 期望 2
```

- [ ] **步骤 5：Commit 元信息（subtree 已自建提交，此处只补充说明）**

`git subtree add` 会自动创建一个 merge 提交，无需额外提交。仅确认：

```bash
git log --oneline -1
```

---

### 任务 4：网站合并

**文件：** 创建 `sunmrrc/website/ios/index.html`、`sunmrrc/website/zh/ios/index.html`；
修改 `sunmrrc/website/index.html`、`sunmrrc/website/zh/index.html`

- [ ] **步骤 1：搬运 iOS 页（HTML only —— CSS/JS 逐字节相同，复用不迁移）**

从 `SunsdrMobile/website/index.html` 生成 `sunmrrc/website/ios/index.html`，路径调整：

| 原引用 | 改为 |
|---|---|
| `css/scope.css?v=2` | `../css/scope.css?v=2` |
| `js/scope.js?v=2` | `../js/scope.js?v=2` |
| `images/qr-wechat-group.jpg` | `../images/qr-wechat-group.jpg` |
| `zh/`（语言切换） | `../zh/ios/` |
| 指向 `/sunsdrmobile/` 的自引 | `/sunmrrc/ios/` |

ZH 版同理 → `sunmrrc/website/zh/ios/index.html`，相对路径上溯两级（`../../css/…`）。

- [ ] **步骤 2：sunmrrc 首页加 iOS 一节 + 导航项**

在 `sunmrrc/website/index.html` 与 `zh/index.html` 增加一节，指向 `ios/`，文案口径：
「服务端 + Web 前端 + 原生 iOS 客户端（SunsdrMobile）」。

- [ ] **步骤 3：验证站内链接可达**

```bash
cd /Users/cheenle/HAM/sunsdr/sunmrrc/website
for u in ios/index.html zh/ios/index.html index.html zh/index.html; do printf "  %-24s %s\n" "$u" "$([ -f "$u" ] && echo 在 || echo 缺)"; done
grep -o 'href="\.\./[a-z]*/[a-z]*\.\(css\|js\)[^"]*"' ios/index.html | sort -u
```

---

### 任务 5：SunsdrMobile 归档产物

**文件（在 SunsdrMobile 仓）：** 创建 `ARCHIVED.md`；修改 `README.md`、`website/deploy.sh`

- [ ] **步骤 1：写 `ARCHIVED.md`** —— 内容照抄规格 §6.1
- [ ] **步骤 2：README 顶部横幅**
- [ ] **步骤 3：deploy.sh 加守卫**（`exit 1`，指向 `/sunmrrc/ios/`）
- [ ] **步骤 4：验证守卫**

```bash
cd /Users/cheenle/HAM/sunsdr/SunsdrMobile && bash website/deploy.sh; echo "exit=$?"
```

- [ ] **步骤 5：Commit + push**

```bash
git add ARCHIVED.md README.md website/deploy.sh
git commit -m "chore: archive project — merged into SunMRRC as its native iOS client"
git push origin scope-redesign
git push origin scope-redesign:main     # 默认分支也要有横幅
```

---

### 任务 6：GitHub 归档

- [ ] **步骤 1：归档 + 验证**

```bash
gh repo archive cheenle/SunsdrMobile --yes
gh repo view cheenle/SunsdrMobile --json isArchived,defaultBranchRef
```

---

### 任务 7：nginx 301

**文件：** `website/nginx/vlsc.net.conf:127-128`

- [ ] **步骤 1：替换**

```nginx
# ── SunsdrMobile: merged 2026-09-12 into SunMRRC as its native iOS client ──
# `^~` is load-bearing for the same reason as /stats/ and /mrrc_ft710/: the
# regex location `~* \.(css|js|…)$` above outranks a plain prefix match, so
# /sunsdrmobile/css/scope.css would be served as a static asset (404, the
# server directory is gone) instead of redirecting.
location ^~ /sunsdrmobile/ { return 301 /sunmrrc/ios/; }
```

- [ ] **步骤 2：结构自检**

```bash
printf "旧块残留: %s (期望 0)\n" "$(grep -c 'location /sunsdrmobile/' nginx/vlsc.net.conf)"
printf "新 ^~ 块: %s (期望 1)\n" "$(grep -c 'location \^~ /sunsdrmobile/' nginx/vlsc.net.conf)"
/usr/bin/python3 -c "s=open('nginx/vlsc.net.conf').read();print('大括号平衡' if s.count('{')==s.count('}') else '❌')"
```

- [ ] **步骤 3：Commit**

---

### 任务 8：portal 呈现层移除

**文件（10 个，EN + ZH）：** `index.html`、`zh/index.html`、`about.html`、`zh/about.html`、
`contact.html`、`zh/contact.html`、`privacy.html`、`zh/privacy.html`、`blog/index.html`、
`js/global-nav.js`；另 `make_sitemap.py` + 重生成 `sitemap.xml`

- [ ] **步骤 1：global-nav.js 三处**（SITE 正则 / PATHS / siteLink）
- [ ] **步骤 2：产品矩阵 2 行 → 1 行**（删除 SunsdrMobile 行，SunMRRC 行描述改为「服务端 + Web 前端 + 原生 iOS 客户端」）
- [ ] **步骤 3：产品卡 2 张 → 1 张**（删除 SunsdrMobile 卡，SunMRRC 卡加 iOS 条目）
- [ ] **步骤 4：页脚 / about / contact / privacy / blog 页脚** 删条目
- [ ] **步骤 5：meta description 产品清单**去掉 SunsdrMobile
- [ ] **步骤 6：`make_sitemap.py` 的 `SUBSITES` 去 `/sunsdrmobile/`，重生成**

```bash
cd /Users/cheenle/HAM/website/portal && python3 make_sitemap.py
grep -c sunsdrmobile sitemap.xml      # 期望 0
```

- [ ] **步骤 7：验证（R2 尤其重要）**

```bash
cd /Users/cheenle/HAM/website/portal
grep -rn "sunsdrmobile\|SunsdrMobile" index.html zh/index.html about.html contact.html privacy.html blog/index.html js/global-nav.js sitemap.xml 2>/dev/null | grep -v "sunsdrmobile.css" || echo "✅ 呈现层 0 命中"
ls css/sunsdrmobile.css               # R2：必须仍在
grep -c "sunsdrmobile.css" index.html # 仍被引用
```

- [ ] **步骤 8：跑测试 + Commit**

---

### 任务 9：CLAUDE.md 标注

- [ ] **步骤 1：改第 15 行 SunsdrMobile 描述** 为「已合并入 SunMRRC 2026-09-12」
- [ ] **步骤 2：改「## SunsdrMobile-specific」章节** 标题加「已归档 2026-09-12」并写明口径
- [ ] **步骤 3：Commit**

---

### 任务 10：部署与删除

- [ ] **步骤 1：部署 sunmrrc 站**

```bash
cd /Users/cheenle/HAM/sunsdr/sunmrrc/website && echo y | ./deploy.sh
```

- [ ] **步骤 2：部署 nginx + portal**

```bash
cd /Users/cheenle/HAM/website
scp nginx/vlsc.net.conf cheenle@www.vlsc.net:/tmp/
ssh cheenle@www.vlsc.net "sudo cp /tmp/vlsc.net.conf /etc/nginx/sites-available/vlsc.net && sudo nginx -t && sudo systemctl reload nginx"
cd portal && echo y | ./deploy.sh
```

- [ ] **步骤 3：验证 301（含静态资源）**

```bash
for u in /sunsdrmobile/ /sunsdrmobile/zh/ /sunsdrmobile/css/scope.css /sunsdrmobile/js/scope.js /sunsdrmobile/index.html; do
  printf "  %-40s %s\n" "$u" "$(curl -sI --max-time 15 https://www.vlsc.net$u | head -1 | tr -d '\r')"
done
printf "  %-40s %s\n" "/sunmrrc/ios/" "$(curl -sS -o /dev/null -w '%{http_code}' --max-time 15 https://www.vlsc.net/sunmrrc/ios/)"
printf "  %-40s %s\n" "/sunmrrc/" "$(curl -sS -o /dev/null -w '%{http_code}' --max-time 15 https://www.vlsc.net/sunmrrc/)"
```

- [ ] **步骤 4：删除服务器目录（R6 -- 只允许这一个）**

```bash
ssh cheenle@www.vlsc.net 'set -e
T=/var/www/vlsc.net/sunsdrmobile
[ -d "$T" ] || { echo "目标不存在，中止"; exit 1; }
case "$T" in /var/www/vlsc.net/sunsdrmobile) ;; *) echo "路径不符，中止"; exit 1;; esac
sudo find "$T" -type f | wc -l | sed "s/^/  文件数: /"
sudo rm -rf "$T"
echo "  deleted: $T"'
```

- [ ] **步骤 5：终检**

```bash
cd /Users/cheenle/HAM/website/portal
/usr/bin/python3 -m pytest tests/ -q
grep -c -i sunsdrmobile agentic.html          # R1：期望 10（未动）
ssh cheenle@www.vlsc.net "ls /var/www/vlsc.net/sunsdrmobile 2>&1 | head -1; ls /var/www/vlsc.net/ | tr '\n' ' '"
```

- [ ] **步骤 6：push**

```bash
cd /Users/cheenle/HAM/website && git push origin main
cd /Users/cheenle/HAM/sunsdr && git push origin scope-redesign
```
