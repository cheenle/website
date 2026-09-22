# 全站语言体系更新 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 把 portal 的编辑性正文（blog 全系列 + `agentic.html` / `engineering.html`）统一到一套双语真镜像、三档文体、可测可执行的「语言体系」，并补齐 4 篇老文缺失的中文版。

**架构：** 规范文档定义判据（`docs/superpowers/specs/2026-09-22-blog-language-system-design.md`）；`ba-quote` 结构组件让引文可配对；`tests/test_blog_language.py` 把体系变成断言（结构、镜像、阈值、术语、禁用词）；内容按 8 个批次逐篇改造，每篇一个 commit、EN+ZH 同 commit。

**技术栈：** 手写 HTML + `octen.css` / `agentic.css` / `blog-article.css` + 字体图标 + Python 3 `unittest`（标准库，无构建步骤、无新依赖）。

**执行顺序说明：** 任务 2（度量工具与测试骨架）先于样板落地，这是 TDD 要求——后文所有任务都用它验证。规范里的「批次」编号不变，只是把批次 1 的一半提前。

**通用命令（后文用 `<T>` 指代任务序号）：**

```bash
# 全量测试（工作目录必须是 portal/）
cd /Users/cheenle/HAM/website/portal && python3 -m unittest discover tests 2>&1 | tail -3

# 单篇度量（把 <PATH> 换成文件路径）
cd /Users/cheenle/HAM/website/portal && python3 -c "
import re,html,sys
s=open(sys.argv[1],encoding='utf-8').read()
s=re.sub(r'<script.*?</script>','',s,flags=re.S); s=re.sub(r'<style.*?</style>','',s,flags=re.S)
m=re.search(r'<main class=\"ba-main\">.*?</main>',s,flags=re.S)
t=html.unescape(re.sub(r'<[^>]+>',' ',m.group(0)))
n=len(re.findall(r'[\u4e00-\u9fff]',t)); sents=len(re.findall(r'[。！？]',t)); d=t.count('——')
print(f'汉字={n} 句={sents} 均句长={n/max(sents,1):.1f} 破折号={d} {d/max(n,1)*1000:.1f}‰')
" blog/<PATH>/zh/index.html
```

---

## 文件结构

**创建：**

| 文件 | 职责 |
| --- | --- |
| `portal/tests/test_blog_language.py` | 语言体系断言：结构、双语镜像、档位判据、语体阈值、术语与禁用词、索引元数据 |
| `portal/blog/ft710-usb-remote-control/zh/index.html` | FT-710 实操文中文版（从零新写） |
| `portal/blog/efhw-esp32s3-auto-tuner/zh/index.html` | EFHW 实操文中文版（从零新写） |
| `portal/blog/opus-vs-pcm-remote-audio/zh/index.html` | Opus 实操文中文版（从零新写） |
| `portal/blog/psk-reporter-dxcc-hunting/zh/index.html` | PSK Reporter 实操文中文版（从零新写） |

**修改：**

| 文件 | 变更 |
| --- | --- |
| `portal/css/blog-article.css` | 追加 `.ba-quote` 系列样式（任务 1） |
| `portal/blog/coda/{index.html,zh/index.html}` | 引文结构化 + EN 镜像（任务 3） |
| `portal/blog/ft710-usb-remote-control/index.html` | 旧版式 → 新骨架（任务 4） |
| `portal/blog/{faculties,ming-li-dao-tian,only-imagination,connections-recursive-intelligence}/{index.html,zh/index.html}` | 论说文对齐（任务 5） |
| `portal/blog/{solo-loop,support-loop,three-axes}/…` + `seven-billion-tokens/{,almanac/,ledger/,playbook/}…` | 实操文对齐（任务 6） |
| `portal/blog/{efhw-esp32s3-auto-tuner,opus-vs-pcm-remote-audio,psk-reporter-dxcc-hunting}/index.html` | 旧版式 → 新骨架（任务 7） |
| `portal/{agentic.html,engineering.html,zh/agentic.html,zh/engineering.html}` | 总纲档对齐（任务 8） |
| `portal/blog/index.html`、`portal/blog/zh/index.html`、`portal/sitemap.xml` | 索引与元数据（任务 9） |
| `portal/{index.html,about.html,contact.html,privacy.html}` + `portal/zh/` 同名 | 术语与导航核对（任务 9） |
| 全部引用 `blog-article.css?v=3` 的 33 个页面 | 版本 bump 到 `?v=4`（任务 1） |

---

## 执行中发现（2026-09-22，批次 0/1 完成后补记）

1. **sitemap 只能在主检出生成。** `mrrc_modern` / `SunsdrMobile` / `ft8` 是**相对**符号链接（如 `mrrc_modern -> ../mrrc_modern/website`），在任何 `.worktrees/*` 里都会断链；`make_sitemap.py` 的 `os.walk` 不会跟随断裂链接，于是**静默丢掉 6 个 mrrc_modern URL**。在 worktree 里生成前必须先把这三个链接临时换成绝对路径，生成后用 `git checkout mrrc_modern SunsdrMobile ft8` 还原（否则符号链接变更会被提交）。任务 9 按此执行。

2. **`tests/test_sitemap.py` 是 pytest 风格**（裸 `def test_`），`python3 -m unittest discover` **一个都不收集**，而本机没有 pytest。它是全站唯一校验「sitemap 与生成器一致 / 子站页面全收录」的文件。手工执行：

   ```bash
   cd portal && python3 -c "
   import sys; sys.path.insert(0,'tests'); import test_sitemap as t
   [getattr(t,n)() for n in dir(t) if n.startswith('test_')]; print('sitemap 契约测试通过')"
   ```

   批次 7 验收必须包含这一步，否则「全绿」是缺面的。

3. **索引与 sitemap 改为随页增量更新**（原计划排在批次 6）：`test_blog_indexes_mirror_each_other` 以页面存在性推断，新 ZH 页一落地就要求两侧索引同时收录该篇，否则假红。批次 6 因此只剩 landing 8 页术语核对与最终复核。

4. **老 4 篇保留原 section id**（`ft4222` / `scopeframe` / `tx` / `fallback` / `vs-sculan10`），不采用任务 7 表格里的重命名 id，避免存量外链失效；另加 `closing` 一节。

5. **`ba-quote-cite` 必须渲染出来**，不能只写在 `data-quote-cite` 属性里——测试已加断言，任务 5/6/8 照此办理。

---

## 任务 1：`.ba-quote` 组件与 CSS 版本 bump

**文件：**

- 修改：`portal/css/blog-article.css`（追加到 `:root` 之后的组件区，建议放在 `.claim-box` 系列之后，约第 300 行）
- 修改：所有 `blog-article.css?v=3` 的引用（33 处）

- [ ] **步骤 1：追加组件样式**

在 `portal/css/blog-article.css` 的 `.claim-box[data-claim-type="thesis"]` 规则块之后插入：

```css
/* 引文块：data-quote-id 是 EN/ZH 配对的锚（见语言体系规范 §4） */
.ba-quote {
 border: 1px solid var(--border);
 border-left: 3px solid var(--text-muted);
 border-radius: 0 1rem 1rem 0;
 padding: 1.15rem 1.25rem;
 margin: 1.6rem 0;
 background: var(--bg-card);
}
.ba-quote-orig {
 margin: 0 0 0.6rem;
 font-size: 1.05rem;
 line-height: 1.75;
 color: var(--text-primary);
}
.ba-quote-orig::before { content: "\300c"; }
.ba-quote-orig::after { content: "\300d"; }
html[lang="en"] .ba-quote-orig::before,
html[lang="en"] .ba-quote-orig::after { content: ""; }
.ba-quote-trans {
 margin: 0;
 font-size: 0.92rem;
 line-height: 1.7;
 color: var(--text-muted);
}
.ba-quote-by {
 font-family: var(--font-mono);
 font-size: 0.75rem;
 font-style: normal;
 letter-spacing: 0.04em;
 white-space: nowrap;
}
.ba-quote-cite {
 display: block;
 margin-top: 0.7rem;
 font-family: var(--font-mono);
 font-size: 0.75rem;
 letter-spacing: 0.04em;
 color: var(--text-muted);
}
.ba-quote[data-quote-kind="classic"] { border-left-color: var(--ag-edge); }
.ba-quote[data-quote-kind="engineering"] { border-left-color: var(--ag-control); }
.ba-quote[data-quote-kind="project"] { border-left-color: var(--ag-safe); }
.ba-quote[data-quote-kind="classic"] .ba-quote-cite { color: var(--ag-edge); }
.ba-quote[data-quote-kind="engineering"] .ba-quote-cite { color: var(--ag-control); }
.ba-quote[data-quote-kind="project"] .ba-quote-cite { color: var(--ag-safe); }
```

> 中文页的引号由 `::before/::after` 生成 `「」`，因此 `ba-quote-orig` 的文本里**不要**再手写引号；英文页不需要引号，用 `html[lang="en"]` 关掉。标记里的语言属性以每页 `<html lang="...">` 为准（中文页 `zh-CN`，英文页 `en`）。

- [ ] **步骤 2：bump CSS 版本**

```bash
cd /Users/cheenle/HAM/website/portal && grep -rl 'blog-article.css?v=3' --include='*.html' . | xargs sed -i '' 's/blog-article\.css?v=3/blog-article.css?v=4/g'
grep -rho 'blog-article.css?v=[0-9]*' --include='*.html' . | sort | uniq -c
```

预期：只剩一行 `33 blog-article.css?v=4`。

- [ ] **步骤 3：提交**

```bash
cd /Users/cheenle/HAM/website && git add -A portal/css/blog-article.css portal/blog portal/agentic.html portal/engineering.html portal/zh portal/index.html
git commit -m "feat(blog): 新增 .ba-quote 引文组件（EN/ZH 配对锚）+ CSS v3→v4"
```

---

## 任务 2：`tests/test_blog_language.py`（度量工具 + 体系断言）

**文件：**
- 创建：`portal/tests/test_blog_language.py`

**验证状态：** 本文件已用真实站点跑通（12 个测试，唯一失败是 `test_pending_entries_are_gone`，正是设计预期）。**直接使用，不要"重写一版"。**

**两个挂起名单**（规范 §5 的豁免机制）：

- `PENDING_DASH`：语体阈值挂起 —— 今天 5 篇破折号超标，到期批次 2 / 3
- `PENDING_ARTICLES`：结构 / 镜像 / 引文 / 标点 / 元数据挂起 —— 按文章 × 语言，到期批次 0 / 2 / 4 / 9

两名单都必须在批次 7 清空；`test_pending_entries_are_gone` 就是验收闸门。

**度量陷阱（务必保留注释）：** 不能用 `HTMLParser` 拼接 `handle_data` 来取正文。相邻表格单元格里的两个「—」（`<td>…—</td><td>—…</td>`）拼接后会变成「——」，使 `ledger` 从 5.7‰ 虚高到 6.7‰、凭空多出 1 篇超标。规范 §3.2 要求「标签替换为空格后再 unescape」，`body_text()` 即按此实现。

- [ ] **步骤 1：创建测试文件**

```python
from __future__ import annotations

import html
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

PORTAL = Path(__file__).resolve().parents[1]
BLOG = PORTAL / "blog"

TIER_ESSAY, TIER_FIELD, TIER_THESIS, TIER_ARCHIVE, TIER_STUB = (
    "essay", "field", "thesis", "archive", "stub")

ARTICLES: dict[str, tuple[str, tuple[str, ...]]] = {
    "coda": (TIER_ESSAY, ("en", "zh")),
    "faculties": (TIER_ESSAY, ("en", "zh")),
    "ming-li-dao-tian": (TIER_ESSAY, ("en", "zh")),
    "only-imagination": (TIER_ESSAY, ("en", "zh")),
    "connections-recursive-intelligence": (TIER_ESSAY, ("en", "zh")),
    "solo-loop": (TIER_FIELD, ("en", "zh")),
    "support-loop": (TIER_FIELD, ("en", "zh")),
    "three-axes": (TIER_FIELD, ("en", "zh")),
    "seven-billion-tokens": (TIER_FIELD, ("en", "zh")),
    "seven-billion-tokens/almanac": (TIER_FIELD, ("en", "zh")),
    "seven-billion-tokens/ledger": (TIER_FIELD, ("en", "zh")),
    "seven-billion-tokens/playbook": (TIER_FIELD, ("en", "zh")),
    "ft710-usb-remote-control": (TIER_FIELD, ("en", "zh")),
    "efhw-esp32s3-auto-tuner": (TIER_FIELD, ("en", "zh")),
    "opus-vs-pcm-remote-audio": (TIER_FIELD, ("en", "zh")),
    "psk-reporter-dxcc-hunting": (TIER_FIELD, ("en", "zh")),
    "juekun": (TIER_ARCHIVE, ("root",)),
    "from-intent-to-delivery": (TIER_STUB, ("en", "zh")),
}

TLDR_MIN = {TIER_ESSAY: 4, TIER_FIELD: 3}
TLDR_EXEMPT = {"seven-billion-tokens/almanac", "seven-billion-tokens/ledger", "seven-billion-tokens/playbook"}
CLASSIC_MIN = {TIER_ESSAY: 3, TIER_FIELD: 0}
MAX_AVG_SENTENCE = {TIER_ESSAY: 40, TIER_FIELD: 55}
MAX_DASH_PERMILLE = 6.0
CLAIM_TYPES = {"fact", "inference", "thesis", "analogy"}

# 语体阈值挂起项（今天是 5 篇破折号超标）
PENDING_DASH: dict[str, str] = {
    "faculties": "batch2",
    "ming-li-dao-tian": "batch2",
    "support-loop": "batch3",
    "seven-billion-tokens": "batch3",
    "seven-billion-tokens/almanac": "batch3",
}

# 结构/镜像/引文/标点/元数据挂起项（按文章 × 语言）
PENDING_ARTICLES: dict[tuple[str, str], str] = {
    ("coda", "en"): "batch0", ("coda", "zh"): "batch0",
    ("faculties", "en"): "batch2", ("faculties", "zh"): "batch2",
    ("ming-li-dao-tian", "en"): "batch2", ("ming-li-dao-tian", "zh"): "batch2",
    ("only-imagination", "en"): "batch2", ("only-imagination", "zh"): "batch2",
    ("connections-recursive-intelligence", "en"): "batch2",
    ("connections-recursive-intelligence", "zh"): "batch2",
    ("ft710-usb-remote-control", "en"): "batch4", ("ft710-usb-remote-control", "zh"): "batch4",
    ("efhw-esp32s3-auto-tuner", "en"): "batch4", ("efhw-esp32s3-auto-tuner", "zh"): "batch4",
    ("opus-vs-pcm-remote-audio", "en"): "batch4", ("opus-vs-pcm-remote-audio", "zh"): "batch4",
    ("psk-reporter-dxcc-hunting", "en"): "batch4", ("psk-reporter-dxcc-hunting", "zh"): "batch4",
    ("juekun", "root"): "batch9",
}

BANNED_PHRASES = ("代理式工程", "三款产品", "由 Agent 写成", "written by AI", "被用来",
                  "值得注意的是", "在当今时代", "深入探讨", "综上所述")


def page_path(slug: str, lang: str) -> Path:
    if lang == "root":
        return BLOG / slug / "index.html"
    return BLOG / slug / ("index.html" if lang == "en" else f"{lang}/index.html")


def canonical(slug: str, lang: str) -> str:
    if lang == "root":
        return f"https://www.vlsc.net/blog/{slug}/"
    return f"https://www.vlsc.net/blog/{slug}/" + ("" if lang == "en" else "zh/")


class ArticleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.section_ids: list[str] = []
        self.ids: set[str] = set()
        self.anchor_targets: list[str] = []
        self.tldr_types: list[str] = []
        self.quotes: list[dict[str, str]] = []
        self.quote_children: dict[str, set[str]] = {}
        self.classes: set[str] = set()
        self._current_quote: str | None = None

    def handle_starttag(self, tag, attrs):
        a = {k: (v or "") for k, v in attrs}
        cls = a.get("class", "")
        self.classes.update(cls.split())
        if a.get("id"):
            self.ids.add(a["id"])
            if tag == "section":
                self.section_ids.append(a["id"])
        if tag == "a" and a.get("href", "").startswith("#"):
            self.anchor_targets.append(a["href"][1:])
        if "ba-tldr-tag" in cls.split():
            self.tldr_types.append(a.get("data-claim-type", ""))
        if "ba-quote" in cls.split():
            self.quotes.append({"id": a.get("data-quote-id", ""),
                                "kind": a.get("data-quote-kind", ""),
                                "cite": a.get("data-quote-cite", "")})
            self._current_quote = a.get("data-quote-id", "")
            self.quote_children.setdefault(self._current_quote, set())
        if self._current_quote and cls:
            self.quote_children[self._current_quote].update(cls.split())

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag == "blockquote":
            self._current_quote = None

    @property
    def quote_ids(self) -> list[str]:
        return [q["id"] for q in self.quotes]


def load(path: Path):
    source = path.read_text(encoding="utf-8")
    parser = ArticleParser()
    parser.feed(source)
    return source, parser


def body_text(source: str) -> str:
    """规范 §3.2：<main class="ba-main"> 可见文本，标签替换为空格后再 unescape。

    不能用 HTMLParser 拼接 handle_data —— 那样会把相邻表格单元格
    (<td>…—</td><td>—…</td>) 里的两个「—」误拼成「——」。
    """
    stripped = re.sub(r"<script.*?</script>", "", source, flags=re.S)
    stripped = re.sub(r"<style.*?</style>", "", stripped, flags=re.S)
    body = re.search(r'<main class="ba-main">.*?</main>', stripped, re.S)
    if body is None:
        return ""
    return html.unescape(re.sub(r"<[^>]+>", " ", body.group(0)))


def metrics(source: str) -> dict[str, float]:
    text = body_text(source)
    han = len(re.findall(r"[\u4e00-\u9fff]", text))
    sentences = len(re.findall(r"[。！？]", text))
    dashes = text.count("——")
    return {"han": han, "sentences": sentences,
            "avg_sentence": han / max(sentences, 1),
            "dash_permille": dashes / max(han, 1) * 1000}


class LanguageSystemTests(unittest.TestCase):
    maxDiff = None

    def test_pending_entries_are_gone(self) -> None:
        self.assertEqual({}, PENDING_DASH, "仍有破折号超标挂起项")
        self.assertEqual({}, PENDING_ARTICLES, "仍有文章级挂起项，未达到验收状态")

    def test_articles_exist_and_parse(self) -> None:
        for slug, (tier, langs) in ARTICLES.items():
            for lang in langs:
                self.assertTrue(
                    (slug, lang) in PENDING_ARTICLES or page_path(slug, lang).exists(),
                    f"{slug}/{lang} 缺失",
                )

    def test_structure_and_bilingual_mirror(self) -> None:
        for slug, (tier, langs) in ARTICLES.items():
            if tier == TIER_STUB:
                continue
            parsed = {}
            for lang in langs:
                p = page_path(slug, lang)
                if p.exists():
                    parsed[lang] = load(p)[1]
            for lang, parser in parsed.items():
                if (slug, lang) in PENDING_ARTICLES:
                    continue
                where = f"{slug}/{lang}"
                self.assertIn("ba-article", parser.classes, where)
                self.assertTrue(parser.section_ids, f"{where}: 无 section")
                for target in parser.anchor_targets:
                    self.assertIn(target, parser.ids, f"{where}: 死锚 #{target}")
            if len(parsed) == 2 and not any(
                (slug, lang) in PENDING_ARTICLES for lang in ("en", "zh")
            ):
                en, zh = parsed["en"], parsed["zh"]
                self.assertEqual(set(en.section_ids), set(zh.section_ids), f"{slug}: section 不对等")
                self.assertEqual(len(en.tldr_types), len(zh.tldr_types), f"{slug}: TL;DR 不对等")
                self.assertEqual(sorted(en.quote_ids), sorted(zh.quote_ids), f"{slug}: 引文不对等")

    def test_tldr_requirements(self) -> None:
        for slug, (tier, langs) in ARTICLES.items():
            if tier in (TIER_STUB, TIER_ARCHIVE) or slug in TLDR_EXEMPT:
                continue
            for lang in langs:
                p = page_path(slug, lang)
                if not p.exists():
                    continue
                if (slug, lang) in PENDING_ARTICLES:
                    continue
                parser = load(p)[1]
                self.assertGreaterEqual(len(parser.tldr_types), TLDR_MIN[tier], f"{slug}/{lang}: TL;DR 不足")
                self.assertTrue(set(parser.tldr_types) <= CLAIM_TYPES,
                                f"{slug}/{lang}: 非法 claim {set(parser.tldr_types) - CLAIM_TYPES}")

    def test_quote_blocks_are_well_formed(self) -> None:
        for slug, (tier, langs) in ARTICLES.items():
            for lang in langs:
                p = page_path(slug, lang)
                if not p.exists():
                    continue
                if (slug, lang) in PENDING_ARTICLES:
                    continue
                parser = load(p)[1]
                ids = [q["id"] for q in parser.quotes]
                self.assertEqual(len(ids), len(set(ids)), f"{slug}/{lang}: id 重复")
                for q in parser.quotes:
                    where = f"{slug}/{lang}/{q['id']}"
                    self.assertTrue(q["id"], f"{where}: 缺 id")
                    self.assertIn(q["kind"], {"classic", "engineering", "project"}, where)
                    self.assertTrue(q["cite"], f"{where}: 缺 cite")
                    children = parser.quote_children[q["id"]]
                    self.assertIn("ba-quote-orig", children, f"{where}: 缺原文")
                    self.assertIn("ba-quote-trans", children, f"{where}: 缺译本")

    def test_tier_citation_rules(self) -> None:
        for slug, (tier, langs) in ARTICLES.items():
            if tier not in (TIER_ESSAY, TIER_FIELD):
                continue
            for lang in langs:
                p = page_path(slug, lang)
                if not p.exists() or (slug, lang) in PENDING_ARTICLES:
                    continue
                parser = load(p)[1]
                classics = [q for q in parser.quotes if q["kind"] == "classic"]
                self.assertGreaterEqual(len(classics), CLASSIC_MIN[tier], f"{slug}/{lang}: 经典不足")
                if tier == TIER_FIELD:
                    self.assertEqual([], classics, f"{slug}/{lang}: 实操文不得引经典")

    def test_zh_style_thresholds(self) -> None:
        for slug, (tier, langs) in ARTICLES.items():
            if tier not in (TIER_ESSAY, TIER_FIELD) or "zh" not in langs:
                continue
            p = page_path(slug, "zh")
            if not p.exists():
                continue
            m = metrics(p.read_text(encoding="utf-8"))
            if slug not in PENDING_DASH:
                self.assertLessEqual(m["dash_permille"], MAX_DASH_PERMILLE,
                                     f"{slug}/zh: {m['dash_permille']:.1f}‰")
            self.assertLessEqual(m["avg_sentence"], MAX_AVG_SENTENCE[tier],
                                 f"{slug}/zh: 均句长 {m['avg_sentence']:.1f}")

    def test_quote_marks_are_unified_in_zh(self) -> None:
        for slug, (tier, langs) in ARTICLES.items():
            if "zh" not in langs or tier == TIER_STUB:
                continue
            p = page_path(slug, "zh")
            if not p.exists():
                continue
            if (slug, "zh") in PENDING_ARTICLES:
                continue
            source = p.read_text(encoding="utf-8")
            body = re.search(r'<main class="ba-main">.*?</main>', source, re.S)
            if body is None:
                continue
            text = re.sub(r"<code>.*?</code>", "", body.group(0), flags=re.S)
            text = re.sub(r"<pre>.*?</pre>", "", text, flags=re.S)
            text = re.sub(r'<section id="references".*?</section>', "", text, flags=re.S)
            stripped = re.sub(r"<[^>]+>", "", text)
            self.assertNotIn('"', stripped, f"{slug}/zh: 半角直引号")
            self.assertNotIn("\u201c", stripped, f"{slug}/zh: 弯引号")
            self.assertNotIn("\u201d", stripped, f"{slug}/zh: 弯引号")

    def test_banned_phrases_and_terminology(self) -> None:
        for slug, (tier, langs) in ARTICLES.items():
            for lang in langs:
                p = page_path(slug, lang)
                if not p.exists():
                    continue
                source = p.read_text(encoding="utf-8")
                for phrase in BANNED_PHRASES:
                    self.assertNotIn(phrase, source, f"{slug}/{lang}: 禁用词「{phrase}」")
                if lang in ("zh", "root") and "agentic engineering" in source.lower():
                    self.assertIn("智能体工程", source, f"{slug}/{lang}: 术语方向")
                if lang == "en" and "智能体工程" in source:
                    self.assertIn("agentic engineering", source.lower(), f"{slug}/en: 术语方向")

    def test_legacy_layout_is_gone(self) -> None:
        for slug, (tier, langs) in ARTICLES.items():
            for lang in langs:
                p = page_path(slug, lang)
                if not p.exists() or (slug, lang) in PENDING_ARTICLES:
                    continue
                parser = load(p)[1]
                for legacy in ("ba-prose", "ba-tags"):
                    self.assertNotIn(legacy, parser.classes, f"{slug}/{lang}: 旧版式 {legacy}")

    def test_blog_indexes_mirror_each_other(self) -> None:
        en = (BLOG / "index.html").read_text(encoding="utf-8")
        zh = (BLOG / "zh/index.html").read_text(encoding="utf-8")
        archive = {s for s, (t, _) in ARTICLES.items() if t == TIER_ARCHIVE}
        no_zh_yet = {
            slug
            for slug, (_, langs) in ARTICLES.items()
            if "zh" in langs and not page_path(slug, "zh").exists()
        }
        en_slugs = (set(re.findall(r'href="/blog/([a-z0-9-]+)/"', en)) - archive - no_zh_yet) - {"zh"}
        zh_slugs = set(re.findall(r'/blog/([a-z0-9-]+)/zh/"', zh))
        self.assertEqual(en_slugs, zh_slugs, "中英索引卡片集合不一致")
        for slug in archive:
            self.assertIn(f'href="/blog/{slug}/"', en, f"英文索引缺 {slug}")
            self.assertIn(f'href="/blog/{slug}/"', zh, f"中文索引缺 {slug}")

    def test_hreflang_and_sitemap(self) -> None:
        sitemap = (PORTAL / "sitemap.xml").read_text(encoding="utf-8")
        for slug, (tier, langs) in ARTICLES.items():
            if tier == TIER_STUB:
                continue
            for lang in langs:
                p = page_path(slug, lang)
                if not p.exists() or (slug, lang) in PENDING_ARTICLES:
                    continue
                source = p.read_text(encoding="utf-8")
                self.assertIn('hreflang="zh-CN"', source, f"{slug}/{lang}: 缺 zh-CN")
                self.assertIn('hreflang="en"', source, f"{slug}/{lang}: 缺 en")
                self.assertIn("x-default", source, f"{slug}/{lang}: 缺 x-default")
                self.assertIn(canonical(slug, lang), sitemap, f"sitemap 缺 {canonical(slug, lang)}")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **步骤 2：运行，确认只剩验收闸门失败**

```bash
cd /Users/cheenle/HAM/website/portal && python3 -m unittest tests.test_blog_language -v 2>&1 | tail -6
```

预期：`Ran 12 tests` → `FAILED (failures=1)`，唯一失败是 `test_pending_entries_are_gone`。

若出现**其他**失败，说明真实站点与规范基线不一致：把它记入对应批次任务，**不得**为了让测试变绿而扩充挂起名单。

- [ ] **步骤 3：确认既有契约测试未被影响**

```bash
cd /Users/cheenle/HAM/website/portal && python3 -m unittest discover tests 2>&1 | tail -3
```

预期：`Ran 90 tests` 左右，`FAILED (failures=1)`（同样是验收闸门）。

- [ ] **步骤 4：提交**

```bash
cd /Users/cheenle/HAM/website && git add portal/tests/test_blog_language.py && git commit -m "test(blog): 语言体系可执行约束——结构/镜像/阈值/术语/禁用词（含双挂起名单）"
```

---

## 任务 3：样板 A —— `coda` 引文镜像

**文件：**

- 修改：`portal/blog/coda/zh/index.html`（8 处引文改为 `ba-quote`）
- 修改：`portal/blog/coda/index.html`（新增 8 处英文 `ba-quote`）

**引文配对表（id / 中文原文 / 英文译本 / 出处）**

| data-quote-id | 中文原文 | 英文（自译，标 trans.） | data-quote-cite |
| --- | --- | --- | --- |
| `wang-yangming-zhi-bu-li` | 志不立，天下无可成之事 | When resolve is not established, nothing in the world can be accomplished. | 王阳明《教条示龙场诸生》 / Wang Yangming, *Instructions for Longchang* |
| `zuozhuan-san-buxiu` | 太上有立德，其次有立功，其次有立言；虽久不废，此之谓不朽 | The highest is to establish virtue; next, achievement; next, words. Though long, they are not discarded — this is called immortality. | 《左传·襄公二十四年》 / *Zuo Zhuan*, Duke Xiang 24 |
| `sima-qian-cang-ming-shan` | 藏之名山，传之其人，通邑大都 | Deposit it in the famous mountains, pass it to the right person, circulate it in the great cities. | 司马迁《报任安书》 / Sima Qian, *Letter to Ren An* |
| `lunyu-min-wu-xin-bu-li` | 自古皆有死，民无信不立 | Death has been the lot of all from of old; but a people without trust cannot stand. | 《论语·颜渊》 / *Analects* 12.7 |
| `laozi-tiandi-bu-ren` | 天地不仁，以万物为刍狗 | Heaven and earth are not benevolent; they treat the myriad things as straw dogs. | 《老子·第五章》 / *Laozi*, ch. 5 |
| `kundera-god-laughs` | 人类一思考，上帝就发笑 | When man thinks, God laughs. | 昆德拉《小说的艺术》 / Milan Kundera, *The Art of the Novel* |
| `tangtaizong-yi-ren-wei-jing` | 以人为镜，可以明得失 | With another person as a mirror, one can see one's own gains and losses. | 唐太宗，见《旧唐书·魏征传》 / Emperor Taizong, *Old Book of Tang* |
| `zhangzai-ji-juexue` | 为往圣继绝学 | Continue the discontinued learning of past sages. | 张载「横渠四句」 / Zhang Zai, *Four Sentences of Hengqu* |

- [ ] **步骤 1：中文侧改标记**

把每处引文改写为（`lang` 属性、引号由 CSS 生成，文本内不写引号）：

```html
<blockquote class="ba-quote" data-quote-id="wang-yangming-zhi-bu-li" data-quote-kind="classic" data-quote-cite="王阳明《教条示龙场诸生》">
  <p class="ba-quote-orig" lang="zh">志不立，天下无可成之事。</p>
  <p class="ba-quote-trans" lang="zh">无志，则天下无事可成。</p>
</blockquote>
```

中文页的 `ba-quote-trans` 也写中文（白话桥接，见规范 §3.4 第 2 条），行文里原本紧跟着的那句白话解释保留在块外。原有 8 处引文删除 `「」` 手写引号，其余正文**一字不动**。

- [ ] **步骤 2：英文侧加镜像**

在英文页对应小节内插入同名 id 的块（原文在上、译本在下）：

```html
<blockquote class="ba-quote" data-quote-id="wang-yangming-zhi-bu-li" data-quote-kind="classic" data-quote-cite="Wang Yangming, *Instructions for Longchang* (1508)">
  <p class="ba-quote-orig" lang="zh">志不立，天下无可成之事。</p>
  <p class="ba-quote-trans" lang="en">When resolve is not established, nothing in the world can be accomplished. <span class="ba-quote-by">trans.</span></p>
</blockquote>
```

英文页同样以 `ba-quote-orig` 放原文（中文），`ba-quote-trans` 放英译——镜像断言只比对 id，不比对语言方向。

- [ ] **步骤 3：验证**

```bash
cd /Users/cheenle/HAM/website/portal && python3 -m unittest tests.test_blog_language -v 2>&1 | tail -5
python3 -c "
import re
for f in ['blog/coda/index.html','blog/coda/zh/index.html']:
    s=open(f,encoding='utf-8').read()
    print(f, re.findall(r'data-quote-id=\"([a-z-]+)\"', s))"
```

预期：两份文件的 id 列表完全相同，且 8 个。

- [ ] **步骤 4：提交**

```bash
cd /Users/cheenle/HAM/website && git add portal/blog/coda && git commit -m "style(blog): 《跋》引文结构化 + 英文侧八处引文镜像（样板 A）"
```

---

## 任务 4：样板 B —— `ft710` 升骨架 + 新写中文

**文件：**

- 修改：`portal/blog/ft710-usb-remote-control/index.html`
- 创建：`portal/blog/ft710-usb-remote-control/zh/index.html`

**结构映射（现有 9 个 h2 → 9 节，编号顺延）**

| 节 | id | 英文标题（保留） | 中文标题 |
| --- | --- | --- | --- |
| 01 | `anatomy` | Anatomy of the FT-710 USB port | 一根线里的三张面孔 |
| 02 | `spi-bridge` | The FT4222 SPI bridge: spectrum without a dongle | FT4222：不要 dongle 的频谱 |
| 03 | `scope-frame` | Inside the 4096-byte scope frame | 4096 字节里的频谱帧 |
| 04 | `cat` | CAT control over the Enhanced COM Port | 增强 COM 口的 CAT 控制 |
| 05 | `pipeline` | From SPI to browser: the data pipeline | 从 SPI 到浏览器 |
| 06 | `transmit` | What happens when you transmit | 发射时发生什么 |
| 07 | `degradation` | Graceful degradation: S-meter fallback | 优雅降级：退回 S 表 |
| 08 | `comparison` | FT-710 + USB vs the SCU-LAN10 | 与本家 dongle 的对照 |
| 09 | `closing` | What this means for MRRC Modern | 这条线的去向 |

**TL;DR（5 条，实操文 fact 为主）**

1. 【事实】USB 口一次暴露三个设备：CP210x CAT、FT4222 SPI 桥、C-Media 音频编解码。
2. 【事实】频谱来自 FT4222 SPI 桥，配置为单 I/O、24 MHz ÷ 64 = 375 kHz、4096 字节/次。
3. 【事实】音频是同一条线上的标准 UAC 设备，无需额外硬件。
4. 【推断】CAT 一条串口、频谱一条 SPI、音频一条 UAC，三条链路可以独立降级互不牵连。
5. 【事实】MRRC Modern 沿用这条通路；FT-710 独立项目已归档，只作历史入口。

- [ ] **步骤 1：英文页换骨架**

把 `<div class="ba-prose">` 正文整块替换为 9 个 `<section class="ag-section">`（每节 `ag-section-header` + `ag-section-label` + `ag-section-title` + `ag-section-subtitle`），并在 `</nav>`（topbar）之后插入 hero 摘要 pills 与 `ag-anchor-nav`：

```html
<div class="ag-hero-stats" aria-label="文章摘要">
  <span class="ag-pill"><i class="fas fa-plug"></i> 1 cable · 3 interfaces</span>
  <span class="ag-pill"><i class="fas fa-wave-square"></i> FT4222 SPI · 4096 B frames</span>
  <span class="ag-pill"><i class="fas fa-microchip"></i> no SCU-LAN10</span>
  <span class="ag-pill"><i class="fas fa-scale-balanced"></i> field evidence, not vendor claims</span>
</div>
<div class="ag-anchor-shell"><div class="container"><nav class="ag-anchor-nav" aria-label="页面章节"><a href="#anatomy">01</a><a href="#spi-bridge">02</a><a href="#scope-frame">03</a><a href="#cat">04</a><a href="#pipeline">05</a><a href="#transmit">06</a><a href="#degradation">07</a><a href="#comparison">08</a><a href="#closing">09</a></nav></div></div>
```

删除 `ul.ba-tags`；把 3 处关键参数表保留为 `ag-table`；每条 TL;DR 用 `ba-tldr`（结构照抄 `portal/blog/three-axes/index.html` 的头两个 section）。正文技术叙述**不改写**，只做搬移与标题分级。

- [ ] **步骤 2：新写中文页**

以英文页为源，按三档中的**实操文**规矩新写中文（不是翻译）：去翻译腔、以数据立论、不引经典、`「」` 引号、均句长 ≤55 字、破折号 ≤6‰。头部照抄 `portal/blog/three-axes/zh/index.html` 的 topbar / hero / 锚点骨架，替换标题与文案；`hreflang` 指回 `https://www.vlsc.net/blog/ft710-usb-remote-control/`。

中文长句上限自查：

```bash
cd /Users/cheenle/HAM/website/portal && python3 -c "
import re,html
s=open('blog/ft710-usb-remote-control/zh/index.html',encoding='utf-8').read()
m=re.search(r'<main class=\"ba-main\">.*?</main>',s,flags=re.S)
t=html.unescape(re.sub(r'<[^>]+>',' ',m.group(0)))
n=len(re.findall(r'[\u4e00-\u9fff]',t)); k=len(re.findall(r'[。！？]',t)); d=t.count('——')
print(f'汉字={n} 均句长={n/k:.1f} 破折号={d/n*1000:.1f}‰')"
```

预期：`均句长` ≤ 55、`破折号` ≤ 6.0。

- [ ] **步骤 3：去掉挂起项并验证**

从 `portal/tests/test_blog_language.py` 的 `PENDING_ARTICLES` 删除 `("ft710-usb-remote-control", "en")` 与 `("ft710-usb-remote-control", "zh")`，然后：

```bash
cd /Users/cheenle/HAM/website/portal && python3 -m unittest tests.test_blog_language -v 2>&1 | tail -5
```

- [ ] **步骤 4：提交**

```bash
cd /Users/cheenle/HAM/website && git add -A portal/blog/ft710-usb-remote-control portal/tests/test_blog_language.py && git commit -m "feat(blog): FT-710 USB 升骨架 + 新写中文（样板 B）"
```

---

## 任务 5：批次 2 —— 论说文对齐（4 篇）

**文件：** `portal/blog/{faculties,ming-li-dao-tian,only-imagination,connections-recursive-intelligence}/{index.html,zh/index.html}`

**逐篇工单**

| 篇 | 中文侧工作 | 英文侧工作 | 阈值 |
| --- | --- | --- | --- |
| `faculties` | 把《庄子·天道》轮扁对话改为 2 个 `ba-quote`：`zhuangzi-lunbian-dialogue`（对话）、`zhuangzi-lunbian-skill`（徐则甘而不固…口不能言） | **英文版完全没有这则故事**，需在第二节前补写英文段落并放置同 id 的 `ba-quote`（`orig` 放中文原文，`trans` 放英译） | 破折号 35→≤29 |
| `ming-li-dao-tian` | 4 处经典改 `ba-quote`：`lunyu-shiwu`（吾十有五而志于学…五十而知天命）、`lunyu-buzhi-ming`（不知命，无以为君子也）、`xunzi-dao-sui-er`（道虽迩，不行不至）、`lunyu-tian-he-yan`（天何言哉？四时行焉） | 英文侧 4 处同 id 镜像 | 破折号 34→≤17 |
| `only-imagination` | **新增 3 处经典**：`wenxin-shen-si`（刘勰《文心雕龙·神思》「思接千载」「视通万里」——与本文标题同源）、`wenfu-guan-gu`（陆机《文赋》「观古今于须臾，抚四海于一瞬」）、`xunzi-zhongri`（《荀子·劝学》「吾尝终日而思矣，不如须臾之所学也」） | 英文侧 3 处同 id 镜像 | 破折号 4.9‰ 已达标 |
| `connections` | 结构迁移：`ul.ba-tags` → hero pills；`citation` → `ba-cite-ref`（22 处，含 CSS 类名）；90 处弯引号 `“”` → `「」`（参考文献条目的英文论文标题除外）；**新增 3 处经典**：`zhouyi-tongsheng`（《周易·乾·文言》「同声相应，同气相求」）、`zhangzai-minwu`（张载《西铭》「民吾同胞，物吾与也」）、`zhuangzi-jibei`（《庄子·则阳》「丘山积卑而为高，江河合水而为大」） | 英文侧 3 处同 id 镜像 + `citation` 改名同步 | 破折号 1.3‰ 已达标 |

**英译（自译，均标 `trans.`，`data-quote-cite` 用英文出处）**

| id | 英文译本 |
| --- | --- |
| `zhuangzi-lunbian-dialogue` | "May I ask what words my lord is reading?" "The words of sages." "Are those sages alive?" "They are dead." "Then what you read is only the dregs and refuse of the ancients." |
| `zhuangzi-lunbian-skill` | If I go easy it is smooth but not firm; if I hurry it grips but will not enter. Neither easy nor hurried, the feel comes to the hand and answers to the heart — I cannot put it into words. |
| `lunyu-shiwu` | At fifteen I set my heart on learning; at thirty I took my stand; at forty I had no doubts; at fifty I knew the decree of Heaven. |
| `lunyu-buzhi-ming` | Without knowing the decree of Heaven, one cannot be a noble person. |
| `xunzi-dao-sui-er` | Though the way is near, it will not arrive unless walked. |
| `lunyu-tian-he-yan` | What does Heaven say? The four seasons run their course; the myriad things come to life. |
| `wenxin-shen-si` | In stillness the thought reaches across a thousand years; in a quiet change of expression the eye travels ten thousand li. |
| `wenfu-guan-gu` | Survey past and present in a moment; touch all within the four seas in a blink. |
| `xunzi-zhongri` | I once spent a whole day in thought, and it was not so good as a moment of learning. |
| `zhouyi-tongsheng` | Like sounds answer each other; like breaths seek one another. |
| `zhangzai-minwu` | All people are my siblings; all things are my companions. |
| `zhuangzi-jibei` | Hills and mountains pile up the low to become high; rivers and seas gather the waters to become great. |

- [ ] **步骤 1：按上表逐篇改中文侧**（每篇改完立刻跑度量命令）
- [ ] **步骤 2：按上表逐篇改英文侧**（id 必须 1:1 对应）
- [ ] **步骤 3：破折号减负**（只删冗余破折号，不删信息；`faculties` 35→29、`ming-li-dao-tian` 34→17）
- [ ] **步骤 4：从 `PENDING_ARTICLES` 删除四篇（两语共 8 条），从 `PENDING_DASH` 删除 `faculties` 与 `ming-li-dao-tian`**

```bash
cd /Users/cheenle/HAM/website/portal && python3 -m unittest tests.test_blog_language -v 2>&1 | tail -5
```

- [ ] **步骤 5：每篇一个 commit**

```bash
cd /Users/cheenle/HAM/website && git add portal/blog/faculties && git commit -m "style(blog): 《斫轮》引文结构化 + 英文侧镜像（补齐庄子·天道开篇）"
# 其余三篇同法，message 用「篇名 + 该篇主要动作」
```

---

## 任务 6：批次 3 —— 实操文对齐（7 页）

**文件：** `portal/blog/solo-loop/…`、`support-loop/…`、`three-axes/…`、`seven-billion-tokens/{,almanac/,ledger/,playbook/}…`（各 EN+ZH）

**工作内容**

| 篇 | 中文侧 | 英文侧 | 阈值 |
| --- | --- | --- | --- |
| `solo-loop` | 把用户上报原文、工具输出原文标为 `ba-quote kind="project"`（如「你发来的东西不会被晾着」） | 同 id 镜像 | 2.4‰ 达标 |
| `support-loop` | 上报原文（「已损坏，无法打开」「安装器拉起来了」）标 `ba-quote kind="project"` | 同 id 镜像 | 49→≤46 |
| `three-axes` | 把契约条文的逐字引用（「PTT 不能卡死」等）标 `ba-quote kind="project"` | 同 id 镜像 | 5.1‰ 达标 |
| `seven-billion-tokens` | 测试输出（`937 collected` 等）标 `ba-quote kind="engineering"` | 同 id 镜像 | 46→≤33 |
| `almanac` | 同上（若有逐字输出） | 同 id 镜像 | 14→≤7 |
| `ledger` | 同上 | 同 id 镜像 | 5.7‰ 达标 |
| `playbook` | 同上 | 同 id 镜像 | 3.4‰ 达标 |

**约束：** 本批全是实操文，`kind="classic"` 必须为 0；进 `ba-quote` 的必须是**逐字外部文本**（用户上报、测试输出、版本行），行文中的概念性引号（如「活成一家公司」）留在散文里，不改成块——否则会制造大量无出处的伪引文。

- [ ] **步骤 1：逐篇标注 `ba-quote`（EN/id 同步）**
- [ ] **步骤 2：破折号减负至阈值内**
- [ ] **步骤 3：从 `PENDING_DASH` 删除 `support-loop`、`seven-billion-tokens`、`seven-billion-tokens/almanac`，跑全量测试**
- [ ] **步骤 4：每篇一个 commit**

```bash
cd /Users/cheenle/HAM/website && git add portal/blog/support-loop && git commit -m "style(blog): 《闻过则喜》上报原文结构化 + 英文侧镜像 + 破折号减负"
```

---

## 任务 7：批次 4 —— 老文补齐（3 篇）

**文件：** `portal/blog/{efhw-esp32s3-auto-tuner,opus-vs-pcm-remote-audio,psk-reporter-dxcc-hunting}/index.html`（改）+ 各自 `zh/index.html`（新建）

**结构映射**

| 篇 | 节（英文原标题保留） | 中文标题建议 |
| --- | --- | --- |
| `efhw-esp32s3-auto-tuner` | `hardware` Hardware platform · `matching` The matching network · `swr-sensing` Where the SWR sensing actually lives · `algorithm` The tuning algorithm · `safety` Safety and fault detection · `rtos` FreeRTOS architecture · `protocol` The JSON protocol · `closing` What ships | 硬件平台 · 匹配网络 · 驻波检测到底在哪 · 调谐算法 · 安全与故障检测 · FreeRTOS 架构 · JSON 协议 · 交付了什么 |
| `opus-vs-pcm-remote-audio` | `bandwidth` The bandwidth math · `encoder` The Opus encoder settings · `ctypes` A real-world ctypes quirk · `switching` PCM ↔ Opus switching · `latency` The latency budget · `transport` The WebSocket audio transport · `rates` Sample rates and the signal path · `closing` What it bought | 带宽算术 · 编码器设置 · 一个真实存在的 ctypes 缺陷 · 无握手的编解码切换 · 延迟预算 · WebSocket 音频通路 · 采样率与信号链 · 换来了什么 |
| `psk-reporter-dxcc-hunting` | `oracle` Your neighbors are a propagation oracle · `dashboard` A personal PSK Reporter dashboard · `recommendation` How the recommendation works · `reading` Reading the table · `session` A real evening session · `actions` The action sequence · `lessons` What I've learned · `closing` Do this tonight | 邻居就是传播预言机 · 自建 PSK Reporter 看板 · 推荐是怎么算出来的 · 怎么读这张表 · 一个真实的傍晚 · 行动顺序 · 学到的东西 · 今晚就能做 |

**每篇 TL;DR：4 条**（fact 为主，末条可为 inference），内容取该篇最硬的三到四个数字或结论；`ba-quote` 允许 `kind="engineering"`（数据手册、scipy/ctypes 文档、PSK Reporter 数据源），`classic` 必须为 0。

- [ ] **步骤 1：`efhw` EN 换骨架 + 新建中文 + 从 `PENDING_ARTICLES` 删两语条目 + 提交**
- [ ] **步骤 2：`opus` EN 换骨架 + 新建中文 + 从 `PENDING_ARTICLES` 删两语条目 + 提交**
- [ ] **步骤 3：`psk` EN 换骨架 + 新建中文 + 从 `PENDING_ARTICLES` 删两语条目 + 提交**

每篇验证：

```bash
cd /Users/cheenle/HAM/website/portal && python3 -m unittest tests.test_blog_language -v 2>&1 | tail -3
```

---

## 任务 8：批次 5 —— 总纲（4 页）

**文件：** `portal/agentic.html`、`portal/engineering.html`、`portal/zh/agentic.html`、`portal/zh/engineering.html`

- [ ] **步骤 1：术语中英对照**

两页的中文版补 `ag-term-grid`（英文版已有对应术语表则对齐），至少覆盖规范 §3.5 的九条术语；术语英文版用 `field` / `judgment stays human` / `two ledgers` / `intent · boundary · verdict` / `agentic engineering` / `Forward Deployed Engineering` / `constraint registry` / `version record`。

```html
<div class="ag-term-grid">
  <div class="ag-card"><h3>现场</h3><p>field</p></div>
  <div class="ag-card"><h3>裁决归人</h3><p>judgment stays human</p></div>
</div>
```

- [ ] **步骤 2：引文挂论点**（总纲档允许经典 + 工程文献）

在 `thesis` / `lineage` 两节各挂 1 处 `ba-quote`，`data-quote-id` 与另一语言页同名；引文必须支撑该节 claim，禁止装饰性引用。

- [ ] **步骤 3：禁用词清理**

```bash
cd /Users/cheenle/HAM/website/portal && grep -n "代理式工程\|被用来\|值得注意的是\|在当今时代\|深入探讨\|综上所述" agentic.html engineering.html zh/agentic.html zh/engineering.html || echo "clean"
```

- [ ] **步骤 4：跑既有契约测试 + 新测试**

```bash
cd /Users/cheenle/HAM/website/portal && python3 -m unittest discover tests 2>&1 | tail -3
```

预期：`Ran <N> tests ... OK`（`test_agentic_pages` / `test_engineering_pages` 的 section 契约不得被破坏）。

- [ ] **步骤 5：提交**

```bash
cd /Users/cheenle/HAM/website && git add portal/agentic.html portal/engineering.html portal/zh/agentic.html portal/zh/engineering.html && git commit -m "style(portal): 总纲两页补齐术语中英对照与论点引文"
```

---

## 任务 9：批次 6 —— 索引与元数据

**文件：** `portal/blog/index.html`、`portal/blog/zh/index.html`、`portal/sitemap.xml`、`portal/{index,about,contact,privacy}.html` + `portal/zh/` 同名

- [ ] **步骤 1：两侧索引卡片对齐**

英文索引每张卡加中文入口（`bc-chips` 内加 `/blog/<slug>/zh/`），中文索引去掉「· 英文」标记（4 篇新中文上线后不再有纯英文文章），两侧 slug 集合由测试断言。

- [ ] **步骤 2：sitemap 收录新中文页**

```bash
cd /Users/cheenle/HAM/website/portal && python3 make_sitemap.py && python3 -c "
import re
s=open('sitemap.xml',encoding='utf-8').read()
for u in ['ft710-usb-remote-control/zh/','efhw-esp32s3-auto-tuner/zh/','opus-vs-pcm-remote-audio/zh/','psk-reporter-dxcc-hunting/zh/']:
    assert u in s, u
print('sitemap OK')"
```

- [ ] **步骤 3：landing 8 页术语与导航核对**

```bash
cd /Users/cheenle/HAM/website/portal && grep -rn "代理式工程\|三款产品\|FDE 方法论" index.html about.html contact.html privacy.html zh/*.html || echo "clean"
```

- [ ] **步骤 4：提交**

```bash
cd /Users/cheenle/HAM/website && git add -A portal/blog/index.html portal/blog/zh/index.html portal/sitemap.xml portal/index.html portal/about.html portal/contact.html portal/privacy.html portal/zh && git commit -m "docs(blog): 中英索引对齐 + sitemap 收录四篇新中文 + landing 术语核对"
```

---

## 任务 10：批次 7 —— 收尾验收

- [ ] **步骤 1：清空挂起项**

`portal/tests/test_blog_language.py` 的两个名单必须都为空：

```python
PENDING_DASH: dict[str, str] = {}
PENDING_ARTICLES: dict[tuple[str, str], str] = {}
```

- [ ] **步骤 2：全量测试**

```bash
cd /Users/cheenle/HAM/website/portal && python3 -m unittest discover tests 2>&1 | tail -3
```

预期：`Ran <N> tests ... OK`（现有 78 + 新增 12），无 failures。

- [ ] **步骤 3：逐篇度量复核**

```bash
cd /Users/cheenle/HAM/website/portal && for f in $(find blog -path '*/zh/index.html' | sort); do
python3 -c "
import re,html,sys
s=open('$f',encoding='utf-8').read()
s=re.sub(r'<script.*?</script>','',s,flags=re.S)
m=re.search(r'<main class=\"ba-main\">.*?</main>',s,flags=re.S)
t=html.unescape(re.sub(r'<[^>]+>',' ',m.group(0)))
n=len(re.findall(r'[\u4e00-\u9fff]',t)); k=len(re.findall(r'[。！？]',t)); d=t.count('——')
print(f'$f 汉字={n} 均句长={n/k:.1f} {d/n*1000:.1f}‰')"; done
```

预期：全部 `≤6.0‰`。

- [ ] **步骤 4：浏览器目检（静态站点，本地开服务）**

```bash
cd /Users/cheenle/HAM/website/portal && python3 -m http.server 8899
```

逐篇确认：TL;DR 卡、锚点导航、`ba-quote` 引文块在 EN/ZH 两页样式一致、`?v=4` 生效（Ctrl+Shift+R 强刷）。

- [ ] **步骤 5：收尾 commit**

```bash
cd /Users/cheenle/HAM/website && git add portal/tests/test_blog_language.py && git commit -m "test(blog): 语言体系挂起项清零——全站达到验收状态"
```

- [ ] **步骤 6：部署（默认不做）**

规范 §2 已定：本次不发版。只有用户明确要求时才执行：

```bash
cd /Users/cheenle/HAM/website/portal && ./deploy.sh
```

---

## 自检记录

**规格覆盖度：**

| 规范章节 | 对应任务 |
| --- | --- |
| §3.1 三档判据 | 任务 2（断言）+ 任务 5/6/7/8（内容） |
| §3.2 度量算法 | 任务 2 的 `metrics()` |
| §3.3 基线 / 超标清单 | 任务 5（2 篇）+ 任务 6（3 篇） |
| §3.4 引文四条规则 | 任务 3/5/6/8 的 `ba-quote` 工单 |
| §3.5 术语表 | 任务 8 步骤 1 |
| §3.6 禁用词 | 任务 2 的 `BANNED_PHRASES` + 任务 8/9 清理 |
| §3.7 档位归属 | 任务 2 的 `ARTICLES` 常量 |
| §4 `ba-quote` 组件 | 任务 1 |
| §5 可执行约束 | 任务 2 |
| §6 施工批次 | 任务 3–10 |
| §8 验收 5 条 | 任务 10 |

**已知偏差（已在计划中显式处理）：**

1. 执行顺序把「测试骨架」提到样板之前（TDD），规范批次编号不变。
2. 挂起名单拆成两个（规范只写了一个「待清」白名单）：`PENDING_DASH` 管语体阈值、`PENDING_ARTICLES` 管结构镜像。原因是这两类失败的生命周期不同——阈值类今天只涉及 5 篇、到期批次 2/3；结构类涉及 12 篇 ×2 语、跨越批次 0/2/4/9。
3. 规范 §3.1 要求论说文经典 ≥3，但 `only-imagination` 与 `connections` 目前**零**经典引用，`faculties` / `ming-li-dao-tian` 的英文侧同样为零。任务 5 因此包含**新增引文**（候选引文与英译已在该任务表中给出），这是规范未显式列出的内容工作。
4. 度量算法必须避坑：`HTMLParser` 拼接会把相邻表格单元格的两个「—」误拼成「——」（`ledger` 5.7‰ → 6.7‰）。测试里 `body_text()` 按规范 §3.2 用"标签替换为空格"实现，已用真实站点验证。
