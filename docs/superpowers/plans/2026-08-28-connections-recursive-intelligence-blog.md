# “链接为王”双语科学随笔实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 将《链接为王：从神经元到文明级智能的递归升级》改写为有一手证据、清晰论证边界和完整引用的中英文科学随笔，并发布到 VLSC Blog。

**架构：** 新建一个双语文章目录和局部样式文件，中文与英文共享章节 ID、引用编号、DOI 集合和事实边界，但分别按语言习惯写作。文章使用 `fact`、`inference`、`analogy`、`thesis` 四类声明区分事实与思想实验；Blog 首页只新增分类、卡片和 JSON-LD 条目。

**技术栈：** HTML5、CSS3、内联 SVG、JSON-LD、Python 3 标准库 `unittest`/`html.parser`、现有 `octen.css`、`blog.css` 和 `global-nav.js`。

---

## 文件结构

- 创建：`portal/blog/connections-recursive-intelligence/index.html` — 英文长文。
- 创建：`portal/blog/connections-recursive-intelligence/zh/index.html` — 中文长文。
- 创建：`portal/blog/connections-recursive-intelligence/article.css` — 声明标签、图表、矩阵、参考文献和响应式样式。
- 创建：`portal/tests/test_connections_article.py` — 双语结构、事实、引用、SEO、资源和可访问性契约。
- 修改：`portal/blog/index.html` — 增加 Intelligence 分类、文章卡片和 Blog JSON-LD 条目。

不修改全局 `blog.css`、`octen.css` 或 `global-nav.js`。主工作区中的 `portal/blog/index.html` 有用户未提交修改；合并前必须单独保存和 stash，合并后恢复。生产环境的 Blog 首页使用精确幂等补丁，不能用本地文件覆盖线上其他内容。

---

### 任务 1：建立文章事实与结构契约

**文件：**
- 创建：`portal/tests/test_connections_article.py`

- [ ] **步骤 1：创建失败测试**

创建测试，定义：

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
ARTICLES = {
    "en": PORTAL / "blog" / "connections-recursive-intelligence" / "index.html",
    "zh": PORTAL / "blog" / "connections-recursive-intelligence" / "zh" / "index.html",
}
BLOG_INDEX = PORTAL / "blog" / "index.html"
REQUIRED_SECTIONS = {
    "premise", "neuron", "connectome", "epistemology",
    "civilization", "limits", "recursion", "references",
}
REQUIRED_CLAIM_TYPES = {"fact", "inference", "analogy", "thesis"}
REQUIRED_DOIS = {
    "10.1038/s41586-024-07558-y",
    "10.1038/s41586-024-07763-9",
    "10.1038/s41592-022-01466-7",
    "10.1126/science.adh1174",
    "10.1038/s41586-019-1424-8",
    "10.1038/s41586-021-03819-2",
    "10.1126/science.ade9097",
    "10.1038/s41586-021-03506-2",
}


class ArticleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.section_ids: set[str] = set()
        self.refs: list[str] = []
        self.svg_stack: list[dict[str, bool]] = []
        self.svg_results: list[dict[str, bool]] = []
        self.canonicals: list[str] = []
        self.hreflangs: set[str] = set()
        self.json_ld: list[dict[str, object]] = []
        self._json_buffer: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        element_id = values.get("id")
        if element_id:
            self.ids.append(element_id)
        if tag == "section" and element_id:
            self.section_ids.add(element_id)
        if tag in {"a", "link", "script", "img"}:
            ref = values.get("href") or values.get("src")
            if ref:
                self.refs.append(ref)
        if tag == "link" and values.get("rel") == "canonical" and values.get("href"):
            self.canonicals.append(values["href"])
        if tag == "link" and values.get("rel") == "alternate" and values.get("hreflang"):
            self.hreflangs.add(values["hreflang"])
        if tag == "svg":
            self.svg_stack.append({"title": False, "desc": False})
        elif tag in {"title", "desc"} and self.svg_stack:
            self.svg_stack[-1][tag] = True
        if tag == "script" and values.get("type") == "application/ld+json":
            self._json_buffer = []

    def handle_data(self, data: str) -> None:
        if self._json_buffer is not None:
            self._json_buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "svg" and self.svg_stack:
            self.svg_results.append(self.svg_stack.pop())
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


class ConnectionsArticleTests(unittest.TestCase):
    def test_articles_exist(self) -> None:
        for language, path in ARTICLES.items():
            self.assertTrue(path.exists(), language)

    def test_sections_and_claim_types_match(self) -> None:
        parsed = {language: load(path) for language, path in ARTICLES.items()}
        for language, (source, parser) in parsed.items():
            self.assertEqual(REQUIRED_SECTIONS, parser.section_ids, language)
            claim_types = set(re.findall(r'data-claim-type="([^"]+)"', source))
            self.assertEqual(REQUIRED_CLAIM_TYPES, claim_types, language)
        self.assertEqual(parsed["en"][1].section_ids, parsed["zh"][1].section_ids)

    def test_connectome_facts_and_boundaries_are_present(self) -> None:
        required = {
            "en": ("139,255", "50 million", "not sufficient", "neuromodulation"),
            "zh": ("139,255", "5×10", "并不充分", "神经调质"),
        }
        forbidden = {
            "en": ("connectome alone produces complete autonomous intelligence", "human participant controlled a robotic arm"),
            "zh": ("连接组本身产生完整自主智能", "人体试验患者用意念控制机械臂"),
        }
        for language, path in ARTICLES.items():
            source, _ = load(path)
            for token in required[language]:
                self.assertIn(token, source, f"{language}: {token}")
            for phrase in forbidden[language]:
                self.assertNotIn(phrase, source, f"{language}: {phrase}")

    def test_citations_and_primary_source_sets_match(self) -> None:
        doi_sets: dict[str, set[str]] = {}
        for language, path in ARTICLES.items():
            source, _ = load(path)
            cited = set(re.findall(r'class="citation" href="#ref-(\d+)"', source))
            listed = set(re.findall(r'<li id="ref-(\d+)"', source))
            self.assertEqual(cited, listed, language)
            self.assertGreaterEqual(len(cited), 12, language)
            dois = {doi.lower() for doi in re.findall(r'doi\.org/([^"<]+)', source)}
            self.assertTrue(REQUIRED_DOIS <= dois, language)
            doi_sets[language] = dois
        self.assertEqual(doi_sets["en"], doi_sets["zh"])

    def test_ids_svg_and_local_assets_are_valid(self) -> None:
        for language, path in ARTICLES.items():
            _, parser = load(path)
            duplicates = [item for item, count in Counter(parser.ids).items() if count > 1]
            self.assertEqual([], duplicates, language)
            self.assertTrue(parser.svg_results, language)
            self.assertTrue(all(item["title"] and item["desc"] for item in parser.svg_results), language)
            for ref in parser.refs:
                parsed = urlparse(ref)
                if parsed.scheme or ref.startswith(("/", "#", "data:", "mailto:")):
                    continue
                self.assertTrue((path.parent / parsed.path).resolve().exists(), f"{language}: {ref}")

    def test_seo_language_links_and_json_ld_are_complete(self) -> None:
        for language, path in ARTICLES.items():
            source, parser = load(path)
            self.assertEqual(1, len(parser.canonicals), language)
            self.assertEqual({"en", "zh-CN", "x-default"}, parser.hreflangs, language)
            self.assertIn('property="og:type" content="article"', source)
            article_data = [item for item in parser.json_ld if item.get("@type") == "Article"]
            self.assertEqual(1, len(article_data), language)
            for field in ("headline", "description", "author", "publisher", "datePublished", "dateModified", "mainEntityOfPage"):
                self.assertIn(field, article_data[0], f"{language}: {field}")

    def test_blog_index_lists_article_and_category(self) -> None:
        source = BLOG_INDEX.read_text(encoding="utf-8")
        self.assertIn('data-filter="intelligence"', source)
        self.assertIn('data-cat="intelligence"', source)
        self.assertIn('/blog/connections-recursive-intelligence/', source)
        self.assertIn("Connections Rule", source)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **步骤 2：运行测试验证红灯**

```bash
python3 portal/tests/test_connections_article.py -v
```

预期：文章不存在、Blog 首页无 Intelligence 分类和文章入口；测试因缺失功能失败或跳过，不能因 Python/JSON 语法错误失败。

- [ ] **步骤 3：提交测试**

```bash
git add portal/tests/test_connections_article.py
git commit -m "test: define connections essay contract"
```

---

### 任务 2：建立文章视觉组件

**文件：**
- 创建：`portal/blog/connections-recursive-intelligence/article.css`

- [ ] **步骤 1：实现局部组件**

样式至少包含：

```css
.claim-box { border: 1px solid var(--border); border-left: 3px solid var(--accent); border-radius: 0 .75rem .75rem 0; padding: 1rem 1.15rem; margin: 1.5rem 0; background: var(--bg-card); }
.claim-label { display: inline-block; margin-bottom: .45rem; font-family: var(--font-mono); font-size: .72rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
.claim-box[data-claim-type="fact"] { border-left-color: #22c55e; }
.claim-box[data-claim-type="inference"] { border-left-color: #22d3ee; }
.claim-box[data-claim-type="analogy"] { border-left-color: #f59e0b; }
.claim-box[data-claim-type="thesis"] { border-left-color: #a78bfa; }
.connection-diagram { margin: 2rem 0; border: 1px solid var(--border); border-radius: 1rem; padding: 1rem; overflow: hidden; }
.connection-svg { display: block; width: 100%; height: auto; }
.scale-ladder { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: .8rem; margin: 1.5rem 0; }
.scale-step { border: 1px solid var(--border); border-radius: .75rem; padding: 1rem; background: var(--bg-card); }
.connection-table-wrap { overflow-x: auto; margin: 1.5rem 0; }
.connection-table { min-width: 900px; width: 100%; border-collapse: collapse; }
.connection-table th, .connection-table td { border-bottom: 1px solid var(--border); padding: .8rem 1rem; text-align: left; vertical-align: top; }
.evidence-boundary { border: 1px solid #f59e0b; border-radius: .8rem; padding: 1.1rem; margin: 1.5rem 0; background: rgba(245,158,11,.07); }
.references-list li { margin-bottom: .8rem; line-height: 1.6; }
.references-list a { overflow-wrap: anywhere; }

@media (max-width: 800px) {
  .scale-ladder { grid-template-columns: 1fr; }
  .claim-box { padding: .9rem; }
}

@media (prefers-reduced-motion: reduce) {
  .scale-step { transition: none; }
}
```

可增加只服务于引用、尺度标签和递归图的选择器，不修改全局 Blog CSS。

- [ ] **步骤 2：运行 CSS 诊断并提交**

```text
lsp_diagnostics(path="portal/blog/connections-recursive-intelligence/article.css", severity="all")
```

```bash
git add portal/blog/connections-recursive-intelligence/article.css
git commit -m "style: add connections essay components"
```

---
### 任务 3：撰写中文证据型科学随笔

**文件：**
- 创建：`portal/blog/connections-recursive-intelligence/zh/index.html`
- 参考：`docs/superpowers/specs/2026-08-28-connections-recursive-intelligence-blog-design.md`

- [ ] **步骤 1：建立 SEO、语言链接和文章骨架**

页面加载：

```html
<link rel="stylesheet" href="../../../css/octen.css?v=6">
<link rel="stylesheet" href="../../../css/blog.css?v=1">
<link rel="stylesheet" href="../article.css?v=1">
```

canonical 为 `https://www.vlsc.net/blog/connections-recursive-intelligence/zh/`。alternate 必须包含：

```html
<link rel="alternate" hreflang="en" href="https://www.vlsc.net/blog/connections-recursive-intelligence/">
<link rel="alternate" hreflang="zh-CN" href="https://www.vlsc.net/blog/connections-recursive-intelligence/zh/">
<link rel="alternate" hreflang="x-default" href="https://www.vlsc.net/blog/connections-recursive-intelligence/">
```

添加 Article JSON-LD，`articleSection` 为 `Intelligence`，发布日期与修改日期使用实施当天日期。正文固定章节：

```html
<section id="premise">...</section>
<section id="neuron">...</section>
<section id="connectome">...</section>
<section id="epistemology">...</section>
<section id="civilization">...</section>
<section id="limits">...</section>
<section id="recursion">...</section>
<section id="references">...</section>
```

- [ ] **步骤 2：撰写 premise 与 neuron**

`premise` 提出限定主张：链接是复杂智能的必要条件之一，但不是充分条件；决定结果的是拓扑、权重、时序、可塑性、身体、环境、协议和反馈。

`neuron` 采用“触达 → 整合 → 传递 → 反馈”，说明化学突触之外也存在电突触，不把阈值发放写成全部神经计算。加入可访问 SVG 和四类声明框中的至少三类。

必须出现：

```html
<div class="claim-box" data-claim-type="fact">...</div>
<div class="claim-box" data-claim-type="analogy">...</div>
<div class="claim-box" data-claim-type="thesis">...</div>
```

- [ ] **步骤 3：撰写 connectome 证据阶梯**

依次论述：

1. FlyWire 成年雌性果蝇全脑图：139,255 个神经元、约 `5×10<sup>7</sup>` 个化学突触，引用 `[2]`。
2. 全脑计算模型：连接和预测的递质身份产生对部分进食/梳理回路的可检验预测，且其中部分由光遗传和行为实验验证，引用 `[3]`。
3. NeuroMechFly：身体、关节、肌肉、环境和控制必须一起建模，引用 `[4]`。
4. 加入神经调质、突触强度和动力学边界，引用 `[15]`。

必须明确写出“连接结构很重要，但对完整智能并不充分”。不得写成完整数字果蝇自主智能已经实现。

- [ ] **步骤 4：重构 epistemology**

并列写作：启示与传统、哲学与逻辑、科学与工程。强调三者不是年代进化阶梯或文化排名。科学的特征写成可观测、可证伪、可重复和工程化，而不是“科学已获得世界全部真实连接”。

使用 `data-claim-type="inference"` 声明框说明：把知识系统看作关系模型是一种分析框架，不是神经机制事实。

- [ ] **步骤 5：撰写 civilization 六层矩阵**

表格固定六行：传输链接、表征链接、协作链接、因果链接、行动链接、生物链接。每行包含已实现能力、代表一手来源和未解决边界。

使用：AlphaFold `[8]`、RAG `[9]`、CICERO `[10]`、Genie/世界模型 `[11]`、RT-2 `[12]`、脑控书写 `[13]`、PRIME 登记 `[14]`、Loihi 2 `[5]`、NorthPole `[6]`、Tianjic `[7]`。

NorthPole 明确写成受脑启发的存算融合推理架构；不得与 Loihi 2 机制等同。视频预测不得直接写成物理因果理解。PRIME 只写外部设备控制研究目标和公开数字设备控制，不写人体机械臂结果。

- [ ] **步骤 6：撰写 limits 与 recursion**

`limits` 覆盖噪声、错误传播、单点失效、平台权力、群体极化、多智能体并不自动理性、跨尺度链接机制不同。结论为：链接质量、协议、反馈、治理和可验证性决定结果。

`recursion` 保留五步闭环，并使用 `data-claim-type="thesis"` 标注为作者判断。结尾使用：

```text
链接是智能的母语之一；治理链接，可能是文明下一阶段的共同工程。
```

不得把宇宙意识写成科学预测。

- [ ] **步骤 7：建立相同编号的参考文献**

使用 `li id="ref-N"`，正文引用使用：

```html
<a class="citation" href="#ref-2" aria-label="参考文献 2">[2]</a>
```

至少 15 条，编号固定为：神经科学基础、FlyWire、果蝇模型、NeuroMechFly、Loihi 2、NorthPole、Tianjic、AlphaFold、RAG、CICERO、Genie/世界模型、RT-2、脑控书写、PRIME、神经回路可变性/调质。八个必需 DOI 必须使用 `https://doi.org/<doi>` 原始格式。

- [ ] **步骤 8：加入文章页脚、语言切换和目录脚本**

复用现有 Blog 的自动目录脚本。语言切换链接到 `../`。全局脚本路径：

```html
<script src="../../../js/global-nav.js?v=6" defer data-gn="1"></script>
```

- [ ] **步骤 9：运行中文结构检查并提交**

```bash
python3 - <<'PY'
from pathlib import Path
s=Path('portal/blog/connections-recursive-intelligence/zh/index.html').read_text()
for section in ('premise','neuron','connectome','epistemology','civilization','limits','recursion','references'):
    assert f'id="{section}"' in s
for claim in ('fact','inference','analogy','thesis'):
    assert f'data-claim-type="{claim}"' in s
assert '139,255' in s and '神经调质' in s and '并不充分' in s
assert s.count('<li id="ref-') >= 15
print('Chinese article structure: PASS')
PY
git add portal/blog/connections-recursive-intelligence/zh/index.html
git commit -m "feat: add Chinese connections essay"
```

---

### 任务 4：撰写英文等价科学随笔

**文件：**
- 创建：`portal/blog/connections-recursive-intelligence/index.html`
- 对照：`portal/blog/connections-recursive-intelligence/zh/index.html`

- [ ] **步骤 1：建立英文 SEO 与同构骨架**

canonical 为 `https://www.vlsc.net/blog/connections-recursive-intelligence/`；alternate 与中文完全一致。样式路径：

```html
<link rel="stylesheet" href="../../css/octen.css?v=6">
<link rel="stylesheet" href="../../css/blog.css?v=1">
<link rel="stylesheet" href="article.css?v=1">
```

使用与中文完全相同的 section ID、`data-claim-type`、参考文献编号和 DOI 集合。语言切换链接 `zh/`。

- [ ] **步骤 2：按英文科技随笔习惯重写，而非逐句翻译**

英文全文约 3500–4500 词。保持以下精确事实：

- `139,255 neurons` 与 `roughly 50 million chemical synapses`。
- connectome is important but `not sufficient` for complete intelligence。
- `neuromodulation`、synaptic strength、dynamics、body、environment 均为边界。
- NorthPole、Loihi 2、Tianjic 的分类不同。
- Neuralink PRIME 不包含已完成的人体机械臂控制主张。

所有中文的核心限定、反例和未解决问题都必须在英文出现。

- [ ] **步骤 3：同步 SVG、矩阵、递归闭环和参考文献**

SVG 的 `title`/`desc` 使用英文且 ID 唯一。文明六层矩阵与中文逐行同构。参考文献编号、URL、DOI 集合必须与中文一致。

- [ ] **步骤 4：加入文章页脚和目录脚本**

复用现有 Blog 模板，脚本路径：

```html
<script src="../../js/global-nav.js?v=6" defer data-gn="1"></script>
```

- [ ] **步骤 5：运行双语文章测试的页面部分并提交**

```bash
python3 portal/tests/test_connections_article.py \
  ConnectionsArticleTests.test_articles_exist \
  ConnectionsArticleTests.test_sections_and_claim_types_match \
  ConnectionsArticleTests.test_connectome_facts_and_boundaries_are_present \
  ConnectionsArticleTests.test_citations_and_primary_source_sets_match \
  ConnectionsArticleTests.test_ids_svg_and_local_assets_are_valid \
  ConnectionsArticleTests.test_seo_language_links_and_json_ld_are_complete -v
```

预期：全部 PASS。

```bash
git add portal/blog/connections-recursive-intelligence/index.html
git commit -m "feat: add English connections essay"
```

---
### 任务 5：接入 Blog 首页

**文件：**
- 修改：`portal/blog/index.html`

- [ ] **步骤 1：增加 Intelligence 分类**

在分类按钮组加入：

```html
<button type="button" data-filter="intelligence">Intelligence</button>
```

- [ ] **步骤 2：增加文章卡片**

在 `blog-grid` 顶部加入：

```html
<article class="blog-card" data-cat="intelligence">
  <div class="bc-cat">Intelligence</div>
  <h2><a href="/blog/connections-recursive-intelligence/">Connections Rule: Recursive Intelligence from Neurons to Civilization</a></h2>
  <p class="bc-excerpt">From the fruit-fly connectome to RAG, multi-agent systems, embodied AI, and brain–computer interfaces: an evidence-led argument for why connection matters—and why connection alone is not enough.</p>
  <div class="bc-meta">BG1SB · Aug 28, 2026 · ~24 min read</div>
</article>
```

- [ ] **步骤 3：更新 Blog JSON-LD**

在 `blogPost` 数组加入：

```json
{
  "@type": "BlogPosting",
  "headline": "Connections Rule: Recursive Intelligence from Neurons to Civilization",
  "url": "https://www.vlsc.net/blog/connections-recursive-intelligence/",
  "datePublished": "2026-08-28"
}
```

保持 JSON 有效。

- [ ] **步骤 4：运行完整契约测试并提交**

```bash
python3 portal/tests/test_connections_article.py -v
git add portal/blog/index.html
git commit -m "feat: list connections essay in VLSC Blog"
```

预期：全部测试 PASS。

---

### 任务 6：事实、链接、可访问性和本地验收

**文件：**
- 修改（仅发现问题时）：文章、局部 CSS、测试或 Blog 首页。

- [ ] **步骤 1：运行 LSP 与综合诊断**

```text
lsp_diagnostics(paths=[
  "portal/blog/connections-recursive-intelligence/index.html",
  "portal/blog/connections-recursive-intelligence/zh/index.html",
  "portal/blog/connections-recursive-intelligence/article.css",
  "portal/tests/test_connections_article.py"
], severity="all", serverScope="all")

lens_diagnostics(mode="full", paths=[
  "portal/blog/connections-recursive-intelligence/",
  "portal/tests/test_connections_article.py"
], severity="all", refreshRunners="cheap")
```

预期：无本次变更引入的 blocking error。

- [ ] **步骤 2：核对来源与禁止断言**

```bash
rg -n '139,255|50 million|5×10|neuromodulation|神经调质|NCT06429735|NorthPole|Loihi 2|Tianjic' \
  portal/blog/connections-recursive-intelligence/index.html \
  portal/blog/connections-recursive-intelligence/zh/index.html
rg -n 'complete autonomous intelligence|人体试验患者用意念控制机械臂|结构即功能|GPT-5|Gemini 2' \
  portal/blog/connections-recursive-intelligence/index.html \
  portal/blog/connections-recursive-intelligence/zh/index.html
```

预期：第一组事实在两种语言中存在；第二组无匹配。若讨论“structure and function”，必须使用限定措辞而不是“结构即功能”。

- [ ] **步骤 3：运行全部相关测试**

```bash
python3 portal/tests/test_connections_article.py -v
python3 portal/tests/test_engineering_pages.py -v
python3 portal/tests/test_fde_pages.py -v
git diff --check 08a4888..HEAD
```

预期：全部 PASS，空白检查无输出。

- [ ] **步骤 4：运行本地 HTTP smoke test**

```bash
python3 -m http.server 8765 --directory portal >/tmp/vlsc-connections-http.log 2>&1 &
server_pid=$!
trap 'kill "$server_pid" 2>/dev/null || true' EXIT
sleep 1
curl -fsS http://127.0.0.1:8765/blog/connections-recursive-intelligence/ >/dev/null
curl -fsS http://127.0.0.1:8765/blog/connections-recursive-intelligence/zh/ >/dev/null
curl -fsS http://127.0.0.1:8765/blog/connections-recursive-intelligence/article.css >/dev/null
curl -fsS http://127.0.0.1:8765/blog/ >/dev/null
kill "$server_pid"
trap - EXIT
```

预期：4/4 请求成功。

- [ ] **步骤 5：人工结构检查**

在桌面和约 390px 宽度检查：目录、claim 标签、SVG、尺度阶梯、六层矩阵横向滚动、数字引用跳转、中英文切换、参考文献长 URL 换行。确认文章没有用视觉样式掩盖事实类型。

- [ ] **步骤 6：提交验收修正**

若产生修正，精确暂存本任务文件并提交：

```bash
git add portal/blog/connections-recursive-intelligence portal/tests/test_connections_article.py portal/blog/index.html
git commit -m "fix: verify connections essay evidence and accessibility"
```

无修正则不创建空提交。

---

### 任务 7：合并、保护 Blog 首页修改并发布

- [ ] **步骤 1：发布前新鲜验证**

```bash
python3 portal/tests/test_connections_article.py -v
python3 portal/tests/test_engineering_pages.py -v
python3 portal/tests/test_fde_pages.py -v
git diff --check 08a4888..HEAD
git status --short
```

预期：全部测试通过，feature worktree 干净。

- [ ] **步骤 2：保护主工作区 Blog 首页修改并快进合并**

在主仓库：

```bash
git diff -- portal/blog/index.html > /tmp/vlsc-blog-index-user.patch
git stash push -m 'pre-merge connections article blog-index edits' -- portal/blog/index.html
git merge --ff-only feature/connections-recursive-intelligence
git stash pop
```

若冲突，保留已提交的 Intelligence 分类、文章卡片和 JSON-LD 条目，并恢复 stash 的其他全部内容。运行测试，确认 Blog 首页原有修改仍为未提交状态。

- [ ] **步骤 3：清理 worktree 和 feature 分支**

```bash
git worktree remove .worktrees/connections-essay
git worktree prune
git branch -d feature/connections-recursive-intelligence
```

- [ ] **步骤 4：备份线上文章目录和 Blog 首页**

创建 `/var/www/backups/connections_<timestamp>/`，备份：

- `/var/www/vlsc.net/blog/connections-recursive-intelligence/`（若存在）
- `/var/www/vlsc.net/blog/index.html`

- [ ] **步骤 5：上传文章目录**

只打包新文章目录：

```bash
stamp=$(date +%Y%m%d_%H%M%S)
package="/tmp/vlsc_connections_${stamp}.tar.gz"
tar -czf "$package" -C portal/blog connections-recursive-intelligence
scp "$package" cheenle@www.vlsc.net:/tmp/
```

远端解压到 `/var/www/vlsc.net/blog/`，设置 `www-data:www-data` 和文件 `0644`。

- [ ] **步骤 6：对线上 Blog 首页执行精确幂等补丁**

远端 Python 脚本执行三项独立补丁：

1. 若没有 `data-filter="intelligence"`，在 `data-filter="field"` 按钮之后插入 Intelligence 按钮。
2. 若没有文章 URL，在第一个 `<div class="blog-grid">` 之后插入文章卡片。
3. 解析 `application/ld+json` 中 `@type=Blog` 对象；若 `blogPost` 中没有文章 URL，则追加 BlogPosting 对象并重新序列化该 JSON 脚本。

每项补丁都必须检查精确锚点；锚点不存在或不唯一时终止，不得模糊替换。随后运行 `sudo nginx -t` 并重载 nginx。

- [ ] **步骤 7：验证生产内容**

```bash
stamp=$(date +%s)
curl -fsS "https://www.vlsc.net/blog/connections-recursive-intelligence/?verify=$stamp" | rg -q 'Connections Rule'
curl -fsS "https://www.vlsc.net/blog/connections-recursive-intelligence/zh/?verify=$stamp" | rg -q '链接为王'
curl -fsS "https://www.vlsc.net/blog/?verify=$stamp" | rg -q '/blog/connections-recursive-intelligence/'
```

下载英文、中文和 CSS，与本地文件逐一 `cmp -s`，预期 3/3 字节一致。线上检查 DOI、语言切换和 Intelligence 分类。报告备份目录用于回滚。

---

## 最终验收清单

- [ ] 中英文长文结构和证据编号一致。
- [ ] 四类声明标签完整区分事实、推论、类比和作者判断。
- [ ] 果蝇连接组数字、计算模型结论和具身边界准确。
- [ ] NorthPole、Loihi 2、Tianjic 未被混为同一机制。
- [ ] 世界模型和脑机接口没有越过一手证据。
- [ ] 神学/哲学/科学改为并列认知姿态，不构成文化排名。
- [ ] “链接必要但不充分”和治理风险完整呈现。
- [ ] SEO、JSON-LD、canonical、hreflang、SVG 与引用均通过测试。
- [ ] 主工作区原有 Blog 首页修改未丢失或误提交。
- [ ] 生产文章文件一致，Blog 首页入口可访问，远端备份已记录。
