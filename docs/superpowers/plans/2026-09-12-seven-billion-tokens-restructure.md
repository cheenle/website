# 《七十亿 token 的全程拆解》系列重构 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）
> 或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 把一篇 19 节的长文重构为「主文 15 节 + 三册分册」的系列（EN + ZH 共 8 个 HTML），
全部数字刷新到 2026-09-12 census，并按已核实的术语表重写中文版用词。

**架构：** 纯静态 HTML/CSS，无构建步骤。主文 `/blog/seven-billion-tokens/` 保留因果链；
三册分册 `/blog/seven-billion-tokens/{ledger,almanac,playbook}/` 承载案例私有内容；
机制类内容仍归 `/engineering.html`。契约测试先行（先红后绿），测试同时是数字的机器可读副本。

**技术栈：** 纯静态 HTML/CSS/JS。测试运行器 **`/usr/bin/python3 -m pytest`**
（系统 Python 3.9.6 + pytest 8.4.2；仓库内 `portal/` 无 venv，只有系统 Python 能跑
`portal/tests/`）。**注意**：被测量的三个产品仓库**已改用各自的 venv**（见附录 A §A3）。

**规格：** `docs/superpowers/specs/2026-09-12-seven-billion-tokens-restructure-design.md`

---

## 本计划的适配说明（执行者必读）

这是**内容型任务**，不是代码型任务。计划的约束方式是：

- **结构**（section id、卷分组、语言镜像）→ 由契约测试逐条锁死
- **数字**（附录 A 的每一张表）→ 由契约测试逐字锁死
- **正文措辞** → 由每个任务的「本节必须包含」清单 + 术语表（附录 B）约束，
  执行者撰写；不提供逐字 HTML（8 个页面约 200KB，无法内联）
- **验证** → 一律靠跑测试，不靠目测

**禁止**为了凑结构而写空话：每节必须给出附录 A 中的真实数字或附录 A 中标注的具体事件。

## 红线（每个任务都隐含包含本节）

| # | 红线 |
|---|---|
| R1 | 绝不声称任何产品族由 AI / agent 建造。EN 禁句：`built by AI`、`built by agents`、`AI-built`、`AI wrote`、`agents built`；ZH 禁句：`代理式工程`、`由 AI 建造`、`由智能体建造`、`AI 打造`、`智能体建造了` |
| R2 | 只有 `mrrc_ft710`(17) / `mrrc_modern`(21) / `ft8`(14) 可描述编辑前门禁；MRRC / SunMRRC / SunsdrMobile / EFHW 必须明写"无机器可读约束注册表，因此不主张编辑前门禁" |
| R3 | FDE 只作为外环 `Echo → Delta → Product` 出现，不得提升为顶层品牌 |
| R4 | 中文术语：**智能体工程**（禁用"代理式工程"）；FDE = **前沿部署工程** |
| R5 | 跨项目可比数字（版本/测试数/发布状态/已知缺陷）唯一主人是 `/agentic.html#evidence`；**token 账本唯一主人是分册 A** |
| R6 | 每条声明带最小证据记录（来源工件 · 版本/commit · 环境 · 验证方法 · 结果 · 局限 · 日期） |
| R7 | 估算值与未记录值必须显式标注，**不得并入"已记录"合计**（iFlow ≈2.47 亿估算）；**且不得在未逐表核对前列为“未记录”**（本轮教训：Hermes 只查 `messages` 漏了 `sessions`，少算 4.85 亿） |
| R8 | **总额下降必须显式标注**；每个 harness 标注测量窗口 |
| R9 | 分册不得重复 `engineering.html` 的机制内容（Harness × Loop × Living SDD、五种工程边界、失败模式），交叉处只外链 |

**不得改动**：任何 `deploy.sh`、任何子站仓库、`nginx/`、`from-intent-to-delivery` 跳转壳。
**不部署**（部署由 `portal/deploy.sh` 单独执行，需 SSH 与人工确认）。

**提交纪律**：工作区有既有未提交改动（微信二维码有效期、`promo-videos*/`、`IMG_*`、
`ma.jpg`、`shot*.mp4`、`efhw/images/`、`portal/images/`、`mrrc_modern` 符号链接、
`.superpowers/`）。**每次 commit 前必须 `git diff --cached --stat` 确认只含本次改动。**

---

## 文件结构

**重写（2 个文件）**

| 路径 | 职责 |
|---|---|
| `portal/blog/seven-billion-tokens/index.html` | 主文 EN，15 节 / 6 卷 + 开篇 |
| `portal/blog/seven-billion-tokens/zh/index.html` | 主文 ZH，与 EN 结构逐节镜像 |

**新增（6 个文件）**

| 路径 | 职责 |
|---|---|
| `portal/blog/seven-billion-tokens/ledger/index.html` + `zh/index.html` | 分册 A《账本与测量边界》5 节 |
| `portal/blog/seven-billion-tokens/almanac/index.html` + `zh/index.html` | 分册 B《模型 × harness 年鉴》4 节 |
| `portal/blog/seven-billion-tokens/playbook/index.html` + `zh/index.html` | 分册 C《实践手册》4 节 |

**新增（2 个测试文件）**

| 路径 | 职责 |
|---|---|
| `portal/tests/test_seven_billion_tokens_article.py` | 主文契约（重写现有文件） |
| `portal/tests/test_seven_billion_tokens_companions.py` | 三册契约（参数化）+ 系列级一致性 |

**修改**

| 路径 | 改什么 |
|---|---|
| `portal/blog/index.html` | 主卡摘要改写 + 卡内三枚分册 chip |
| `portal/css/blog-article.css` | 新增 `.bc-chips`（本次唯一新增组件类），引用版本 `?v=2` → `?v=3` |
| `portal/sitemap.xml` | 由 `make_sitemap.py` 重生成（不手工编辑） |
| `portal/agentic.html`、`portal/zh/agentic.html` | **条件**：Modern 682 → 724、census 日期 2026-09-05 → 2026-09-12 |
| `portal/engineering.html`、`portal/zh/engineering.html` | **条件**：同上，仅 `633`/`682` 类数字与 census 日期 |

---

## 任务 0：数据底座冻结

**文件：**
- 不产生仓库内文件（脚本留在 `/tmp`，按 D3 不发布）
- 产出：本计划附录 A 的值被逐条确认或修正

- [ ] **步骤 1：重跑 census**

**先记录截止时间戳**（例如 `2026-09-12T02:30:00+08:00`）。它会写进分册 A，并成为全部
census 数字的限定词（见 §A1 的观察者效应说明）。

按 `docs/superpowers/specs/2026-09-05-seven-billion-tokens-article-design.md` §4 的字段语义
重算 7 个 harness。字段语义（不得改）：

| harness | 日志位置 | 取值字段 |
|---|---|---|
| claude-code | `~/.claude/projects/**/*.jsonl` → `message.usage` | `input_tokens + output_tokens + cache_creation_input_tokens + cache_read_input_tokens`（四桶互斥可加）；去重口径按 `message.id` |
| pi | `~/.pi/agent/sessions/**/*.jsonl` → `message.usage` | **`totalTokens`**（`input` 不含 `cacheRead`） |
| kimi-code | `~/.kimi-code/sessions/**/wire.jsonl` → `usage`（**仅 `usageScope=="turn"`**） | `inputOther + output + inputCacheRead + inputCacheCreation` |
| codex | `~/.codex/{sessions,archived_sessions}/**/*.jsonl` → `token_count.info.total_token_usage` | **`cached_input_tokens` 是 `input_tokens` 子集，不得另加**；每 session 取最后一次累计快照 |
| mulerun | `~/.mulerun/agent-data/opencode/opencode/opencode.db` → `session.tokens_*` | 五列相加（含 `tokens_reasoning`） |
| opencode | `~/.local/share/opencode/opencode.db` → `message.data.tokens.total`（role=assistant） | 该库 `session` 表**无** `tokens_*` 列 |
| cursor | `~/Library/Application Support/Cursor/User/globalStorage/state.vscdb` → `cursorDiskKV` key `bubbleId:%` | `tokenCount.inputTokens + outputTokens` |
| **Hermes** | `~/.hermes/state.db` → `sessions` | `input_tokens + output_tokens + cache_read_tokens + cache_write_tokens + reasoning_tokens`；**必查 `sessions` 表，不是 `messages.token_count`**（后者全 0） |
| **AgnesCode** | `~/.agnes/data/sessions/sessions.db` → `usage_ledger` | `total_tokens`；与 `sessions.accumulated_total_tokens` 互证 |
| **DeepSeek Harness** | `~/.dsh/sessions/*/*/session.jsonl.zstd` | zstd 解压后取 `data.chunk.usage` 的 `inputTokens+outputTokens+cacheReadTokens+reasoningTokens`（**不是顶层 `usage`**） |

> **主动搜索义务**：新增 harness 不会自己出现。重跑时必须用两个扫描工具（脚本留在 `/tmp`，不发布）：
> ① 扫全盘 SQLite：凡表名/列名含 `token` 且行数 >0 且求和非 0 即报出；
> ② 扫全盘 `*.jsonl` / `*.json`（>500KB）中含 `totalTokens|total_tokens|tokens_used|input_tokens|cached_tokens` 字段的文件。
> 已知应报出的三源：Hermes / AgnesCode / `.dsh`；已知应排除：Hermes `state-snapshots/`、
> Agnes `llm_request.*.jsonl`、`~/Library/Application Support/Qoder`（Cursor 重复子集）。

预期输出（2026-09-12 实测，见附录 A §A1）。若任何一行不同，**以重跑结果为准**并同步更新附录 A。

- [ ] **步骤 2：重跑上周过程指标**

范围 `2026-09-05 .. 2026-09-12`，按仓库归属（`cwd` → 仓库名；别名
`mrrc`→`MRRC`、`mrrc_ic7300`→`mrrc_modern`）。预期输出见附录 A §A2。
commit 计数必须用**明确定义且带时区的命令**并记录在案：

```bash
# ✅ 确定性：显式时区
git -C <repo> log --since='2026-09-05T00:00:00+08:00' --oneline | wc -l
# ❌ 禁止：裸日期被 git 解析为“那一天的此刻”，随查询时间变化
# git -C <repo> log --since=2026-09-05 --oneline | wc -l

git -C <repo> log --oneline | wc -l          # HEAD 口径（附录 A §A4 用这个）
```

- [ ] **步骤 3：复核产品数字（必须实跑，不得抄 CHANGELOG）**

```bash
cd /Users/cheenle/HAM/mrrc_ft710 && .venv/bin/python3 -m pytest -q
cd /Users/cheenle/HAM/mrrc_modern && .venv/bin/python3 -m pytest -q
cd /Users/cheenle/HAM/ft8 && venv/bin/python3 -m pytest -q
```

预期：`439 passed` / `724 passed, 8 subtests passed` / `935 passed, 1 skipped, 1 xfailed`。
**注意**：三个仓库已改用 venv（Python 3.13 + pytest 9.1.1）； `/usr/bin/python3` 会因
`X | None` 语法在收集期报 `TypeError`，**那不是产品缺陷**，不要写进文章。

- [ ] **步骤 4：复核约束注册表**

```bash
for d in mrrc_ft710 mrrc_modern ft8; do
  /usr/bin/python3 -c "import json;print(len(json.load(open('/Users/cheenle/HAM/$d/.agents/skills/sdd-guardian/harness/constraints.json'))['rules']))"
done
```

预期 `17 / 21 / 14`（合计 52，一周未增——这是**如实结论**，不是坏消息）。

- [ ] **步骤 5：把差异写回附录 A**

若步骤 1–4 的结果与附录 A 不符，**直接内联修正附录 A**，再继续。附录 A 是全计划唯一的
数字来源，后续所有任务只从附录 A 取值。

---

## 任务 1：主文契约测试先行（红）

**文件：**
- 修改：`portal/tests/test_seven_billion_tokens_article.py`（整体重写）
- 参考：现有文件保留 `ArticleParser`、`load()`、`section_body()` 三个工具函数原样

**接口：**
- 产出模块级常量，后续任务全部依赖这些**精确名字与值**：
  `REQUIRED_SECTIONS`、`VOLUMES`、`UNVOLUMED_SECTIONS`、`VOLUME_TITLES`、
  `EN_TITLE`、`ZH_TITLE`、`LEDGER_CONSTANTS`、`FORBIDDEN`、`GATE_OWNERS`、
  `GATE_FORBIDDEN_NEIGHBOURS`、`ESTIMATE_PROBES`、`ESTIMATE_LABELS`、
  `NO_MERGE_PHRASE`、`DUAL_CALIBER_NOTE`、`CANONICAL`

- [ ] **步骤 1：改写常量与断言**

```python
REQUIRED_SECTIONS = {
    # 开篇（不属卷）
    "ledger-shrank",
    # 卷 I · 意图
    "intents", "control-group",
    # 卷 II · 过程
    "intervention", "unit-cost", "rework", "cadence",
    # 卷 III · 方法
    "method-timeline", "incident-chains", "evidence-ledgers",
    # 卷 IV · 模型
    "model-shift",
    # 卷 V · 归因
    "attribution", "advice", "closing",
    # 卷 VI · 四维度
    "four-dimensions",
}

VOLUMES = (
    ("intent", ("intents", "control-group")),
    ("process", ("intervention", "unit-cost", "rework", "cadence")),
    ("method", ("method-timeline", "incident-chains", "evidence-ledgers")),
    ("models", ("model-shift",)),
    ("verdict", ("attribution", "advice", "closing")),
    ("dimensions", ("four-dimensions",)),
)
UNVOLUMED_SECTIONS = ("ledger-shrank",)

EN_TITLE = "Seven Billion Tokens, Dissected: The Ledger That Shrank"
ZH_TITLE = "七十亿 token 的全程拆解：一本会倒退的账"

VOLUME_TITLES = {
    "en": {
        "intent": "Intent never starts with",
        "process": "From round-trips to right-first-time",
        "method": "What the harness and the SDD did at each stage",
        "models": "The model is not the long-term variable",
        "verdict": "Where the efficiency actually came from",
        "dimensions": "Separate judgment from execution",
    },
    "zh": {
        "intent": "意图从不以",
        "process": "从「来来回回」到「一次做对」",
        "method": "harness 与 SDD 在各阶段的作用",
        "models": "模型不是长期变量",
        "verdict": "效率究竟从哪里来",
        "dimensions": "把判断从执行中分离",
    },
}
```

- [ ] **步骤 2：写死新数字常量**

> **常量范围原则**：`LEDGER_CONSTANTS` 里的**每一个值都必须真实出现在主文中**
> （测试逐字断言它存在于主文 EN + ZH）。只属于分册的数字（完整账本表、测量边界、模型年鉴）
> 定义在各自分册的常量里（任务 4/5 的 `LEDGER_TABLE`、`BOUNDARY_CONSTANTS`），
> **不得塞进这里**。
```python
LEDGER_CONSTANTS = {
    # 双口径门面（附录 C1 的 ledger-shrank 节）
    "published_line_census": "7,007,437,567",
    "recomputed_line_census": "7,404,583,808",
    "recomputed_dedup_census": "5,695,506,675",
    "delta_vs_published": "397,146,241",
    # 两个方向的误差各一个代表数
    "claude_dedup_census": "818,520,401",
    "hermes_tokens": "485,213,348",
    "codex_tokens": "547,796,667",
    # 对照期（不变）
    "iflow_turns": "37,202",
    "iflow_sessions": "185",
    "glm5_peak_week_turns": "10,420",
    # 上周过程指标
    "modern_week_commits": "41",
    "modern_week_fix_share": "41%",
    "modern_week_human_per_commit": "0.73",
    "modern_week_megatokens_per_commit": "5.95",
    "website_week_commits": "35",
    "website_week_fix_share": "23%",
    "website_week_human_per_commit": "2.43",
    "mrrc_week_megatokens_per_commit": "47.07",
    "mrrc_week_human_per_commit": "6.00",
    # 历史过程指标（不变，须逐字保留）
    "intervention_drop": "17.1 → 0.3",
    "ft8_peak_unit_cost": "75.5",
    "ft8_maintenance_unit_cost": "0.9",
    "red_green_median_minutes": "19",
    # 方法
    "constraints_total": "52",
    "constraints_split": "ft710 17 / modern 21 / ft8 14",
    "incident_ft710_days": "13",
    "incident_backup_days": "7",
    # 产品（2026-09-12 实跑）
    "tests_ft710": "439",
    "tests_modern": "724",
    "tests_ft8": "935",
    "modern_version": "v1.14.3",
    # 模型
    "claude_top_model": "qwen3.8-max-0902",
    "pi_new_model": "glm-5.3-flash",
    # 缓存经济
    "cache_read_share": "93.7%",
    "cache_subset_share": "83.5%",
    # 日期
    "census_date": "2026-09-12",
}
# 已移入分册、**不再属于主文常量**的值（防止误加回主文）：
#   claude_line / claude_api_ids / pi_tokens / kimi_tokens / mulerun_tokens /
#   cursor_tokens / opencode_tokens / hermes_window / agnes_tokens / dsh_tokens
#                                                     → 任务 4 LEDGER_TABLE
#   mrrc_w25_doubtful / commit_class_error            → 任务 4 BOUNDARY_CONSTANTS
#   models_era_count                                  → 任务 5 ALMANAC_CONSTANTS
#   mrrc_tag                                          → 不写入文章（R5：版本归 /agentic.html#evidence）
```

- [ ] **步骤 3：改写断言**

保留原文件的这些测试（只改常量与结构，逻辑不动）：
`test_articles_and_css_exist`、`test_sections_and_claim_types_match`、
`test_ledger_constants_appear_verbatim`、`test_estimates_are_labelled`、
`test_recorded_and_estimated_ledgers_are_not_merged`、`test_gate_claims_only_near_owning_repos`、
`test_forbidden_phrases_absent`、`test_zh_uses_mandated_terminology`、
`test_titles_are_bilingual`、`test_volumes_group_sections_correctly`、
`test_distillation_layer_is_present`、`test_chain_reproduction_block_is_present`、
`test_ids_and_local_assets_are_valid`、`test_seo_language_links_and_json_ld_are_complete`、
`test_links_to_thesis_and_mechanism_pages`。

**删除**：`test_dual_caliber_is_presented_side_by_side`（移到分册 A 测试）、
`test_blog_index_lists_article`、`test_sitemap_lists_both_languages`（移到 Task 8）。

**新增两条**：

```python
    def test_main_article_owns_no_ledger_tables(self) -> None:
        """R5: 账本表唯一主人是分册 A；主文只许引结论句。"""
        for language, path in ARTICLES.items():
            source, _ = load(path)
            for token in ("7,007,437,567", "7,404,583,808", "5,695,506,675"):
                self.assertIn(token, source, f"{language}: {token}")
            self.assertLess(source.count("<table"), 8, f"{language}: 主文表格过多，账本/年鉴应外链")

    def test_date_modified_is_census_date(self) -> None:
        for language, path in ARTICLES.items():
            _source, parser = load(path)
            data = [i for i in parser.json_ld if i.get("@type") == "Article"][0]
            self.assertEqual("2026-09-12", data["dateModified"], language)
            self.assertEqual("2026-09-05", data["datePublished"], language)
```

- [ ] **步骤 4：运行测试确认失败**

运行：`cd /Users/cheenle/HAM/website/portal && /usr/bin/python3 -m pytest tests/test_seven_billion_tokens_article.py -q`
预期：FAIL（`REQUIRED_SECTIONS` 与实际不符、新数字找不到）

- [ ] **步骤 5：Commit**

```bash
cd /Users/cheenle/HAM/website
git add portal/tests/test_seven_billion_tokens_article.py
git diff --cached --stat        # 确认只含这一个文件
git commit -m "test(blog): 主文契约改为 15 节/6 卷 + 2026-09-12 census 常量"
```

---

## 任务 2：主文 EN 重写

**文件：**
- 重写：`portal/blog/seven-billion-tokens/index.html`
- 输入：附录 A（数字）、附录 B（术语）、附录 C（每节必须包含）

- [ ] **步骤 1：写 head 与门面**

`<title>` / `og:title` / JSON-LD `headline` 都用 `EN_TITLE`；`datePublished` 保持
`2026-09-05`，`dateModified` 改 `2026-09-12`；三条 hreflang 与 canonical 不变
（`https://www.vlsc.net/blog/seven-billion-tokens/`）。hero 三枚 pill 改成：

```html
<span class="ag-pill"><i class="fas fa-database"></i> 7,404,583,808 recorded tokens</span>
<span class="ag-pill"><i class="fas fa-arrow-trend-up"></i> +397,146,241 vs the published census</span>
<span class="ag-pill"><i class="fas fa-shield-halved"></i> 52 machine-readable constraints</span>
```

- [ ] **步骤 2：写 TL;DR 卡（5 条带标签结论 + 速读路径）**

必须保持 `class="ba-tldr"`、5 个 `class="ba-tldr-tag"`、以及指向 `#four-dimensions` 的速读路径
（测试断言依赖）。5 条结论按附录 C §C1。

- [ ] **步骤 3：按卷写正文**

逐卷写，每卷末尾一条 `class="volume-takeaway"`（**共 5 条，卷六不加**）。每节的
「必须包含」清单见附录 C §C1。**不得**把附录 A §A1 的账本表整表搬进主文（R5）。

- [ ] **步骤 4：写附录外链与页脚**

正文末尾保留 Related pages（`/agentic.html`、`/engineering.html`）与产品族链接；
新增三册链接：`ledger/`、`almanac/`、`playbook/`。

- [ ] **步骤 5：运行局部测试**

运行：`cd /Users/cheenle/HAM/website/portal && /usr/bin/python3 -m pytest tests/test_seven_billion_tokens_article.py -q -k "not zh"`
预期：EN 相关断言通过（ZH 仍红）

- [ ] **步骤 6：Commit**

```bash
git add portal/blog/seven-billion-tokens/index.html
git diff --cached --stat
git commit -m "feat(blog): 主文 EN 重写——开篇改为会倒退的账本，压缩至 15 节"
```

---

## 任务 3：主文 ZH 重写

**文件：**
- 重写：`portal/blog/seven-billion-tokens/zh/index.html`

- [ ] **步骤 1–4：与任务 2 逐节镜像**

**ZH 独有的强制要求**（附录 B）：

1. token 量一律「亿 tokens」：`7,404,583,808` → 「74.0 亿 tokens」但**快照数字保留原样**
   （`7,007,437,567` 等原样，因为它是对外可核对的账本值）
2. 不造词：不得出现"沉淀地"；改「知识的载体」
3. 引号用「」；中英文之间保留半角空格
4. 首现加注：`harness`（智能体框架）、`token`（词元）、`SDD`（规格驱动开发）、
   `FDE`（前沿部署工程）、`PTT`、`CAT`
5. 四个动词严格分工：**委托 / 拦截 / 沉淀 / 裁决**
6. 禁句不得出现：`代理式工程`

- [ ] **步骤 5：运行测试**

运行：`cd /Users/cheenle/HAM/website/portal && /usr/bin/python3 -m pytest tests/test_seven_billion_tokens_article.py -q`
预期：PASS

- [ ] **步骤 6：Commit**

```bash
git add portal/blog/seven-billion-tokens/zh/index.html
git diff --cached --stat
git commit -m "feat(blog): 主文 ZH 重写并统一术语（智能体工程/规格驱动开发/亿 tokens）"
```

---

## 任务 4：分册 A《账本与测量边界》

**文件：**
- 创建：`portal/blog/seven-billion-tokens/ledger/index.html`、`ledger/zh/index.html`

- [ ] **步骤 1：写契约测试（先红）**

新建 `portal/tests/test_seven_billion_tokens_companions.py`，先只填分册 A：

```python
import json
import re
import unittest
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

PORTAL = Path(__file__).resolve().parents[1]
SERIES_ROOT = PORTAL / "blog" / "seven-billion-tokens"
BLOG_INDEX = PORTAL / "blog" / "index.html"
SITEMAP = PORTAL / "sitemap.xml"
COMPANION_CSS = PORTAL / "css" / "blog-article.css"

COMPANIONS = {
    "ledger": {
        "sections": {"census", "window", "repos", "boundaries", "verify"},
        "slug": "ledger",
        "title_en": "The Ledger and Its Measurement Boundaries",
        "title_zh": "账本与测量边界",
    },
    # 任务 5、6 追加 almanac / playbook
}


def companion_paths(slug: str):
    """产出 (language, path) 对，EN 在前、ZH 在后。"""
    root = SERIES_ROOT / COMPANIONS[slug]["slug"]
    return (("en", root / "index.html"), ("zh", root / "zh" / "index.html"))


CANONICAL = {
    slug: {
        "en": f"https://www.vlsc.net/blog/seven-billion-tokens/{spec['slug']}/",
        "zh": f"https://www.vlsc.net/blog/seven-billion-tokens/{spec['slug']}/zh/",
    }
    for slug, spec in COMPANIONS.items()
}

# R2：与主文测试同源同值（两文件各自复制一份，改动时两处同步）
GATE_OWNERS = ("mrrc_ft710", "mrrc_modern", "ft8", "FT-710", "Modern", "MRRC-FT8")
GATE_FORBIDDEN_NEIGHBOURS = ("SunMRRC", "SunsdrMobile", "EFHW", "MRRC Universal")
ARTICLES = {
    "en": SERIES_ROOT / "index.html",
    "zh": SERIES_ROOT / "zh" / "index.html",
}
```

> `ArticleParser` / `load()` / `section_body()` 从
> `tests/test_seven_billion_tokens_article.py` **复制一份**（两份测试文件不共享模块，
> 以符合仓库现有“一文章一测试文件”惯例；改动时两处同步）。

断言（参数化，对每册每语言跑一遍）：section id 集合相等、`data-claim-type`
⊆ {fact, inference, thesis} 且三者均出现、canonical 唯一、三条 hreflang 齐全、
JSON-LD `Article` 字段完整、本地资源可解析、id 无重复。

分册 A 专有常量与断言（**这些值不得出现在主文常量里**）：

```python
LEDGER_TABLE = {
    "claude_line": "2,527,597,534",
    "claude_dedup": "818,520,401",
    "claude_api_ids": "6,600",
    "claude_window": "2026-08-08 .. 2026-09-08",
    "pi_tokens": "1,926,003,139",
    "kimi_tokens": "1,254,875,254",
    "mulerun_tokens": "537,961,611",
    "hermes_tokens": "485,213,348",
    "hermes_window": "2026-05-15 .. 2026-07-24",
    "agnes_tokens": "82,931,675",
    "agnes_window": "2026-07-13 .. 2026-07-26",
    "cursor_tokens": "27,079,705",
    "dsh_tokens": "10,931,069",
    "opencode_tokens": "4,190,890",
    "iflow_estimate": "247,000,000",
    "last_cleanup": "2026-09-07T13:13:57Z",
    "codex_crosscheck": "546,858,767",
    "observer_effect_delta": "51,427,037",
    "census_cutoff": "2026-09-12T02:40:59Z",
}
BOUNDARY_CONSTANTS = {
    "mrrc_w25_doubtful": "27.6",
    "commit_class_error": "±10%",
    "census_date": "2026-09-12",
}

    def test_ledger_owns_dual_caliber(self) -> None:
        for language, path in companion_paths("ledger"):
            source, _ = load(path)
            missing = [f"{k}={v}" for k, v in LEDGER_TABLE.items() if v not in source]
            self.assertEqual([], missing, language)
            missing = [f"{k}={v}" for k, v in BOUNDARY_CONSTANTS.items() if v not in source]
            self.assertEqual([], missing, language)
            self.assertIn("message.id", source, language)
            self.assertIn("must not be merged" if language == "en" else "不合并", source, language)

    def test_dual_caliber_is_presented_side_by_side(self) -> None:
        for language, path in companion_paths("ledger"):
            source, _ = load(path)
            body = section_body(source, "census", language)
            self.assertIn("2,527,597,534", body, language)
            self.assertIn("818,520,401", body, language)
            self.assertIn("message.id", body, language)
```

- [ ] **步骤 2：运行确认失败**

运行：`cd /Users/cheenle/HAM/website/portal && /usr/bin/python3 -m pytest tests/test_seven_billion_tokens_companions.py -q`
预期：FAIL（文件不存在 → `SkipTest` 或断言失败）

- [ ] **步骤 3：写 EN 与 ZH 正文**

五节内容按附录 C §C2。`census` 节必须给完整的 7 行 harness 表（含**每行窗口**），
`window` 节必须给 claude-code 的清理证据（`~/.claude/.last-cleanup` = `2026-09-07T13:13:57Z`）
与 codex 的"逐位不变"交叉校验（`547,796,667`）。

- [ ] **步骤 4：运行测试确认通过**

运行：`cd /Users/cheenle/HAM/website/portal && /usr/bin/python3 -m pytest tests/test_seven_billion_tokens_companions.py -q -k ledger`
预期：PASS

- [ ] **步骤 5：Commit**

```bash
git add portal/blog/seven-billion-tokens/ledger portal/tests/test_seven_billion_tokens_companions.py
git diff --cached --stat
git commit -m "feat(blog): 新增分册 A《账本与测量边界》——滑动窗口实证与双口径"
```

---

## 任务 5：分册 B《模型 × harness 年鉴》

**文件：**
- 创建：`portal/blog/seven-billion-tokens/almanac/index.html`、`almanac/zh/index.html`

- [ ] **步骤 1：追加 page spec 与断言**

```python
    "almanac": {
        "sections": {"eras", "shift", "benchmarks", "routing"},
        "slug": "almanac",
        "title_en": "The Model × Harness Almanac",
        "title_zh": "模型 × harness 年鉴",
    },
```

- [ ] **步骤 2：运行确认失败**

运行：`/usr/bin/python3 -m pytest tests/test_seven_billion_tokens_companions.py -q -k almanac`
预期：FAIL

- [ ] **步骤 3：写 EN 与 ZH 正文**

四节内容按附录 C §C3。`shift` 节必须给出附录 A §A5 的模型调用计数表；
`benchmarks` 节必须把**独立评测**与**厂商口径**分成两层写（不得混排）；
`routing` 节必须点名 `big-pickle`、`code-supernova-1-million`、`kimi-for-coding` 三个路由标签。

- [ ] **步骤 4：运行测试确认通过 + Commit**

```bash
/usr/bin/python3 -m pytest tests/test_seven_billion_tokens_companions.py -q -k almanac
git add portal/blog/seven-billion-tokens/almanac portal/tests/test_seven_billion_tokens_companions.py
git diff --cached --stat
git commit -m "feat(blog): 新增分册 B《模型 × harness 年鉴》——主力一周切换实证"
```

---

## 任务 6：分册 C《实践手册》

**文件：**
- 创建：`portal/blog/seven-billion-tokens/playbook/index.html`、`playbook/zh/index.html`

- [ ] **步骤 1：追加 page spec 与断言**

```python
    "playbook": {
        "sections": {"disciplines", "checklists", "templates", "incidents"},
        "slug": "playbook",
        "title_en": "The Practitioner's Playbook",
        "title_zh": "实践手册",
    },
```

分册 C 专有断言（R9，防止重复 `engineering.html`）：

```python
    def test_playbook_does_not_duplicate_mechanism(self) -> None:
        banned = ("Harness × Loop", "Living SDD", "五种工程边界", "five engineering boundaries")
        for language, path in companion_paths("playbook"):
            source, _ = load(path)
            for phrase in banned:
                self.assertNotIn(phrase, source, f"{language}: R9 — 机制内容归 engineering.html")
            self.assertIn("/engineering.html", source, language)
```

- [ ] **步骤 2：运行确认失败**

运行：`/usr/bin/python3 -m pytest tests/test_seven_billion_tokens_companions.py -q -k playbook`
预期：FAIL

- [ ] **步骤 3：写 EN 与 ZH 正文**

四节内容按附录 C §C4。**硬要求**：`checklists` / `templates` / `incidents` 三节的每一条
必须能指向一个真实事故或裁决（附录 A §A6），不得出现空泛建议。

- [ ] **步骤 4：运行测试确认通过 + Commit**

```bash
/usr/bin/python3 -m pytest tests/test_seven_billion_tokens_companions.py -q -k playbook
git add portal/blog/seven-billion-tokens/playbook portal/tests/test_seven_billion_tokens_companions.py
git diff --cached --stat
git commit -m "feat(blog): 新增分册 C《实践手册》——清单/模板/案例事故库"
```

---

## 任务 7：系列级一致性测试

**文件：**
- 修改：`portal/tests/test_seven_billion_tokens_companions.py`

- [ ] **步骤 1：写一致性断言**

```python
    def test_series_links_are_reciprocal(self) -> None:
        """主文挂三册；三册回链主文与彼此。"""
        for slug in ("ledger", "almanac", "playbook"):
            for language, path in companion_paths(slug):
                source, _ = load(path)
                self.assertIn("..", source, slug)          # 回主文
                self.assertIn("/blog/", source, slug)

    def test_shared_numbers_match_the_main_article(self) -> None:
        """同一事实在两个页面出现时必须同值。"""
        en_main, _ = load(ARTICLES["en"])
        shared = ("7,404,583,808", "5,695,506,675", "485,213,348", "52", "0.73")
        for slug in ("ledger", "almanac", "playbook"):
            for language, path in companion_paths(slug):
                source, _ = load(path)
                for token in shared:
                    if token in source:
                        self.assertIn(token, en_main,
                                      f"{slug}/{language}: {token} 只在分册出现，主文缺")

    def test_no_companion_claims_a_gate_it_does_not_own(self) -> None:
        """R2 在分册同样生效。"""
        pattern = re.compile(r"pre-edit gate|编辑前门禁|编辑前拦截|PreToolUse")
        for slug in ("ledger", "almanac", "playbook"):
            for language, path in companion_paths(slug):
                source, _ = load(path)
                for match in pattern.finditer(source):
                    window = source[max(0, match.start() - 700): match.start() + 700]
                    self.assertTrue(any(o in window for o in GATE_OWNERS), f"{slug}/{language}")
                    for bad in GATE_FORBIDDEN_NEIGHBOURS:
                        self.assertNotIn(bad, window, f"{slug}/{language}: R2")

    def test_terminology_ban_holds_series_wide(self) -> None:
        for slug in ("ledger", "almanac", "playbook"):
            for language, path in companion_paths(slug):
                source, _ = load(path)
                self.assertNotIn("代理式工程", source, f"{slug}/{language}")
                self.assertNotIn("沉淀地", source, f"{slug}/{language}")
```

- [ ] **步骤 2：运行全部测试**

运行：`cd /Users/cheenle/HAM/website/portal && /usr/bin/python3 -m pytest tests/ -q`
预期：**全部 PASS**（含既有的 `test_agentic_pages.py`、`test_engineering_pages.py`、
`test_connections_article.py`、`test_from_intent_to_delivery_article.py`、`test_sitemap.py`）

- [ ] **步骤 3：Commit**

```bash
git add portal/tests/test_seven_billion_tokens_companions.py
git diff --cached --stat
git commit -m "test(blog): 系列级一致性——跨页数字同值、R2/R9 与术语禁句全系列生效"
```

---

## 任务 8：博客首页与 sitemap

**文件：**
- 修改：`portal/blog/index.html`、`portal/sitemap.xml`

- [ ] **步骤 1：改主卡**

主卡标题/日期字符串**不动**（既有测试断言依赖 `Seven Billion Tokens` 与 `Sep 5, 2026`）；
只改 `bc-excerpt` 摘要为新主文结论，并在卡内加三枚分册 chip：

```html
<div class="bc-chips">
  <a href="/blog/seven-billion-tokens/ledger/">Ledger</a>
  <a href="/blog/seven-billion-tokens/almanac/">Almanac</a>
  <a href="/blog/seven-billion-tokens/playbook/">Playbook</a>
</div>
```

- [ ] **步骤 2：加 chip 样式**

在 `portal/css/blog-article.css` 末尾追加（仅此一个组件类，不新建文件）：

```css
/* 系列 chip：主卡内导向三册分册 */
.bc-chips { display: flex; flex-wrap: wrap; gap: .5rem; margin-top: .75rem; }
.bc-chips a {
  font-family: var(--font-mono, ui-monospace, monospace);
  font-size: .75rem; letter-spacing: .02em;
  padding: .2rem .6rem; border-radius: 999px;
  border: 1px solid var(--accent, #22d3ee);
  color: var(--accent, #22d3ee); text-decoration: none;
}
.bc-chips a:hover { background: var(--accent, #22d3ee); color: #0a0e14; }
```

并把 `portal/blog/index.html` 引用的 `blog-article.css?v=2` 改为 `?v=3`
（四个系列页面同步）。

- [ ] **步骤 3：重生成 sitemap**

运行：`cd /Users/cheenle/HAM/website/portal && python3 make_sitemap.py`
预期：`sitemap.xml` 新增 6 个 URL（三册 × EN/ZH）

- [ ] **步骤 4：把博客首页/sitemap 断言加回测试**

在 `test_seven_billion_tokens_companions.py` 补：

```python
    def test_blog_index_lists_series(self) -> None:
        source = BLOG_INDEX.read_text(encoding="utf-8")
        for path in ("/blog/seven-billion-tokens/",
                     "/blog/seven-billion-tokens/ledger/",
                     "/blog/seven-billion-tokens/almanac/",
                     "/blog/seven-billion-tokens/playbook/"):
            self.assertIn(path, source, path)

    def test_sitemap_lists_all_four_pages_both_languages(self) -> None:
        source = SITEMAP.read_text(encoding="utf-8")
        for slug in ("", "ledger/", "almanac/", "playbook/"):
            base = f"https://www.vlsc.net/blog/seven-billion-tokens/{slug}"
            self.assertIn(base, source, base)
            self.assertIn(base + "zh/", source, base + "zh/")

    def test_chips_class_is_styled(self) -> None:
        self.assertIn(".bc-chips", COMPANION_CSS.read_text(encoding="utf-8"))
```

- [ ] **步骤 5：运行测试**

运行：`/usr/bin/python3 -m pytest tests/ -q`
预期：PASS

- [ ] **步骤 6：Commit**

```bash
git add portal/blog/index.html portal/css/blog-article.css portal/sitemap.xml \
        portal/tests/test_seven_billion_tokens_companions.py
git diff --cached --stat
git commit -m "feat(blog): 首页主卡挂三册 chip、新增 .bc-chips 样式并重生成 sitemap"
```

---

## 任务 9：portal 产品数字同步（条件任务）

**触发条件**：任务 0 步骤 3 的实跑结果与 `/agentic.html#evidence` 现有值不符。

实测已知：Modern 由 `682` 变为 **`724`**，因此**本任务必须执行**。

**文件：**
- 修改：`portal/agentic.html`、`portal/zh/agentic.html`、`portal/engineering.html`、`portal/zh/engineering.html`

- [ ] **步骤 1：定点替换**

```bash
cd /Users/cheenle/HAM/website/portal
SITES=(portal/ mrrc/ mrrc_ft710/ mrrc_modern/ sunmrrc/ SunsdrMobile/ mrrc_ft8/ efhw/)   # 仅作参照
grep -n "682" agentic.html zh/agentic.html engineering.html zh/engineering.html
grep -n "2026-09-05" agentic.html zh/agentic.html
```

把 Modern 的 `682` 改为 `724`，把 census 日期 `2026-09-05` 改为 `2026-09-12`。
**不得**改任何子站仓库（那些是带日期的历史记录）。

- [ ] **步骤 2：跑既有页面测试**

运行：`/usr/bin/python3 -m pytest tests/test_agentic_pages.py tests/test_engineering_pages.py -q`
预期：若断言锁死了 `682`/日期，需要同步更新对应测试常量；其余 PASS

- [ ] **步骤 3：Commit**

```bash
git add portal/agentic.html portal/zh/agentic.html portal/engineering.html portal/zh/engineering.html portal/tests/
git diff --cached --stat
git commit -m "fix(portal): Modern 测试数 682→724、census 日期改 2026-09-12"
```

---

## 任务 10：术语联网核对

**文件：** 不产生文件；产出为对 `zh/index.html` 的修正

- [ ] **步骤 1：核对新引入术语**

对本次新用的词逐个检索（`cn.bing.com`，读前 5 条标题而非结果条数——Bing 不严格遵守引号）：

```
"快照" 数据库 备份 含义
"保留策略" 日志 保留期
"测量窗口" 含义
```

无法确证的词一律换成已确证的表述。

- [ ] **步骤 2：反查已确证术语未被改坏**

```bash
cd /Users/cheenle/HAM/website/portal/blog/seven-billion-tokens
grep -c "智能体工程" zh/index.html ledger/zh/index.html almanac/zh/index.html playbook/zh/index.html
grep -c "代理式工程" zh/index.html ledger/zh/index.html almanac/zh/index.html playbook/zh/index.html
grep -c "前沿部署工程" zh/index.html
```

预期：第一条 ≥1；第二条恒为 0；第三条 ≥1。

- [ ] **步骤 3：Commit（若有修正）**

```bash
git add portal/blog/seven-billion-tokens
git diff --cached --stat
git commit -m "docs(blog): ZH 术语按联网核对结果修正"
```

---

## 任务 11：终检与交接

- [ ] **步骤 1：全量测试**

运行：`cd /Users/cheenle/HAM/website/portal && /usr/bin/python3 -m pytest tests/ -q`
预期：全部 PASS，0 failed

- [ ] **步骤 2：本地预览**

```bash
cd /Users/cheenle/HAM/website/portal && python3 -m http.server 8899
# 浏览 http://localhost:8899/blog/seven-billion-tokens/
#      http://localhost:8899/blog/seven-billion-tokens/ledger/
#      http://localhost:8899/blog/seven-billion-tokens/almanac/
#      http://localhost:8899/blog/seven-billion-tokens/playbook/
#   以及各自的 zh/ 版本；确认无断图、无死链、导航可达
```

- [ ] **步骤 3：核对 R5 未被破坏**

```bash
cd /Users/cheenle/HAM/website/portal
SITES=(portal/ mrrc/ mrrc_ft710/ mrrc_modern/ sunmrrc/ SunsdrMobile/ mrrc_ft8/ efhw/)
grep -Rn "7,404,583,808" $SITES        # 只应出现在 portal/blog/seven-billion-tokens/**
```

- [ ] **步骤 4：汇报并等待部署指令**

打印：改动文件清单、`git log --oneline -12`、测试结果、**未部署**状态。
部署需用户明确指示后单独执行 `portal/deploy.sh`。

---

# 附录 A · 权威数据表（2026-09-12 实测）

> 全计划唯一的数字来源。任务 0 若重跑出不同值，直接改本附录后再继续。

## A1 · Token 账本（已记录口径）

> **CENSUS CUTOFF：`2026-09-12T02:40:59Z`（= 10:40:59 +0800）**
> 所有数字均为该时刻的快照。重跑不同不叫误差，叫时间在走。
>
> **❗ 两条必读警告**
>
> **① 观察者效应**：census 测量的机器上，**执行本次测量的会话本身也在被测量**。
> 同一脚本相隔 12 分钟得出的 pi 总额已从 `1,874,576,102` 跑到 `1,926,003,139`（+51,427,037，
> 主要为本次会话自己写入的 token）。因此：① 必须记录**截止时间戳**；
> ② 只能报告“截至某时刻的快照”，不得描述成“累计总量”。
>
> **② 原发表值同时虚高与虚低。** 已发表门面值 `7,007,437,567` 建立在 7 个 harness 上，
> 而实测至少还有 **3 个带完整 token 记录的 harness 被遗漏**（Hermes / AgnesCode /
> DeepSeek Harness），同时 claude-code 的行口径又把同一 API 响应重复计入约 2.7×。
> **两个方向的误差同时存在**——这就是“账本不是资产，是读数”的最硬证据。

| harness | tokens（行口径） | 测量窗口 | 会话 | 备注 |
|---|---|---|---|---|
| claude-code | 2,527,597,534 | 2026-08-08 .. 2026-09-08 | 48 | 保留期已删早期历史；去重后 818,520,401（6,600 个 API 响应） |
| pi | 1,926,003,139 | 2026-07-22 .. 2026-09-12 | 67 | 含本次测量会话自身 |
| kimi-code | 1,254,875,254 | 2026-07-18 .. 2026-09-06 | 245 | `usageScope=="turn"` |
| codex | 547,796,667 | 2026-05-27 .. 2026-08-30 | 116 | 已冻结；`state_5.sqlite` 独立复核 546,858,767（差 0.17%） |
| mulerun | 537,961,611 | 2026-05-20 .. 2026-09-06 | 183 | |
| **Hermes** | **485,213,348** | 2026-05-15 .. 2026-07-24 | 292 | **原文记作“未记录”——错**：只查了 `messages.token_count`（全 0），漏了 `sessions` 表。分项 input 9,015,580 / output 1,725,832 / cache_read 474,471,936；85% 的 `cwd` 为空 |
| **AgnesCode** | **82,931,675** | 2026-07-13 .. 2026-07-26 | 1142 | **原普查未含**；`usage_ledger`；`sessions.accumulated_total_tokens` 精确互证 |
| cursor | 27,079,705 | — | — | 无 cwd，无法归属 |
| **DeepSeek Harness** | **10,931,069** | 2026-08-16 | 2 | **原普查未含**；`~/.dsh/sessions/*/*/session.jsonl.zstd` |
| opencode | 4,190,890 | — | 6 | |
| Qoder | 2,916 | — | — | `agent_memory.token_count`，非会话账本 |
| **合计（行口径）** | **7,404,583,808** | | | **比已发表值多 397,146,241** |
| **合计（去重口径）** | **5,695,506,675** | claude-code 去重后 | | 唯一可比口径 |

**新增三源的提取方法（不得改）**

| harness | 位置 | 字段 |
|---|---|---|
| Hermes | `~/.hermes/state.db` → `sessions`（292 行） | `input_tokens + output_tokens + cache_read_tokens + cache_write_tokens + reasoning_tokens` |
| AgnesCode | `~/.agnes/data/sessions/sessions.db` → `usage_ledger`（1142 行） | `total_tokens` |
| DeepSeek Harness | `~/.dsh/sessions/*/*/session.jsonl.zstd`（zstd 解压） | `data.chunk.usage` 的 `inputTokens + outputTokens + cacheReadTokens + reasoningTokens`（**不是顶层 `usage`**） |

**必须排除的重复源**：Hermes `sessions/*.jsonl`（无 token 字段）、
Hermes `state-snapshots/*/state.db`（旧快照）、Agnes `state/logs/llm_request.*.jsonl`
（`usage` 全为 `null`）、Qoder（Cursor 重复子集）。

**缓存结构**（仅三个有完整分列的 harness：claude-code / pi / kimi-code）：
cache-read `5,347,191,146` / fresh `337,872,196` / output `23,412,585`；缓存读取占 **93.7%**。

**不并入合计**：iFlow ≈247,000,000（估算，`usage` 全零，195 会话 / 890,601,145 字符）。

## A2 · 上周过程指标（`2026-09-05T00:00:00+08:00` .. 2026-09-12）

> **❗ 必须用带时区的显式时刻。** `git log --since=2026-09-05`（裸日期）被 git 解析成
> **“那一天的此刻”**：`git rev-parse --since=2026-09-05` → `--max-age=1788576106`
> = `2026-09-05 10:41:46 +0800`。同一条命令在 01:47 与 10:41 运行会得出不同结果
> （实测 website 32→27、ft710 1→0）。
> **固定命令**：`git log --since='2026-09-05T00:00:00+08:00'`。

| 仓库 | commits | fix | feat | fix% | tokens | 人类轮次 | 轮次/提交 | M tokens/提交 |
|---|---|---|---|---|---|---|---|---|
| mrrc_modern | 41 | 17 | 4 | 41% | 244,037,840 | 30 | 0.73 | 5.95 |
| website | 35 | 8 | 6 | 23% | 248,244,447 | 85 | 2.43 | 7.09 |
| MRRC | 2 | 0 | 0 | 0% | 94,144,081 | 12 | 6.00 | 47.07 |
| mrrc_ft710 | 1 | 1 | 0 | 100% | 0 | 0 | 0.00 | 0.00 |
| ft8 | 2 | 2 | 0 | 100% | 0 | 0 | 0.00 | 0.00 |
| sunsdr | 0 | 0 | 0 | — | 0 | 0 | — | — |
| 未归属 | — | — | — | — | 141,892,599 | 109 | — | — |

> **内生的观察者效应**：website 的 35 个提交里有 **4 个是本次普查/重构自身的文档提交**。
> 测量正在把被测量对象改变一点点——写进分册 A 的 `window` 节。

## A3 · 产品数字（实跑，非 CHANGELOG）

| 产品 | 数字 | 运行器 |
|---|---|---|
| MRRC FT-710 | `439 passed` | `mrrc_ft710/.venv/bin/python3 -m pytest -q` |
| MRRC Modern | `724 passed, 8 subtests passed` | `mrrc_modern/.venv/bin/python3 -m pytest -q` |
| MRRC-FT8 | `935 passed, 1 skipped, 1 xfailed` | `ft8/venv/bin/python3 -m pytest -q` |

版本：FT-710 tag `v1.8.0`；Modern CHANGELOG `v1.14.3`（09-11）/ tag `v1.14.2`；
MRRC tag `V5.7.0`；FT8 tag `v1.1.0`。

**方法变更（必须写进"边界"）**：三个产品仓库已从系统 Python 迁移到各自 venv
（Python 3.13.14 + pytest 9.1.1）。用 `/usr/bin/python3`（3.9.6）会因 `X | None`
语法在收集期报 `TypeError` —— 这是**环境限制，不是产品缺陷**。

## A4 · 提交计数（HEAD 口径）

| 仓库 | `git log --oneline \| wc -l` |
|---|---|
| MRRC | 181 |
| mrrc_ft710 | 162 |
| mrrc_modern | 281 |
| ft8 | 253 |
| website | 111 |
| sunsdr | 67（另有 SunsdrMobile 9） |

> 口径警告：`--all` 会得到显著不同的值（如 MRRC 328、website 213）。
> **全文只能用一个口径**，并在分册 A `boundaries` 注明。

## A5 · 模型调用计数（各 harness 保留窗口内，次数非 token）

| harness | 前列模型（调用次数） |
|---|---|
| claude-code | deepseek-v4-flash 12,402 / **qwen3.8-max-0902 3,883** / qwen3.8-flash 1,077 / glm-5.2 800 / deepseek-v4-pro 506 |
| pi | deepseek-v4-flash 4,417 / gpt-5.6 2,721 / qwen3.8-flash 1,227 / **glm-5.3-flash 745** / deepseek-v4-pro 522 / deepseek-v4-flash-vision-exp 85 |
| kimi-code | kimi-code/k3 5,891 / kimi-for-coding 2,097 / k3-256k 1,903 / kimi-for-coding-highspeed 306 |
| codex | gpt-5.5 143 / gpt-5.6-sol 128 / deepseek-v4-flash 17 / gpt-5.3-codex 15 / deepseek-v4-pro 2 |
| mulerun | gpt-5.5 162 / deepseek-v4-flash-free 16 / qwen3.6-plus 2 / gemini-3-pro-preview 1 / gemini-3.1-pro-preview 1 |
| opencode | big-pickle 61 / qwen3.6-plus-free 1 |

## A6 · 案例事故与决策（分册 C 的素材，均已在前作中核实）

| 事故 | 根因 | 代价 | 转成的规则 | 可复现 |
|---|---|---|---|---|
| FT-710 频率漂移 | `DN;` 是 VFO 步进命令而非 DNR 查询，每 2 秒轮询一次 | 活电台频率每次漂移 ~20 Hz | `cat-no-dn`（AD-014，07-20 `2498ec2`） | `sdd_context.py check` 退出码 2 |
| 部署备份撑满磁盘 | 整站 `cp -r` 备份，含 `downloads/`、`videos/` | 服务器 `/var/tmp` 100%（单份 ~300 MB） | 备份按站瘦身 + 轮转（保留 3 份） | `rsync --exclude` |
| portal 备份从未生效 | 远端 heredoc 未加引号，本地 shell 先展开 | 每次都打印一个不存在的备份路径 | 远端 heredoc 必须 `<<'REMOTE'`（`067f565`） | `git log -S"<<'REMOTE'"` |
| 测量口径错误 | codex `cached_input_tokens` 是 `input_tokens` 子集；pi `totalTokens` 已含全部 | 首次 census 多算 16 亿 | 逐工具字段语义表 | 附录 A1 |
| 账本倒退 | claude-code 日志有保留期 | 一周后 claude-code 行口径 **−679,899,086** | **证据必须被快照**（本次新增的第一原则） | `~/.claude/.last-cleanup` |
| 观察者效应 | 测量脚本与被测量对象同机运行 | 12 分钟内 pi 总额 +51,427,037，全为测量会话自己 | census 值必须携带**截止时间戳** | 短时间连跑两次同一脚本 |
| **裸日期陷阱** | `git log --since=2026-09-05` 被解析为“那天的此刻” | 同一命令两次运行给出不同提交数（website 32→27、ft710 1→0） | git 窗口必须写显式时区：`--since='2026-09-05T00:00:00+08:00'` | `git rev-parse --since=<日期>` |
| **查错表：宣布“未记录”而未查全** | 只查 `messages.token_count`（全 0），未查 `sessions` 表 | 已发表账本少算 **485,213,348**（Hermes） | 逐工具字段语义表必须覆盖**整库所有表**；宣布“未记录”前必须列出查过的表 | `PRAGMA table_info` 逐表扫 `token` 列 |

---

# 附录 B · 中文术语表（已联网核实）

| 英文 | 采用 | 证据 |
|---|---|---|
| Agentic Engineering | 智能体工程 | 百度百科《智能体工程技术》；多篇专题 |
| ~~代理式工程~~ | **禁用** | 检索仅返回"网络代理"结果，该说法不存在 |
| Harness | 保留 `harness`，首现注"（智能体框架）" | 机器之心《一文读懂 Harness Engineering：智能体的框架》《万字讲透 Agent Harness 的十二大模块》 |
| Context Engineering | 上下文工程 | 百度百科《上下文工程》 |
| Subagent | 子智能体 | 知乎《图解 Claude Code 子智能体 Sub-agent》、ZCode 文档 |
| FDE | 前沿部署工程（首现注全称） | 百度百科《前沿部署工程师 (FDE)》 |
| SDD | 规格驱动开发（SDD） | 知乎《SDD 规格驱动开发》《SDD + TDD AI Coding 开发模式实战》 |
| Gate | 门禁 | 通用工程术语 |
| Eval / Benchmark | 评测 | 榜单生态通用 |
| Token | 保留 `token`，首现注"（词元）" | 工程语境普遍不译 |
| Contract | 契约 | 通用 |
| Agent | 智能体（**不译"代理"**） | 百度百科《智能体》 |
| Guardrail | **本次不使用** | 未能确证，检索被物理护栏污染 |

**六条修订规则**：① token 量用「亿 tokens」，快照数字原样保留；② 不造词（禁"沉淀地"）；
③ 字段名保留 `<code>`，叙述句用中文；④ 中文用「」，中英文间保留半角空格；
⑤ 首现加注 harness / token / SDD / FDE / PTT / CAT；⑥ 委托 / 拦截 / 沉淀 / 裁决 四词严格分工。

---

# 附录 C · 每节必须包含

## C1 · 主文（15 节）

| section id | 必须包含 |
|---|---|
| `ledger-shrank` | **开场即给新事实**：已发表 `7,007,437,567` → 重算 `7,404,583,808`（**+397,146,241**）；三个方向的误差各一条硬证据：**虚高**（claude-code 行口径重复计，去重后 `818,520,401`）、**虚低**（Hermes `485,213,348` 被原文记作“未记录”）、**漂移**（保留期：`~/.claude/.last-cleanup` = `2026-09-07T13:13:57Z`；观察者效应：12 分钟内 pi 自增 `51,427,037`；裸日期陷阱）；对照 = codex `547,796,667` **逐位不变**；结论 = **证据必须被快照，不能被累计；每个数字必须带截止时间戳**。标 `fact` + `thesis` |
| `intents` | 四个业务意图（MRRC `ba66892` / sunsdr `38cb85e` / ft710 `9403e2e` / ft8 08-03），去掉 AI 仍成立。标 `thesis` |
| `control-group` | 对照期 185 会话 / `37,202` 轮 / 单周 `10,420` 轮；usage 全零、零沉淀。标 `fact` |
| `intervention` | 三条曲线同向：ft8 `17.1 → 0.3`；新增上周 modern `0.73` 轮/提交、MRRC `6.00`。标 `fact` |
| `unit-cost` | ft8 峰值 `75.5` M → 维护 `0.9` M；新增上周 modern `5.95` M、MRRC `47.07` M（**新需求推高单位成本**）。标 `inference` |
| `rework` | ft710 36%→6–12%；ft8 29%→17%；**反证**：上周 modern fix% `41%`（41 提交中 17 个 fix）。标 `fact` |
| `cadence` | modern 5 天 4 版（v1.14.0→v1.14.3）；红绿中位 `19` 分钟。标 `fact` |
| `method-timeline` | 文档时代（`58aa675` / `88f519f`）→ 契约时代（`2498ec2`）；ft8 整包继承（`d4a7a32`）；约束 `52`（`ft710 17 / modern 21 / ft8 14`，**上周未增**）。标 `fact` |
| `incident-chains` | 13 天与 7 天两条链；含 `cat-no-dn` 复现块（`sdd_context.py`、`DN;`、退出码 2）。标 `fact` |
| `evidence-ledgers` | 两本账互不背书；`439` / `724` / `935` 的实跑口径差异（含 `X \| None` 环境限制说明）。标 `thesis` |
| `model-shift` | claude-code 主力出现 `qwen3.8-max-0902`（3,883 次）；pi 新见 `glm-5.3-flash`（745）；结论 = 不要把方法绑死在某个模型上；年鉴外链 `almanac/`。标 `inference` |
| `attribution` | 四证据分离；模型定上限、方法定兑现比例。标 `inference` |
| `advice` | 两条轨（你控制的 / 市场给的），压缩为纪律 + 链接 `playbook/`。标 `thesis` |
| `closing` | 先问"判断沉淀在哪里"。标 `thesis` |
| `four-dimensions` | 工程史 / 认识论 / 经济学（缓存 `93.7%`，覆盖三个有完整分列的 harness）/ 责任；四纪律。标 `thesis` |

## C2 · 分册 A（5 节）

| section id | 必须包含 |
|---|---|
| `census` | 附录 A1 全表（**11 个 harness**，含每行**测量窗口**）+ 双口径 + 新增三源的提取方法 + 必须排除的重复源 + 不并入合计项（iFlow 估算） |
| `window` | claude-code 清理证据（`~/.claude/.last-cleanup` = `2026-09-07T13:13:57Z`）；codex 冻结（`547,796,667` **逐位不变**）；**观察者效应实证**：12 分钟内 pi 自增 `51,427,037`（全为测量会话自己）→ **每个 census 值必须带截止时间戳**；**裸日期陷阱**：`git log --since=2026-09-05` 被解析为“那天的此刻”，同命令两次运行不同 → 必须写 `--since='2026-09-05T00:00:00+08:00'`；"总额不是单调量" |
| `repos` | 附录 A4 的 HEAD 口径表 + `--all` 口径警告 |
| `boundaries` | 测量边界扩充：窗口口径、**观察者效应**、**“未记录”的宣布标准**（必须先列出查过的表）、venv 方法变更、`--all` 口径警告 |
| `verify` | 每工具字段语义表（附录 A1 的方法列）；哪些可自跑、哪些只能信；**两处独立交叉校验**：codex `sessions` 547,796,667 vs `state_5.sqlite` 546,858,767；AgnesCode `usage_ledger` vs `sessions.accumulated_total_tokens` 精确相等 |

## C3 · 分册 B（4 节）

| section id | 必须包含 |
|---|---|
| `eras` | 六个时代（Probing / 裸对话 / GPT-5.5 / K3 家族 / Flash 霸权 / 多极竞争） |
| `shift` | 附录 A5 的模型计数表 + 任务 × 模型 × harness 匹配表 |
| `benchmarks` | **独立评测**与**厂商口径**分两层写，不得混排 |
| `routing` | `big-pickle`（OpenCode 官方承认的隐身模型）、`code-supernova-1-million`（2025 隐身营销名）、`kimi-for-coding`（订阅 API 别名） |

## C4 · 分册 C（4 节）

| section id | 必须包含 |
|---|---|
| `disciplines` | 四条纪律展开（定义先于实现 / 每次事故变成规则 / 盯住不确定性花在哪 / 两本账分开） |
| `checklists` | 三类清单：验收前 / 落盘前 / 发布前；每条能指向附录 A6 的事故或裁决 |
| `templates` | 三个模板：验收条件条目 / 约束注册表条目 / 事故→约束流程 |
| `incidents` | 附录 A6 的事故库表（现像 → 根因 → 代价 → 规则 → 可复现命令），机制视角外链 `/engineering.html` |
