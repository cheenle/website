# Agentic Engineering 全站重构 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或
> superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**规格：** `docs/superpowers/specs/2026-09-02-agentic-engineering-refactor-design.md`

**目标：** 把 Agentic Engineering（智能体工程）提升为 VLSC 全站工程总纲，FDE 降为其交付环节与前史；
`portal/fde.html` 演化为 `/agentic.html`，`engineering.html` 重定位为机制分册，术语层与「分工与资产」
小节铺到 6 个可改子站。

**架构：** 纯静态 HTML/CSS/JS，无构建步骤、无框架。纲（`/agentic.html`）/ 目（`/engineering.html`）
两层页面，父子关系由导航与面包屑表达。旧 URL 由 nginx 集中 301。事实账本单一来源在 portal。

**技术栈：** HTML5 + `css/octen.css` 设计系统 + 原生 `<details>`；Python `unittest`（stdlib
`html.parser`）做页面契约测试；nginx 配置；各站 `deploy.sh`（tar+scp+ssh）。

**关键环境事实（工程师必须知道）：**

1. `website/mrrc`、`mrrc_modern`、`mrrc_ft710`、`sunmrrc`、`SunsdrMobile`、`mrrc_ft8`、`ft8`
   **都是符号链接**（`portal`、`efhw`、`nginx` 是真实目录）。

   **普查铁律（实测 2026-09-02，macOS BSD grep 2.6.0）：** 从仓库根扫 `.` 时，`-r` 与 `-R`
   **都不**进入符号链接子站 —— 跟随嵌套链接是 GNU grep `-R` 的行为，本机没有。实测漏检量：

   | 站点 | `grep -Ran PAT .` 可见 | 显式 `站点/` 实扫 |
   | --- | --- | --- |
   | `mrrc` | 0 | 106 |
   | `mrrc_modern` | 0 | 45 |
   | `mrrc_ft710` | 0 | 30 |
   | `sunmrrc` / `SunsdrMobile` / `mrrc_ft8` | 0 | 各 1 |
   | `portal` / `efhw`（真实目录） | 45 / 4 | 45 / 4 |

   所以**绝不可**用 `grep -R … .` 做全站普查 —— 它会报告干净而实际漏掉 184 处，形成**假绿**。
   唯一正确形式是逐个显式列出站点目录、**并带尾斜杠**（尾斜杠是决定因素，裸名同样返回 0）：

   ```bash
   cd /Users/cheenle/HAM/website
   SITES="portal/ mrrc/ mrrc_ft710/ mrrc_modern/ sunmrrc/ SunsdrMobile/ mrrc_ft8/ efhw/"
   grep -Ran "PAT" $SITES     # 全部可见
   grep -Ran "PAT" mrrc       # 0 —— 错：裸符号链接名不进入
   ```

   例外：任务内先 `cd` 进某站的**真实仓库目录**（如 `/Users/cheenle/HAM/MRRC/website`）再扫 `.`
   是安全的，那里没有符号链接层。需要文件清单时用 `find -L . -name '*.html'`（`-L` 才跟随链接）。
   下文所有「全站普查」步骤均已按此形式写好，不要简化回 `grep -R … .`。

   **查基线禁止 `git stash`（任务 2 踩坑）：** 要对比改动前的行为，用 `git show HEAD:<path>`
   取原内容，或 `git worktree add` 开临时工作树。`git stash --include-untracked` 会把未跟踪文件
   一并卷入，pop 后又打断 `git mv` 的重命名记录（表现为 `A`+`D`、`git diff --cached -M`
   看不到重命名），实测只能重做提交来补救，风险远大于收益。

   **执行期陷阱（任务 1 实测）：** `git mv` 之后必须重新 `read` 新路径才能编辑——读文件守卫不认旧路径；
   且 `tests/__pycache__/` 会留下旧模块的 `.pyc`，`git mv` 后顺手 `rm -f tests/__pycache__/<旧名>.*.pyc`。
   改测试模块名后还要 `grep -rn "<旧模块名>" portal/` 确认无其他引用。

2. `website/mrrc` 原指向已搬走的 `/Users/cheenle/UHRR/MRRC/website`，**规划阶段已重指向**
   `/Users/cheenle/HAM/MRRC/website`（commit `9ad7a21`）；MRRC 站**纳入本轮**（任务 11）。
3. 子站各自的仓库在 `/Users/cheenle/HAM/<name>/`，其 `website/` 目录才是站点根。
4. `portal/deploy.sh` 的 `REQUIRED_FILES` 只含 `index.html`、`zh/index.html`、`css/octen.css`，
   不含 `fde.html` —— 改名不需要改它。
5. `portal/make_sitemap.py` 走目录树自动生成 `sitemap.xml` —— 改名后**重跑即可**，不要手编 `sitemap.xml`。
6. **子站各自属于不同的 git 仓库** —— commit 必须落在对应仓库，不是 website 仓库：

   | 站点 | 仓库根 |
   | --- | --- |
   | `portal`、`efhw`、`nginx`、`CLAUDE.md` | `/Users/cheenle/HAM/website` |
   | `mrrc_modern` | `/Users/cheenle/HAM/mrrc_modern` |
   | `mrrc_ft710` | `/Users/cheenle/HAM/mrrc_ft710` |
   | `mrrc_ft8` | `/Users/cheenle/HAM/ft8` |
   | `sunmrrc` | `/Users/cheenle/HAM/sunsdr` |
   | `SunsdrMobile` | `/Users/cheenle/HAM/sunsdr/SunsdrMobile` |

   下文统一用 `REPO=<仓库根>` 变量，`git -C "$REPO" …` 形式调用。

---

## 文件结构

### portal（纲 + 目）

| 文件 | 动作 | 职责 |
| --- | --- | --- |
| `portal/tests/test_agentic_pages.py` | 由 `test_fde_pages.py` `git mv` | 页面契约：节 id、EN/ZH 对等、产品族嵌套、可访问性、资源存在 |
| `portal/agentic.html` | 由 `fde.html` `git mv` + 重写 | 总纲：命题 / 分工 / FDE 前史 / 机制摘要 / 三赛道 / 五产品族 / 杠杆 / 本体底座 / 能力矩阵 / 证据纪律 |
| `portal/zh/agentic.html` | 由 `zh/fde.html` `git mv` + 重写 | 同上中文版（节 id 必须与 EN 完全相等） |
| `portal/css/agentic.css` | 由 `css/fde.css` `git mv` + 前缀改名 | `ag-*` 组件样式 + 新增 `ag-proc--*` 过程证据徽章 |
| `portal/engineering.html` | 修改 | 机制分册：标题、导航、外层环标签、指向总纲的面包屑 |
| `portal/zh/engineering.html` | 修改 | 同上中文版 |
| `portal/index.html` | 修改 | 方法论节改写 + 导航术语 |
| `portal/zh/index.html` | 修改 | 同上中文版 |
| `portal/about.html` `contact.html` `privacy.html` + `zh/` 同名 | 修改 | 仅导航术语 |
| `portal/js/global-nav.js` | 修改 | SITE 判定正则、`PATHS` 路由表、`siteLink` 标签 |
| `nginx/vlsc.net.conf` | 修改 | 四条集中 301 |

### 子站

| 文件 | 动作 | 职责 |
| --- | --- | --- |
| `mrrc/agentic.html`、`mrrc/zh/agentic.html` | 由 `fde.html` `git mv` | MRRC 站长页：改名 + 术语 + §8.2 数字口径（**不重做设计**，任务 11） |
| `mrrc/` 另 21 个含 `fde.html` 链接的 HTML/JS | 修改 | 三种相对深度的导航（任务 11 步骤 3） |
| `mrrc_modern/agentic.html` | 由 `fde.html` `git mv` + 改造 | 本族 agentic 叙事；删过时数字（任务 12） |
| `mrrc_ft710/agentic.html` | 由 `fde.html` `git mv` + 改造 | 同上 |
| `mrrc_modern/index.html`、`mrrc_ft710/index.html` | 修改 | 导航 + 新增「分工与资产」小节 |
| `efhw/index.html`、`sunmrrc/index.html`、`SunsdrMobile/index.html`、`mrrc_ft8/index.html` | 修改 | 各新增一节「分工与资产」 |
| 10 个 `js/global-nav.js` / `js/scope.js`（清单见任务 5） | 修改 | 三处统一模式（`fde: '/fde.html'`、`siteLink('fde','FDE')`、SITE 正则） |
| 各站 `zh/index.html` | 修改 | 导航术语（本期不新建子站中文长页） |
| `CLAUDE.md`（workspace 根） | 修改 | 事实单一来源规则、符号链接普查约定、新 URL 结构 |

**每个任务独立 commit。** 任务 1 契约测试必须先红后绿；2–9 属 portal（含跨站 JS 术语层）；
10 属 nginx；11 MRRC；12 两张子站长页；13 四个子站小改；14 收尾与部署。
任务 10 的 301 与任务 2/11/12 的改名必须同一时间窗发布，**且 nginx 最后加载**（见任务 14 步骤 4）。

### 规格覆盖映射（自检用）

| 规格节 | 要求 | 实现任务 |
| --- | --- | --- |
| §2 核心主张 | 三角色分工 + 知识复利 | 任务 3、4（`thesis`/`roles`/`lineage`） |
| §3 措辞红线表 | 禁句、禁「AI 赋能」、禁声称产品由 Agent 写成 | 任务 1 步骤 5（禁句断言）、任务 7 步骤 1（逐仓核实表）、任务 14 步骤 1（回写 `CLAUDE.md`） |
| §4.1 重定向 | 集中 301 | 任务 10 |
| §4.2 导航统一 | 纲/目层级在导航中表达 | 任务 5、任务 9 步骤 1–2 |
| §4.3 术语约定 | 智能体工程 / 前沿部署工程 | 任务 5 步骤 3、任务 14 步骤 1 |
| §4.4 CSS 改名范围 | `.fde-` → `.ag-` | 任务 2 步骤 3、5 |
| §5.1 契约测试同步 | 10 个 section id、EN/ZH 对等 | 任务 1 |
| §5.2 产品族新字段 | `Agent Execution` / `Human Retained Judgment` / `Contract Left Behind` | 任务 7（portal）、任务 12 步骤 4、任务 13 步骤 1（子站同模板） |
| §6.1 已核实实装 | 52 条约束、三仓库 | 任务 6 步骤 1–2（数据）、任务 7 步骤 1（逐族证据上限） |
| §6.2 概念→消费方表 | 7 行真实锚点 | 任务 6 步骤 1 |
| §6.3 每行可点开 | 锚点可 grep、不可核实即删 | 任务 6 步骤 5 |
| §6.4 后续可选搬迁 | 本期不做 | 无任务（明确排除） |
| §8.1 现状 | 三份互相矛盾的 FDE 数字 | 任务 11 步骤 4、任务 12 步骤 2 |
| §8.2 单一来源规则 | 子站删数字、改指账本 | 任务 11 步骤 5、任务 12 步骤 2/4、任务 14 步骤 3 |
| §8.3 双阶梯 | `ag-proc--*` 徽章 + 互推禁令 | 任务 8 |
| §9.1–9.8 验证 | 契约、术语、链接、数字、视觉、a11y、诊断 | 任务 1、任务 14 步骤 3 与 3b |
| §9.9–9.10 部署与抽查 | `deploy.sh`、线上 301 | 任务 14 步骤 4 |

---

## 任务 1：契约测试先行（B0，必须先红）

**文件：**

- 重命名：`portal/tests/test_fde_pages.py` → `portal/tests/test_agentic_pages.py`
- 修改：新文件内的常量与断言

- [ ] **步骤 1：git mv 保留历史**

```bash
cd /Users/cheenle/HAM/website/portal
git mv tests/test_fde_pages.py tests/test_agentic_pages.py
```

- [ ] **步骤 2：把节 id 集合改成新架构（先让它红）**

编辑 `portal/tests/test_agentic_pages.py`，把 `REQUIRED_SECTIONS` 整块替换为：

```python
REQUIRED_SECTIONS = {
    "thesis",
    "roles",
    "lineage",
    "harness",
    "tracks",
    "families",
    "leverage",
    "ontology",
    "capabilities",
    "evidence",
}
```

- [ ] **步骤 3：把测试对象指向新文件名**

把 `PAGES` 整块替换为：

```python
PAGES = {
    "en": PORTAL / "agentic.html",
    "zh": PORTAL / "zh" / "agentic.html",
}
```

同文件内把类名 `class FdePageTests` 改为 `class AgenticPageTests`。

- [ ] **步骤 4：新增两条本架构专属断言（放进 `AgenticPageTests` 内）**

```python
    def test_agentic_thesis_and_role_split_are_stated(self) -> None:
        required = {
            "en": (
                "Agentic engineering is the discipline",
                "Intent",
                "Boundaries",
                "Judgment",
            ),
            "zh": ("智能体工程", "意图", "边界", "裁决"),
        }
        for language, path in PAGES.items():
            source, _ = load_page(path)
            for token in required[language]:
                self.assertIn(token, source, f"{language}: {token}")

    def test_ontology_consumers_cite_real_constraint_rule_ids(self) -> None:
        rule_ids = (
            "ptt-authority",
            "no-direct-serial",
            "cat-no-dn",
            "poll-stale-guard",
            "vendor-readonly",
        )
        for language, path in PAGES.items():
            source, _ = load_page(path)
            cited = [r for r in rule_ids if r in source]
            self.assertGreaterEqual(len(cited), 4, language)
```

- [ ] **步骤 5：扩写既有禁句断言**

`test_obsolete_top_level_counts_are_removed` 内 `forbidden` 元组整块替换为：

```python
        forbidden = (
            "FDE Across Three Projects",
            'One Methodology<br><span class="gradient">Three Products',
            "跨三项目的 FDE 实战",
            '一套方法论<br><span class="gradient">三款产品',
            "One Field. Three Tracks.",
            "Built Through Forward Deployed Engineering",
            "由 Agent 写成",
            "written by AI",
        )
```

前四条来自上一轮（生态本体）规格，保留不动；后四条是本轮新增。

- [ ] **步骤 6：运行测试，确认按预期变红**

```bash
cd /Users/cheenle/HAM/website/portal && python3 -m unittest tests.test_agentic_pages -v
```

预期：**FAIL / ERROR**，报错含 `FileNotFoundError`（`agentic.html` 尚不存在）。
若意外 PASS，说明步骤 3 的路径没改到位 —— 先修再继续。

- [ ] **步骤 7：Commit（红测试单独一次 commit）**

```bash
cd /Users/cheenle/HAM/website
git add portal/tests/test_agentic_pages.py
git commit -m "test: 定义 Agentic Engineering 总纲页契约（先红）"
```

---

## 任务 2：portal 文件改名 + CSS 类前缀机械重命名（B1a）

**文件：**

- `git mv`：`portal/fde.html` → `portal/agentic.html`
- `git mv`：`portal/zh/fde.html` → `portal/zh/agentic.html`
- `git mv`：`portal/css/fde.css` → `portal/css/agentic.css`
- 修改：`portal/engineering.css:106,119`、4 个 portal HTML

- [ ] **步骤 1：三次 git mv**

```bash
cd /Users/cheenle/HAM/website/portal
git mv fde.html agentic.html
git mv zh/fde.html zh/agentic.html
git mv css/fde.css css/agentic.css
cd /Users/cheenle/HAM/website && git diff --cached --stat -M   # 预期 3 个重命名、0 行增删
git commit -m "refactor(portal): 纯改名 fde → agentic（三文件，零内容变更）"
```

**必须单独成提交（任务 2 实测教训）：** 若把改名与后面的 259 行类名改写合并成一次提交，
相似度会被压到 git 默认重命名阈值（50%）以下，`git log --follow portal/agentic.html`
追不到改名前的历史 —— 「用 git mv 保历史」的目的落空。拆开后实测可追到 4 个历史提交。
此刻 CSS 与页面引用暂时不一致，由本任务后续步骤闭合。

- [ ] **步骤 2：确认改名范围与实际类名（防止漏改/过改）**

```bash
cd /Users/cheenle/HAM/website/portal
grep -Rno 'fde-[a-z-]*' *.html zh/*.html css/*.css | awk -F: '{print $1}' | sort | uniq -c
```

预期恰好 6 个文件：`agentic.html`、`zh/agentic.html`、`engineering.html`、
`zh/engineering.html`、`css/agentic.css`、`css/engineering.css`。
出现任何子站文件即停 —— portal 类名与子站样式表是两套，不得跨仓库 `sed`。

- [ ] **步骤 3：一次性类前缀重命名**

```bash
cd /Users/cheenle/HAM/website/portal
LC_ALL=C sed -i '' -E 's/fde-/ag-/g' \
  agentic.html zh/agentic.html engineering.html zh/engineering.html \
  css/agentic.css css/engineering.css
```

`fde-status--field` → `ag-status--field`、`fde-card` → `ag-card` 等 47 个类同批完成。

**执行期实测补充：** `fde-` 在 CSS 里既是类名前缀也是**自定义属性前缀**（`--fde-control` 等 19 个），
同一条 sed 会一起改。跑之前先确认两件事，缺一即停：
`grep -Rl 'fde-' portal/` 证明 `--fde-*` 的引用点自包含在 `css/agentic.css` 内（实测成立），
且 portal 内不存在既有 `ag-` 名（实测 0 个）→ 无冲突。子站色值（`#f0a030` 等）不含 `fde-`，不受影响。

- [ ] **步骤 4：改链接与缓存版本**

```bash
cd /Users/cheenle/HAM/website/portal
LC_ALL=C sed -i '' 's|css/fde.css?v=1|css/agentic.css?v=2|g' \
  agentic.html zh/agentic.html engineering.html zh/engineering.html
grep -n 'agentic.css\|fde.css' agentic.html zh/agentic.html engineering.html zh/engineering.html
```

预期：4 行都命中 `css/agentic.css?v=2`，无 `fde.css` 残留。

- [ ] **步骤 5：验证无孤儿类**

```bash
cd /Users/cheenle/HAM/website/portal
python3 - <<'PY'
import re, pathlib
defined = set(re.findall(r'\.(ag-[a-z0-9-]+)', pathlib.Path('css/agentic.css').read_text()
                + pathlib.Path('css/engineering.css').read_text()))
used = set()
for f in ('agentic.html', 'zh/agentic.html', 'engineering.html', 'zh/engineering.html'):
    for cls in re.findall(r'class="([^"]+)', pathlib.Path(f).read_text()):
        used |= {c for c in cls.split() if c.startswith('ag-')}
print('孤儿（用了但没定义）:', sorted(used - defined))
PY
```

预期输出：`孤儿（用了但没定义）: []`。非空即逐个补定义或删用法，不得留到下个任务。

- [ ] **步骤 5b：修总纲页自身的 6 处旧名引用（初稿遗漏；改名后契约测试立刻抓到）**

`agentic.html` / `zh/agentic.html` 各 3 处，三类方向不同，只改导航必漏：导航**自链**、
EN↔ZH **语言按钮**、**页脚**语言链接。

```bash
cd /Users/cheenle/HAM/website/portal
LC_ALL=C sed -i '' -e 's|<li><a href="fde\.html">FDE</a></li>|<li><a href="agentic.html">Agentic</a></li>|g' \
  -e 's|href="zh/fde\.html"|href="zh/agentic.html"|g' agentic.html
LC_ALL=C sed -i '' -e 's|<li><a href="fde\.html">FDE</a></li>|<li><a href="agentic.html">Agentic</a></li>|g' \
  -e 's|href="\.\./fde\.html"|href="../agentic.html"|g' zh/agentic.html
grep -c 'fde\.html' agentic.html zh/agentic.html      # 预期均 0
```

- [ ] **步骤 5c：修 `engineering.html` 两页各 3 处（原计划留给任务 9，提前到此）**

实测 **3 处而非任务 9 记的 2 处**：导航项、页尾 CTA（`Read FDE in Practice` / `阅读 FDE 实战`）、
页脚语言链接。改名后即已知断链，不能带着它跑 7 个任务。

```bash
cd /Users/cheenle/HAM/website/portal
LC_ALL=C sed -i '' -e 's|<li><a href="fde\.html">FDE</a></li>|<li><a href="/agentic.html">Agentic</a></li>|g' \
  -e 's|href="fde\.html">Read FDE in Practice|href="/agentic.html">Read the Agentic Engineering thesis|g' \
  -e 's|href="fde\.html">FDE</a>|href="/agentic.html">Agentic</a>|g' engineering.html
LC_ALL=C sed -i '' -e 's|<li><a href="fde\.html">FDE</a></li>|<li><a href="/zh/agentic.html">Agentic</a></li>|g' \
  -e 's|href="fde\.html">阅读 FDE 实战|href="/zh/agentic.html">阅读智能体工程总纲|g' \
  -e 's|href="fde\.html">FDE</a>|href="/zh/agentic.html">Agentic</a>|g' zh/engineering.html
grep -c 'fde\.html' engineering.html zh/engineering.html   # 预期均 0
```

- [ ] **步骤 5d：repoint `test_engineering_pages.py`（初稿完全遗漏的第二个契约测试文件）**

该文件第 14-17 行有 `FDE_PAGES = {... "fde.html" ...}`，第 196 行 `("fde", FDE_PAGES)`。
危险之处：**它的 `load_page` 对不存在的文件抛 `SkipTest`（101-102 行）**，所以改名后
相关用例不是变红、而是**静默跳过**（实测 skip 从基线 0 变成 2）—— 覆盖率悄悄流失，
比红测试更危险。改法（本任务内只做路径与命名，节 id 断言留到任务 4）：

- `FDE_PAGES` → `AGENTIC_PAGES`，两个路径改指 `agentic.html` / `zh/agentic.html`
- 用例名 `test_fde_summary_precedes_ontology_and_links_to_engineering` →
  `test_agentic_summary_...`；分组标签 `("fde", FDE_PAGES)` → `("agentic", AGENTIC_PAGES)`
- **不要**动 `test_nested_loops_are_explicit` 里的 `data-loop="fde"` —— FDE 作为闭环名保留

```bash
cd /Users/cheenle/HAM/website/portal
python3 -m unittest tests.test_engineering_pages -v 2>&1 | tail -3   # 预期 skip 0
```

- [ ] **步骤 6：Commit（第二次提交：内容改写）**

```bash
cd /Users/cheenle/HAM/website
git add portal/agentic.html portal/zh/agentic.html portal/css/agentic.css \
        portal/css/engineering.css portal/engineering.html portal/zh/engineering.html \
        portal/tests/test_engineering_pages.py
git commit -m "refactor(portal): 类前缀 fde- → ag-，样式引用升 v=2，修 12 处旧名链接"
git status --porcelain portal/ | grep '^??' || true
```

**必须逐路径 `git add`，禁止 `git add -A portal/`：** 该目录下有**不属于任何任务**的未跟踪文件
（实测 `portal/IMG_9243.JPG`、`portal/images/`），`-A` 会把它们一并提交进去。
最后一条 grep 用来确认没有误收。

预期测试状态：`Ran 26 tests / FAILED (failures=4) / skipped=0`，
且 4 处红全在 `test_agentic_pages`（任务 1 故意留红，待任务 3-9 转绿）。
若 skip 不为 0 或红项越出 `test_agentic_pages`，说明 5b-5d 有漏，停下修
---

## 任务 3：总纲前三节（EN）——命题、分工、FDE 前史（B1b）

**文件：** 修改 `portal/agentic.html`（Hero 块 + `<main>` 开头）

- [ ] **步骤 1：替换 Hero 块**

把 `portal/agentic.html` 中 `<header class="ag-hero">…</header>` 整块替换为：

```html
    <header class="ag-hero">
        <div class="ag-hero-inner">
            <div class="hero-badge"><i class="fas fa-robot"></i><span>Agentic Engineering · 智能体工程</span></div>
            <h1>Human Intent.<br><span class="gradient">Agentic Execution. Field Evidence.</span></h1>
            <p>Agentic engineering is the discipline of building environments where an agent can be trusted to execute, and where a human remains the only one who can decide. VLSC reached it through field engineering, not the other way round.</p>
            <div class="ag-hero-stats" aria-label="Thesis summary">
                <span class="ag-pill"><i class="fas fa-bullseye"></i> Intent stays human</span><span class="ag-pill"><i class="fas fa-gears"></i> Inner loop delegated</span><span class="ag-pill"><i class="fas fa-shield-halved"></i> Boundaries enforced</span><span class="ag-pill"><i class="fas fa-scale-balanced"></i> Evidence decides</span>
            </div>
        </div>
    </header>
```

- [ ] **步骤 2：替换锚点导航**

`<nav class="ag-anchor-nav" …>` 内的链接整行替换为：

```html
        <a href="#thesis">Thesis</a><a href="#roles">Division</a><a href="#lineage">Lineage</a><a href="#harness">Harness</a><a href="#tracks">Tracks</a><a href="#families">Families</a><a href="#ontology">Ontology</a><a href="#evidence">Evidence</a>
```

- [ ] **步骤 3：把原 `id="method"` 一节整块替换为三节**

定位起点 `<section class="ag-section" id="method">`、终点（不含）`<section class="ag-section" id="tracks">`，
用下面内容替换。三节顺序即 `thesis` → `roles` → `lineage`。

```html
        <section class="ag-section" id="thesis">
            <div class="container">
                <header class="ag-section-header"><span class="ag-section-label">01 · Thesis</span><h2 class="ag-section-title">Execution can be delegated. Judgment cannot.</h2><p class="ag-section-subtitle">Three claims hold this page together. Each one is checked against an artifact, not an opinion.</p></header>
                <div class="ag-term-grid">
                    <article class="ag-card"><h3><i class="fas fa-arrows-spin"></i> Roles changed</h3><p>The inner engineering loop — Specify, Implement, Test, Review, Observe, Update SDD — is executed by agents with real tools, real repositories, and real gates.</p></article>
                    <article class="ag-card"><h3><i class="fas fa-database"></i> Why now</h3><p>Because an agent actually loads the contract before acting. <code>AGENTS.md</code>, the living SDD, and the domain ontology stopped being documents and became runtime context.</p></article>
                    <article class="ag-card"><h3><i class="fas fa-route"></i> FDE still gates</h3><p>Field discipline produced the contracts worth reusing — and it keeps the parts an agent may never sign off: PCB, bench, RF safety, live stations.</p></article>
                </div>
                <div class="ag-note" style="margin-top:1.25rem;"><strong>Testable form:</strong> a field incident becomes an SDD ruling, the ruling becomes a machine-readable constraint, and the constraint blocks the agent from re-introducing the incident. Any claim on this page that cannot be traced onto that chain is not made.</div>
            </div>
        </section>

        <section class="ag-section" id="roles">
            <div class="container">
                <header class="ag-section-header"><span class="ag-section-label">02 · Division of Work</span><h2 class="ag-section-title">Agents run the loop. Humans hold three things.</h2><p class="ag-section-subtitle">The split is not by task size or by skill. It is by who is accountable when the result is wrong.</p></header>
                <div class="ag-loop-grid">
                    <article class="ag-card" data-track="control">
                        <h3>Delegated to agents</h3>
                        <div class="ag-flow" aria-label="Inner engineering loop executed by agents"><span class="ag-flow-step">Specify</span><span class="ag-flow-arrow">→</span><span class="ag-flow-step">Implement</span><span class="ag-flow-arrow">→</span><span class="ag-flow-step">Test</span><span class="ag-flow-arrow">→</span><span class="ag-flow-step">Review</span><span class="ag-flow-arrow">→</span><span class="ag-flow-step">Observe</span><span class="ag-flow-arrow">→</span><span class="ag-flow-step">Update&nbsp;SDD</span></div>
                        <p>Agents read the constraint registry before editing, run the verification appropriate to each claim, and write the outcome back into the same contract they started from.</p>
                    </article>
                    <article class="ag-card" data-track="sdr">
                        <h3>Retained by humans</h3>
                        <div class="ag-term-grid" style="grid-template-columns:1fr;"><div><strong>Intent</strong> — why this work exists, what counts as success, what is deliberately out of scope.</div><div><strong>Boundaries</strong> — architecture rulings, safety invariants, and the constraints an agent may not trade away for a passing test.</div><div><strong>Judgment</strong> — whether the available evidence is enough to say a thing is done, shipped, or safe.</div></div>
                    </article>
                </div>
                <div class="ag-note ag-note--warning" style="margin-top:1.25rem;"><strong>Agents carry execution, not accountability.</strong> Responsibility for a transmit, a release, or a safety claim stays with the named human who signs the evidence. No delegation changes that.</div>
            </div>
        </section>
        <section class="ag-section" id="lineage">
            <div class="container">
                <header class="ag-section-header"><span class="ag-section-label">03 · Lineage</span><h2 class="ag-section-title">Forward Deployed Engineering is where the contracts came from</h2><p class="ag-section-subtitle">Ontology is not a fourth FDE phase, and agentic engineering does not retire FDE. The loops are coupled and each keeps a veto.</p></header>
                <div class="ag-loop-grid">
                    <article class="ag-card" data-track="control">
                        <h3>FDE delivery loop</h3>
                        <div class="ag-flow" aria-label="Echo to Delta to Product"><span class="ag-flow-step"><strong>Echo</strong><br><small>Field evidence</small></span><span class="ag-flow-arrow">→</span><span class="ag-flow-step"><strong>Delta</strong><br><small>Risky proof</small></span><span class="ag-flow-arrow">→</span><span class="ag-flow-step"><strong>Product</strong><br><small>Stable delivery</small></span></div>
                        <p>Echo observes the actual station and operator. Delta validates the highest-risk assumption with a working vertical slice. Product hardens the result into an operable boundary, contract, or reusable component — which is exactly the object an agent can later be handed.</p>
                    </article>
                    <article class="ag-card" data-track="sdr">
                        <h3>Ontology engineering loop</h3>
                        <div class="ag-flow" aria-label="Scope to terms, relations, constraints and validation"><span class="ag-flow-step">Scope</span><span class="ag-flow-arrow">→</span><span class="ag-flow-step">Terms</span><span class="ag-flow-arrow">→</span><span class="ag-flow-step">Relations</span><span class="ag-flow-arrow">→</span><span class="ag-flow-step">Constraints</span><span class="ag-flow-arrow">→</span><span class="ag-flow-step">Validate</span></div>
                        <p>Product evidence stabilizes vocabulary and exposes invariants. The model then gives later work — human or agentic — better questions, cleaner boundaries, and fewer accidental protocol assumptions.</p>
                    </article>
                </div>
                <h3 style="margin-top:2.5rem;">What an agent may not compress</h3>
                <div class="ag-plane-grid">
                    <article class="ag-card"><h3>Hardware</h3><p>PCB fabrication and bench bring-up. EFHW V3.0 design and firmware are complete; its claims stay design-target until a board exists.</p></article>
                    <article class="ag-card"><h3>RF safety</h3><p>PTT paths and transmit authority on real radios. A passing server test does not sign off a client.</p></article>
                    <article class="ag-card"><h3>Live stations</h3><p>Field verification on the operator's own antenna, band conditions, and neighbors.</p></article>
                    <article class="ag-card"><h3>Publication</h3><p>Release decisions and what gets labeled shipped, because the label is a promise to a person.</p></article>
                </div>
                <div class="ag-note" style="margin-top:1.25rem;"><strong>Bidirectional feedback:</strong> products generate evidence for ontology revisions; the ontology supplies language, boundaries, and competency questions for the next field cycle — now loaded by the agent before it edits.</div>
            </div>
        </section>
```

- [ ] **步骤 4：把 `engineering` 节改名为 `harness` 并物理移动到第 4 位**

`portal/agentic.html` 中 `<section class="ag-section" id="engineering">` → `id="harness"`；
其 section-label `05 · Engineering System` → `04 · Engineering System (summary)`。

> **计划补正（执行时发现的第 7 处缺陷，已修正）。** 原步骤只改 id 与编号，**没有把该节移动到文档顺序第 4 位**。
> 插入三节后该节物理位置落在 `leverage` 之后（第 7 位），结果是编号序列变成
> `01 02 03 05 06 07 04 08 09 10`——页码数字与滚动顺序不一致，且步骤 2 的锚点导航里
> `Harness` 排在 `Tracks` 之前，点击会**往回跳**。
> 规格 §5.1 的节序 `thesis, roles, lineage, harness, tracks, …` 就是目标 DOM 顺序。
> 因此本步骤必须包含移动：把整节（`<section … id="harness">` 至下一个 `<section` 前）
> 剪切并插回 `<section class="ag-section" id="tracks">` 之前。
> 验收：`grep -o 'ag-section-label">[0-9][0-9]' agentic.html` 必须输出严格递增的 01…10。

- [ ] **步骤 5：全节编号顺延（插了三节，后面全部错位）**

`portal/agentic.html` 内按此表逐条替换 section-label 的前缀数字（文本其余不动）：

| 现值 | 改为 |
| --- | --- |
| `02 · Ecosystem Map` | `05 · Ecosystem Map` |
| `03 · Product Families` | `06 · Product Families` |
| `04 · Engineering Leverage` | `07 · Engineering Leverage` |
| `06 · Domain Ontology` | `08 · Domain Ontology` |
| `07 · Capability Matrix` | `09 · Capability Matrix` |
| `08 · Evidence Discipline` | `10 · Evidence Discipline` |

```bash
grep -o 'ag-section-label">[0-9]* · [^<]*' /Users/cheenle/HAM/website/portal/agentic.html
```

预期改完后为：`01 · Thesis`、`02 · Division of Work`、`03 · Lineage`、`04 · Engineering System (summary)`、
`05 · Ecosystem Map`、`06 · Product Families`、`07 · Engineering Leverage`、`08 · Domain Ontology`、
`09 · Capability Matrix`、`10 · Evidence Discipline`（缺项即漏改）。

- [ ] **步骤 6：本地静态检查**

```bash
cd /Users/cheenle/HAM/website/portal && python3 -m unittest tests.test_agentic_pages -v 2>&1 | tail -20
```

预期：`en` 相关断言通过，`zh` 因缺 `thesis`/`roles`/`lineage`/`harness` 节而 FAIL。
这是预期中间态（EN 先行），**不要**为了让 zh 变绿而偷改测试。

- [ ] **步骤 7：Commit**

```bash
cd /Users/cheenle/HAM/website
git add portal/agentic.html
git commit -m "feat(portal): 总纲新增命题/分工/FDE 前史三节（EN），engineering 节降为机制摘要"
```

此刻 `zh` 断言仍红属预期，任务 4 收尾。**发布动作在各站 `deploy.sh`，此前线上不受影响。**

---

## 任务 4：总纲前三节（ZH）——与 EN 完全对等（B1c）

**文件：** 修改 `portal/zh/agentic.html`

中文页现有标签沿用 `01 · 双循环` 等，节 id 必须与 EN 严格相等（§9.1 断言）。

- [ ] **步骤 1：替换 Hero**

把 `portal/zh/agentic.html` 的 `<h1>` 由「一个领域，三条轨道…」改为：

```html
<h1>人的意图。<br><span class="gradient">智能体的执行。现场的证据。</span></h1>
```

副标 `<p>` 替换为：

```html
<p>智能体工程的纪律，是构建一个「智能体可被信任去执行、而人保留唯一裁决权」的工程环境。VLSC 是从现场工程走到这里的，而不是相反。</p>
```

badge 文案改为 `<span>Agentic Engineering · 智能体工程</span>`。

- [ ] **步骤 2：替换锚点导航**

```html
        <a href="#thesis">命题</a><a href="#roles">分工</a><a href="#lineage">前史</a><a href="#harness">机制摘要</a><a href="#tracks">轨道</a><a href="#families">产品族</a><a href="#ontology">领域本体</a><a href="#evidence">证据纪律</a>
```

- [ ] **步骤 3：把 `id="method"` 一节整块替换为三节（ZH）**

定位起点 `<section class="ag-section" id="method">`、终点（不含）`<section class="ag-section" id="tracks">`。
节 id 与 EN 严格相等，编号与 EN 逐节对应。

```html
        <section class="ag-section" id="thesis">
            <div class="container">
                <header class="ag-section-header"><span class="ag-section-label">01 · 命题</span><h2 class="ag-section-title">执行可以委托，<span class="gradient">判断不行</span></h2><p class="ag-section-subtitle">撑起本页的是三个主张，每一个都对照工件校验，而非观点。</p></header>
                <div class="ag-term-grid">
                    <article class="ag-card"><h3><i class="fas fa-arrows-spin"></i> 角色变了</h3><p>工程内循环——规格、实现、测试、审查、观测、回写 SDD——由智能体携带真实工具、在真实仓库与真实门禁下执行。</p></article>
                    <article class="ag-card"><h3><i class="fas fa-database"></i> 为什么是现在</h3><p>因为智能体在行动前真的会加载契约。<code>AGENTS.md</code>、活体 SDD 与领域本体，从文档变成了运行时上下文。</p></article>
                    <article class="ag-card"><h3><i class="fas fa-route"></i> FDE 仍然是门禁</h3><p>现场纪律产出了值得复用的契约；它也保留了智能体永远不能代为签字的部分：PCB、台架、RF 安全、真实台站。</p></article>
                </div>
                <div class="ag-note" style="margin-top:1.25rem;"><strong>可证伪形式：</strong>一次现场事故变成一条 SDD 裁决，裁决变成一条机器可读约束，约束阻止智能体重新引入该事故。本页任何无法沿这条链回溯的主张，都不写。</div>
            </div>
        </section>
```

```html
        <section class="ag-section" id="roles">
            <div class="container">
                <header class="ag-section-header"><span class="ag-section-label">02 · 分工</span><h2 class="ag-section-title">智能体跑循环，<span class="gradient">人握住三样东西</span></h2><p class="ag-section-subtitle">这条分界线不按任务大小或技能划分，而按「结果出错时谁负责」划分。</p></header>
                <div class="ag-loop-grid">
                    <article class="ag-card" data-track="control">
                        <h3>委托给智能体</h3>
                        <div class="ag-flow" aria-label="由智能体执行的工程内循环"><span class="ag-flow-step">规格</span><span class="ag-flow-arrow">→</span><span class="ag-flow-step">实现</span><span class="ag-flow-arrow">→</span><span class="ag-flow-step">测试</span><span class="ag-flow-arrow">→</span><span class="ag-flow-step">审查</span><span class="ag-flow-arrow">→</span><span class="ag-flow-step">观测</span><span class="ag-flow-arrow">→</span><span class="ag-flow-step">回写&nbsp;SDD</span></div>
                        <p>智能体在动手前先读取约束注册表，按每条主张的性质选择对应的验证手段，并把结论写回它出发时所用的同一份契约。</p>
                    </article>
                    <article class="ag-card" data-track="sdr">
                        <h3>人保留的三样</h3>
                        <div class="ag-term-grid" style="grid-template-columns:1fr;"><div><strong>意图</strong>——这件事为何存在、什么算成功、什么刻意不做。</div><div><strong>边界</strong>——架构裁决、安全不变量，以及智能体不得为了跑绿而交易掉的约束。</div><div><strong>裁决</strong>——现有证据是否足以说一句「完成 / 已发布 / 安全」。</div></div>
                    </article>
                </div>
                <div class="ag-note ag-note--warning" style="margin-top:1.25rem;"><strong>智能体承担执行，不承担问责。</strong>一次发射、一次发布、一句安全主张的责任，始终属于签署证据的那个具名的人。任何委托都不改变这一点。</div>
            </div>
        </section>
```

```html
        <section class="ag-section" id="lineage">
            <div class="container">
                <header class="ag-section-header"><span class="ag-section-label">03 · 前史</span><h2 class="ag-section-title">契约从<span class="gradient">前沿部署工程</span>里来</h2><p class="ag-section-subtitle">本体不是 FDE 的第四个阶段，智能体工程也不使 FDE 退役。两个循环耦合，且各自握有否决权。</p></header>
                <div class="ag-loop-grid">
                    <article class="ag-card" data-track="control">
                        <h3>FDE 交付循环</h3>
                        <div class="ag-flow" aria-label="Echo 到 Delta 再到 Product"><span class="ag-flow-step"><strong>Echo</strong><br><small>现场证据</small></span><span class="ag-flow-arrow">→</span><span class="ag-flow-step"><strong>Delta</strong><br><small>高风险验证</small></span><span class="ag-flow-arrow">→</span><span class="ag-flow-step"><strong>Product</strong><br><small>稳定交付</small></span></div>
                        <p>Echo 观察真实台站与操作者；Delta 用可运行的垂直切片验证风险最高的假设；Product 把结果固化为可运维的边界、契约或可复用组件——而这正是日后能交给智能体的东西。</p>
                    </article>
                    <article class="ag-card" data-track="sdr">
                        <h3>本体工程循环</h3>
                        <div class="ag-flow" aria-label="范围、术语、关系、约束、验证"><span class="ag-flow-step">范围</span><span class="ag-flow-arrow">→</span><span class="ag-flow-step">术语</span><span class="ag-flow-arrow">→</span><span class="ag-flow-step">关系</span><span class="ag-flow-arrow">→</span><span class="ag-flow-step">约束</span><span class="ag-flow-arrow">→</span><span class="ag-flow-step">验证</span></div>
                        <p>产品证据稳定词汇、暴露不变量；模型再为下一轮工作——无论人做还是智能体做——提供更干净的问题、更明确的边界，以及更少的偶然协议假设。</p>
                    </article>
                </div>
```

```html
                <h3 style="margin-top:2.5rem;">智能体不能压缩的部分</h3>
                <div class="ag-plane-grid">
                    <article class="ag-card"><h3>硬件</h3><p>PCB 制板与台架 bring-up。EFHW V3.0 设计与固件已完成；在实物板子存在之前，它的主张停留在设计目标。</p></article>
                    <article class="ag-card"><h3>RF 安全</h3><p>真实电台上的 PTT 路径与发射权限。服务端测试通过，不等于客户端签字放行。</p></article>
                    <article class="ag-card"><h3>真实台站</h3><p>在操作者自己的天线、波段条件与邻居环境下的现场验证。</p></article>
                    <article class="ag-card"><h3>发布</h3><p>发布决策，以及什么可以被标注为「已发布」——因为这个标签是对一个人的承诺。</p></article>
                </div>
                <div class="ag-note" style="margin-top:1.25rem;"><strong>双向反馈：</strong>产品为模型修订提供证据；模型为下一轮现场循环提供语言、边界与能力问题——而现在这份上下文是由智能体在编辑前加载的。</div>
            </div>
        </section>
```

- [ ] **步骤 4：`engineering` 节改名 + 编号顺延（与 EN 同表）**

`id="engineering"` → `id="harness"`；`05 · Engineering System` → `04 · 机制摘要`。
其余 label 按任务 3 步骤 5 的数字表改，中文文本不动（`02 · 双循环`→`05 · 生态地图` 之类以
`grep -o 'ag-section-label">[^<]*' zh/agentic.html` 实际输出为准逐条对齐 EN 序号）。

**同批改 `test_engineering_pages.py` 的 3 行断言**（两侧都改名后才动手，中途必有一侧不一致）：

```python
    def test_agentic_summary_precedes_ontology_and_links_to_engineering(self) -> None:
        for language, path in AGENTIC_PAGES.items():
            source, parser = load_page(path)
            self.assertIn("harness", parser.section_ids, language)
            # 机制摘要紧跟纲（thesis/roles/lineage）、置于目（tracks…evidence）之前
            self.assertLess(source.index('id="lineage"'), source.index('id="harness"'), language)
            self.assertLess(source.index('id="harness"'), source.index('id="tracks"'), language)
            self.assertLess(source.index('id="harness"'), source.index('id="ontology"'), language)
            self.assertIn('href="engineering.html"', source, language)
```

删掉步骤 5d 留的那行「任务 3/4 届时更新」注释。

- [ ] **步骤 4b：确认无残留旧节名**

```bash
cd /Users/cheenle/HAM/website/portal
grep -c 'id="engineering"' agentic.html zh/agentic.html    # 预期均 0
grep -n 'id="engineering"' tests/test_engineering_pages.py  # 预期只剩对 engineering.html 页的引用，无节 id
```

- [ ] **步骤 5：跑契约测试，确认 EN/ZH 结构对等**

```bash
cd /Users/cheenle/HAM/website/portal && python3 -m unittest tests.test_agentic_pages.AgenticPageTests.test_ids_are_unique_and_section_parity_is_preserved -v
```

预期 PASS。若 FAIL，报错会列出两侧 section id 差集——以差集为准补齐，不要改测试。

- [ ] **步骤 6：Commit**

```bash
cd /Users/cheenle/HAM/website
git add portal/zh/agentic.html
git commit -m "feat(portal): 中文总纲同步新增命题/分工/前史三节"
```

---

## 任务 5：跨站导航与共享 JS 术语层（机械改名）

**文件（9 个 JS，模式完全一致）：**

```
portal/js/global-nav.js                      ← 含 SITE 正则 + PATHS + siteLink
mrrc_modern/js/global-nav.js   mrrc_modern/js/scope.js
mrrc_ft710/js/global-nav.js    mrrc_ft710/js/scope.js
efhw/js/global-nav.js          efhw/js/scope.js
sunmrrc/js/scope.js            SunsdrMobile/js/scope.js            mrrc_ft8/js/scope.js
```

**两类 `fde` 链接语义不同，不可用一条 sed 打天下：**

| 出现形式 | 语义 | 改成 |
| --- | --- | --- |
| JS 里 `fde: '/fde.html'`（绝对路径） | **portal 总纲页** | `agentic: '/agentic.html'` |
| JS 里 `else if (/\/fde\.html/.test(p)) SITE = 'fde';` | 高亮判定 portal 总纲页 | 正则与值都换成 `agentic` |
| 子站 HTML 里 `href="fde.html"`（相对路径） | **该子站自己的长页** | `href="agentic.html"`（任务 12 改名后才有效） |

- [ ] **步骤 1：改 9 个 JS 的三处模式**

```bash
cd /Users/cheenle/HAM/website
FILES="portal/js/global-nav.js \
mrrc_modern/js/global-nav.js mrrc_modern/js/scope.js \
mrrc_ft710/js/global-nav.js mrrc_ft710/js/scope.js \
efhw/js/global-nav.js efhw/js/scope.js \
sunmrrc/js/scope.js SunsdrMobile/js/scope.js mrrc_ft8/js/scope.js"
LC_ALL=C sed -i '' \
  -e "s|fde: '/fde.html',|agentic: '/agentic.html',|g" \
  -e "s|/\\\\/fde\\\\.html/|/\\\\/agentic\\\\.html/|g" \
  -e "s|SITE = 'fde'|SITE = 'agentic'|g" \
  -e "s|siteLink('fde', 'FDE')|siteLink('agentic', 'Agentic')|g" \
  $FILES
grep -Rc "fde" $FILES | grep -v ':0$' || echo "OK: 10 个 JS 内 fde 归零"
```

预期最后一行输出 `OK: 10 个 JS 内 fde 归零`。`SITE = 'agentic'` 与 `PATHS.agentic` 必须同时改，
否则总纲页高亮失效（`siteLink` 用 `PATHS[key]`，key 不存在会生成 `href="undefined"`）。

- [ ] **步骤 2：portal 四个 HTML 的硬编码导航**

```bash
cd /Users/cheenle/HAM/website/portal
LC_ALL=C sed -i '' \
  -e 's|<li><a href="/fde.html">FDE</a></li>|<li><a href="/agentic.html">Agentic</a></li>|g' \
  index.html about.html contact.html privacy.html
LC_ALL=C sed -i '' \
  -e 's|<li><a href="/zh/fde.html">FDE</a></li>|<li><a href="/zh/agentic.html">Agentic</a></li>|g' \
  zh/index.html zh/about.html zh/contact.html zh/privacy.html
grep -Rn 'fde\.html' *.html zh/*.html
```

实测最后一条 grep **归零**（0 行）：`engineering.html` / `zh/engineering.html` 各 3 处旧链接
已在**任务 2 步骤 5c** 提前修掉（初稿此处记为「×2、由任务 10 处理」是错的——任务 10 只管 nginx
集中 301，修不了页面内的相对链接，且实际是 3 处不是 2 处）。

`index.html` 的 `/fde.html` CTA 按钮（含文案 `Read the FDE Story`）**仍留在此处未改**，
它不是 `<li>` 结构、上面的 sed 不命中，由**任务 9 步骤 5** 改写 —— 属预期中间态，
不是漏改。

- [ ] **步骤 3：统一 FDE 中文译名（现状自相矛盾）**

`portal/zh/fde.html`（现 `zh/agentic.html`）用「前沿部署工程」×2，`portal/zh/about.html` 用
「前置部署工程」×1。取定义该术语的主页所用者：

```bash
cd /Users/cheenle/HAM/website/portal
LC_ALL=C sed -i '' 's/前置部署工程/前沿部署工程/g' zh/about.html
grep -Rc "前置部署工程" zh/*.html *.html | grep -v ':0$' || echo "OK: 全 portal 统一为前沿部署工程"
```

- [ ] **步骤 4：按仓库分别 commit（10 个 JS 分属 5 个仓库）**

```bash
cd /Users/cheenle/HAM/website
git add portal/js/global-nav.js portal/index.html portal/about.html portal/contact.html \
        portal/privacy.html portal/zh/index.html portal/zh/about.html portal/zh/contact.html \
        portal/zh/privacy.html efhw/js/global-nav.js efhw/js/scope.js
git commit -m "refactor: 全站导航术语 FDE → Agentic，统一 FDE 中文译名"

git -C /Users/cheenle/HAM/mrrc_modern add website/js/global-nav.js website/js/scope.js \
  && git -C /Users/cheenle/HAM/mrrc_modern commit -m "refactor(nav): FDE → Agentic 术语与 portal 总纲链接"
git -C /Users/cheenle/HAM/mrrc_ft710 add website/js/global-nav.js website/js/scope.js \
  && git -C /Users/cheenle/HAM/mrrc_ft710 commit -m "refactor(nav): FDE → Agentic 术语与 portal 总纲链接"
git -C /Users/cheenle/HAM/sunsdr add sunmrrc/website/js/scope.js \
  && git -C /Users/cheenle/HAM/sunsdr commit -m "refactor(nav): FDE → Agentic 术语与 portal 总纲链接"
git -C /Users/cheenle/HAM/sunsdr/SunsdrMobile add website/js/scope.js \
  && git -C /Users/cheenle/HAM/sunsdr/SunsdrMobile commit -m "refactor(nav): FDE → Agentic 术语与 portal 总纲链接"
git -C /Users/cheenle/HAM/ft8 add website/js/scope.js \
  && git -C /Users/cheenle/HAM/ft8 commit -m "refactor(nav): FDE → Agentic 术语与 portal 总纲链接"
```

已核实的仓库前缀（照抄，勿再猜）：

| 站点目录 | 仓库根 | 仓库内路径前缀 |
| --- | --- | --- |
| `portal`、`efhw` | `/Users/cheenle/HAM/website` | `portal/`、`efhw/` |
| `mrrc_modern` | `/Users/cheenle/HAM/mrrc_modern` | `website/` |
| `mrrc_ft710` | `/Users/cheenle/HAM/mrrc_ft710` | `website/` |
| `mrrc_ft8` | `/Users/cheenle/HAM/ft8` | `website/` |
| `sunmrrc` | `/Users/cheenle/HAM/sunsdr` | `sunmrrc/website/` |
| `SunsdrMobile` | `/Users/cheenle/HAM/sunsdr/SunsdrMobile` | `website/` |

**已知未跟踪文件（本计划会首次把它们纳入版本控制）：** `efhw/js/scope.js`、`efhw/css/scope.css`、
`efhw/images/`。它们线上在跑（`deploy.sh` 打包整个目录），但 git 里没有——`git add` 时一并提交，
这是修复而非误操作。若某仓库报 `no changes added to commit`，先 `git -C <repo> check-ignore -v <path>`
确认是否被忽略，不要盲目 `git add -f`
---

## 任务 6：本体节改写为「Agent 运行时底座」（EN + ZH）

**文件：** 修改 `portal/agentic.html`、`portal/zh/agentic.html` 的 `id="ontology"` 一节

规格 §6.2 的 7 行表格逐行落地。每一行的规则 ID 都已核实存在于对应仓库：
`mrrc_ft710`(17)、`mrrc_modern`(21)、`ft8`(14) 的
`.agents/skills/sdd-guardian/harness/constraints.json`。**不得增删行、不得改规则 ID。**

- [ ] **步骤 1：在 EN `ontology` 节的 `</header>` 之后插入消费方映射表**

```html
<div class="ag-table-wrap"><table class="ag-table">
<thead><tr><th>Ontology concept / axiom</th><th>Consumer</th><th>Verifiable anchor</th></tr></thead>
<tbody>
<tr><td><code>Policy/Constraint</code>: single authoritative state holder, serial exclusivity</td><td>Agent runtime hard block</td><td>ft8 <code>no-direct-serial</code> — "rigctld is the sole serial owner" [AD-008]; ft710 / modern <code>cat-direct-serial-io</code> [AD-002]</td></tr>
<tr><td><code>Safety</code>: TX authorization and PTT ownership</td><td>Agent runtime hard block</td><td>ft8 <code>ptt-authority</code> — "PTT controlled only by rig and safety components" [AD-007; NFR-050; Ch15]</td></tr>
<tr><td><code>CommandIntent ≠ Actuation</code></td><td><code>info</code> hint to the agent</td><td>ft710 <code>ptt-release-no-verify</code> — "TX0 is fire-and-forget" [AD-007; Ch15; V1.2]</td></tr>
<tr><td><code>Observation</code>: a stale read must not pollute state</td><td><code>info</code> constraint + unit test</td><td>ft710 / modern <code>poll-stale-guard</code> [AD-009; §9.6; V1.7 filter race fix]</td></tr>
<tr><td><code>Protocol Binding ≠ Capability</code></td><td>Code fact + specialized constraint</td><td>modern <code>audio-pyaudio-rate</code> — "rate comes from backend capabilities" [AD-011 amended V2.9/V2.14]</td></tr>
<tr><td><code>Evidence/Provenance</code>: knowledge must not go stale</td><td>Routing index stores no content</td><td><code>harness/index.json</code> — "holds no content — refs are sliced live from SDD/*.md, so it never goes stale"</td></tr>
<tr><td><code>Information Object</code>: a change implies a doc sync</td><td>Lifecycle enforcement</td><td><code>SKILL.md</code> Phase 0–6; <code>docs-sync</code> rule [§14]</td></tr>
</tbody></table></div>
```

- [ ] **步骤 2：在表格后追加计数与普查标注（EN）**

```html
<div class="ag-note" style="margin-top:1.25rem;">
  <strong>52 machine-readable constraints across three repositories</strong> — mrrc_ft710: 17, mrrc_modern: 21, mrrc_ft8: 14 (census 2026-09-02).
  Each rule carries a severity (<code>block</code> / <code>warn</code> / <code>info</code>), an <code>sdd_ref</code> pointing back at an
  architecture decision or a real incident, a <code>scope</code> glob and <code>patterns</code>.
  <code>harness/sdd_context.py</code> exposes <code>prime</code> / <code>check</code> / <code>hook</code>;
  <code>install_hooks.py</code> registers <code>SessionStart → prime</code> and <code>PreToolUse(Edit|Write) → hook</code>.
  One semantic, three consumers: agent context, runtime block, human review.
</div>
```

- [ ] **步骤 3：把该节标题与副标从「文档」改为「底座」口径（EN）**

```bash
cd /Users/cheenle/HAM/website/portal
grep -n 'id="ontology"' -A2 agentic.html | head
```

把 `<h2 class="ag-section-title">` 内文案改为
`The ontology is loaded before the agent types`，
`ag-section-subtitle` 改为
`Not a documentation habit: the same terms, boundaries and axioms are consumed by agent context, by a pre-edit gate, and by human review.`

- [ ] **步骤 4：ZH 同节同步（步骤 1–3 的中文对等）**

表头「本体概念 / 公理」「消费方」「可核查锚点」；
7 行正文按规格 §6.2 中文原文照抄（规则 ID 与 `[AD-xxx]` 保持英文原样，不译）；
标注块中文为「三仓库共 52 条机器可读约束……普查日期 2026-09-02」；
标题改「本体在智能体动手之前被加载」，副标
「不是文档习惯：同一套术语、边界与公理，被智能体上下文、编辑前门禁与人工审查三方消费。」

- [ ] **步骤 5：验证规则 ID 可 grep（防止页面写了不存在的锚点）**

```bash
cd /Users/cheenle/HAM && for id in no-direct-serial cat-direct-serial-io ptt-authority ptt-release-no-verify poll-stale-guard audio-pyaudio-rate docs-sync; do
  hit=$(grep -Rl "\"$id\"" mrrc_ft710/.agents mrrc_modern/.agents ft8/.agents 2>/dev/null | wc -l | tr -d ' ')
  printf "%-26s repos=%s\n" "$id" "$hit"; done
```

预期 8 行全部 `repos>=1`。任何 `repos=0` 一律**删该行**，不改测试、不弱化措辞。

- [ ] **步骤 6：Commit**

```bash
cd /Users/cheenle/HAM/website && git add portal/agentic.html portal/zh/agentic.html \
  && git commit -m "feat(portal): 本体节升为 Agent 运行时底座，附 52 条约束的消费方映射表"
```

此刻 `test_ontology_consumers_cite_real_constraint_rule_ids` 仍红：本节只引入 5 个受测规则 ID 中的
3 个（`no-direct-serial`、`ptt-authority`、`poll-stale-guard`）。`vendor-readonly` 在任务 7 的
FT-8 卡片、`cat-no-dn` 在任务 8 的复现样本里出现，断言于**任务 7 步骤 4 转绿**（阈值 4）。不要为此改测试
---

## 任务 7：五张产品族卡片追加两字段（EN + ZH）

**文件：** 修改 `portal/agentic.html`、`portal/zh/agentic.html` 的 `id="families"` 一节

现有 8 字段（`Field Problem` … `Maturity / Evidence`）顺序与徽章**一律不动**，
在每张卡 `</dl>` 前追加两个 `fde-field`→现为 `ag-field` 块。

- [ ] **步骤 1：逐仓工件普查（已核实 2026-09-02，照此写，不得美化）**

| 卡片 | `AGENTS.md` | `.agents` 约束注册表 | 可声明的最高阶梯 B |
| --- | --- | --- | --- |
| MRRC Universal | ✅ 58 行 | ❌ | B2（spec/plan 留痕） |
| MRRC Direct USB（FT-710 + Modern） | ✅ 两仓都有 | ✅ 17 / 21 条 | **B4**（阻断被验证） |
| SunMRRC | ✅ 仓库根 `/Users/cheenle/HAM/sunsdr/AGENTS.md` | ❌ | B2 |
| MRRC-FT8 | ✅ | ✅ 14 条 | **B4** |
| EFHW Auto Tuner V3.0 | ❌（仅 `efhw-knowledge/` 知识库 + workspace `CLAUDE.md`） | ❌ | B2 |

**没有注册表 = 不得写「编辑前门禁」或「hook 阻断」**，只能写「Agent 按 `AGENTS.md` 载入入口契约」。

- [ ] **步骤 2：EN 追加字段（五张卡各一段，按表替换尖括号内容）**

```html
<div class="ag-field"><dt>Agent Execution</dt><dd><入口文件> — the inner-loop steps an agent actually runs: <步骤列表>. Census 2026-09-02.</dd></div>
<div class="ag-field"><dt>Human Retained Judgment</dt><dd><Agent 不得自行签字的环节> · <Contract Left Behind>：本族新产出、可被下一个 Agent 加载的工件。</dd></div>
```

逐卡实际文案（**照抄，不要自行加戏**）：

**MRRC Universal**

```html
<div class="ag-field"><dt>Agent Execution</dt><dd><code>AGENTS.md</code> at the repo root — run-and-verify, config and port conventions, and the <code>/CONFIG</code> restart caveat are stated for agents before they touch the Tornado app. No machine-readable constraint registry yet. Census 2026-09-02.</dd></div>
<div class="ag-field"><dt>Human Retained Judgment</dt><dd>Live-station PTT and RF safety on operator hardware; release labelling. · <strong>Contract Left Behind:</strong> the run-and-verify entry contract reused by every later family.</dd></div>
```

**MRRC Direct USB (FT-710 · Modern)**

```html
<div class="ag-field"><dt>Agent Execution</dt><dd><code>AGENTS.md</code> plus <code>.agents/skills/sdd-guardian/</code>: 17 constraints (ft710) and 21 (modern) with severity, <code>sdd_ref</code>, scope globs and patterns. <code>SessionStart → prime</code> loads them; <code>PreToolUse(Edit|Write) → hook</code> blocks violations before the edit lands. Census 2026-09-02.</dd></div>
<div class="ag-field"><dt>Human Retained Judgment</dt><dd>PTT safety path on real radios; PCB and bench bring-up; whether evidence supports a "shipped" label. · <strong>Contract Left Behind:</strong> the constraint registry itself, plus <code>harness/index.json</code> routing to live SDD slices.</dd></div>
```

**SunMRRC**

```html
<div class="ag-field"><dt>Agent Execution</dt><dd><code>AGENTS.md</code> and <code>CLAUDE.md</code> at the <code>sunsdr</code> repo root, in front of a reverse-engineered protocol document and a living SDD. No constraint registry — so no claim of a pre-edit gate here. Census 2026-09-02.</dd></div>
<div class="ag-field"><dt>Human Retained Judgment</dt><dd>Every protocol inference drawn from observation rather than a datasheet; PTT on hardware we did not design. · <strong>Contract Left Behind:</strong> <code>PROTOCOL.md</code> and the SDD chapters that later families cite as a boundary source.</dd></div>
```

**MRRC-FT8**

```html
<div class="ag-field"><dt>Agent Execution</dt><dd><code>AGENTS.md</code> plus <code>.agents/skills/sdd-guardian/</code>: 14 constraints including <code>vendor-readonly</code>, <code>no-direct-serial</code> and <code>ptt-authority</code>, enforced through the same prime / hook pair. Census 2026-09-02.</dd></div>
<div class="ag-field"><dt>Human Retained Judgment</dt><dd>Decoder fidelity against real band conditions; UTC slot discipline where a mistake costs an emission. · <strong>Contract Left Behind:</strong> the vendored-decoder rule: <code>wsjtx-3.0.2/</code> is read-only and changes go to <code>dsp/patched/</code> [<code>vendor-readonly</code>, NFR-080 / AD-002].</dd></div>
```

**EFHW Auto Tuner V3.0**

```html
<div class="ag-field"><dt>Agent Execution</dt><dd>Site and knowledge-base work runs under the workspace <code>CLAUDE.md</code>; the antenna research corpus in <code>efhw-knowledge/</code> is the shared ontology source. No firmware constraint registry. Census 2026-09-02.</dd></div>
<div class="ag-field"><dt>Human Retained Judgment</dt><dd>PCB fabrication and bench validation — this family's claims stay design-target until a physical board exists. · <strong>Contract Left Behind:</strong> the tuner state model and the 49:1 vs LC test report other families can cite.</dd></div>
```

- [ ] **步骤 3：ZH 追加字段（dt 用固定译名，dd 逐卡对等）**

`dt` 统一：`智能体承担环节` / `人保留裁决`。`dd` 文案（照抄）：

| 卡片 | 智能体承担环节 | 人保留裁决 |
| --- | --- | --- |
| MRRC Universal | 仓库根 `AGENTS.md`：运行与验证、配置与端口约定、`/CONFIG` 重启陷阱在行动前告知智能体。尚无机器可读约束注册表。普查 2026-09-02。 | 真实台站上的 PTT 与 RF 安全；发布标注。· **沉淀契约：** 被后续各族复用的运行与验证入口契约。 |
| MRRC Direct USB | 根 `AGENTS.md` + `.agents/skills/sdd-guardian/`：ft710 17 条、modern 21 条，带 severity、`sdd_ref`、scope glob 与 patterns。`SessionStart → prime` 加载，`PreToolUse(Edit\|Write) → hook` 在落盘前阻断。普查 2026-09-02。 | 真机 PTT 安全路径；PCB 与台架点亮；证据是否足以称「已发布」。· **沉淀契约：** 约束注册表本身，加上把路由指向活体 SDD 切片的 `harness/index.json`。 |
| SunMRRC | `sunsdr` 仓库根的 `AGENTS.md` 与 `CLAUDE.md`，位于一份逆向协议文档与活体 SDD 之前。无约束注册表——因此本节不主张编辑前门禁。普查 2026-09-02。 | 所有靠观察而非数据手册得出的协议推断；非自家设计硬件上的 PTT。· **沉淀契约：** `PROTOCOL.md` 与被后续各族当作边界来源引用的 SDD 章节。 |
| MRRC-FT8 | 根 `AGENTS.md` + `.agents/skills/sdd-guardian/`：14 条约束，含 `vendor-readonly`、`no-direct-serial`、`ptt-authority`，由同一套 prime / hook 执行。普查 2026-09-02。 | 解码保真度对真实波段条件；UTC 时隙纪律（出错即是一次多余发射）。· **沉淀契约：** 已购解码器只读规则——`wsjtx-3.0.2/` 只读，改动走 `dsp/patched/`。 |
| EFHW | 站点与知识库工作在工作区 `CLAUDE.md` 下进行；`efhw-knowledge/` 是共享本体来源。无固件约束注册表。普查 2026-09-02。 | PCB 制板与台架验证——在实物板子存在之前，本族主张停留在设计目标。· **沉淀契约：** 调谐器状态模型与 49:1 vs LC 测试报告。 |

- [ ] **步骤 4：跑契约测试 + Commit**

```bash
cd /Users/cheenle/HAM/website/portal && python3 -m unittest tests.test_agentic_pages -v 2>&1 | tail -8
```

预期：`test_ontology_consumers_cite_real_constraint_rule_ids` **此刻转绿**；
`test_obsolete_top_level_counts_are_removed` 可能仍红（`Built Through Forward Deployed Engineering`
在 `index.html`、`One Field. Three Tracks.` 在旧 Hero），归任务 9 清除——属预期中间态。

```bash
cd /Users/cheenle/HAM/website && git add portal/agentic.html portal/zh/agentic.html \
  && git commit -m "feat(portal): 五产品族补智能体承担环节与人保留裁决字段（逐仓核实）"
```

---

## 任务 8：证据节双阶梯与 `ag-proc--*` 徽章（EN + ZH + CSS）

**文件：** 修改 `portal/agentic.html`、`portal/zh/agentic.html`、`portal/css/agentic.css`

- [ ] **步骤 1：CSS 新增第二色族（过程证据，紫灰；与产品成熟度色族视觉分离）**

追加到 `portal/css/agentic.css` 末尾：

```css
.ag-proc { display: inline-flex; align-items: center; gap: .35rem; padding: .15rem .55rem; border-radius: 999px; font-family: 'JetBrains Mono', monospace; font-size: .6875rem; letter-spacing: .02em; border: 1px solid; }
.ag-proc--registry { color: #a78bfa; border-color: rgba(167,139,250,.35); background: rgba(167,139,250,.08); }
.ag-proc--spec     { color: #818cf8; border-color: rgba(129,140,248,.35); background: rgba(129,140,248,.08); }
.ag-proc--enforced { color: #38bdf8; border-color: rgba(56,189,248,.35); background: rgba(56,189,248,.08); }
.ag-proc--blocked  { color: #34d399; border-color: rgba(52,211,153,.35); background: rgba(52,211,153,.08); }
```

- [ ] **步骤 2：在 `ag-legend` 之后插入阶梯 B 图例与说明（EN）**

```html
<div class="ag-legend" style="margin-top:1rem;" aria-label="Engineering process evidence levels">
  <span class="ag-proc ag-proc--registry">B1 constraint registry entry</span>
  <span class="ag-proc ag-proc--spec">B2 spec / plan trail</span>
  <span class="ag-proc ag-proc--enforced">B3 enforced in session</span>
  <span class="ag-proc ag-proc--blocked">B4 block verified</span>
</div>
<div class="ag-note ag-note--warning" style="margin-top:1rem;">
  <strong>The two ladders do not cross.</strong> The row above measures whether an engineering process was constrained; the row above it measures whether a product behaviour is true. A B4 badge never promotes an A-level claim, and no count of constraints makes a bench result less necessary.
</div>
```

- [ ] **步骤 3：插入「链条被实测复现」样本（EN）**

B4 已于 2026-09-02 在 `mrrc_ft710` 实测通过（越界片段 → `exit 2`），非推断。原文照录：

```html
<details class="ag-details" style="margin-top:1.25rem;">
  <summary>The chain, reproduced end to end (2026-09-02)</summary>
  <div class="ag-details-body"><pre class="ag-diagram"><code>$ python3 .agents/skills/sdd-guardian/harness/sdd_context.py check probe_b4_tmp.py
SDD-GUARDIAN: blocking violations found:
[BLOCK] cat-no-dn (AD-014; SDD V1.2 freq-drift incident) probe_b4_tmp.py:2: return c.query("DN;")
    → On the FT-710, 'DN;' is NOT a DNR query — it steps the active VFO DOWN ~20 Hz per call.
      Polling it caused a live frequency-drift incident (V1.2). DNR level is intentionally not polled.
$ echo $?
2</code></pre>
<p>A field incident became an SDD ruling, the ruling became a machine-readable constraint, and the constraint blocked an agent from re-introducing the incident. This is the claim this page makes, and it is reproducible.</p></div>
</details>
```

- [ ] **步骤 4：给三张有注册表的证据卡加过程徽章（EN）**

在 `ag-evidence-grid` 内 `MRRC FT-710`、`MRRC Modern`、`MRRC-FT8` 三张卡的第二个 `<p>` 末尾追加：

```html
<strong>Process evidence:</strong> <span class="ag-proc ag-proc--blocked">B4 block verified</span>
```

其余卡片（MRRC Universal、SunMRRC、EFHW）追加：

```html
<strong>Process evidence:</strong> <span class="ag-proc ag-proc--spec">B2 spec / plan trail</span>
```

**不得**给无注册表的族写 `B3`/`B4`。

- [ ] **步骤 5：ZH 对等**

阶梯 B 图例：`B1 约束注册表条目` / `B2 规格·计划留痕` / `B3 会话内强制执行` / `B4 阻断被验证`；
互推禁令 note 中文：「**两条阶梯不互推。**上一行衡量工程过程是否被约束，上一行之上衡量产品行为是否为真。B4 徽章不提升任何 A 级主张；约束条数再多，也不能减少一次台架验证的必要性。」
样本 `<summary>`：「这条链的端到端复现（2026-09-02）」，`<pre>` 内容**保持英文原样不译**（它是命令输出）。
过程徽章：`过程证据：` + 同上徽章类。

- [ ] **步骤 6：Commit**

```bash
cd /Users/cheenle/HAM/website && git add portal/agentic.html portal/zh/agentic.html portal/css/agentic.css \
  && git commit -m "feat(portal): 证据节引入阶梯 B 与 ag-proc 徽章，附实测阻断复现样本"
```

---

## 任务 9：机制分册重定位 + portal 首页方法论节（EN + ZH）

**文件：** `portal/engineering.html`、`portal/zh/engineering.html`、`portal/index.html`、`portal/zh/index.html`

- [ ] **步骤 1：`engineering.html` 降为「分册」（改 4 处，行号来自 2026-09-02 普查）**

| 行 | 现值 | 改为 |
| --- | --- | --- |
| 10 | `<title>Engineering System — Harness, Loops &amp; Living SDD \| VLSC</title>` | `<title>Engineering Mechanism — Harness, Loops &amp; Living SDD \| VLSC</title>` |
| 28 | badge `Engineering System · From Intent to Field Evidence` | `Mechanism Volume · Part of Agentic Engineering` |
| 57 | `<span class="eng-key">OUTER · FDE DELIVERY</span>` | `<span class="eng-key">OUTER · FDE DELIVERY LOOP</span>`（保留 FDE，补 loop 以与纲的口径一致） |
| 102 | `eng-cta` 一节 | 文案改为「机制如何服务于总纲」并指向 `/agentic.html`，链接文字 `FDE` → `Agentic Engineering` |

并在 `eng-hero` 之后插入分册面包屑（新增类 `ag-crumb`，样式在步骤 4）：

```html
    <div class="container"><nav class="ag-crumb" aria-label="Part of"><a href="/agentic.html"><i class="fas fa-arrow-left"></i> Agentic Engineering</a><span class="ag-crumb--here">Engineering mechanism</span></nav></div>
```

同文件的 `href="fde.html"` 已在**任务 2 步骤 5c** 改完（实测 3 处：导航 + 页尾 CTA + 页脚）；
本步只做验证 `grep -c 'fde\.html' engineering.html` 为 0，不重复改。

- [ ] **步骤 2：`zh/engineering.html` 同步**

`<title>` 第 8 行、badge 第 16 行、`eng-cta` 第 41 行按上表中文对等：
badge → `机制分册 · 属于智能体工程`；CTA 标题 → 「机制如何服务于总纲」；面包屑 → `← 智能体工程` / `工程机制`。
两处 `href="fde.html"` 同步改为 `href="/zh/agentic.html"`。

- [ ] **步骤 3：`portal/index.html` 方法论节重写（第 313–326 行 `<section>`）**

```html
<!-- Agentic Engineering -->
<section class="section" style="background: var(--bg-secondary);">
    <div class="container">
        <div class="section-header">
            <span class="section-label">Engineering</span>
            <h2 class="section-title">Built Through Agentic Engineering</h2>
            <p class="section-subtitle">Agents run the inner loop against written contracts; humans keep intent, boundaries and the final judgment. Field discipline produced those contracts — and still signs off what an agent cannot.</p>
        </div>
        <div style="text-align:center;">
            <a href="/agentic.html" class="btn btn-primary btn-large">
                <i class="fas fa-book"></i> Read the Agentic Engineering thesis
            </a>
        </div>
    </div>
</section>
```

中文 `zh/index.html` 第 277 行同一节：标题「由智能体工程构建」，副标「智能体依据成文契约执行工程内循环；人保留意图、边界与最终裁决。现场纪律产出了这些契约——它也仍然为智能体不能签字的部分放行。」，按钮「阅读智能体工程主张」→ `/zh/agentic.html`。

- [ ] **步骤 4：`ag-crumb` 样式**

追加到 `portal/css/agentic.css` 末尾：

```css
.ag-crumb{display:flex;gap:.75rem;align-items:center;flex-wrap:wrap;padding:.75rem 0;font-size:.8125rem;color:var(--text-secondary);}
.ag-crumb a{color:var(--accent);text-decoration:none;}
.ag-crumb--here{color:var(--text-muted);}
```

- [ ] **步骤 5：口径核对（不强制改文案）**

```bash
cd /Users/cheenle/HAM/website/portal && grep -n "Four Approaches\|four approaches\|三条轨道\|四个" index.html zh/index.html | cut -c1-120
```

若「Four Approaches」指四条**技术路径**（CAT / USB / UDP IQ / 原生客户端）则与产品族数不冲突，保留；
若被读成「四个产品族」则改为明确的技术路径措辞。判据：同节 `<p>` 是否逐条列举协议路径。

- [ ] **步骤 6：契约测试应全绿**

```bash
cd /Users/cheenle/HAM/website/portal && python3 -m unittest tests.test_agentic_pages -v 2>&1 | tail -6
```

预期 `OK`（任务 1 的全部断言此刻应成立，含 `test_obsolete_top_level_counts_are_removed` 里
`Built Through Forward Deployed Engineering` 与 `One Field. Three Tracks.` 两条 —— 后者若仍红，
说明 `index.html` 或 `about.html` 还留着旧 Hero 句，按步骤 7 清掉）。

- [ ] **步骤 7：清残留旧句**

```bash
cd /Users/cheenle/HAM/website/portal
grep -Rn "One Field. Three Tracks.\|一个领域，三条轨道" *.html zh/*.html
```

逐处改写为总纲口径（首页 Hero 若含此句，改为 `Agentic Engineering. Field Evidence.` /
「智能体工程 · 现场证据」），直到 grep 无输出。

- [ ] **步骤 8：Commit**

```bash
cd /Users/cheenle/HAM/website && git add portal/ && git commit -m "feat(portal): engineering 降为机制分册，首页方法论节改智能体工程口径"
```

---

## 任务 10：nginx 集中 301（B3，须与页面改名同批发布）

**文件：** 修改 `nginx/vlsc.net.conf`

- [ ] **步骤 1：确认插入点**

```bash
grep -n "Static asset caching" /Users/cheenle/HAM/website/nginx/vlsc.net.conf
```

锚点：`# ── Static asset caching (all sub-sites) ──` 那一行**之前**。
必须在缓存与 `location ~* \.html$` 块之前，否则 `return 301` 会被 regex location 抢走。

- [ ] **步骤 2：插入六条精确重定向**

```nginx
    # ── FDE → Agentic Engineering: canonical URL migrations (2026-09-02) ──
    location = /fde.html              { return 301 /agentic.html; }
    location = /zh/fde.html           { return 301 /zh/agentic.html; }
    location = /mrrc/fde.html         { return 301 /mrrc/agentic.html; }
    location = /mrrc/zh/fde.html      { return 301 /mrrc/zh/agentic.html; }
    location = /mrrc_modern/fde.html  { return 301 /mrrc_modern/agentic.html; }
    location = /mrrc_ft710/fde.html   { return 301 /mrrc_ft710/agentic.html; }
```

用 `location =`（精确匹配），不用 `rewrite`：六条都是整页改名，无路径变形。

- [ ] **步骤 3：语法校验 + 部署**

```bash
cd /Users/cheenle/HAM/website
scp nginx/vlsc.net.conf cheenle@www.vlsc.net:/tmp/
ssh cheenle@www.vlsc.net "sudo cp /tmp/vlsc.net.conf /etc/nginx/sites-available/vlsc.net && sudo nginx -t && sudo systemctl reload nginx"
```

预期 `nginx: configuration file ... test is successful`。
**若 `nginx -t` 失败，立刻停止**：不要把服务器留在失败配置上（`reload` 不会加载坏配置，但 `cp` 已覆盖）。
回滚：`ssh cheenle@www.vlsc.net "sudo cp /etc/nginx/sites-available/vlsc.net.bak /etc/nginx/sites-available/vlsc.net && sudo nginx -t && sudo systemctl reload nginx"`
—— 因此步骤 3 前先在服务器上留一份 `.bak`：

```bash
ssh cheenle@www.vlsc.net "sudo cp -n /etc/nginx/sites-available/vlsc.net /etc/nginx/sites-available/vlsc.net.bak"
```

---

## 任务 11：MRRC 站改名 + 术语层（B3.5）

**文件：** 站点根 `/Users/cheenle/HAM/MRRC/website`（经 `website/mrrc` 软链访问；仓库根 `/Users/cheenle/HAM/mrrc`）

- [x] **步骤 1：软链重指向 —— 规划阶段已完成并提交（`9ad7a21`）**

`website/mrrc` 已从失效的 `/Users/cheenle/UHRR/MRRC/website` 重指向 `/Users/cheenle/HAM/MRRC/website`。
执行本任务时**跳过此步**，只做验证：

```bash
cd /Users/cheenle/HAM/website && readlink mrrc && ls mrrc/agentic.html 2>/dev/null || ls mrrc/fde.html
```

- [ ] **步骤 2：改名 EN/ZH 长页**

```bash
cd /Users/cheenle/HAM/MRRC/website && git mv fde.html agentic.html && git mv zh/fde.html zh/agentic.html
```

- [ ] **步骤 3：23 文件 28 处导航链接批量改名**

```bash
cd /Users/cheenle/HAM/MRRC/website
FILES=$(grep -Rl 'fde\.html' --include=*.html --include=*.js .)
echo "$FILES" | wc -l          # 预期 23
LC_ALL=C sed -i '' \
  -e 's|\.\./\.\./fde\.html|../../agentic.html|g' \
  -e 's|\.\./fde\.html|../agentic.html|g' \
  -e 's|href="fde\.html"|href="agentic.html"|g' \
  -e "s|fde: '/fde.html',|agentic: '/agentic.html',|g" \
  -e "s|/\\\\/fde\\\\.html/|/\\\\/agentic\\\\.html/|g" \
  -e "s|SITE = 'fde'|SITE = 'agentic'|g" \
  -e "s|siteLink('fde', 'FDE')|siteLink('agentic', 'Agentic')|g" \
  -e '>FDE</a>|>Agentic</a>|g' \
  $FILES
grep -Rn "fde\.html" --include=*.html --include=*.js . | grep -v agentic | head
```

最后一条 grep 应无输出。`docs/design/*.html` 用 `../../fde.html`，`docs/*.html` 用 `../fde.html`，
顶层用 `fde.html` —— 三种相对深度都已在 sed 中覆盖，漏一种即出现 404。

- [ ] **步骤 4：§8.2 数字口径修复（`agentic.html` 内部）**

该页自述 `15 cycles`、`4 days`、`3 commits`、`17 files`、`Git-Verified` 均无 as-of 范围。逐处处理：

```bash
cd /Users/cheenle/HAM/MRRC/website
grep -n "15 cycles\|4 days\|3 commits\|17 files\|Git-Verified" agentic.html | head
```

规则：commit / 文件计数类**删除**并改为指向 portal 账本（`/agentic.html#evidence`）；
`15 cycles (Mar–Jun 2026)` 这类带时间窗的**保留但补 as-of 标注**：
`15 field cycles recorded Mar–Jun 2026 (historical; see the evidence ledger)`。

- [ ] **步骤 5：页尾加账本指针（该页无 portal 组件，用裸标签）**

```bash
cd /Users/cheenle/HAM/MRRC/website
python3 - <<'PY'
import pathlib, re
for p in ('agentic.html', 'zh/agentic.html'):
    t = pathlib.Path(p).read_text()
    link = ('<p style="text-align:center;margin-top:2rem;font-size:.85rem;opacity:.8;">'
            'Cross-project versions, test counts and release status live in the '
            '<a href="/agentic.html#evidence">VLSC evidence ledger</a> '
            '(single source of truth). 本页不再自述可比数字。'
            if p.startswith('zh') else
            '<p style="text-align:center;margin-top:2rem;font-size:.85rem;opacity:.8;">'
            'Cross-project versions, test counts and release status live in the '
            '<a href="/agentic.html#evidence">VLSC evidence ledger</a> '
            '(single source of truth). This page no longer self-reports comparable numbers.')
    assert '</body>' in t, f'no </body> in {p}'
    # 实测：mrrc 的 fde.html 与 zh/fde.html 均无 </main>，各有 1 个 </body>
    t2 = t.replace('</body>', link + '</p>\n</body>', 1)
    pathlib.Path(p).write_text(t2)
    print('inserted into', p)
PY
```

锚点已实测：`agentic.html` 与 `zh/agentic.html` 各含 0 个 `</main>`、1 个 `</body>`，故用 `</body>`。
插完跑 `grep -c 'evidence ledger' agentic.html zh/agentic.html`，预期各为 1。

- [ ] **步骤 6：Commit（落在 mrrc 仓库）**

```bash
git -C /Users/cheenle/HAM/mrrc add -A website && git -C /Users/cheenle/HAM/mrrc commit -m \
 "refactor(website): fde.html → agentic.html，导航术语 Agentic，跨站数字改指 portal 账本"
```

- [ ] **步骤 7：三种相对深度的独立复核（只验，不重复改）**

```bash
cd /Users/cheenle/HAM/MRRC/website
grep -Rn "fde\.html" --include=*.html --include=*.js . | grep -v agentic
```

预期：无输出。若有输出，说明步骤 3 的 sed 漏了某种相对深度（`../../`、`../`、裸名之外的第四种形态），
按实际输出补一条 sed 后重跑本步骤；**不要**放宽 grep、不要跳过。若步骤 6 已 commit，
把补充改动 `git add` 后用 `git commit --amend` 合入同一次提交
---

## 任务 12：两张子站长页（`mrrc_modern` · `mrrc_ft710`，B4）

**文件：** `/Users/cheenle/HAM/mrrc_modern/website/fde.html`、`/Users/cheenle/HAM/mrrc_ft710/website/fde.html`

**已实测：两文件各 1124 行、仅差 6 行**（第 8 行 meta、12 行 title、21 行 css 版本号）。
其余同文——所以过时数字在两站的行号一致（`348`、`501`、`636`），用一条循环处理。

- [ ] **步骤 1：改名（各自仓库）**

```bash
for r in /Users/cheenle/HAM/mrrc_modern /Users/cheenle/HAM/mrrc_ft710; do
  git -C "$r" mv website/fde.html website/agentic.html || echo "FAIL $r"; done
```

- [ ] **步骤 2：删/改三处过时数字（§8.2）**

```bash
for r in /Users/cheenle/HAM/mrrc_modern /Users/cheenle/HAM/mrrc_ft710; do
  cd "$r/website"
  # 8c 版「V1.0 to V2.1 — 16 days, 262 tests」：整句重写（实测在 348 行附近）
  # 501 行「12 FDE Cycles (Git-Verified)」：整节标题删除（规格 §8.2 规则 4）
  grep -n "V1.0) to multi-client\|12 FDE Cycles\|Git-Verified" agentic.html
done
```

预期每站 3 个命中。逐处按下面替换：

| 位置 | 原文 | 改为 |
| --- | --- | --- |
| ~348 | `(V1.0) to multi-client TX ownership fix (V2.1) — 16 days, 262 tests, 6` | `from first bring-up to the multi-client TX ownership fix — every step recorded in the <a href="/agentic.html#evidence">VLSC evidence ledger</a>, which owns version and test counts` |
| ~501 | `<h2 class="section-title">12 FDE Cycles (Git-Verified)</h2>` | `<h2 class="section-title">Field Signals, Version Steps</h2>`，并把其 `<p class="section-subtitle">` 补为定性描述：`Each field signal drove one version step. Counts and as-of dates live in the evidence ledger.` |
| ~636 | `<td>5 tests + <code>TX session:</code> logging</td>` | `<td>Automated tests + <code>TX session:</code> logging</td>` |

- [ ] **步骤 3：页内其余 `fde.html` 自链与术语**

```bash
for r in /Users/cheenle/HAM/mrrc_modern /Users/cheenle/HAM/mrrc_ft710; do
  cd "$r/website"
  LC_ALL=C sed -i '' -e 's|href="fde\.html"|href="agentic.html"|g' -e '>FDE</a>|>Agentic</a>|g' \
    index.html zh/index.html agentic.html 2>/dev/null
  grep -n "fde\.html" *.html zh/*.html js/*.js 2>/dev/null | grep -v agentic
done
```

最后一行应无输出。

- [ ] **步骤 4：新增「分工与资产」一节（两站同结构，文案按族区分）**

插在 `agentic.html` 主内容最后一个 `</section>` 之后。两页样式同源，用该页既有类名
（实测该类名存在于本页：`section` / `container` / `section-header`(**`div` 而非 `header`**) /
`section-label` / `section-title` / `section-subtitle` / `insight-grid` / `insight-card`。
**不要引入 portal 的 `ag-*` 类** —— 子站样式表里没有这些定义。）

```html
<section class="section" id="division">
  <div class="container">
    <div class="section-header">
      <span class="section-label">Division &amp; Contracts</span>
      <h2 class="section-title">What this repository hands an agent</h2>
      <p class="section-subtitle">And what it never lets the agent sign off.</p>
    </div>
    <div class="insight-grid">
      <div class="insight-card"><h3>Loaded before editing</h3><p><code>AGENTS.md</code> at the repo root, plus <code>.agents/skills/sdd-guardian/</code>: <NN> machine-readable constraints carrying severity, <code>sdd_ref</code>, scope globs and patterns. <code>SessionStart → prime</code> injects them; <code>PreToolUse(Edit|Write) → hook</code> blocks a violation before it lands.</p></div>
      <div class="insight-card"><h3>Human sign-off stays here</h3><p>PTT and TX authorization on real radios, PCB and bench bring-up, and whether the evidence supports a release label.</p></div>
      <div class="insight-card"><h3>Contract left behind</h3><p>The constraint registry and <code>harness/index.json</code>, which routes to live <code>SDD/*.md</code> slices and stores no content of its own, so it cannot go stale.</p></div>
    </div>
    <p style="margin-top:1.5rem;font-size:.85rem;opacity:.8;">Constraint count as of 2026-09-02. Cross-project comparable numbers live in the <a href="/agentic.html#evidence">VLSC evidence ledger</a>.</p>
  </div>
</section>
```

`<NN>` 分别填 **21**（modern）与 **17**（ft710）—— 用命令取，不要手写：

```bash
for r in /Users/cheenle/HAM/mrrc_modern /Users/cheenle/HAM/mrrc_ft710; do
  printf "%-16s " "$(basename $r)"; python3 -c "
import json;d=json.load(open('$r/.agents/skills/sdd-guardian/harness/constraints.json'))
print(len(d if isinstance(d,list) else d.get('rules',[])))"; done
```

- [ ] **步骤 5：Commit**

```bash
git -C /Users/cheenle/HAM/mrrc_modern add -A website && git -C /Users/cheenle/HAM/mrrc_modern commit -m \
 "refactor(website): fde → agentic，删过时 cycle/测试数，新增分工与资产节"
git -C /Users/cheenle/HAM/mrrc_ft710 add -A website && git -C /Users/cheenle/HAM/mrrc_ft710 commit -m \
 "refactor(website): fde → agentic，删过时 cycle/测试数，新增分工与资产节"
```

---

## 任务 13：四个子站各加一节「分工与资产」（B5，术语层已在任务 5）

**文件：** `efhw/index.html`、`sunmrrc/index.html`、`SunsdrMobile/index.html`、`mrrc_ft8/index.html`

**四站网格与卡片类名各不相同，不可共用模板。** 已实测：

| 站点 | 网格类 | 卡片类 | 站点根 |
| --- | --- | --- | --- |
| `efhw` | `arch-grid` | `arch-card` | `/Users/cheenle/HAM/website/efhw` |
| `sunmrrc` | `fx-grid` | `scope-card` | `/Users/cheenle/HAM/sunsdr/sunmrrc/website` |
| `SunsdrMobile` | `features-grid` | `scope-card`（实测 `SunsdrMobile/index.html:221-222`） | `/Users/cheenle/HAM/sunsdr/SunsdrMobile/website` |
| `mrrc_ft8` | `arch-grid` | `scope-card` | `/Users/cheenle/HAM/ft8/website` |

做法：复制**该页相邻一节**的骨架（`section` + `container` + `section-header`/`section-label`/
`section-title`/`section-subtitle` + 本站网格与卡片类），只替换标题与三张卡文案。

- [ ] **步骤 1：三张卡的固定内容（按族填，逐仓核实 2026-09-02）**

标题：`Division of Work and Contracts Left Behind` / 中文站用「分工与沉淀契约」。
四站均已有 `zh/index.html`（实测 2026-09-02），EN/ZH 两侧都要加同一节。

| 卡 | 文案要点 |
| --- | --- |
| 1 · Loaded before editing | `efhw`：workspace `CLAUDE.md`；**无**产品级 `AGENTS.md`、**无**约束注册表 → 只写「按站点契约执行」，不得写门禁。`sunmrrc`：`/Users/cheenle/HAM/sunsdr/AGENTS.md` + `CLAUDE.md` + `SDD/`；**无**注册表。`SunsdrMobile`：`CLAUDE.md`；**无**注册表。`mrrc_ft8`：`AGENTS.md` + 14 条注册表 + prime/hook（唯一可写门禁的四者之一） |
| 2 · Human sign-off | `efhw`：PCB 制板与台架验证（设计目标≠实测）。`sunmrrc`：逆向协议推断、非自家硬件上的 PTT。`SunsdrMobile`：App Store 发布、真机音频链路。`mrrc_ft8`：真实波段解码保真度、UTC 时隙 |
| 3 · Contract left behind | `efhw`：调谐器状态模型 + `efhw-knowledge/` 语料。`sunmrrc`：`PROTOCOL.md` 与 SDD 章节。`SunsdrMobile`：客户端能力边界描述。`mrrc_ft8`：`vendor-readonly`（`wsjtx-3.0.2/` 只读，改动走 `dsp/patched/`） |

- [ ] **步骤 2：每站加校验（改完立即跑，别攒到最后）**

```bash
cd /Users/cheenle/HAM/website
for p in efhw sunmrrc SunsdrMobile mrrc_ft8; do
  printf "%-14s division节:%s fde残留:%s\n" "$p" \
    "$(grep -c 'id="division"' $p/index.html)" "$(grep -c 'fde\.html' $p/index.html)"
done
for p in efhw sunmrrc SunsdrMobile mrrc_ft8; do
  printf "%-14s zh division节:%s\n" "$p" "$(grep -c 'id="division"' $p/zh/index.html)"
done
```

预期四站 `division节:1`、`fde残留:0`、`zh division节:1`。`efhw` 属 website 仓库，其余三站各自仓库。

- [ ] **步骤 2b：`efhw` 正文里的 FDE 提法（实测四站唯一命中，EN + ZH 各一处）**

四站 `index.html` / `zh/index.html` 均**无** `fde.html` 链接（导航全部由任务 5 改过的 JS 注入），
但 `efhw` 有一句正文把 FDE 与 SDD 并列为顶级体系：

- `efhw/index.html:560`：`SDD, FDE, reference designs, and community comparison.`
- `efhw/zh/index.html:547`：`SDD、FDE、参考设计和社区对比。`

改为（FDE 不再与 SDD 并列，且指向总纲）。EN：

```html
            <p class="section-subtitle">SDD, the Agentic Engineering thesis, reference designs, and community comparison. <a href="/agentic.html">Read the thesis →</a></p>
```

ZH：

```html
            <p class="section-subtitle">SDD、智能体工程总纲、参考设计与社区对比。<a href="/zh/agentic.html">阅读总纲 →</a></p>
```

```bash
cd /Users/cheenle/HAM/website/efhw
grep -n "FDE" index.html zh/index.html || echo "OK: efhw 正文 FDE 提法已处理"
```

- [ ] **步骤 3：Commit（分仓库）**

```bash
git -C /Users/cheenle/HAM/website add efhw/index.html efhw/zh/index.html \
  && git -C /Users/cheenle/HAM/website commit -m "feat(efhw): 新增分工与沉淀契约节"
git -C /Users/cheenle/HAM/sunsdr add sunmrrc/website/index.html sunmrrc/website/zh/index.html \
  && git -C /Users/cheenle/HAM/sunsdr commit -m "feat(sunmrrc): 新增分工与沉淀契约节"
git -C /Users/cheenle/HAM/sunsdr/SunsdrMobile add website/index.html website/zh/index.html \
  && git -C /Users/cheenle/HAM/sunsdr/SunsdrMobile commit -m "feat(sunsdrmobile): 新增分工与沉淀契约节"
git -C /Users/cheenle/HAM/ft8 add website/index.html website/zh/index.html \
  && git -C /Users/cheenle/HAM/ft8 commit -m "feat(mrrc-ft8): 新增分工与沉淀契约节"
```

**顺带记录（不在本轮修）：** `SunsdrMobile/index.html:163` 为
`<body data-site="sunsdrmobile" class="fx-grid">` —— `fx-grid` 疑似误挂在 `<body>` 上。
本轮只观察不修改，另立一条 issue
---

## 任务 14：规则回写 `CLAUDE.md` + sitemap + 全站终检（B6）

**文件：** 修改 `CLAUDE.md`（workspace 根），重跑 `portal/make_sitemap.py`

- [ ] **步骤 1：`CLAUDE.md` 新增一节**

在 `## Overview` 之后插入：

````markdown
## Site-wide editorial rules

### Agentic Engineering is the umbrella; FDE is one loop inside it

`/agentic.html` is the thesis page (EN + `zh/`). `/engineering.html` is the mechanism volume.
Forward Deployed Engineering (Echo → Delta → Product) stays documented inside §03 Lineage as the
predecessor that produced the contracts agents now load. Do not re-promote FDE as the top-level
brand, and do not delete it. Chinese term: 智能体工程 (never 代理式工程); FDE 中文统一为「前沿部署工程」.

### Facts have one owner

The portal Evidence section (`/agentic.html#evidence`) is the single source of truth for
cross-project comparable numbers: versions, test counts, release status, known defects.
Sub-sites keep their own architecture, module tables and protocol detail — they must not
self-report comparable numbers. Link to the ledger instead.

Never claim a product family was built by AI or agents. Process evidence (constraint registry,
spec trail, hooks, verified blocks) is graded separately from product maturity and never
promotes it. Repositories without `.agents/skills/sdd-guardian/` must not describe a pre-edit gate.

### Cross-site checks

Sub-site directories under `website/` are symlinks into other git repositories
(`mrrc/`, `mrrc_modern/`, `mrrc_ft710/`, `sunmrrc/`, `SunsdrMobile/`, `mrrc_ft8/`, `ft8/`);
`portal/`, `efhw/` and `nginx/` are real directories.

**Site-wide greps must list the site directories explicitly, each with a trailing slash.**
On this machine (macOS BSD grep) both `-r` and `-R` refuse to descend into symlinked
sub-directories when you search from `.`, so `grep -R pattern .` reports a clean tree while
every sub-site hit stays invisible — a silent false green. Use:

```bash
SITES="portal/ mrrc/ mrrc_ft710/ mrrc_modern/ sunmrrc/ SunsdrMobile/ mrrc_ft8/ efhw/"
grep -Rn "pattern" $SITES      # correct
grep -Rn "pattern" .           # WRONG: misses all symlinked sub-sites
grep -Rn "pattern" mrrc        # WRONG: bare symlink arg is not followed either
```

`find` needs the same care: use `find -L` to follow symlinks. Grepping `.` is only safe
after `cd` into a sub-site's real repository directory (e.g. `/Users/cheenle/HAM/MRRC/website`).
Commits go to the owning repository, not this one.
````

- [ ] **步骤 2：重生成 sitemap（勿手编）**

```bash
cd /Users/cheenle/HAM/website/portal && python3 make_sitemap.py
grep -n "agentic.html\|fde.html" sitemap.xml
```

预期：`/agentic.html` 与 `/zh/agentic.html` 各 1 行，`fde.html` **0 行**（旧名不进气清单，
由 nginx 301 兜住外部链接）。

- [ ] **步骤 3：全站终检（规格 §9）**

```bash
cd /Users/cheenle/HAM/website
python3 -m unittest discover -s portal/tests -p 'test_*.py' -v 2>&1 | tail -5
# skip 必须为 0：load_page 对缺失文件抛 SkipTest，任何 skip = 一条契约静默失效
python3 -m unittest discover -s portal/tests -p 'test_*.py' 2>&1 | grep -q skipped \
  && echo "!! 有契约测试被跳过，必须查清" || echo "OK: skip 0"
# 全站普查：必须逐个显式列出站点目录并带尾斜杠（见文首「普查铁律」）。
# 从 . 扫的 -r/-R 都进不去符号链接子站，会假绿通过。
SITES="portal/ mrrc/ mrrc_ft710/ mrrc_modern/ sunmrrc/ SunsdrMobile/ mrrc_ft8/ efhw/"
echo "--- 全站 fde.html 引用残留（应为 0）---"
grep -Rn "fde\.html" --include=*.html --include=*.js $SITES || echo "OK: 八站无 fde.html 引用"
echo "--- nginx 配置里的旧路径（应在 301 规则内，其余为 0）---"
grep -n "fde" nginx/vlsc.net.conf
echo "--- §9.5 数字一致性：portal 账本之外不得有第二处版本/测试数 ---"
grep -RnE "439 tests|262 tests|v1\.8\.1|v1\.12\.0" --include=*.html \
  mrrc/ mrrc_ft710/ mrrc_modern/ sunmrrc/ SunsdrMobile/ mrrc_ft8/ efhw/ \
  || echo "OK: 账本外无第二处可比数字"
echo "--- nginx 301 清单 ---"; grep -c "return 301 /.*agentic" nginx/vlsc.net.conf
```

预期：测试 `OK` **且 skip 为 0**（`load_page` 对缺失文件抛 `SkipTest`，任何 skip 都意味着一条
契约在静默失效，必须查明而不是容忍）；术语残留 grep 无输出（`promo-videos-long/shared/source-snapshots/` 是历史快照，
已排除、不改）；数字一致性输出 `OK: …`；301 计数为 **6**。

- [ ] **步骤 3b：本地 HTTP 冒烟 + 视觉与键盘核验（规格 §9.6 / §9.8，部署前必做）**

```bash
cd /Users/cheenle/HAM/website
python3 -m http.server 8099 --directory portal >/tmp/httpd.log 2>&1 &
sleep 1
for u in / /agentic.html /zh/agentic.html /engineering.html; do
  printf "%-22s %s\n" "$u" "$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8099$u)"
done
curl -s http://localhost:8099/agentic.html | grep -o 'id="[a-z]*"' | sort -u | wc -l
kill %1
```

预期 4 行 `200`、节 id 计数 **10**。然后开浏览器访问 `http://localhost:8099/agentic.html`，
逐项人工确认（这是清单，不是「看一眼」）：

| 检查项 | 1280px | 390px |
| --- | --- | --- |
| Hero 标题不截断、`gradient` 行不破版 | ☐ | ☐ |
| 锚点导航 8 项不溢出、可换行 | ☐ | ☐ |
| 本体 3 列宽表横向滚动而非溢出容器 | ☐ | ☐（滚动条可达） |
| 五族卡片追加 2 字段后卡片不被撑破 | ☐ | ☐ |
| 两类徽章 `ag-status--*` / `ag-proc--*` 视觉上可区分 | ☐ | ☐ |

键盘核验：`Tab` 聚焦 `<summary>` → `Enter`/`Space` 展开 → 确认 `aria-expanded` 翻转且内容可见。
最后跑 `lens_diagnostics mode=all`，确认无阻塞错误后才进入步骤 4。

- [ ] **步骤 4：部署（逐站 `deploy.sh`，按 CLAUDE.md 顺序）**

**发布顺序有硬约束：nginx 的 301 必须最后加载。** 否则 301 指向的新页还不存在，旧链接从「可读到」
变成「重定向到 404」——比不修更糟。正确顺序：

1. 先 deploy 全部 6 个含改名的站点（内容侧此时新旧并存：`agentic.html` 已上线，`fde.html` 文件已不在，
   外部旧链接短暂 404，窗口以秒计）；
2. 最后 copy nginx 配置 + `nginx -t` + `reload`，旧链接恢复可用并永久指向新页。

```bash
cd /Users/cheenle/HAM/website/portal && ./deploy.sh                       # 纲 + 目 + nginx 引用
git -C /Users/cheenle/HAM/mrrc config --get user.name >/dev/null         # 确认仓库可用后逐站部署
cd /Users/cheenle/HAM/MRRC/website     && ./deploy.sh
cd /Users/cheenle/HAM/mrrc_modern/website && ./deploy.sh
cd /Users/cheenle/HAM/mrrc_ft710/website  && ./deploy.sh
cd /Users/cheenle/HAM/ft8/website        && ./deploy.sh
cd /Users/cheenle/HAM/sunsdr/sunmrrc/website && ./deploy.sh
cd /Users/cheenle/HAM/sunsdr/SunsdrMobile/website && ./deploy.sh
cd /Users/cheenle/HAM/website/efhw      && ./deploy.sh
# ↓ 全部就位后才切 301
scp /Users/cheenle/HAM/website/nginx/vlsc.net.conf cheenle@www.vlsc.net:/tmp/
ssh cheenle@www.vlsc.net "sudo cp /tmp/vlsc.net.conf /etc/nginx/sites-available/vlsc.net && sudo nginx -t && sudo systemctl reload nginx"
ssh cheenle@www.vlsc.net "for u in /fde.html /zh/fde.html /mrrc/fde.html /mrrc/zh/fde.html /mrrc_modern/fde.html /mrrc_ft710/fde.html; do printf '%-24s %s\n' \"\$u\" \"\$(curl -sI https://www.vlsc.net\$u | grep -o 'HTTP/[0-9.]* [0-9]*')\"; done"
```

预期 6 行全部 `HTTP/2 301`。各站 `deploy.sh` 会提示确认并自动备份；备份路径记下来用于回滚。
已核实（2026-09-02）：8 站全部存在 `deploy.sh`，且 `grep -c fde deploy.sh` 全站为 **0** ——
没有任何部署脚本把 `fde.html` 列为必备文件，改名不会让 `deploy.sh` 失败。`portal/deploy.sh`
的 `REQUIRED_FILES` 只有 `index.html`、`zh/index.html`、`css/octen.css`。

- [ ] **步骤 5：Commit**

```bash
cd /Users/cheenle/HAM/website && git add CLAUDE.md portal/sitemap.xml \
  && git commit -m "docs: 回写全站编辑规则（事实单一来源、术语、符号链接普查约定）并重生成 sitemap"
```

---

## 附录 A：执行期补正记录（计划写完 ≠ 计划对）

本表按发现顺序记录**计划本身的缺陷**。每条都是执行时实测出来的，不是一次性写对的，
后续任何人重跑本计划须以本表为准。列含义：缺陷 → 若不修会怎样 → 已如何修。

| # | 缺陷 | 若不修的后果 | 处置 |
| --- | --- | --- | --- |
| 1 | 「用 `grep -R` 可跟符号链接」的普查约定在 macOS BSD grep 上不成立 | 全站扫描漏 184+ 处子站引用，**报告干净实则漏改** | 改为显式枚举站点目录且带尾斜杠；写进 §9.3 与 CLAUDE.md 草稿 |
| 2 | `test_engineering_pages.py` 全计划 0 次提及，其 `load_page` 对缺文件抛 `SkipTest` | 改名后 2 个契约用例**静默跳过**（skip 0→2），绿色里看不见覆盖率流失 | 任务 2 增 5b–5d 步 repoint；任务 14 加 skip 归零断言 |
| 3 | `git mv` 与大规模改写合并成一次提交 | 相似度跌破 git 默认阈值，`--follow` 追不到改名前历史 | 拆「纯改名（0 行增删）」+「内容改写」两提交，实测可追 4 个历史提交 |
| 4 | 计划遗漏 6 处旧名链接（导航自链、语言按钮、页脚各 3） | 404 | 任务 2 步骤 5a 补齐 |
| 5 | `engineering.html` 的 fde.html 引用是 3 处而非 2 处 | 漏 1 处 | 同上 |
| 6 | 任务 4 引用了不存在的测试方法名 | 该步直接挂 | 换成真实方法名 |
| 7 | 任务 3 步骤 4 只改 harness 的 id 与编号，**未移动到文档第 4 位** | 编号呈 `01 02 03 05 06 07 04 08 09 10`，锚点 Harness 往回跳 | 步骤 4 增加物理移动；验收改为「编号严格递增」 |
| 8 | 任务 4 步骤 4 的测试片段沿用 `leverage < harness` 旧序 | 与补正 7 冲突 → 该用例永红，且报错方向误导 | 片段改编码规格 §5.1 目标序 `lineage < harness < tracks` |
| 9 | 任务 4 步骤 1 漏列 ZH Hero 四枚计数 pill | 禁句清单不含 ZH 旧标题串与 pill 文案 → **一屏旧框架仍全绿** | ZH 同步命题 pill，`aria-label` 生态概览→命题概览 |
| 10 | `<title>` / description / keywords 全计划 0 次提及 | meta 是搜索与链接预览里唯一可见文案，结构断言全看不见 → 正文改完仍假绿 | 两页 meta 改伞形术语（FDE 按策略 B 退居关键词后位）；新增 `test_page_metadata_leads_with_new_umbrella` 固定成契约 |
| 11 | 假设 ZH 与 EN 版式一致（锚点导航独占一行） | 整行替换 `StopIteration`；改用 `re.S` + `</div></div>` 收口时因中间隔换行+缩进，**惰性匹配一路吞到文档后部**，删掉 `<main>` 起始 | ZH 侧改行内定位替换；HTML 一律禁用 `</div>…</div>` 作边界 |

### 由补正 10 得到的一般教训

新写的守卫**必须反向验证**：注入一次旧值，确认它真能被捕获，否则「测试变绿」
只说明断言没生效。本条已实测：把 ZH `<title>` 临时改回旧值后守卫确实报红，还原后转绿。

### 执行纪律（本次踩坑换出的三条）

1. 不得在同一批次里并发多个改写同一文件的调用。执行中三次犯此错：两次读到写入中途
   的残缺文件而报错，一次发出两个互相冲突的替换变体。改文件要么串行、要么合并成一次。
2. 不要用 git stash 查改名前的基线——会打断 rename 记录；读旧版一律 git show HEAD:<path>。
3. git mv 之后读守卫失效，紧随的首次编辑必须先 read。
