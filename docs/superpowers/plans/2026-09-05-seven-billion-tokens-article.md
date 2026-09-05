# 《Seven Billion Tokens, One Field Incident》实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 `portal/blog/` 下发布一篇台账先行的端到端 Agentic Engineering 长文（EN + ZH，13 节，四类断言标记），并把 portal 三个页面上已被实测推翻的数字校正到 2026-09-05 普查值。

**Architecture:** 文章是纯静态 HTML，完全复用 connections 一文的骨架（`.blog-article` → `.blog-header` → `#blog-toc` → `.blog-content` → `<section id>`），并随文携带自己的 `article.css`（`.claim-box` 四色规则不在共享 `blog.css` 里）。所有数字来自 2026-09-05 本机普查，逐工具校正过 token 语义。契约测试先行（B0 先红），锁死 13 个 section id、四类 `data-claim-type`、禁句、gate 归属、数字常量、卡片与 sitemap。Part 2 只改 portal 自己的 6 个文件 —— 跨站普查已证明子站携带的是**带日期的历史记录**，不是与之竞争的当前声明，因此不改任何子站仓库。

**Tech Stack:** 纯静态 HTML/CSS，无构建步骤。测试运行器 **`/usr/bin/python3 -m pytest`**（系统 Python 3.9.6 + pytest 8.4.2）—— 已实测：Homebrew 的 `python3`(3.14)、`python3.11`、`python3.12`、`python3.13` **都没有 pytest 模块**，仓库内也没有 venv，只有系统 Python 能跑。测试代码用 `from __future__ import annotations`，因此 `dict[str, str]` / `str | None` 这类注解在 3.9 下合法（已实测通过）。`portal/make_sitemap.py` 重生成 sitemap（`os.walk`，自动收录新目录），用任意 `python3` 均可。

**Spec:** `docs/superpowers/specs/2026-09-05-seven-billion-tokens-article-design.md`

## Global Constraints

以下为 spec 的项目级要求，逐字复制。**每个任务的要求都隐含包含本节。**

- **R1** 绝不声称某个产品族由 AI / agent 建造。EN 禁句：`built by AI`、`built by agents`、`AI-built`、`AI wrote`。ZH 禁句：`由 AI 建造`、`由智能体建造`、`AI 打造`。
- **R2** 只有 `mrrc_ft710`(17 条)、`mrrc_modern`(21 条)、`ft8`(14 条) 三个仓库可描述 pre-edit gate。MRRC / SunMRRC / SunsdrMobile / EFHW 必须明写"无机器可读约束注册表，因此不主张编辑前门禁"。
- **R3** FDE 只作为外环 `Echo → Delta → Product` 出现，不得提升为顶层品牌。顶层品牌是 Agentic Engineering。
- **R4** 中文术语：**智能体工程**（禁用"代理式工程"）；FDE 中文统一为**前沿部署工程**。
- **R5** 跨项目可比数字的唯一主人是 `/agentic.html#evidence`。本文的 token 台账写在本文 `references` 节并标 census 日期，不散落到子站。
- **R6** 每条声明带最小证据记录：`Claim · Source artifact · Version / commit · Environment · Verification method · Result · Limitations · Date`。
- **R7** 估算值与未记录值必须显式标注，**不得并入"已记录"合计**。
- **已记录合计（census 2026-09-05）**：`7,007,437,567` tokens / `41,257` 轮 / `882` 会话。
- **含估算合计**：`~7,241,684,966` tokens / `87,580` 次交互 / `1,359` 会话。
- **fresh（非 cache-read）**：`336,661,475` = `4.8%`；**cache-read**：`6,670,776,092` = `95.2%`；模型输出：`30,061,161`。
- **Pi 成本**：`$15.11`（= `$15.1135`）/ `1,625,562,962` tokens = `$9.30` per billion。用 `cost.total`，**不得**把各分量再相加（会得到 $30.23，是重复计）。
- **实测测试数（2026-09-05，macOS）**：FT-710 `Ran 439 tests ... OK`；Modern `Ran 682 tests`，1 个 loader error `test_macos_launcher`（Windows 专用启动器测试在 macOS 导入失败，**非产品缺陷**）；FT8 `937 tests collected`（pytest，**collected ≠ passed**）。
- **约束注册表**：52 条 = ft710 17（block 8 / warn 4 / info 5）+ modern 21（block 8 / warn 6 / info 7）+ ft8 14（block 9 / warn 1 / info 4）。
- **不得改动**：任何 `deploy.sh`、任何子站仓库、nginx 配置。不部署。
- **既有未提交改动不得卷入**：工作区有微信二维码有效期改动（`portal/index.html`、`portal/zh/index.html`、`efhw/index.html`、`efhw/zh/index.html` 各 1 行，Aug 29 → Sep 12）。提交前必须确认 diff 只含本次改动。

### 双标题与三卷（spec §5.0，2026-09-05 增补）

- **EN 标题**：`Seven Billion Tokens, One Field Incident`（不变）
- **ZH 标题**：`格物致知 —— Agentic AI 的思考`
- **slug 不变**：`seven-billion-tokens`。canonical / hreflang / sitemap / 测试里的 URL 常量**全部不受影响**。
- **EN 页不得出现「格物致知」四字**（`test_titles_are_bilingual` 用 `assertNotIn` 断言）。两个框架不互相稀释：EN 读者得具体钩子，ZH 读者得经典框架，两版 13 节结构与三卷分组完全相同。
- **三卷分组**（13 个 section id 不变，卷标记用 `<div class="volume" data-volume="...">` 包裹，**绝不用 `<section>`** —— 否则 `section_ids` 会多出 3 个 id，破坏 `REQUIRED_SECTIONS` 的精确相等断言）：

| `data-volume` | EN 卷题 | ZH 卷题 | 含 section id（顺序固定） |
|---|---|---|---|
| `gewu` | Volume I · Investigating Things | 卷一 · 格物 | `ledger`, `floor`, `numbers-lie`, `intent`, `before` |
| `zhizhi` | Volume II · Extending Knowledge | 卷二 · 致知 | `machine`, `chain`, `scale` |
| `zhixing` | Volume III · Unity of Knowing and Acting | 卷三 · 知行合一 | `delivery`, `drift`, `human`, `playbook` |
| —（不包裹） | Appendix · Provenance | 附录 · 溯源 | `references` |

- **五处必含的经典对应**（缺一即测试红）：
  1. `before` 节：`data-claim-type="analogy"` 的 **阳明格竹七日而病** ↔ iFlow 时代 37,202 轮 / 6 模型 / 零注册表
  2. `numbers-lie` 节：**致知在格物，不在台账** ↔ 我自己的 `5,380,941,148` 是一次「不格物」
  3. `chain` 节：**物格而后知至** 四步链（电台实际行为 → SDD 裁决 → 机器可读约束 → 运行时拦截）
  4. `scale` 节：朱子「今日格一物，明日格一物，积习既多，然后脱然自有贯通处」↔ 17→21→14 条约束的积累
  5. `human` 节：**知而不行，只是未知** ↔ 一条不会 block 的约束等于没有这条约束
- **引文纪律**：经典引文只能标 `analogy` 或 `thesis`，**不得**标 `fact`；每处须给出处（《大学》/ 朱熹《大学章句》补传 / 王阳明《传习录》）。**禁止**目的论断言（如"中国早就有了 agentic engineering"）—— 那是 R1 的近亲。

## 已核实的普查结论（执行者不必重查，但若要改数字必须先重跑）

| 结论 | 依据 | 处置 |
|---|---|---|
| MRRC `280+ commits` **正确** | `git -C /Users/cheenle/HAM/MRRC log --all --oneline \| wc -l` = 326（含 12 个 tag） | **保留不改** |
| FT-710 当前版本 `v1.8.1` **正确** | `mrrc_ft710/CHANGELOG.md` 有 `## [v1.8.1] — 2026-08-16`；git tag 与 SDD README 停在 `v1.8.0`（= 已打包的 Windows 安装器） | 台账 **保留** `Source: v1.8.1 / Windows package: v1.8.0` 的双字段写法 |
| Modern 已到 `v1.12.1` | `mrrc_modern/SDD/README.md` 含 `v1.12.1`；`SDD V2.30` | 台账 `v1.12.0`→`v1.12.1` |
| SunMRRC `40+ commits` 低估 | `git -C /Users/cheenle/HAM/sunsdr log --oneline \| wc -l` = 67 | → `65+ commits` |
| SunsdrMobile `3 commits` 过时 | `git -C /Users/cheenle/HAM/sunsdr/SunsdrMobile log --oneline \| wc -l` = 9（独立仓库） | → `9 commits` |
| 子站的 `439 tests` / `633 tests` **不改** | `mrrc_modern/sdd.html` 是 `v1.12.0 (V2.27)` 的**带日期发布记录**；`mrrc_modern/sdd/14-version-history.html` 是 `SDD V2.30 / 2026-08-29 / 作者 Kimi` 的历史行；`mrrc_ft710/index.html` 的 `439 tests` 已自带 "physical RF monitoring remains" 局限 | 改历史即造假。**只改 portal 当前态声明** |
| 注册表 `sdd_version` 三仓全部滞后 | ft710 注册表 `V1.7` vs SDD `v1.8.0`；modern `V2.27` vs `V2.30`；ft8 `V1.0` vs `V1.8` | 写入文章 `drift` 节（fact），**不修注册表**（属产品仓库，范围外） |
| 子站不自报可比测试数 | 8 站定点 grep：命中仅在 portal 与 `sdd/` 生成物 | R5 无跨站违规 |

### ⚠️ 本机 grep 陷阱（执行者必读）

CLAUDE.md 教的 `SITES="portal/ mrrc/ ..."` + `grep -Rn "pat" $SITES` 在本机**静默失败**：本机 `grep` 是 **ugrep**，shell 是 **zsh**，而 zsh **不对未加引号的变量做词分割**，于是 8 个目录被当成 1 个不存在的路径：

```
ugrep: warning: portal/ mrrc/ ... efhw/: No such file or directory   # exit=2
```

交互式看起来就是"没有命中"—— 一次彻底的假绿。**必须用数组**：

```zsh
SITES=(portal/ mrrc/ mrrc_ft710/ mrrc_modern/ sunmrrc/ SunsdrMobile/ mrrc_ft8/ efhw/)
grep -RnF "pattern" $SITES        # 数组会展开成 8 个参数
```

本计划所有跨站 grep 步骤都已用数组写法。

## File Structure

**新增（4 个文件，全部在 `website` 仓）**

| 路径 | 职责 |
|---|---|
| `portal/tests/test_seven_billion_tokens_article.py` | 契约测试。锁 13 个 section id、四类断言标记、R1/R2/R4 禁句、数字常量、卡片、sitemap、SEO、链接可解析。**它同时是本文数字的机器可读副本** —— 数字改了测试就红 |
| `portal/blog/seven-billion-tokens/article.css` | 本文私有样式：`.claim-box` 四色 + `.ledger-table` + `.term-block`（终端复现块）+ `.prov`（溯源行）。从 connections 的 `article.css` 移植 `.claim-box`/`.claim-label` 原样，其余新增 |
| `portal/blog/seven-billion-tokens/index.html` | EN 正文，13 节 |
| `portal/blog/seven-billion-tokens/zh/index.html` | ZH 正文，与 EN 结构完全对等（同 13 个 id、同四类断言） |

**修改（7 个文件）**

| 路径 | 改什么 |
|---|---|
| `portal/blog/index.html` | 加一张 `data-cat="intelligence"` 卡片（置于列表首位） |
| `portal/sitemap.xml` | 由 `make_sitemap.py` 重生成（不手工编辑） |
| `portal/index.html` | 5 个 `<li>` 数字（165 行保留） |
| `portal/zh/index.html` | 对应 5 个 `<li>` |
| `portal/agentic.html` | 台账 Modern 行 `633`→`682`、`v1.12.0`→`v1.12.1`；census `2026-09-02`→`2026-09-05`（6 处） |
| `portal/zh/agentic.html` | 同上（`633 项`→`682 项`、普查日期 5 处 + 复现块日期） |
| `portal/engineering.html` + `portal/zh/engineering.html` | `633`→`682`（各 2 处：`#sdd` 警示块与 `#evidence` 族表） |

**不发布**（`portal/deploy.sh` 已排除，本次不动该脚本）：`portal/tests/`、`portal/make_sitemap.py`、`.pytest_cache`、`IMG_*`

---

## Task 1（B0）：契约测试先行 —— 先让它红

**Files:**
- Create: `portal/tests/test_seven_billion_tokens_article.py`

**Interfaces:**
- Consumes: 无（首个任务）
- Produces: 模块级常量，后续任务全部依赖这些**精确名字与值**：
  - `SLUG: str` = `"seven-billion-tokens"`
  - `ARTICLES: dict[str, Path]` — 键 `"en"` / `"zh"`；`ARTICLE_CSS: Path`；`BLOG_INDEX: Path`；`SITEMAP: Path`
  - `CANONICAL: dict[str, str]` — 两个绝对 URL，`test_seo_language_links_and_json_ld_are_complete` 断言 canonical **恰好等于**它
  - `REQUIRED_SECTIONS: set[str]` — 13 个 id
  - `REQUIRED_CLAIM_TYPES: set[str]` — `{"fact","inference","analogy","thesis"}`
  - `VOLUMES: tuple[tuple[str, tuple[str, ...]], ...]` — 三卷，顺序 `gewu` → `zhizhi` → `zhixing`，每卷带其 section id 元组
  - `UNVOLUMED_SECTIONS: tuple[str, ...]` — `("references",)`
  - `VOLUME_TITLES: dict[str, dict[str, str]]` — `["en"]` / `["zh"]` 各三个卷题串，必须在全文逐字出现
  - `ZH_TITLE: str` = `"格物致知"`（ZH 页必须有，**EN 页必须没有**）、`EN_TITLE: str`
  - `LEDGER_CONSTANTS: dict[str, str]` — 29 个数字串，两版都必须逐字出现
  - `CLASSICAL_ANCHORS: dict[str, dict[str, tuple[str, ...]]]` — 5 个 section × 两语言的逐字锚点
  - `CLASSICAL_TERMS` / `CITATION_SOURCES` / `FORBIDDEN_TELEOLOGY` — 均按语言分列
  - `FORBIDDEN: dict[str, tuple[str, ...]]` — R1/R4 禁句
  - `STALE_NUMBERS: tuple[str, ...]` — 已被推翻、不得出现的旧值
  - `GATE_OWNERS` / `GATE_FORBIDDEN_NEIGHBOURS` — R2 的窗口判定
  - `ESTIMATE_LABELS: dict[str, tuple[str, ...]]` — R7 的标注词
  - `ArticleParser` —— **基于** `test_connections_article.py` 的同名类**扩展**而来，新增 `section_volume: dict[str, str | None]`、`volume_order: list[str]`、`div_depth: int`（用于断言 `<div>` 平衡）。原有的 `ids` / `section_ids` / `refs` / `canonicals` / `hreflangs` / `json_ld` 行为不变，但**去掉了 svg title/desc 检查**（本文不要求 SVG；若正文加入 SVG，需自行补回）
  - `load(path) -> tuple[str, ArticleParser]`（文件不存在时抛 `unittest.SkipTest`）

- [ ] **步骤 1：写失败测试**

创建 `portal/tests/test_seven_billion_tokens_article.py`，内容如下（完整，可直接落盘）：

```python
from __future__ import annotations

import json
import re
import unittest
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

PORTAL = Path(__file__).resolve().parents[1]
SLUG = "seven-billion-tokens"
ARTICLES = {
    "en": PORTAL / "blog" / SLUG / "index.html",
    "zh": PORTAL / "blog" / SLUG / "zh" / "index.html",
}
ARTICLE_CSS = PORTAL / "blog" / SLUG / "article.css"
BLOG_INDEX = PORTAL / "blog" / "index.html"
SITEMAP = PORTAL / "sitemap.xml"
CANONICAL = {
    "en": f"https://www.vlsc.net/blog/{SLUG}/",
    "zh": f"https://www.vlsc.net/blog/{SLUG}/zh/",
}

REQUIRED_SECTIONS = {
    "ledger",
    "floor",
    "numbers-lie",
    "intent",
    "before",
    "machine",
    "chain",
    "scale",
    "delivery",
    "drift",
    "human",
    "playbook",
    "references",
}
REQUIRED_CLAIM_TYPES = {"fact", "inference", "analogy", "thesis"}

# Three volumes (spec §5.0). Order matters; `references` is an appendix and
# deliberately sits OUTSIDE every volume.
VOLUMES = (
    ("gewu", ("ledger", "floor", "numbers-lie", "intent", "before")),
    ("zhizhi", ("machine", "chain", "scale")),
    ("zhixing", ("delivery", "drift", "human", "playbook")),
)
UNVOLUMED_SECTIONS = ("references",)
VOLUME_TITLES = {
    "en": {"gewu": "Investigating Things", "zhizhi": "Extending Knowledge",
           "zhixing": "Unity of Knowing and Acting"},
    "zh": {"gewu": "格物", "zhizhi": "致知", "zhixing": "知行合一"},
}
ZH_TITLE = "格物致知"
EN_TITLE = "Seven Billion Tokens, One Field Incident"

# Five required classical correspondences (spec §5.0). Anchors are per-language:
# the ZH page carries the classical Chinese; the EN page carries the standard
# English gloss (and MAY additionally carry the Chinese term, but is not forced to).
CLASSICAL_ANCHORS = {
    "before": {
        "zh": ("格竹",),
        "en": ("investigating the bamboo",),
    },
    "numbers-lie": {
        "zh": ("致知在格物",),
        "en": ("investigating things",),
    },
    "chain": {
        "zh": ("物格而后知至",),
        "en": ("things investigated", "knowledge arrives"),
    },
    "scale": {
        "zh": ("豁然贯通",),
        "en": ("sudden thorough comprehension",),
    },
    "human": {
        "zh": ("知而不行",),
        "en": ("knowing and not acting",),
    },
}
# Classical claims must be analogy or thesis, never fact. Terms that mark a
# claim-box as classical, per language.
CLASSICAL_TERMS = {
    "zh": ("格竹", "格物", "致知", "知行", "贯通"),
    "en": ("bamboo", "investigating things", "extending knowledge",
           "unity of knowing", "comprehension"),
}
# At least one source must be named, per language.
CITATION_SOURCES = {
    "zh": ("大学", "传习录", "大学章句"),
    "en": ("Great Learning", "Chuanxi", "Zhu Xi", "Wang Yangming"),
}
# Teleological claims are forbidden (R1's near cousin).
FORBIDDEN_TELEOLOGY = ("早就有了", "already had agentic", "invented agentic")

# Census 2026-09-05. These strings must appear verbatim in BOTH languages.
LEDGER_CONSTANTS = {
    "recorded_tokens": "7,007,437,567",
    "recorded_turns": "41,257",
    "recorded_sessions": "882",
    "with_estimates_tokens": "7,241,684,966",
    "with_estimates_interactions": "87,580",
    "with_estimates_sessions": "1,359",
    "fresh_tokens": "336,661,475",
    "cache_read_tokens": "6,670,776,092",
    "output_tokens": "30,061,161",
    "cache_read_share": "95.2",
    "fresh_share": "4.8",
    "pi_tokens": "1,625,562,962",
    "pi_cost": "15.11",
    "cost_per_billion": "9.30",
    "constraints_total": "52",
    "constraints_ft710": "17",
    "constraints_modern": "21",
    "constraints_ft8": "14",
    "tests_ft710": "439",
    "tests_modern": "682",
    "tests_ft8_collected": "937",
    "iflow_turns": "37,202",
    "iflow_estimate": "234,247,399",
    "hermes_sessions": "292",
    "hermes_messages": "9,121",
    "hermes_toolcalls": "4,336",
    "first_pass_wrong": "5,380,941,148",
    "codex_db_corroboration": "546,858,767",
    "census_date": "2026-09-05",
}

# R1 / R4 red lines.
FORBIDDEN = {
    "en": (
        "built by AI",
        "built by agents",
        "AI-built",
        "AI wrote",
        "agents built",
    ),
    "zh": (
        "代理式工程",
        "由 AI 建造",
        "由智能体建造",
        "AI 打造",
        "智能体建造了",
    ),
}

# Numbers overturned by the 2026-09-05 census. Must NOT appear as current claims.
STALE_NUMBERS = ("180+ tests", "180+ 测试", "593 tests", "593 测试", "v1.10.1")

# R2: a pre-edit-gate claim may only sit near these three repos.
GATE_OWNERS = ("mrrc_ft710", "mrrc_modern", "ft8", "FT-710", "Modern", "MRRC-FT8")
GATE_FORBIDDEN_NEIGHBOURS = ("SunMRRC", "SunsdrMobile", "EFHW", "MRRC Universal")

# R7: estimates must be visibly labelled.
ESTIMATE_LABELS = {
    "en": ("estimate", "not recorded", "unrecorded"),
    "zh": ("估算", "未记录", "工具记 0"),
}


class ArticleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.section_ids: set[str] = set()
        self.refs: list[str] = []
        self.canonicals: list[str] = []
        self.hreflangs: set[str] = set()
        self.json_ld: list[dict[str, object]] = []
        self.section_volume: dict[str, str | None] = {}
        self.volume_order: list[str] = []
        self.div_depth = 0
        self._div_stack: list[str | None] = []
        self._json_buffer: list[str] | None = None

    def _enclosing_volume(self) -> str | None:
        for value in reversed(self._div_stack):
            if value is not None:
                return value
        return None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        element_id = values.get("id")
        if element_id:
            self.ids.append(element_id)
        if tag == "div":
            self.div_depth += 1
            volume = values.get("data-volume")
            self._div_stack.append(volume)
            if volume and volume not in self.volume_order:
                self.volume_order.append(volume)
        if tag == "section" and element_id:
            self.section_ids.add(element_id)
            self.section_volume[element_id] = self._enclosing_volume()
        if tag in {"a", "link", "script", "img"}:
            ref = values.get("href") or values.get("src")
            if ref:
                self.refs.append(ref)
        href = values.get("href")
        if tag == "link" and values.get("rel") == "canonical" and href:
            self.canonicals.append(href)
        hreflang = values.get("hreflang")
        if tag == "link" and values.get("rel") == "alternate" and hreflang:
            self.hreflangs.add(hreflang)
        if tag == "script" and values.get("type") == "application/ld+json":
            self._json_buffer = []

    def handle_data(self, data: str) -> None:
        if self._json_buffer is not None:
            self._json_buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "div":
            self.div_depth -= 1
            if self._div_stack:
                self._div_stack.pop()
        if tag == "script" and self._json_buffer is not None:
            self.json_ld.append(json.loads("".join(self._json_buffer)))
            self._json_buffer = None


def load(path: Path) -> tuple[str, ArticleParser]:
    if not path.exists():
        raise unittest.SkipTest(f"not created yet: {path}")
    source = path.read_text(encoding="utf-8")
    parser = ArticleParser()
    parser.feed(source)
    return source, parser


class SevenBillionTokensArticleTests(unittest.TestCase):
    def test_articles_and_css_exist(self) -> None:
        self.assertTrue(ARTICLE_CSS.exists(), "article.css")
        for language, path in ARTICLES.items():
            self.assertTrue(path.exists(), language)

    def test_sections_and_claim_types_match(self) -> None:
        parsed = {language: load(path) for language, path in ARTICLES.items()}
        for language, (source, parser) in parsed.items():
            self.assertEqual(REQUIRED_SECTIONS, parser.section_ids, language)
            claim_types = set(re.findall(r'data-claim-type="([^"]+)"', source))
            self.assertEqual(REQUIRED_CLAIM_TYPES, claim_types, language)
        self.assertEqual(parsed["en"][1].section_ids, parsed["zh"][1].section_ids)

    def test_ledger_constants_appear_verbatim(self) -> None:
        for language, path in ARTICLES.items():
            source, _ = load(path)
            missing = [
                f"{name}={value}"
                for name, value in LEDGER_CONSTANTS.items()
                if value not in source
            ]
            self.assertEqual([], missing, language)

    def test_stale_numbers_are_gone(self) -> None:
        targets = list(ARTICLES.values()) + [
            PORTAL / "index.html",
            PORTAL / "zh" / "index.html",
            PORTAL / "agentic.html",
            PORTAL / "zh" / "agentic.html",
            PORTAL / "engineering.html",
            PORTAL / "zh" / "engineering.html",
        ]
        for path in targets:
            if not path.exists():
                continue
            source = path.read_text(encoding="utf-8")
            # The article's `drift` section must be able to QUOTE a wrong number
            # in order to show it was wrong. Quoted values are wrapped in
            # <del class="stale">…</del> and stripped before the check, so a
            # struck-through citation is allowed but a live claim is not.
            live = re.sub(r'<del class="stale">.*?</del>', " ", source, flags=re.S)
            hits = [n for n in STALE_NUMBERS if n in live]
            self.assertEqual([], hits, str(path.relative_to(PORTAL)))

    def test_drift_section_quotes_stale_values_as_struck_through(self) -> None:
        # Positive counterpart: the pedagogy must survive the stripping above.
        # Each stale value the article names has to appear inside <del class="stale">.
        for language, path in ARTICLES.items():
            source, _parser = load(path)
            start = source.find('<section id="drift"')
            self.assertNotEqual(-1, start, f"{language}: drift section")
            end = source.find("</section>", start)
            body = source[start:end]
            struck = re.findall(r'<del class="stale">(.*?)</del>', body, re.S)
            self.assertGreaterEqual(len(struck), 3, f"{language}: drift quotes")
            joined = " ".join(struck)
            for value in ("180+", "593", "v1.10.1"):
                self.assertIn(value, joined, f"{language}: struck-through {value}")

    def test_estimates_are_labelled(self) -> None:
        for language, path in ARTICLES.items():
            source, _ = load(path)
            for value in (
                LEDGER_CONSTANTS["iflow_estimate"],
                LEDGER_CONSTANTS["first_pass_wrong"],
            ):
                index = source.find(value)
                self.assertNotEqual(-1, index, f"{language}: {value}")
                window = source[max(0, index - 900) : index + 900].lower()
                self.assertTrue(
                    any(label in window for label in ESTIMATE_LABELS[language]),
                    f"{language}: {value} needs an estimate/unrecorded label nearby",
                )

    def test_gate_claims_only_near_owning_repos(self) -> None:
        pattern = re.compile(r"pre-edit gate|编辑前门禁|编辑前拦截|PreToolUse")
        for language, path in ARTICLES.items():
            source, _ = load(path)
            for match in pattern.finditer(source):
                window = source[max(0, match.start() - 700) : match.start() + 700]
                self.assertTrue(
                    any(owner in window for owner in GATE_OWNERS),
                    f"{language}: gate claim at {match.start()} lacks an owning repo",
                )
                for bad in GATE_FORBIDDEN_NEIGHBOURS:
                    if bad in window:
                        self.assertNotIn(
                            bad,
                            window,
                            f"{language}: gate claim near {bad} violates R2",
                        )

    def test_forbidden_phrases_absent(self) -> None:
        for language, path in ARTICLES.items():
            source, _ = load(path)
            for phrase in FORBIDDEN[language]:
                self.assertNotIn(phrase, source, f"{language}: {phrase}")

    def test_zh_uses_mandated_terminology(self) -> None:
        source, _ = load(ARTICLES["zh"])
        self.assertIn("智能体工程", source)
        self.assertIn("前沿部署工程", source)
        self.assertNotIn("代理式工程", source)

    def test_titles_are_bilingual(self) -> None:
        en_source, _ = load(ARTICLES["en"])
        zh_source, _ = load(ARTICLES["zh"])
        self.assertIn(EN_TITLE, en_source)
        self.assertIn(ZH_TITLE, zh_source)
        # The EN page keeps the concrete hook and stays free of the ZH title,
        # so the two frames never blur into one.
        self.assertNotIn(ZH_TITLE, en_source)
        # each page must still offer the other language
        self.assertIn('href="zh/"', en_source)
        self.assertIn('href="../"', zh_source)

    def test_volumes_group_sections_correctly(self) -> None:
        expected = {
            section: volume for volume, sections in VOLUMES for section in sections
        }
        for section in UNVOLUMED_SECTIONS:
            expected[section] = None
        self.assertEqual(REQUIRED_SECTIONS, set(expected))
        for language, path in ARTICLES.items():
            source, parser = load(path)
            self.assertEqual(0, parser.div_depth, f"{language}: unbalanced <div>")
            self.assertEqual(
                [v for v, _ in VOLUMES], parser.volume_order,
                f"{language}: volume order",
            )
            self.assertEqual(expected, parser.section_volume, language)
            for volume, _sections in VOLUMES:
                self.assertIn(VOLUME_TITLES[language][volume], source, language)

    def test_classical_anchors_are_present_in_their_sections(self) -> None:
        for language, path in ARTICLES.items():
            source, _parser = load(path)
            for section, per_language in CLASSICAL_ANCHORS.items():
                start = source.find(f'<section id="{section}"')
                self.assertNotEqual(-1, start, f"{language}: section {section}")
                end = source.find("</section>", start)
                self.assertNotEqual(-1, end, f"{language}: unclosed {section}")
                body = source[start:end]
                for anchor in per_language[language]:
                    self.assertIn(anchor, body, f"{language}: {section} needs {anchor}")

    def test_classical_citations_are_not_graded_as_fact(self) -> None:
        for language, path in ARTICLES.items():
            source, _parser = load(path)
            terms = CLASSICAL_TERMS[language]
            boxes = re.findall(
                r'<div class="claim-box" data-claim-type="([^"]+)">((?:(?!</div>).)*)',
                source,
                re.S,
            )
            self.assertTrue(boxes, f"{language}: no claim-box found")
            for kind, body in boxes:
                if any(term in body for term in terms):
                    self.assertIn(
                        kind,
                        {"analogy", "thesis"},
                        f"{language}: classical claim graded as '{kind}'",
                    )
            self.assertTrue(
                any(name in source for name in CITATION_SOURCES[language]),
                f"{language}: no classical source named",
            )
            lowered = source.lower()
            for phrase in FORBIDDEN_TELEOLOGY:
                self.assertNotIn(phrase.lower(), lowered, f"{language}: {phrase}")

    def test_chain_reproduction_block_is_present(self) -> None:
        required = (
            "sdd_context.py",
            "cat-no-dn",
            "AD-014",
            "DN;",
        )
        for language, path in ARTICLES.items():
            source, _ = load(path)
            for token in required:
                self.assertIn(token, source, f"{language}: {token}")
            self.assertRegex(source, r"exit|退出码|\$\?")
            self.assertIn("2", source)

    def test_ids_and_local_assets_are_valid(self) -> None:
        for language, path in ARTICLES.items():
            _, parser = load(path)
            duplicates = [i for i, c in Counter(parser.ids).items() if c > 1]
            self.assertEqual([], duplicates, language)
            for ref in parser.refs:
                parsed = urlparse(ref)
                if parsed.scheme or ref.startswith(("/", "#", "data:", "mailto:")):
                    continue
                self.assertTrue(
                    (path.parent / parsed.path).resolve().exists(),
                    f"{language}: {ref}",
                )

    def test_seo_language_links_and_json_ld_are_complete(self) -> None:
        for language, path in ARTICLES.items():
            source, parser = load(path)
            self.assertEqual([CANONICAL[language]], parser.canonicals, language)
            self.assertEqual({"en", "zh-CN", "x-default"}, parser.hreflangs, language)
            self.assertIn('property="og:type" content="article"', source)
            article_data = [i for i in parser.json_ld if i.get("@type") == "Article"]
            self.assertEqual(1, len(article_data), language)
            for field in (
                "headline",
                "description",
                "author",
                "publisher",
                "datePublished",
                "dateModified",
                "articleSection",
                "mainEntityOfPage",
            ):
                self.assertIn(field, article_data[0], f"{language}: {field}")
            self.assertEqual("2026-09-05", article_data[0]["datePublished"], language)
            self.assertEqual("Intelligence", article_data[0]["articleSection"], language)

    def test_links_to_thesis_and_mechanism_pages(self) -> None:
        for language, path in ARTICLES.items():
            source, _ = load(path)
            self.assertIn("/agentic.html", source, language)
            self.assertIn("/engineering.html", source, language)

    def test_blog_index_lists_article(self) -> None:
        source = BLOG_INDEX.read_text(encoding="utf-8")
        self.assertIn(f"/blog/{SLUG}/", source)
        self.assertIn('data-cat="intelligence"', source)
        self.assertIn("Seven Billion Tokens", source)
        self.assertIn("Sep 5, 2026", source)

    def test_sitemap_lists_both_languages(self) -> None:
        source = SITEMAP.read_text(encoding="utf-8")
        self.assertIn(CANONICAL["en"], source)
        self.assertIn(CANONICAL["zh"], source)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **步骤 2：跑测试，确认按预期变红**

```zsh
cd /Users/cheenle/HAM/website/portal
/usr/bin/python3 -m pytest tests/test_seven_billion_tokens_article.py -q
```

预期（**已用 dry-run 实测确认，不是推测**）：

```
4 failed, 15 skipped in 0.06s
```

- **4 failed**：`test_articles_and_css_exist`（`article.css` 不存在）、`test_blog_index_lists_article`（卡片尚无）、`test_sitemap_lists_both_languages`（sitemap 尚无）、`test_stale_numbers_are_gone`
- **15 skipped**：其余方法都经 `load()` 抛 `unittest.SkipTest`（文章文件尚不存在）
- 合计 **19 个测试方法**

`test_stale_numbers_are_gone` 的失败信息必须逐字为：

```
AssertionError: Lists differ: [] != ['180+ tests', '593 tests', 'v1.10.1'] : index.html
```

**若该条没有变红、或红出来的旧值列表与上面不同，说明 `STALE_NUMBERS` 常量或 `portal/index.html` 的现状与普查不符 —— 停下核实，不要继续。**

- [ ] **步骤 3：确认既有 4 个测试文件仍然全绿（基线）**

```zsh
cd /Users/cheenle/HAM/website/portal
/usr/bin/python3 -m pytest tests -q --ignore=tests/test_seven_billion_tokens_article.py
```

预期（**已实测**）：`32 passed in 0.32s`。这一步确立基线 —— 之后任何红都能归因到本次改动。

- [ ] **步骤 4：提交（红测试单独一次 commit）**

```zsh
cd /Users/cheenle/HAM/website
git add portal/tests/test_seven_billion_tokens_article.py
git diff --cached --name-only          # 确认只有这一个文件
git commit -m "test(portal): 《Seven Billion Tokens》契约测试先行（红）

13 个 section id、四类 data-claim-type、R1/R2/R4 禁句与 gate 归属、
29 个台账数字常量、旧值清除、估算标注、SEO/JSON-LD、卡片与 sitemap。
本提交后测试为红：文章、卡片、sitemap 尚未存在，portal/index.html 仍含 180+ tests。

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 2（B1）：`article.css` + EN 正文

**Files:**
- Create: `portal/blog/seven-billion-tokens/article.css`
- Create: `portal/blog/seven-billion-tokens/index.html`

**Interfaces:**
- Consumes: Task 1 的 `REQUIRED_SECTIONS`（13 个 id，一字不差）、`LEDGER_CONSTANTS`（29 个数字串必须逐字出现）、`FORBIDDEN["en"]`、`CANONICAL["en"]`
- Produces: 供 Task 3（ZH）逐节对齐的 EN 结构 —— 13 个 `<section id>` 的顺序与 id、每个 claim-box 的 `data-claim-type` 位置、`.ledger-table` / `.term-block` / `.prov` 三个类名

- [ ] **步骤 1：写 `article.css`**

`.claim-box` 与 `.claim-label` 从 `portal/blog/connections-recursive-intelligence/article.css` **原样移植**（含四色：fact `#22c55e` / inference `#22d3ee` / analogy `#f59e0b` / thesis `#a78bfa`，每型两条规则）。然后追加本文私有的三个类：

```css
/* ---- ledger table: the opening evidence table ---- */
.ledger-table { width: 100%; border-collapse: collapse; margin: 1.5rem 0; font-size: 0.9rem; }
.ledger-table th, .ledger-table td { border: 1px solid var(--border); padding: 0.5rem 0.65rem; text-align: left; vertical-align: top; }
.ledger-table th { background: rgba(34, 211, 238, 0.06); font-family: var(--font-mono); font-size: 0.72rem; letter-spacing: 0.06em; text-transform: uppercase; }
.ledger-table td.num { font-family: var(--font-mono); text-align: right; white-space: nowrap; }
.ledger-table tr.total td { font-weight: 700; background: rgba(34, 211, 238, 0.04); }
.ledger-table caption { caption-side: bottom; font-size: 0.78rem; color: var(--text-secondary); padding-top: 0.5rem; text-align: left; }

/* ---- term-block: reproducible command + real output ---- */
.term-block { margin: 1.5rem 0; border: 1px solid var(--border); border-radius: 0.75rem; overflow: hidden; background: #06090d; }
.term-block .term-head { font-family: var(--font-mono); font-size: 0.7rem; letter-spacing: 0.08em; text-transform: uppercase; color: var(--text-secondary); padding: 0.45rem 0.8rem; border-bottom: 1px solid var(--border); }
.term-block pre { margin: 0; padding: 0.85rem; overflow-x: auto; font-family: var(--font-mono); font-size: 0.8rem; line-height: 1.55; }
.term-block .exit { color: #22c55e; }

/* ---- prov: the minimum evidence record under a claim ---- */
.prov { font-family: var(--font-mono); font-size: 0.74rem; line-height: 1.7; color: var(--text-secondary); border-left: 2px solid var(--border); padding-left: 0.75rem; margin: 0.75rem 0 0; }
.prov b { color: var(--text-primary); font-weight: 600; }

/* ---- volume: the three-movement wrapper (spec §5.0) ----
   MUST be a <div data-volume>, never a <section>: the contract test asserts
   section_ids == REQUIRED_SECTIONS exactly, so a wrapper <section> would add
   three unexpected ids and fail. div_depth must return to 0 (balanced tags). */
.volume { margin: 3.5rem 0 0; }
.volume-head { border-top: 1px solid var(--border); padding-top: 1.25rem; margin-bottom: 2rem; }
.volume-head .volume-num { font-family: var(--font-mono); font-size: 0.7rem; letter-spacing: 0.14em; text-transform: uppercase; color: var(--accent); display: block; margin-bottom: 0.35rem; }
.volume-head h2 { font-size: 1.6rem; margin: 0 0 0.4rem; }
.volume-head .volume-gloss { font-size: 0.9rem; color: var(--text-secondary); margin: 0; }
.volume[data-volume="gewu"] .volume-head .volume-num { color: #f59e0b; }
.volume[data-volume="zhizhi"] .volume-head .volume-num { color: #22d3ee; }
.volume[data-volume="zhixing"] .volume-head .volume-num { color: #a78bfa; }

/* ---- stale: a superseded number, quoted only to be struck through ----
   The contract test strips <del class="stale">…</del> before checking that no
   stale number survives as a live claim, and separately requires the `drift`
   section to quote at least three of them inside this element. So: use it for
   every superseded value you name, and never for a current one. */
del.stale { font-family: var(--font-mono); color: #f87171; text-decoration: line-through; text-decoration-thickness: 1px; opacity: 0.85; white-space: nowrap; }
.stale-pair { font-family: var(--font-mono); font-size: 0.86rem; white-space: nowrap; }
.stale-pair .arrow { color: var(--text-secondary); margin: 0 0.35rem; }
```

- [ ] **步骤 2：写 EN `index.html` 的 head 与骨架**

head 必须逐字包含（契约测试断言 canonical 恰好等于 `CANONICAL["en"]`、hreflang 恰好为三值集合、JSON-LD `datePublished == "2026-09-05"` 且 `articleSection == "Intelligence"`）：

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Seven Billion Tokens, One Field Incident — VLSC Blog</title>
    <meta name="description" content="A reproducible end-to-end account of agentic engineering: 7,007,437,567 tokens across seven agent harnesses, one field frequency-drift incident, and the machinery that made the spend safe. Every number carries provenance and limits.">
    <meta name="keywords" content="agentic engineering, AI agent harness, token accounting, evidence discipline, living SDD, constraint registry, forward deployed engineering, amateur radio">
    <meta name="author" content="BG1SB">
    <meta property="og:type" content="article"><meta property="og:title" content="Seven Billion Tokens, One Field Incident"><meta property="og:description" content="What it actually takes to let agents ship: a ledger-first account with provenance on every number."><meta property="og:url" content="https://www.vlsc.net/blog/seven-billion-tokens/"><meta property="og:site_name" content="VLSC Projects">
    <link rel="canonical" href="https://www.vlsc.net/blog/seven-billion-tokens/">
    <link rel="alternate" hreflang="en" href="https://www.vlsc.net/blog/seven-billion-tokens/">
    <link rel="alternate" hreflang="zh-CN" href="https://www.vlsc.net/blog/seven-billion-tokens/zh/">
    <link rel="alternate" hreflang="x-default" href="https://www.vlsc.net/blog/seven-billion-tokens/">
    <link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="../../css/octen.css?v=6"><link rel="stylesheet" href="../../css/blog.css?v=1"><link rel="stylesheet" href="article.css?v=1"><link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script type="application/ld+json">{"@context":"https://schema.org","@type":"Article","headline":"Seven Billion Tokens, One Field Incident","description":"A ledger-first, reproducible account of agentic engineering from field intent to delivery and self-correction.","author":{"@type":"Person","name":"BG1SB","url":"https://github.com/cheenle"},"publisher":{"@type":"Organization","name":"VLSC Projects","url":"https://www.vlsc.net/"},"datePublished":"2026-09-05","dateModified":"2026-09-05","keywords":"agentic engineering, harness, living SDD, constraint registry, evidence discipline","articleSection":"Intelligence","mainEntityOfPage":"https://www.vlsc.net/blog/seven-billion-tokens/"}</script>
</head>
<body data-site="portal">
<article class="blog-article">
    <nav class="blog-breadcrumb"><a href="/">Home</a> › <a href="/blog/">Blog</a> › <span class="blog-cat">Intelligence</span> › Seven Billion Tokens</nav>
    <div class="article-language"><a href="zh/" lang="zh-CN">中文版</a></div>
    <header class="blog-header"><div class="blog-cat-badge"><i class="fas fa-receipt"></i> Intelligence</div><h1>Seven Billion Tokens, One Field Incident</h1><p class="blog-subtitle">What it actually takes to let agents ship — from one business intent to delivery, use, and self-correction</p><div class="blog-meta">By BG1SB &nbsp;·&nbsp; <time datetime="2026-09-05">Sep 5, 2026</time> &nbsp;·&nbsp; ~30 min read</div><ul class="blog-tags"><li><a href="/blog/">#agentic-engineering</a></li><li><a href="/blog/">#evidence</a></li><li><a href="/blog/">#harness</a></li><li><a href="/blog/">#living-sdd</a></li></ul></header>
    <nav class="blog-toc" id="blog-toc" aria-label="Table of contents"></nav>
    <div class="blog-content">
```

正文的三卷嵌套结构（**`<div class="volume">` 不是 `<section>`**；`references` 不包裹）：

```html
        <div class="volume" data-volume="gewu">
            <header class="volume-head"><span class="volume-num">Volume I</span><h2>Investigating Things</h2><p class="volume-gloss">格物 — go to the thing itself. Five sections on what the transcripts, the test runs and the radio actually said, and on two ways of failing to look.</p></header>
            <section id="ledger">…</section>
            <section id="floor">…</section>
            <section id="numbers-lie">…</section>
            <section id="intent">…</section>
            <section id="before">…</section>
        </div>

        <div class="volume" data-volume="zhizhi">
            <header class="volume-head"><span class="volume-num">Volume II</span><h2>Extending Knowledge</h2><p class="volume-gloss">致知 — 物格而后知至. How an observation becomes a contract a machine can read, and how 52 of them become an ontology.</p></header>
            <section id="machine">…</section>
            <section id="chain">…</section>
            <section id="scale">…</section>
        </div>

        <div class="volume" data-volume="zhixing">
            <header class="volume-head"><span class="volume-num">Volume III</span><h2>Unity of Knowing and Acting</h2><p class="volume-gloss">知行合一 — 知而不行，只是未知. Delivery, the drift that proves knowledge stops being knowledge, and what a human still signs.</p></header>
            <section id="delivery">…</section>
            <section id="drift">…</section>
            <section id="human">…</section>
            <section id="playbook">…</section>
        </div>

        <section id="references">…</section>
```

每个 `<div class="volume">` 必须正确闭合 —— 契约测试断言 `parser.div_depth == 0`。卷题字符串 `Investigating Things` / `Extending Knowledge` / `Unity of Knowing and Acting` 必须逐字出现（`VOLUME_TITLES["en"]`）。

尾部与 connections 一文同构（作者块 + Related reading + `</article>`）。**必须包含指向 `/agentic.html` 与 `/engineering.html` 的链接**（契约测试断言）。

- [ ] **步骤 3：写 `ledger` 节（开场即台账）**

必须包含：
- 一张 `.ledger-table`，7 行工具 + 1 行小计，列为 `Harness / Tokens / Turns / Sessions / Provenance / Span`，数值用 `<td class="num">`。数值**逐字**取自 Global Constraints：claude-code `3,129,411,481`/`21,648`/`194`；pi `1,625,562,962`/`8,719`/`60`；kimi-code `1,201,837,537`/`9,769`/`229`；codex `547,796,667`/`717`/`116`；mulerun `471,558,325`/`181`/`181`；cursor `27,079,705`/`217`/`96`；opencode `4,190,890`/`6`/`6`；小计 `7,007,437,567`/`41,257`/`882`。
- `<caption>` 写明 census `2026-09-05`、机器（macOS, arm64）、方法（解析本机各 harness 会话库）。
- 三个结构数字：`95.2%` cache-read、`4.8%` fresh（`336,661,475`）、模型输出 `30,061,161`。
- Pi 成本：`$15.11` / `1,625,562,962` = `$9.30` per billion，并注明"唯一自己计价的 harness"。
- 一个 `data-claim-type="fact"` 的 `.claim-box`，其下紧跟 `.prov` 块，八字段齐全（`Claim · Source artifact · Version / commit · Environment · Verification method · Result · Limitations · Date`）。

- [ ] **步骤 4：写 `floor` 节（为什么这是下限）**

必须包含 iFlow `37,202` 轮 / 估算 `234,247,399`（**且 900 字符窗口内出现 `estimate` 或 `not recorded`**，契约测试 `test_estimates_are_labelled` 会查）、Hermes `292` 会话 / `9,121` 消息 / `4,336` 工具调用 / `token_count` 列全空、Qoder 是 Cursor 严格子集（0 条独有）、Cursor `ai-code-tracking.db` 6 表 5 空、Claude Code 留存只到 `2026-08-05` 而 MRRC 仓始于 `2026-03-06`、Cursor 不记 cwd 故 `27,079,705` 无法按仓库归属。

- [ ] **步骤 5：写 `numbers-lie` 节（含自纠错）**

必须包含 `5,380,941,148`（**900 字符窗口内出现 `estimate` / `not recorded` 之一** —— 用 "first-pass figure, since corrected" 这类措辞时，必须同时带上 `not recorded` 或 `estimate` 字样以满足断言；最稳妥写法是明说 "the first pass was wrong in two directions: it missed Pi/MuleRun/Cursor/opencode, and it double-counted"），以及 `546,858,767`（Codex 自己 DB 的 `threads.tokens_used`，是发现语义错误的线索）。必须解释两处重复计：Codex `cached_input_tokens ⊂ input_tokens`；Pi `totalTokens` 已含各分量。并引 `engineering.html` 的六种"看起来像速度的失败模式"。

- [ ] **步骤 6：写 `intent` / `before` / `machine` 三节**

- `intent`：FT-710 远程诉求；原厂 SCU-LAN10 是专有配件；诉求是"一根已有的 USB 线"；Echo 观测到 USB serial/audio 行为与 FT4222 SPI 可出真频谱（~21fps）。
- `before`：iFlow 时代 `2025-10-20 → 2026-04-16`，`185` 会话 / `37,202` 轮 / 6 个模型（glm-5 `17,925`、qwen3-coder-plus `6,706`、kimi-k2.5 `6,500`、minimax-m2.5 `4,315`、glm-4.7 `1,080`、iFlow-ROME-30BA3B `673`）/ **零 harness**。其中 `-Users-cheenle-UHRR-MRRC` `13,219` 轮、`UHRR_mac` `15,674` 轮、pskreporter `3,193` 轮。对照成熟度阶梯 1 Ad hoc → 2 Repeatable。
- `machine`：外层约束 harness（Business `WHY · WHO · SUCCESS` / Technical `HOW · BOUNDARIES · PROOF` / Product `DELIVERABLE · ACCEPTANCE · REUSE`）× 内层执行 harness（Human+AI Agents → Repository+SDD → Tools+Diagnostics → Tests+Review → Deployment → Field Telemetry）；嵌套双环（外 `Echo → Delta → Product`，内 `Specify → Implement → Test → Review → Deploy/Observe → Update SDD`）；Living SDD 8 个生命周期状态；最小证据记录 8 字段。

- [ ] **步骤 7：写 `chain` 节（全文证明点）**

必须包含一个 `.term-block`，内容是**真实命令与真实输出**（不得改写）：

```
$ python3 .agents/skills/sdd-guardian/harness/sdd_context.py check probe_b4_tmp.py
SDD-GUARDIAN: blocking violations found:
[BLOCK] cat-no-dn (AD-014; SDD V1.2 freq-drift incident) probe_b4_tmp.py:2: return c.query("DN;")
 → On the FT-710, 'DN;' is NOT a DNR query — it steps the active VFO DOWN ~20 Hz per call.
   Polling it caused a live frequency-drift incident (V1.2). DNR level is intentionally not polled.
$ echo $?
2
```

叙事顺序：现场事故（每 2 秒轮询 `DN;` → 实机频率下漂 ~20 Hz/次，V1.2）→ SDD 裁决 `AD-014` → 机器可读约束 `cat-no-dn`（severity `block`，带 `sdd_ref`、`scope` glob、`patterns`）→ `install_hooks.py` 注册 `SessionStart → prime` 与 `PreToolUse(Edit|Write) → hook` → 编辑落地前被拒，退出码 `2`。必须写明 `harness/index.json` 不存内容、引用实时切自 `SDD/*.md`，因此不会变陈旧。

- [ ] **步骤 8：写 `scale` / `delivery` / `drift` 三节**

- `scale`：按仓库 token 表（ft8 `1,875,258,566`；mrrc_ft710 `1,275,611,389`；mrrc_modern `1,260,804,213`；MRRC `1,150,197,250`；website `819,343,926`；sunsdr `64,490,898`；pskreporter `54,409,498`；efhw-knowledge `45,949,584`；wfview `23,459,822`；未归属 `410,832,716`；可归属合计 `6,980,357,862`，无线电生态小计 `6,491,655,826`）。校验式必须写出：`6,980,357,862 + 27,079,705 = 7,007,437,567`。`52` 条约束（`17`/`21`/`14`）随事故生长；`mrrc_modern` 与 `mrrc_ft710` 共享同一 initial commit `9403e2e`；`ft8` 首个提交 `d4a7a32` 同时引入 `AGENTS.md` + `SDD` + `sdd-guardian`；commit `2bc3d30` "SDD V2.23 — record issues I8-I11, expand sdd-guardian harness to 21 rules"。
- `delivery`：实测 `439`（FT-710，`Ran 439 tests ... OK`）、`682`（Modern，含 1 个 `test_macos_launcher` loader error，macOS 导入失败，非产品缺陷）、`937` collected（FT8，pytest，collected ≠ passed）。部署机制：校验→打包→远端备份→scp→解包→权限→reload nginx；三条安全规则（远端 heredoc 必须 `<<'REMOTE'` 引号化、`tar -x` 从不删除、备份按站瘦身 `rsync --exclude downloads --exclude videos` 且只留 3 份、回滚只还自己那一目录）；共享 DocumentRoot 禁止整根 `rm -rf` / `chown -R`。
- `drift`：本次现场抓到的四类漂移 —— ① `portal/index.html` 的过时数字；② 台账 Modern 行落后一个补丁（`v1.12.0`/`633` → `v1.12.1`/`682`）；③ 三个仓库注册表的 `sdd_version` 全部滞后（ft710 `V1.7` vs SDD `v1.8.0`；modern `V2.27` vs `V2.30`；ft8 `V1.0` vs `V1.8`）；④ **反向案例**：FT-710 的 git tag / SDD README / 子站都说 `v1.8.0`，只有 `CHANGELOG.md` 有 `[v1.8.1] — 2026-08-16`，而台账"Source: v1.8.1 / Windows package: v1.8.0"的双字段写法是唯一正确的 —— 差一点就把对的数字改错。必须写明结论：**带日期的历史记录不得被"更新"**（`mrrc_modern/sdd.html` 的 "Published after 633/633 tests" 是 v1.12.0 的发布记录，改成 682 就是造假）。

  **⚠️ 硬性标记要求**：本节凡引用一个**已被推翻的旧值**，必须包在 `<del class="stale">` 里，并紧跟新值。原因是契约测试有两条互锁的断言：`test_stale_numbers_are_gone` 会先剥掉 `<del class="stale">…</del>` 再检查旧值是否作为**活的声明**残留；`test_drift_section_quotes_stale_values_as_struck_through` 反过来要求 `drift` 节内至少 3 处 `<del class="stale">`，且其中必须能看到 `180+`、`593`、`v1.10.1` 三个串。**裸写 `180+ tests` 会让前一条红；不写又会让后一条红。** 推荐写法：

```html
<p>The landing page carried <span class="stale-pair"><del class="stale">V1.0 · 180+ tests</del><span class="arrow">→</span>v1.8.1 · 439 tests</span> for the FT-710, and <span class="stale-pair"><del class="stale">v1.10.1 · 593 tests</del><span class="arrow">→</span>v1.12.1 · 682 tests</span> for Modern. Both were verified by running the suites, not by reading a document.</p>
```

  注意 `40 tests`（FT8 旧值）**不在** `STALE_NUMBERS` 里，裸写无害，但为了体例一致也建议同样标记。

- [ ] **步骤 9：写 `human` / `playbook` / `references` 三节**

- `human`：人保留 Intent / Boundaries / Judgment；四件不可压缩（Hardware PCB+bench、RF safety PTT、Live stations、Publication）；**FT710Mobile 有未解决的 P0 PTT 安全问题**，服务端自动化测试与其他客户端结果都不能关闭它；EFHW V3.0 只有 `B2 spec / plan trail`，无台架验证前不得声称 bench/field-verified；**两条阶梯不相交**（A 级产品成熟度：design target → simulation → automated test → bench-verified → field-verified → released → deferred/known-issue；B 级过程约束：`B1` 注册表条目 → `B2` spec/plan trail → `B3` 会话内执行 → `B4` 拦截已验证）。B4 永不提升 A 级。
- `playbook`：7 步可迁移做法 + 成熟度 1–5 自评 + `engineering.html` 的 7 条评审清单。至少一个 `data-claim-type="analogy"` 与一个 `data-claim-type="thesis"` 的 claim-box（契约测试要求四类齐全）。
- `references`：完整溯源清单（每个数字的来源路径 / 命令 / census 日期）、站内链接（`/agentic.html`、`/engineering.html`、五个产品族）、标准引用（Stanford Ontology Development 101、W3C PROV-O、SOSA/SSN、SKOS、Time、WoT Thing Description、ETSI SAREF、QUDT）。

- [ ] **步骤 9b：五处经典对应（EN 措辞，契约测试逐个断言）**

`test_classical_anchors_are_present_in_their_sections` 会在**指定 section 的 `<section id="X"` 与 `</section>` 之间**逐字查找下列字符串。措辞可自然嵌入正文，但这几个串必须原样出现：

| section | 必须逐字出现（EN） | claim-type | 出处（须在 references 或就地注明） |
|---|---|---|---|
| `before` | `investigating the bamboo` | **analogy** | 王阳明格竹七日而病，《传习录》 |
| `numbers-lie` | `investigating things` | thesis | 「致知在格物」，《大学》 |
| `chain` | `things investigated` **与** `knowledge arrives` | fact（指链条本身）+ thesis（指对应） | 「物格而后知至」，《大学》 |
| `scale` | `sudden thorough comprehension` | analogy | 朱熹《大学章句》补传「一旦豁然贯通焉」 |
| `human` | `knowing and not acting` | thesis | 「知而不行，只是未知」，《传习录》 |

三条纪律：

1. **经典对应只能是 `analogy` 或 `thesis`，不得是 `fact`。** `test_classical_citations_are_not_graded_as_fact` 会扫描每个 `<div class="claim-box" data-claim-type="...">`，只要正文里出现 `bamboo` / `investigating things` / `extending knowledge` / `unity of knowing` / `comprehension` 任一词，其 `data-claim-type` 就必须是 `analogy` 或 `thesis`。`chain` 节里那条链**本身**是 fact（有命令有退出码），但「这条链就是物格而后知至」这句对应必须是独立的 thesis claim-box —— **两者不要写进同一个 claim-box**。
2. **必须点名出处**：EN 页至少出现 `Great Learning` / `Chuanxi` / `Zhu Xi` / `Wang Yangming` 之一。
3. **禁止目的论断言**：不得出现 `already had agentic` / `invented agentic`（ZH 页不得出现 `早就有了`）。古典概念是用来照见方法的，不是用来主张优先权的。

- [ ] **步骤 9c：三卷卷题与卷首引语**

三处 `.volume-head` 的 `<h2>` 必须逐字为 `Investigating Things`、`Extending Knowledge`、`Unity of Knowing and Acting`（`VOLUME_TITLES["en"]`）。每卷 `.volume-gloss` 用一句话交代该卷与「格物 / 致知 / 知行合一」的对应，并列出本卷包含的节 —— 但 **EN 页不得出现「格物致知」四字连用**（`assertNotIn(ZH_TITLE, en_source)`）。允许出现单个词的拼音或分开的英文释义；最稳妥的写法是 gloss 全用英文，把中文术语只留在 ZH 页。

- [ ] **步骤 10：跑测试，确认 EN 相关断言转绿**

```zsh
cd /Users/cheenle/HAM/website/portal
/usr/bin/python3 -m pytest tests/test_seven_billion_tokens_article.py -q
```

预期：`test_articles_and_css_exist` 仍红（缺 zh）；`test_sections_and_claim_types_match`、`test_ledger_constants_appear_verbatim`、`test_estimates_are_labelled`、`test_gate_claims_only_near_owning_repos`、`test_forbidden_phrases_absent`、`test_chain_reproduction_block_is_present`、`test_ids_and_local_assets_are_valid`、`test_seo_language_links_and_json_ld_are_complete`、`test_links_to_thesis_and_mechanism_pages` 中凡只依赖 EN 的断言应通过；凡遍历两语言的仍红。

**若 `test_ledger_constants_appear_verbatim` 报缺失，逐个补齐 —— 不得为了让测试过而修改测试里的常量值。** 常量值来自 census，是唯一真值。

- [ ] **步骤 11：提交**

```zsh
cd /Users/cheenle/HAM/website
git add portal/blog/seven-billion-tokens/article.css portal/blog/seven-billion-tokens/index.html
git diff --cached --name-only
git commit -m "feat(blog): 《Seven Billion Tokens, One Field Incident》EN 正文 + article.css

台账先行：开场即 7,007,437,567 tokens / 41,257 轮 / 882 会话的七工具普查表，
每条声明带最小证据记录与四类 data-claim-type 标记。

13 节按三卷组织（div.volume，非 section）：卷一 Investigating Things
（格物：ledger/floor/numbers-lie/intent/before）、卷二 Extending Knowledge
（致知：machine/chain/scale）、卷三 Unity of Knowing and Acting
（知行合一：delivery/drift/human/playbook），references 为卷外附录。
五处经典对应按 spec §5.0 落位，均标 analogy/thesis 并点名出处。
EN 页不出现「格物致知」四字——两个标题框架不互相稀释。

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 3（B2）：ZH 正文

**Files:**
- Create: `portal/blog/seven-billion-tokens/zh/index.html`

**Interfaces:**
- Consumes: Task 2 的 EN 13 个 section id 与顺序、每个 claim-box 的 `data-claim-type`、`.ledger-table` / `.term-block` / `.prov` 类名、`LEDGER_CONSTANTS` 全部 29 个数字串
- Produces: EN/ZH 结构对等（`test_sections_and_claim_types_match` 断言两版 `section_ids` 集合相等）

- [ ] **步骤 1：复制 EN 骨架，替换标题、lang 与互链方向**

ZH 标题为 **《格物致知 —— Agentic AI 的思考》**，出现在三处且**只**在这三处：

```html
<title>格物致知 —— Agentic AI 的思考 — VLSC Blog</title>
...
<h1>格物致知 —— Agentic AI 的思考</h1>
...
<script type="application/ld+json">{"@context":"https://schema.org","@type":"Article","headline":"格物致知 —— Agentic AI 的思考", ... ,"datePublished":"2026-09-05","dateModified":"2026-09-05","articleSection":"Intelligence", ...}</script>
```

`blog-subtitle` 用：`七十亿 token、一次现场频漂事故，以及让这笔开销变得安全的那套机器 —— 每个数字都带溯源与局限，包括我算错的那些`。

其余替换：`<html lang="zh-CN">`；`.article-language` 改为 `<a href="../" lang="en">English</a>`（契约测试断言 `href="../"` 逐字出现）；canonical 改为 `https://www.vlsc.net/blog/seven-billion-tokens/zh/`；三条 hreflang 的 URL 相应调整（en 指 EN 绝对 URL，zh-CN 指自身，x-default 指 EN）；样式路径深一层：`../../../css/octen.css?v=6`、`../../../css/blog.css?v=1`、`../article.css?v=1`。JSON-LD `datePublished` 仍为 `2026-09-05`，`articleSection` 仍为英文字面值 `Intelligence`（契约测试断言）。

- [ ] **步骤 2：逐节翻译，保持 id、三卷分组与断言类型不变**

13 个 `<section id>` 一字不改；三个 `<div class="volume" data-volume="...">` 的 `data-volume` 值与嵌套关系一字不改（`gewu` / `zhizhi` / `zhixing`，`references` 在卷外）。每个 claim-box 的 `data-claim-type` 与 EN 同位置同值。**29 个数字串逐字保留**（含千分位逗号与 `$15.11`、`95.2`、`4.8`）—— 契约测试对 ZH 同样断言 `LEDGER_CONSTANTS` 全部出现。

三卷卷题必须逐字为（`VOLUME_TITLES["zh"]`，测试会在全文查找这三个串）：**格物**、**致知**、**知行合一**。建议 `.volume-head` 写法：

```html
<header class="volume-head"><span class="volume-num">卷一</span><h2>格物 · Investigating Things</h2><p class="volume-gloss">到现场去问那个东西。五节讲会话库、测试运行与电台各自实际说了什么，以及两种「不去看」的失败。</p></header>
```

（`卷二 · 致知 · Extending Knowledge`、`卷三 · 知行合一 · Unity of Knowing and Acting` 同构。ZH 页可以中英并列，EN 页不行。）

术语强制（R4，`test_zh_uses_mandated_terminology` 断言）：
- 必须出现 **智能体工程**、**前沿部署工程**
- 必须**不出现** `代理式工程`
- `data-claim-type` 四类的中文标签：fact = 事实、inference = 推论、analogy = 类比、thesis = 主张
- `harness` 全文统一一种译法（建议保留英文 `harness`，与 `zh/engineering.html` 一致）；`Living SDD` 译 **活的双向契约**（与 `zh/engineering.html` 的 `04 · 活的双向契约` 一致）
- `pre-edit gate` 译 **编辑前门禁**（契约测试的 R2 正则已含此串）

**五处经典对应的 ZH 逐字要求**（`CLASSICAL_ANCHORS[...]["zh"]`，测试在指定 section 内查找）：

| section | 必须逐字出现 | claim-type |
|---|---|---|
| `before` | `格竹`（阳明格竹七日而病 ↔ iFlow 时代 37,202 轮 / 6 模型 / 零注册表） | **analogy** |
| `numbers-lie` | `致知在格物`（致知在格物，不在台账 ↔ 我自己的 5,380,941,148 是一次不格物） | thesis |
| `chain` | `物格而后知至`（电台实际行为 → SDD 裁决 → 机器可读约束 → 运行时拦截） | thesis |
| `scale` | `豁然贯通`（朱子「今日格一物，明日格一物，积习既多，然后脱然自有贯通处」↔ 17→21→14） | analogy |
| `human` | `知而不行`（知而不行，只是未知 ↔ 一条不会 block 的约束等于没有这条约束） | thesis |

出处须点名：`《大学》`、`朱熹《大学章句》补传`、`王阳明《传习录》` 至少各出现一次（测试要求 `大学` / `传习录` / `大学章句` 至少命中一个）。**不得**出现 `早就有了` 这类目的论断言。

`chain` 节的 `.term-block` **不翻译**（命令与输出是逐字证据），但其前后的叙述翻译。

- [ ] **步骤 3：跑测试，确认两版对等断言转绿**

```zsh
cd /Users/cheenle/HAM/website/portal
/usr/bin/python3 -m pytest tests/test_seven_billion_tokens_article.py -q -k "sections or titles or volumes or classical or zh or forbidden or estimates or gate or chain or ids or seo or links or ledger"
```

预期：以上全部 PASS。仍红的只应剩下 `test_stale_numbers_are_gone`（Task 5 修）、`test_blog_index_lists_article`、`test_sitemap_lists_both_languages`（Task 4 修）。

- [ ] **步骤 4：人工核对 EN/ZH 结构对等（含三卷）**

```zsh
cd /Users/cheenle/HAM/website/portal/blog/seven-billion-tokens
diff <(grep -oE '<section id="[^"]+"' index.html) <(grep -oE '<section id="[^"]+"' zh/index.html) && echo "SECTIONS IDENTICAL"
diff <(grep -oE 'data-claim-type="[^"]+"' index.html | sort | uniq -c) <(grep -oE 'data-claim-type="[^"]+"' zh/index.html | sort | uniq -c) && echo "CLAIM TYPES IDENTICAL"
diff <(grep -oE 'data-volume="[^"]+"' index.html) <(grep -oE 'data-volume="[^"]+"' zh/index.html) && echo "VOLUMES IDENTICAL"
for f in index.html zh/index.html; do
  printf "  %-16s div open=%s close=%s " "$f" "$(grep -o '<div' $f | wc -l | tr -d ' ')" "$(grep -o '</div>' $f | wc -l | tr -d ' ')"
  [ "$(grep -o '<div' $f | wc -l)" = "$(grep -o '</div>' $f | wc -l)" ] && echo "✓ balanced" || echo "✗ UNBALANCED"
done
grep -c '格物致知' index.html | sed 's/^/  EN 页「格物致知」出现次数（必须为 0）: /'
```

预期：三行 IDENTICAL；两行 ✓ balanced；EN 页计数为 **0**。

若 claim-type 计数不同，说明某处断言在翻译时被降级或升级 —— 修正文，不要改测试。若 EN 页计数非 0，说明卷首 gloss 里混进了中文四字连用 —— 改成英文释义。

- [ ] **步骤 5：提交**

```zsh
cd /Users/cheenle/HAM/website
git add portal/blog/seven-billion-tokens/zh/index.html
git commit -m "feat(blog): 《格物致知 —— Agentic AI 的思考》ZH 正文（与 EN 结构对等）

双标题：EN 保留 Seven Billion Tokens 做台账钩子，ZH 用格物致知做经典框架。
13 节 id、三卷 data-volume 分组与四类断言标记与 EN 完全一致；29 个台账数字逐字保留。

三卷卷题：卷一 格物 / 卷二 致知 / 卷三 知行合一。五处经典对应按 spec §5.0
落位并点名出处（《大学》、朱熹《大学章句》补传、王阳明《传习录》），
一律标 analogy 或 thesis，不标 fact；不作目的论断言。
术语按 R4：智能体工程 / 前沿部署工程；不出现「代理式工程」。
chain 节的命令与输出不翻译——那是逐字证据。

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 4（B3）：blog 卡片 + sitemap 重生成

**Files:**
- Modify: `portal/blog/index.html`（列表首位插入卡片）
- Regenerate: `portal/sitemap.xml`

**Interfaces:**
- Consumes: `SLUG = "seven-billion-tokens"`、`CANONICAL`、卡片标题串 `Seven Billion Tokens`、日期串 `Sep 5, 2026`（`test_blog_index_lists_article` 断言这四者）
- Produces: 无（末梢任务）

- [ ] **步骤 1：在 `blog/index.html` 列表首位插入卡片**

现有卡片格式（逐字复制自 connections 卡片，只换内容）：

```html
        <article class="blog-card" data-cat="intelligence">
            <div class="bc-cat">Intelligence</div>
            <h2><a href="/blog/seven-billion-tokens/">Seven Billion Tokens, One Field Incident</a></h2>
            <p class="bc-excerpt">7,007,437,567 tokens across seven agent harnesses, one field frequency-drift incident, and the machinery that made the spend safe — a ledger-first account where every number carries provenance and limits, including the ones I got wrong.</p>
            <div class="bc-meta">BG1SB · Sep 5, 2026 · ~30 min read</div>
        </article>
```

插入位置：`blog/index.html` 中第一张 `<article class="blog-card"` 之前（本文是最新文章，列表按时间倒序）。**不新增 `data-filter` chip** —— `intelligence` 已存在。

- [ ] **步骤 2：重生成 sitemap（不手工编辑）**

```zsh
cd /Users/cheenle/HAM/website/portal
python3 make_sitemap.py
```

预期输出：`wrote sitemap.xml with N URLs`，N 比改前多 2（EN + zh）。`make_sitemap.py` 用 `os.walk` 遍历 portal 树，会自动收录 `blog/seven-billion-tokens/` 与其 `zh/`。

- [ ] **步骤 3：验证 sitemap 含两条且未丢失既有 URL**

```zsh
cd /Users/cheenle/HAM/website/portal
grep -c '<url>' sitemap.xml
grep -F 'blog/seven-billion-tokens/' sitemap.xml
git diff --stat sitemap.xml
git diff sitemap.xml | grep -c '^-<url>' || echo "0 removed"
```

预期：两条新 URL 都在；`0 removed`（或仅 lastmod 日期变化导致的行替换）。**若有 URL 被删除，停下排查** —— 已知 `make_sitemap.py` 曾有六站 agentic/engineering 收录回归丢失的缺陷（见 commit `eca4be8`）。

- [ ] **步骤 4：跑测试**

```zsh
cd /Users/cheenle/HAM/website/portal
/usr/bin/python3 -m pytest tests/test_seven_billion_tokens_article.py tests/test_sitemap.py -q
```

预期：`test_blog_index_lists_article` 与 `test_sitemap_lists_both_languages` 转绿；`test_sitemap.py` 保持绿。

- [ ] **步骤 5：提交**

```zsh
cd /Users/cheenle/HAM/website
git add portal/blog/index.html portal/sitemap.xml
git diff --cached --name-only
git commit -m "feat(blog): 首页卡片 + sitemap 收录《Seven Billion Tokens》EN/ZH

复用既有 intelligence 类目，不新增筛选 chip。sitemap 由 make_sitemap.py
重生成（os.walk 自动收录），未手工编辑；已核对无既有 URL 丢失。

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 5（B4）：Part 2 数字校正（仅 portal，6 个文件）

**Files:**
- Modify: `portal/index.html`（5 处）、`portal/zh/index.html`（5 处）
- Modify: `portal/agentic.html`、`portal/zh/agentic.html`（Modern 行 + census 日期）
- Modify: `portal/engineering.html`、`portal/zh/engineering.html`（各 2 处 `633`）

**Interfaces:**
- Consumes: `STALE_NUMBERS`（Task 1）—— `test_stale_numbers_are_gone` 会对这 6 个文件断言旧值消失
- Produces: 无

**前置事实（已在普查中核实，不必重查；若要改数字必须先重跑对应命令）**

| 目标值 | 核实命令 | 结果 |
|---|---|---|
| FT-710 `439` | `cd /Users/cheenle/HAM/mrrc_ft710 && venv/bin/python -m unittest discover -s tests` | `Ran 439 tests in 10.675s` / `OK` |
| Modern `682` | `cd /Users/cheenle/HAM/mrrc_modern && venv/bin/python -m unittest discover -s tests` | `Ran 682 tests` / `FAILED (errors=1)`，error = `unittest.loader._FailedTest.test_macos_launcher` |
| FT8 `937` collected | `cd /Users/cheenle/HAM/ft8 && venv/bin/python -m pytest tests -q --collect-only` | `937 tests collected in 1.24s` |
| Modern `v1.12.1` | `grep -ohE 'v1\.12\.[0-9]' /Users/cheenle/HAM/mrrc_modern/SDD/README.md` | `v1.12.1` |
| FT-710 `v1.8.1` | `grep -F '[v1.8.1]' /Users/cheenle/HAM/mrrc_ft710/CHANGELOG.md` | `## [v1.8.1] — 2026-08-16` |
| MRRC `280+ commits` | `git -C /Users/cheenle/HAM/MRRC log --all --oneline \| wc -l` | `326` → **保留不改** |
| SunMRRC `65+` | `git -C /Users/cheenle/HAM/sunsdr log --oneline \| wc -l` | `67` |
| SunsdrMobile `9` | `git -C /Users/cheenle/HAM/sunsdr/SunsdrMobile log --oneline \| wc -l` | `9` |

- [ ] **步骤 1：改 `portal/index.html`（5 处，165 行不动）**

逐条 Edit（old → new）：

| 行 | old | new |
|---|---|---|
| 182 | `<li>V1.0 · 180+ tests · GPLv3</li>` | `<li>v1.8.1 · 439 tests · GPLv3</li>` |
| 198 | `<li>v1.10.1 · 593 tests · GPLv3</li>` | `<li>v1.12.1 · 682 tests · GPLv3</li>` |
| 214 | `<li>V1.0 · 40+ commits · GPLv3</li>` | `<li>V1.0 · 65+ commits · GPLv3</li>` |
| 231 | `<li>V1.0 · 3 commits · MIT</li>` | `<li>V1.0 · 9 commits · MIT</li>` |
| 264 | `<li>v0.1.0 · 40 tests · GPLv3</li>` | `<li>v0.1.0 · 937 tests collected · GPLv3</li>` |

**165 行 `<li>V5.6.5 · 280+ commits · GPLv3</li>` 保持不变**（已核实 326）。

- [ ] **步骤 2：改 `portal/zh/index.html`（对应 5 处）**

| 行 | old | new |
|---|---|---|
| 177 | `<li>V1.0 · 180+ 测试 · GPLv3</li>` | `<li>v1.8.1 · 439 项测试 · GPLv3</li>` |
| 192 | `<li>v1.10.1 · 593 测试 · GPLv3</li>` | `<li>v1.12.1 · 682 项测试 · GPLv3</li>` |
| 207 | `<li>V1.0 · 40+ 提交 · GPLv3</li>` | `<li>V1.0 · 65+ 提交 · GPLv3</li>` |
| 223 | `<li>V1.0 · 3 提交 · MIT</li>` | `<li>V1.0 · 9 提交 · MIT</li>` |
| 255 | `<li>v0.1.0 · 40 测试 · GPLv3</li>` | `<li>v0.1.0 · 937 项测试（collected）· GPLv3</li>` |

**161 行 `280+ 提交` 保持不变。**

- [ ] **步骤 3：改 `portal/agentic.html` 台账 Modern 行 + census 日期**

- 1647 行 `<strong>Version:</strong> v1.12.0` → `v1.12.1`
- 1653 行 `633` → `682`
- 1734 行 `<td>MRRC Modern v1.12.0</td>` → `<td>MRRC Modern v1.12.1</td>`
- Modern 台账行的 limitation 文案：`IC physical-radio acceptance is separately recorded.` → `IC physical-radio acceptance is separately recorded. 682 ran on macOS 2026-09-05 with 1 collection error (test_macos_launcher, a Windows-only launcher test that cannot import on macOS) — an environment limit, not a product defect.`
- census 日期 6 处：629 / 736 / 839 / 937 / 1027 行的 `Census 2026-09-02.` → `Census 2026-09-05.`；1248 行 `(census 2026-09-02)` → `(census 2026-09-05)`；1610 行 `reproduced end to end (2026-09-02)` → `(2026-09-05)`
- **FT-710 行 `v1.8.1` / `439` / `v1.8.0` 全部保持不变**（已核实正确）

改前先确认行号未漂移：

```zsh
cd /Users/cheenle/HAM/website/portal
grep -nF 'v1.12.0' agentic.html; grep -nF '633' agentic.html; grep -nF '2026-09-02' agentic.html
```

- [ ] **步骤 4：改 `portal/zh/agentic.html` 对应处**

- 1376 行 `<strong>版本：</strong>v1.12.0` → `v1.12.1`
- 1378 行 `633 项` → `682 项`
- 1437 行附近的 Modern 台账行同步
- 普查日期 5 处（554-555 / 641 / 725-726 / 802 / 875 行）`2026-09-02` → `2026-09-05`；1056 行 `（普查日期 2026-09-02）` → `2026-09-05`；1343 行 `这条链的端到端复现（2026-09-02）` → `（2026-09-05）`
- Modern limitation 中文补句：`IC 实机验收单列。682 项于 2026-09-05 在 macOS 上运行，1 个收集错误（test_macos_launcher，Windows 专用启动器测试无法在 macOS 导入）——环境局限，非产品缺陷。`

- [ ] **步骤 5：改 `portal/engineering.html`（2 处）**

- 69 行 `633 automated tests do not prove every radio in the field` → `682 automated tests do not prove every radio in the field`
- 80 行族表 `FT-710: 439 tests; Modern: 633 tests.` → `FT-710: 439 tests; Modern: 682 tests.`

- [ ] **步骤 6：改 `portal/zh/engineering.html`（2 处）**

- 26 行 `633 项自动化测试不能证明全部电台已经现场验证` → `682 项自动化测试不能证明全部电台已经现场验证`
- 29 行族表 `FT-710：439 项测试；Modern：633 项测试。` → `FT-710：439 项测试；Modern：682 项测试。`

- [ ] **步骤 7：跑全部测试**

```zsh
cd /Users/cheenle/HAM/website/portal
/usr/bin/python3 -m pytest tests -q
```

预期：**全绿**，包含 `test_stale_numbers_are_gone`（6 个文件都不再含 `180+ tests` / `593 tests` / `v1.10.1` / 及中文版）、`test_agentic_pages.py`、`test_engineering_pages.py`、`test_sitemap.py`、`test_connections_article.py`。

若 `test_agentic_pages.py` 或 `test_engineering_pages.py` 变红：先读失败信息。已核实这两个文件**不含** `439/633/593/682` 等数字字面量（`grep -nE '\b(439|633|593|682|937|180|280)\b' tests/*.py` 无命中），因此若变红，原因必是节结构或禁句断言被我的编辑破坏 —— 修编辑，不改测试。

- [ ] **步骤 8：确认没卷入二维码改动，然后提交**

```zsh
cd /Users/cheenle/HAM/website
git diff --stat
git diff portal/index.html portal/zh/index.html | grep -E '^[+-]' | grep -iE 'qr|Sep 12|Aug 29'
```

预期：第二条命令**无输出**（我的改动不含二维码行）。若有输出，说明工作区既有的二维码改动会被一起提交 —— 停下，先问用户是否单独提交那 4 个文件的二维码改动，再继续。

```zsh
git add portal/index.html portal/zh/index.html portal/agentic.html portal/zh/agentic.html portal/engineering.html portal/zh/engineering.html
git diff --cached --name-only
git commit -m "fix(portal): 数字校正到 2026-09-05 普查值

index.html 项目卡：FT-710 180+→439 tests（并 V1.0→v1.8.1，据 CHANGELOG
[v1.8.1] 2026-08-16）、Modern v1.10.1/593→v1.12.1/682、FT8 40→937 collected、
SunMRRC 40+→65+ 提交、SunsdrMobile 3→9 提交。MRRC 280+ 提交经 git log --all
核实为 326，保留不改。

agentic.html 台账 Modern 行 633→682、v1.12.0→v1.12.1，并补 loader error 的
环境局限；census 2026-09-02→2026-09-05（EN 7 处 / ZH 7 处）。
engineering.html 两版各 2 处 633→682。

FT-710 v1.8.1/439 与 Windows package v1.8.0 的双字段写法经核实正确，未改。
子站的 439/633 是带日期的历史发布记录，改历史即造假，未改。

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 6（B5）：跨站普查 + R1–R7 逐条复核

**Files:** 只读复核，预期**不改文件**。若发现违规，改动归入本任务并单独提交。

**Interfaces:**
- Consumes: Global Constraints 的 R1–R7、本计划的 zsh 数组 grep 写法
- Produces: 一份可粘贴进最终汇报的普查结论

- [ ] **步骤 1：R5 普查 —— 子站是否自报可比数字（用数组，不要用字符串变量）**

```zsh
cd /Users/cheenle/HAM/website
SITES=(portal/ mrrc/ mrrc_ft710/ mrrc_modern/ sunmrrc/ SunsdrMobile/ mrrc_ft8/ efhw/)
for n in "439 tests" "682 tests" "937 tests" "633 tests" "593 tests" "180+ tests" "40 tests" "439 项" "682 项" "633 项"; do
  printf "  %-12s -> " "$n"; grep -RlF "$n" $SITES 2>/dev/null | tr '\n' ' '; echo
done
```

预期命中（已核实，作为对照基线）：
- `439 tests` → `portal/agentic.html`、`portal/engineering.html`、`mrrc_ft710/index.html`、`mrrc_ft710/sdd/14-version-history.html`、`mrrc_modern/sdd/14-version-history.html`
- `682 tests` → 仅 portal（agentic / engineering / index）与本文
- `633 tests` → **不应再出现在 portal/**；只应剩 `mrrc_modern/sdd.html` 与 `mrrc_modern/sdd/14-version-history.html`（历史记录，保留）
- `593 tests` / `180+ tests` / `40 tests` → **零命中**

若 `633 tests` 仍在 portal 命中，或 `593/180+/40` 有命中 → Task 5 漏改，回去补。

- [ ] **步骤 2：确认没有把历史记录改坏**

```zsh
cd /Users/cheenle/HAM/website
grep -oF "Published after 633/633 tests" mrrc_modern/sdd.html && echo "  ✓ 历史记录完好"
grep -oF "633/633 tests" mrrc_modern/sdd/14-version-history.html | head -2 && echo "  ✓ 版本史完好"
git -C /Users/cheenle/HAM/mrrc_modern status --porcelain website/ | head
git -C /Users/cheenle/HAM/mrrc_ft710 status --porcelain website/ | head
```

预期：前两条打印 ✓；后两条只显示**本次之前就存在**的改动（`website/index.html`、`website/zh/index.html`、`website/images/qr-wechat-group.jpg` 各 3 项，属二维码改动）。**若出现 `website/sdd.html` 或 `website/sdd/` 被修改，立即 `git checkout` 还原** —— 那是历史证据，不该动。

- [ ] **步骤 3：R1/R3/R4 禁句全站复核**

```zsh
cd /Users/cheenle/HAM/website
SITES=(portal/ mrrc/ mrrc_ft710/ mrrc_modern/ sunmrrc/ SunsdrMobile/ mrrc_ft8/ efhw/)
for p in "built by AI" "built by agents" "AI-built" "代理式工程" "由 AI 建造" "AI 打造"; do
  printf "  %-18s -> " "$p"; grep -RlF "$p" $SITES 2>/dev/null | tr '\n' ' '; echo "（应为空）"
done
```

预期：全部零命中。任何命中都必须修（本文内命中 → 改正文；其他页命中 → 报告用户，不在本次范围擅自改）。

- [ ] **步骤 4：R2 复核 —— gate 措辞不得贴到无注册表的仓库**

```zsh
cd /Users/cheenle/HAM/website
grep -n "pre-edit gate" portal/blog/seven-billion-tokens/index.html
grep -n "编辑前门禁" portal/blog/seven-billion-tokens/zh/index.html
ls -d /Users/cheenle/HAM/MRRC/.agents /Users/cheenle/HAM/sunsdr/.agents 2>&1 | head -2
```

预期：每处 gate 措辞的上下文都属于 ft710 / modern / ft8；后一条确认 `MRRC` 与 `sunsdr` **没有** `.agents` 目录（因此文中对它们只能说"无注册表，不主张门禁"）。

- [ ] **步骤 5：R6/R7 复核 —— 估算与未记录必须带标注**

```zsh
cd /Users/cheenle/HAM/website/portal/blog/seven-billion-tokens
grep -o '.\{0,120\}234,247,399.\{0,120\}' index.html
grep -o '.\{0,120\}5,380,941,148.\{0,120\}' index.html
grep -c 'not recorded\|estimate' index.html
```

预期：两个数字的上下文都能看到 `estimate` 或 `not recorded`；第三条计数 ≥ 4（iFlow 估算、iFlow 未记录、Hermes 未记录、首轮错值）。契约测试 `test_estimates_are_labelled` 已用 900 字符窗口自动校验，此处为人工二次确认。

- [ ] **步骤 6：R7 复核 —— 估算未并入已记录合计**

```zsh
cd /Users/cheenle/HAM/website/portal/blog/seven-billion-tokens
python3 - <<'PY'
import re
s=open('index.html',encoding='utf-8').read()
rec=7007437567; est=234247399
print('recorded  7,007,437,567 present:', '7,007,437,567' in s)
print('with-est  7,241,684,966 present:', '7,241,684,966' in s)
print('sum check:', rec+est == 7241684966)
print('234,247,399 present:', '234,247,399' in s)
# the two totals must not be used interchangeably: each must appear
PY
```

预期：四项全 True。文中 `7,007,437,567` 只能被称作"已记录"，`7,241,684,966` 只能被称作"含估算"。

- [ ] **步骤 7：如有改动则提交，否则记录普查结论**

```zsh
cd /Users/cheenle/HAM/website
git status --porcelain
```

若为空 → 无改动，把步骤 1–6 的结论原样写进最终汇报。若有改动：

```zsh
git add -u portal/
git commit -m "fix(portal): B5 跨站普查发现的口径修正

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 7（B6）：最终验证与人工浏览

**Files:** 不改文件（除非验证发现缺陷）

**Interfaces:**
- Consumes: 全部前序任务产物
- Produces: 可交付状态 + 最终汇报

- [ ] **步骤 1：全测试套绿**

```zsh
cd /Users/cheenle/HAM/website/portal
/usr/bin/python3 -m pytest tests -q
```

预期：5 个测试文件全部 PASS，0 failed，0 error。记录实际用例数。

- [ ] **步骤 2：本地起服务，人工看四件事**

```zsh
cd /Users/cheenle/HAM/website/portal
python3 -m http.server 8899 &
sleep 1
echo "http://localhost:8899/blog/seven-billion-tokens/"
echo "http://localhost:8899/blog/seven-billion-tokens/zh/"
echo "http://localhost:8899/blog/"
```

人工检查（用浏览器打开上述三个 URL）：
1. `#blog-toc` 被 JS 自动填充出 13 条（说明 `blog.css`/`global-nav.js` 的 TOC 逻辑认得本文的 `<section id>` + `<h2>` 结构）
2. 四类 `.claim-box` 左边框颜色不同（绿 / 青 / 琥珀 / 紫 `#a78bfa`）
3. `.ledger-table` 在 375px 宽度下不溢出（`td.num` 有 `white-space: nowrap`，需确认可横向滚动而非撑破版面）
4. EN ↔ ZH 互链可点，语言按钮位置与 connections 一文一致

检查完关掉服务：`kill %1`

- [ ] **步骤 3：确认打包边界没被破坏**

```zsh
cd /Users/cheenle/HAM/website/portal
grep -nE "exclude='\./tests'|exclude='\./make_sitemap.py'" deploy.sh
git status --porcelain | grep -E 'deploy\.sh' && echo "⚠ deploy.sh 被改动 —— 计划禁止" || echo "✓ deploy.sh 未改动"
```

预期：两条 exclude 仍在；`deploy.sh` 未被改动。**不执行部署** —— 部署由用户另行触发。

- [ ] **步骤 4：确认工作区只剩用户自己的既有改动**

```zsh
cd /Users/cheenle/HAM/website
git status --porcelain
```

预期剩余：`efhw/index.html`、`efhw/zh/index.html`（二维码，用户的既有改动）、以及本次之前就存在的未跟踪文件（`.superpowers/`、`IMG_9385.jpg`、`ma.jpg`、`mrrc_modern`、`efhw/css/scope.css`、`efhw/images/`、`portal/IMG_9243.JPG` 等）。`portal/index.html` 与 `portal/zh/index.html` **不应再出现**（已在 Task 5 提交）。

若 `portal/index.html` 仍显示为 modified，说明二维码改动与我的改动混在同一文件未提交 —— 回到 Task 5 步骤 8 处理。

- [ ] **步骤 5：写最终汇报**

汇报必须包含（用 Global Constraints 的值，不要重新计算）：
- 新增 4 文件 / 修改 7 文件的清单
- `/usr/bin/python3 -m pytest tests -q` 的实际结果行
- Task 6 六步普查的实际输出结论
- 三条已知遗留：① 三仓注册表 `sdd_version` 滞后（ft710 V1.7 / modern V2.27 / ft8 V1.0）—— 属产品仓库，范围外；② Modern 的 `test_macos_launcher` loader error —— 属产品仓库，范围外；③ CLAUDE.md 教的 `$SITES` 字符串写法在本机 zsh + ugrep 下静默失败，建议改为数组写法（**需用户确认是否要改 CLAUDE.md**）
- 明确声明：**未部署**

---

## Self-Review 记录

**1. Spec 覆盖**

| Spec 条目 | 落在哪个任务 |
|---|---|
| §3 R1–R7 七条红线 | Global Constraints + Task 1 步骤 1（禁句/gate/估算断言）+ Task 6 步骤 3–6（人工复核） |
| §4.1 已记录台账 7 工具 | Task 2 步骤 3（`ledger` 节表格） |
| §4.2 未记录/估算 | Task 2 步骤 4（`floor` 节）+ Task 1 `test_estimates_are_labelled` |
| §4.3 合计与结构（95.2%/4.8%/$15.11/$9.30） | Global Constraints + Task 2 步骤 3 |
| §4.4 按仓库 + 校验式 | Task 2 步骤 8（`scale` 节） |
| §4.5 模型与 API 源 + 表述纪律 | Task 2 步骤 6/8；纪律由 `data-claim-type` 区分 fact/inference 落实 |
| §4.6 Hermes 三来源 | Task 2 步骤 4（`floor`）与步骤 6（`before` 之后的机器节）|
| §4.7 测量自纠错 | Task 2 步骤 5（`numbers-lie` 节）|
| §5 十二节 + hero | Task 2 步骤 3–9（EN）、Task 3（ZH）|
| **§5.0 双标题** | Task 3 步骤 1（ZH 标题三处）+ Task 1 `test_titles_are_bilingual`（含 EN 页 `assertNotIn("格物致知")`）|
| **§5.0 三卷结构** | Task 2 步骤 2（`<div class="volume">` 嵌套骨架）+ 步骤 9c（EN 卷题）+ Task 3 步骤 2（ZH 卷题）+ Task 1 `test_volumes_group_sections_correctly`（`div_depth==0`、卷序、13 节归属、卷题逐字）|
| **§5.0 五处经典对应** | Task 2 步骤 9b（EN 措辞表 + 三条纪律）+ Task 3 步骤 2（ZH 措辞表）+ Task 1 `test_classical_anchors_are_present_in_their_sections` |
| **§5.0 引文纪律**（不得标 fact、须点名出处、禁目的论） | Task 1 `test_classical_citations_are_not_graded_as_fact`（`CLASSICAL_TERMS` / `CITATION_SOURCES` / `FORBIDDEN_TELEOLOGY`，均按语言分列）|
| §5.1 断言分类纪律 | Task 1 `test_sections_and_claim_types_match` + Task 3 步骤 4 diff 校验 |
| §5.2 页面骨架 + head + article.css | Task 2 步骤 1–2、Task 3 步骤 1 |
| §6.1 实测表 | Task 5 前置事实表（含核实命令与结果）|
| §6.2 改动清单 1–3 | Task 5 步骤 1–6 |
| §6.2 改动清单 4（跨站普查） | Task 6 步骤 1–2 |
| §6.2 改动清单 5（sitemap） | Task 4 步骤 2–3 |
| §6.3 部署边界 | Global Constraints + Task 7 步骤 3 |
| §7.1 十一条契约测试断言 | Task 1 步骤 1（11 条 → 实际 **18 个测试方法**，覆盖全部 11 条并新增 4 条守护 §5.0：`test_titles_are_bilingual`、`test_volumes_group_sections_correctly`、`test_classical_anchors_are_present_in_their_sections`、`test_classical_citations_are_not_graded_as_fact`）|
| §7.2 既有测试不得变红 | Task 1 步骤 3（基线）+ Task 5 步骤 7 |
| §7.3 人工验证 | Task 7 步骤 2 |
| §8 Q1（FT8 不补台账） | Task 5：只在 index.html 写 `937 tests collected`，台账不加测试数 |
| §8 Q2（MRRC commits） | 已解决：`git log --all` = 326 → **保留 `280+`**（Task 5 步骤 1 明确不改 165 行）|
| §8 Q3（sunsdr 一仓两产品） | 已解决：SunsdrMobile 是独立仓库（9 commits），SunMRRC 用 sunsdr 仓（67）→ 分别写 `9` 与 `65+` |
| §8 Q4（不点名供应商） | Task 2 步骤 3/6：只写 `model_provider` / `provider` 字段字面值（`api111`、`mulerun`）作为 fact，多源路由写成 inference |
| §9 范围外 6 条 | Global Constraints「不得改动」+ Task 5 步骤 1/2（不改子站、不改历史）+ Task 7 步骤 3（不部署）|
| §10 B0–B6 | Task 1–7 一一对应 |
| §11 文件清单 | File Structure 节，与实际任务一致 |

**Spec 未覆盖但计划新增的两项**（均为普查中新发现，已在本计划中记录）：
- 本机 `zsh + ugrep` 下 CLAUDE.md 的 `$SITES` 字符串写法静默失败 → 计划全文改用数组写法，并在 Task 7 步骤 5 作为遗留问题上报（是否改 CLAUDE.md 交用户决定）。
- 三仓注册表 `sdd_version` 全部滞后于其守护的 SDD → 写入文章 `drift` 节作为 fact，**不修注册表**（属产品仓库，范围外）。

**2. 占位符扫描**：无 TBD / TODO / "类似 Task N" / "添加适当的错误处理"。所有代码步骤给出完整可落盘内容；所有 Edit 步骤给出精确 old → new 字符串与行号；所有验证步骤给出可执行命令与预期输出。

**3. 类型/命名一致性**：
- `SLUG`、`ARTICLES`、`ARTICLE_CSS`、`BLOG_INDEX`、`SITEMAP`、`CANONICAL`、`REQUIRED_SECTIONS`、`REQUIRED_CLAIM_TYPES`、`LEDGER_CONSTANTS`、`FORBIDDEN`、`STALE_NUMBERS`、`GATE_OWNERS`、`GATE_FORBIDDEN_NEIGHBOURS`、`ESTIMATE_LABELS`、`ArticleParser`、`load()` —— 均在 Task 1 定义，Task 2–7 只引用不改名。
- `13` 个 section id 在 Task 1 常量、Task 2 步骤 3–9、Task 3 步骤 2、Self-Review 中完全一致：`ledger, floor, numbers-lie, intent, before, machine, chain, scale, delivery, drift, human, playbook, references`。
- CSS 类名 `.ledger-table` / `.term-block` / `.prov` / `.claim-box` / `.claim-label` 在 Task 2 步骤 1 定义，步骤 3/7 与 Task 3 引用一致。
- 数字串在 Global Constraints、Task 1 `LEDGER_CONSTANTS`、Task 2 各步骤三处逐字一致（含千分位逗号）。
- 测试运行器统一为 `/usr/bin/python3 -m pytest`（系统 Python 3.9.6 + pytest 8.4.2）。已实测：Homebrew 的 `python3`(3.14)、`python3.11`、`python3.12`、`python3.13` **全部没有 pytest 模块**，仓库无 venv。`.pytest_cache` 里留有 `cpython-311-pytest-7.4.3` 与 `cpython-314-pytest-7.4.3` 的旧 pyc，说明历史上曾有过可用环境，现已不存在 —— 不要照抄旧命令。测试代码用 `from __future__ import annotations`，故 `dict[str, str]` / `str | None` 注解在 3.9 下合法（已实测）。
- 本地预览用 `python3 -m http.server`（任意 python3 均可，不需要 pytest）。
- **计划已 dry-run 验证**：Task 1 的测试代码被抽出、`PORTAL` 重指向后实跑，结果 `4 failed, 14 skipped`（18 个方法），`test_stale_numbers_are_gone` 报出的旧值正是 `['180+ tests', '593 tests', 'v1.10.1']`；既有测试 `/usr/bin/python3 -m pytest tests -q` = `32 passed`。Task 1 步骤 2/3 的预期值来自这次实测，不是推测。
- `LEDGER_CONSTANTS` 实测为 **29** 项（计划早期草稿写 28，已全部改正）。已用脚本校验：`VOLUMES` 覆盖 12 节 + `UNVOLUMED_SECTIONS` 1 节 = 13 = `REQUIRED_SECTIONS`，无重复无遗漏；`CLASSICAL_ANCHORS` 5 个 section 均在 `REQUIRED_SECTIONS` 内且都有 `en`/`zh` 两套锚点。
