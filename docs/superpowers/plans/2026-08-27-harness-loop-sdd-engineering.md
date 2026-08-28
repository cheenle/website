# Harness、Loop 与 SDD Engineering System 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 在 Portal 新增双语 Engineering System 页面，并在 FDE 页面加入 Harness × Loop × SDD 摘要入口，以证据驱动方式解释五个产品族背后的工程系统。

**架构：** 保持纯静态 HTML/CSS。Engineering 是总框架，双层 Harness、嵌套 Loop 和双向 SDD Living Contract 是三个协同支柱；英文和中文页面使用相同 section ID、机器可读属性和证据口径。使用 Python 标准库静态契约测试约束结构、语义、资源和可访问性。

**技术栈：** HTML5、CSS3、内联 SVG、Python 3 `unittest`/`html.parser`、现有 `octen.css`、`fde.css` 与 `global-nav.js`。

---

## 文件结构

- 创建：`portal/engineering.html` — 英文 Engineering System 完整页面。
- 创建：`portal/zh/engineering.html` — 中文等价页面。
- 创建：`portal/css/engineering.css` — Engineering 页面和 FDE 摘要的专用组件样式。
- 创建：`portal/tests/test_engineering_pages.py` — 双语结构、Harness/Loop/SDD、证据矩阵、资源和无障碍契约。
- 修改：`portal/fde.html` — 增加 `engineering` 摘要章节、锚点和导航链接。
- 修改：`portal/zh/fde.html` — 同步中文摘要。
- 修改：`portal/index.html` — 导航增加 `Engineering`。
- 修改：`portal/zh/index.html` — 导航增加“工程体系”。

不修改 `octen.css`、`global-nav.js` 或产品子站。当前主工作区的 `portal/index.html` 与 `portal/zh/index.html` 存在用户未提交修改；实现必须在隔离 worktree 中提交，合并前单独保存这些文件的补丁，合并后恢复并确认用户修改仍为未提交状态。

---

### 任务 1：建立 Engineering 静态契约测试

**文件：**
- 创建：`portal/tests/test_engineering_pages.py`
- 检查：`portal/fde.html`
- 检查：`portal/zh/fde.html`
- 检查：`portal/index.html`
- 检查：`portal/zh/index.html`

- [ ] **步骤 1：创建失败的契约测试**

创建 `portal/tests/test_engineering_pages.py`：

```python
from __future__ import annotations

import re
import unittest
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

PORTAL = Path(__file__).resolve().parents[1]
PAGES = {
    "en": PORTAL / "engineering.html",
    "zh": PORTAL / "zh" / "engineering.html",
}
FDE_PAGES = {
    "en": PORTAL / "fde.html",
    "zh": PORTAL / "zh" / "fde.html",
}
INDEX_PAGES = {
    "en": PORTAL / "index.html",
    "zh": PORTAL / "zh" / "index.html",
}
REQUIRED_SECTIONS = {
    "overview",
    "harness",
    "loop",
    "sdd",
    "integration",
    "evidence",
    "maturity",
}
REQUIRED_HARNESSES = {"business", "technical", "product"}
REQUIRED_EXECUTION_STAGES = {
    "agents",
    "repository",
    "tools",
    "tests-review",
    "deployment",
    "field-evidence",
}
REQUIRED_STATES = {
    "planned",
    "implemented",
    "tested",
    "bench-verified",
    "field-verified",
    "released",
    "deferred",
    "known-issue",
}
REQUIRED_FAMILIES = {
    "mrrc-universal",
    "mrrc-direct-usb",
    "sunmrrc",
    "mrrc-ft8",
    "efhw",
}


class AuditParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.section_ids: set[str] = set()
        self.refs: list[str] = []
        self.local_scripts: list[str] = []
        self.svg_stack: list[dict[str, bool]] = []
        self.svg_results: list[dict[str, bool]] = []
        self.details_count = 0
        self.summary_count = 0

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
                parsed = urlparse(ref)
                if tag == "script" and not parsed.scheme and not ref.startswith("/"):
                    self.local_scripts.append(parsed.path)
        if tag == "svg":
            self.svg_stack.append({"title": False, "desc": False})
        elif tag in {"title", "desc"} and self.svg_stack:
            self.svg_stack[-1][tag] = True
        elif tag == "details":
            self.details_count += 1
        elif tag == "summary":
            self.summary_count += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "svg" and self.svg_stack:
            self.svg_results.append(self.svg_stack.pop())


def load_page(path: Path) -> tuple[str, AuditParser]:
    if not path.exists():
        raise unittest.SkipTest(f"not created yet: {path}")
    source = path.read_text(encoding="utf-8")
    parser = AuditParser()
    parser.feed(source)
    return source, parser


class EngineeringPageTests(unittest.TestCase):
    def test_engineering_pages_exist(self) -> None:
        for language, path in PAGES.items():
            self.assertTrue(path.exists(), language)

    def test_required_sections_and_language_parity(self) -> None:
        parsed = {language: load_page(path)[1] for language, path in PAGES.items()}
        for language, parser in parsed.items():
            self.assertTrue(REQUIRED_SECTIONS <= parser.section_ids, language)
        self.assertEqual(parsed["en"].section_ids, parsed["zh"].section_ids)

    def test_dual_layer_harness_is_explicit(self) -> None:
        for language, path in PAGES.items():
            source, _ = load_page(path)
            harnesses = set(re.findall(r'data-harness="([^"]+)"', source))
            stages = set(re.findall(r'data-execution-stage="([^"]+)"', source))
            self.assertEqual(REQUIRED_HARNESSES, harnesses, language)
            self.assertEqual(REQUIRED_EXECUTION_STAGES, stages, language)

    def test_nested_loops_are_explicit(self) -> None:
        for language, path in PAGES.items():
            source, _ = load_page(path)
            self.assertIn('data-loop="fde"', source, language)
            self.assertIn('data-loop="engineering"', source, language)
            for token in ("Echo", "Delta", "Product", "Specify", "Implement", "Test", "Review", "Update SDD"):
                self.assertIn(token, source, f"{language}: {token}")

    def test_sdd_lifecycle_states_are_complete(self) -> None:
        for language, path in PAGES.items():
            source, _ = load_page(path)
            states = set(re.findall(r'data-sdd-state="([^"]+)"', source))
            self.assertEqual(REQUIRED_STATES, states, language)

    def test_five_family_evidence_matrix_is_complete(self) -> None:
        for language, path in PAGES.items():
            source, _ = load_page(path)
            families = set(re.findall(r'data-engineering-family="([^"]+)"', source))
            self.assertEqual(REQUIRED_FAMILIES, families, language)

    def test_fde_summary_precedes_ontology_and_links_to_engineering(self) -> None:
        expected_links = {"en": "engineering.html", "zh": "engineering.html"}
        for language, path in FDE_PAGES.items():
            source, parser = load_page(path)
            self.assertIn("engineering", parser.section_ids, language)
            self.assertLess(source.index('id="leverage"'), source.index('id="engineering"'))
            self.assertLess(source.index('id="engineering"'), source.index('id="ontology"'))
            self.assertIn(f'href="{expected_links[language]}"', source, language)

    def test_portal_navigation_links_to_engineering(self) -> None:
        expected_links = {"en": "engineering.html", "zh": "engineering.html"}
        for language, path in INDEX_PAGES.items():
            source, _ = load_page(path)
            self.assertIn(f'href="{expected_links[language]}"', source, language)

    def test_ids_svg_details_and_scripts_are_accessible(self) -> None:
        for language, path in PAGES.items():
            _, parser = load_page(path)
            duplicates = [item for item, count in Counter(parser.ids).items() if count > 1]
            self.assertEqual([], duplicates, language)
            self.assertTrue(parser.svg_results, language)
            self.assertTrue(all(item["title"] and item["desc"] for item in parser.svg_results), language)
            self.assertGreater(parser.details_count, 0, language)
            self.assertEqual(parser.details_count, parser.summary_count, language)
            expected_script = "js/global-nav.js" if language == "en" else "../js/global-nav.js"
            self.assertEqual([expected_script], parser.local_scripts, language)

    def test_relative_assets_exist(self) -> None:
        for group_name, pages in (("engineering", PAGES), ("fde", FDE_PAGES)):
            for language, path in pages.items():
                _, parser = load_page(path)
                for ref in parser.refs:
                    parsed = urlparse(ref)
                    if parsed.scheme or ref.startswith(("/", "#", "data:", "mailto:")):
                        continue
                    target = (path.parent / parsed.path).resolve()
                    self.assertTrue(
                        target.exists(), f"{group_name}/{language}: missing {ref}"
                    )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **步骤 2：运行测试并确认旧站点失败**

运行：

```bash
python3 portal/tests/test_engineering_pages.py -v
```

预期：`test_engineering_pages_exist`、FDE 摘要和 Portal 导航测试失败；依赖尚未创建页面的测试显示 skipped。失败原因必须是 Engineering 页面和入口不存在，而不是测试语法错误。

- [ ] **步骤 3：提交测试契约**

```bash
git add portal/tests/test_engineering_pages.py
git commit -m "test: define Engineering System page contract"
```

---

### 任务 2：建立 Engineering 视觉组件

**文件：**
- 创建：`portal/css/engineering.css`

- [ ] **步骤 1：创建专用样式文件**

创建 `portal/css/engineering.css`，至少包含以下组件和响应式行为：

```css
:root {
  --eng-business: #f59e0b;
  --eng-technical: #22d3ee;
  --eng-product: #a78bfa;
  --eng-evidence: #22c55e;
  --eng-risk: #f87171;
}

.eng-hero { position: relative; overflow: hidden; padding: 10rem 2rem 5rem; text-align: center; }
.eng-hero-inner { position: relative; z-index: 1; max-width: 980px; margin: 0 auto; }
.eng-hero h1 { margin: 1rem 0; font-size: clamp(2.5rem, 7vw, 5rem); line-height: 1.02; letter-spacing: -.05em; }
.eng-section { padding: 6rem 2rem; }
.eng-section:nth-of-type(even) { background: var(--bg-secondary); }
.eng-section-header { max-width: 800px; margin: 0 auto 3rem; text-align: center; }
.eng-anchor-shell { position: sticky; top: var(--global-nav-height, 44px); z-index: 20; border-block: 1px solid var(--border); background: rgba(5,8,13,.94); backdrop-filter: blur(16px); }
.eng-anchor-nav { display: flex; gap: .5rem; overflow-x: auto; padding: .8rem 0; }
.eng-anchor-nav a { flex: 0 0 auto; white-space: nowrap; }
.eng-grid-3, .eng-harness-grid, .eng-execution-grid, .eng-state-grid, .eng-maturity-grid { display: grid; gap: 1.25rem; }
.eng-grid-3, .eng-harness-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.eng-execution-grid { grid-template-columns: repeat(6, minmax(0, 1fr)); }
.eng-state-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.eng-maturity-grid { grid-template-columns: repeat(5, minmax(0, 1fr)); }
.eng-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 1rem; padding: 1.5rem; }
.eng-card[data-harness="business"] { border-top: 3px solid var(--eng-business); }
.eng-card[data-harness="technical"] { border-top: 3px solid var(--eng-technical); }
.eng-card[data-harness="product"] { border-top: 3px solid var(--eng-product); }
.eng-step { position: relative; border: 1px solid var(--border); border-radius: .8rem; padding: 1rem; text-align: center; }
.eng-loop { display: flex; flex-wrap: wrap; align-items: center; justify-content: center; gap: .65rem; }
.eng-loop-arrow { color: var(--accent); font-family: var(--font-mono); }
.eng-state { border: 1px solid var(--border); border-radius: .75rem; padding: .85rem; }
.eng-state[data-sdd-state="field-verified"], .eng-state[data-sdd-state="released"] { border-color: var(--eng-evidence); }
.eng-state[data-sdd-state="deferred"], .eng-state[data-sdd-state="known-issue"] { border-color: var(--eng-risk); }
.eng-system-svg { display: block; width: 100%; height: auto; }
.eng-table-wrap { overflow-x: auto; border: 1px solid var(--border); border-radius: .85rem; }
.eng-table { min-width: 980px; width: 100%; border-collapse: collapse; }
.eng-table th, .eng-table td { border-bottom: 1px solid var(--border); padding: .85rem 1rem; text-align: left; vertical-align: top; }
.eng-details { margin-bottom: .75rem; border: 1px solid var(--border); border-radius: .75rem; background: var(--bg-card); }
.eng-details summary { cursor: pointer; padding: 1rem 1.25rem; font-weight: 600; }
.eng-details-body { padding: 1.25rem; }
.fde-engineering-summary { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1.25rem; }

@media (max-width: 1100px) {
  .eng-execution-grid, .eng-maturity-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}

@media (max-width: 900px) {
  .eng-grid-3, .eng-harness-grid, .eng-execution-grid, .eng-state-grid, .eng-maturity-grid, .fde-engineering-summary { grid-template-columns: 1fr; }
  .eng-hero { padding: 8rem 1.25rem 4rem; }
  .eng-section { padding: 4rem 1.25rem; }
  .eng-loop-arrow { transform: rotate(90deg); }
}

@media (prefers-reduced-motion: reduce) {
  .eng-card, .eng-step { transition: none; }
}
```

可增加只服务于三角协同图、证据模板和反模式卡片的选择器；不得复制全局 navbar/footer 规则。

- [ ] **步骤 2：运行 CSS 诊断**

运行工具：

```text
lsp_diagnostics(path="portal/css/engineering.css", severity="all")
```

预期：无错误。

- [ ] **步骤 3：提交样式基础**

```bash
git add portal/css/engineering.css
git commit -m "style: add Engineering System components"
```

---
### 任务 3：实现英文 Engineering System 页面

**文件：**
- 创建：`portal/engineering.html`
- 参考：`docs/superpowers/specs/2026-08-27-harness-loop-sdd-engineering-design.md`

- [ ] **步骤 1：建立页面骨架、元数据与导航**

使用：

```html
<title>Engineering System — Harness, Loops & Living SDD | VLSC</title>
<meta name="description" content="How VLSC combines engineering harnesses, nested feedback loops, and living software design documents to build evidence-backed remote-radio products.">
<link rel="stylesheet" href="css/octen.css?v=6">
<link rel="stylesheet" href="css/sunsdrmobile.css?v=1">
<link rel="stylesheet" href="css/fde.css?v=1">
<link rel="stylesheet" href="css/engineering.css?v=1">
```

Navbar 必须包含 Home、Projects、Blog、FDE、Engineering、GitHub 和中文切换。Hero 使用：

```html
<header class="eng-hero">
  <div class="eng-hero-inner">
    <div class="hero-badge">Engineering System · From Intent to Field Evidence</div>
    <h1>Harness. Loop. SDD.<br><span class="gradient">Engineering That Learns.</span></h1>
    <p>...</p>
  </div>
</header>
```

增加页内锚点导航，链接固定章节 `overview`、`harness`、`loop`、`sdd`、`integration`、`evidence`、`maturity`。

- [ ] **步骤 2：实现 Engineering 总览**

创建：

```html
<section class="eng-section" id="overview">...</section>
```

内容必须明确：Engineering 是持续产生可信产品的系统；Harness、Loop、SDD 是三根支柱，不是产品。使用三个卡片和一个带可访问标题/描述的 SVG：

```html
<svg class="eng-system-svg" role="img" aria-labelledby="eng-overview-title eng-overview-desc">
  <title id="eng-overview-title">Engineering System from field problem to evidence-backed product</title>
  <desc id="eng-overview-desc">Harness, Loop, and SDD transform field problems into code, tests, evidence, products, and reusable assets.</desc>
  ...
</svg>
```

- [ ] **步骤 3：实现双层 Harness**

创建：

```html
<section class="eng-section" id="harness">...</section>
```

外层必须正好包含：

```html
<article class="eng-card" data-harness="business">...</article>
<article class="eng-card" data-harness="technical">...</article>
<article class="eng-card" data-harness="product">...</article>
```

内层执行链必须正好包含：

```html
<div class="eng-step" data-execution-stage="agents">Human + AI Agents</div>
<div class="eng-step" data-execution-stage="repository">Repository + SDD</div>
<div class="eng-step" data-execution-stage="tools">Tools + Diagnostics</div>
<div class="eng-step" data-execution-stage="tests-review">Tests + Review</div>
<div class="eng-step" data-execution-stage="deployment">Deployment</div>
<div class="eng-step" data-execution-stage="field-evidence">Field Telemetry + Evidence</div>
```

正文必须包含五条边界：失败可见、工具输出可追溯、测试不替代台架/现场验证、部署与遥测属于 Engineering、AI 不越过审查与安全验收。

- [ ] **步骤 4：实现嵌套 Loop**

创建：

```html
<section class="eng-section" id="loop">...</section>
```

外层：

```html
<div class="eng-loop" data-loop="fde">
  <span>Echo</span><span>→</span><span>Delta</span><span>→</span><span>Product</span><span>→ Field Echo</span>
</div>
```

内层：

```html
<div class="eng-loop" data-loop="engineering">
  <span>Specify</span><span>→</span><span>Implement</span><span>→</span>
  <span>Test</span><span>→</span><span>Review</span><span>→</span>
  <span>Deploy / Observe</span><span>→</span><span>Update SDD</span>
</div>
```

逐项解释每个步骤，并明确外层降低产品风险、内层确保增量可靠；模型不是瀑布。

- [ ] **步骤 5：实现 SDD Living Contract**

创建：

```html
<section class="eng-section" id="sdd">...</section>
```

展示 Intent/Constraints/Decisions 与 Code/Tests/Deployment/Field Evidence 双向更新。使用下列唯一机器状态：

```html
<div class="eng-state" data-sdd-state="planned">...</div>
<div class="eng-state" data-sdd-state="implemented">...</div>
<div class="eng-state" data-sdd-state="tested">...</div>
<div class="eng-state" data-sdd-state="bench-verified">...</div>
<div class="eng-state" data-sdd-state="field-verified">...</div>
<div class="eng-state" data-sdd-state="released">...</div>
<div class="eng-state" data-sdd-state="deferred">...</div>
<div class="eng-state" data-sdd-state="known-issue">...</div>
```

正文说明状态不是自动升级链，并列出最小证据字段：Claim、Source artifact、Version/commit、Environment、Verification method、Result、Limitations、Date。

- [ ] **步骤 6：实现协同模型、证据矩阵与成熟度**

创建：

```html
<section class="eng-section" id="integration">...</section>
<section class="eng-section" id="evidence">...</section>
<section class="eng-section" id="maturity">...</section>
```

`integration` 使用可访问 SVG 展示 Harness、Loop、SDD 三角协同，并列出五种缺失一环的失败模式。

`evidence` 使用表格，五行分别带：

```text
data-engineering-family="mrrc-universal"
data-engineering-family="mrrc-direct-usb"
data-engineering-family="sunmrrc"
data-engineering-family="mrrc-ft8"
data-engineering-family="efhw"
```

事实口径必须与规格第 9 节一致，特别保留 439/633 测试与实机验收分离、服务端/客户端证据分离、MRRC-FT8 发布与 SDD V1.8 分离、EFHW 不越级为现场验证。

`maturity` 展示 Ad hoc、Repeatable、Traceable、Evidence-driven、Reusable 五级模型，并说明不是产品排名。列出文档替代验证、测试数量替代证据、AI 生成替代审查、发布替代现场安全、SDD 不回写和设计目标冒充实现事实等反模式。

- [ ] **步骤 7：实现附录、CTA、页脚与脚本**

使用原生 `<details class="eng-details">`，至少包含：SDD 章节映射、最小证据记录模板、Engineering review checklist。页面末尾链接到 FDE 和五个产品族。只加载已有脚本：

```html
<script src="js/global-nav.js?v=6" defer data-gn="1"></script>
```

- [ ] **步骤 8：运行英文结构检查**

运行：

```bash
python3 - <<'PY'
import re
from pathlib import Path
source = Path('portal/engineering.html').read_text()
assert all(f'id="{section}"' in source for section in ('overview','harness','loop','sdd','integration','evidence','maturity'))
assert set(re.findall(r'data-harness="([^"]+)"', source)) == {'business','technical','product'}
assert set(re.findall(r'data-sdd-state="([^"]+)"', source)) == {'planned','implemented','tested','bench-verified','field-verified','released','deferred','known-issue'}
assert source.count('data-engineering-family=') == 5
print('English Engineering structure: PASS')
PY
```

预期：PASS。

- [ ] **步骤 9：提交英文页面**

```bash
git add portal/engineering.html
git commit -m "feat: add English Engineering System page"
```

---

### 任务 4：实现中文 Engineering System 页面

**文件：**
- 创建：`portal/zh/engineering.html`
- 对照：`portal/engineering.html`

- [ ] **步骤 1：逐节建立中文同构页面**

使用与英文完全相同的 section ID、`data-harness`、`data-execution-stage`、`data-loop`、`data-sdd-state` 和 `data-engineering-family` 值。

标题使用：

```html
<title>工程体系 — Harness、Loop 与 Living SDD | VLSC</title>
<header class="eng-hero">
  <div class="eng-hero-inner">
    <div class="hero-badge">Engineering System · 从工程意图到现场证据</div>
    <h1>Harness、Loop、SDD<br><span class="gradient">持续学习的工程体系</span></h1>
  </div>
</header>
```

样式路径使用 `../css/`，语言切换链接 `../engineering.html`，脚本使用：

```html
<script src="../js/global-nav.js?v=6" defer data-gn="1"></script>
```

- [ ] **步骤 2：统一关键术语**

首次出现保留英文：

```text
Engineering System = 工程体系
Harness = 工程护栏与执行环境
Business Harness = 业务 Harness
Technical Harness = 技术 Harness
Product Harness = 产品 Harness
Engineering Loop = 工程闭环
Living Contract = 活的双向契约
Field Evidence = 现场证据
Evidence-driven = 证据驱动
Known issue = 已知问题
```

机器状态值保持英文，显示文本翻译为中文。

- [ ] **步骤 3：同步全部事实与反模式**

中文五产品族矩阵必须与英文逐行同构。439、633、SDD V1.8、FT710Mobile P0 PTT 和 EFHW PCB/台架状态不得弱化或省略。成熟度不得译成产品等级或排名。

- [ ] **步骤 4：运行页面级契约测试**

运行：

```bash
python3 portal/tests/test_engineering_pages.py \
  EngineeringPageTests.test_engineering_pages_exist \
  EngineeringPageTests.test_required_sections_and_language_parity \
  EngineeringPageTests.test_dual_layer_harness_is_explicit \
  EngineeringPageTests.test_nested_loops_are_explicit \
  EngineeringPageTests.test_sdd_lifecycle_states_are_complete \
  EngineeringPageTests.test_five_family_evidence_matrix_is_complete \
  EngineeringPageTests.test_ids_svg_details_and_scripts_are_accessible -v
```

预期：上述测试全部 PASS；FDE 摘要和 Portal 导航测试尚未运行。

- [ ] **步骤 5：提交中文页面**

```bash
git add portal/zh/engineering.html
git commit -m "feat: add Chinese Engineering System page"
```

---
### 任务 5：接入 FDE 摘要和 Portal 导航

**文件：**
- 修改：`portal/fde.html`
- 修改：`portal/zh/fde.html`
- 修改：`portal/index.html`
- 修改：`portal/zh/index.html`

- [ ] **步骤 1：在 FDE 页面加载 Engineering 样式并增加锚点**

英文 `<head>` 在 `fde.css` 后加入：

```html
<link rel="stylesheet" href="css/engineering.css?v=1">
```

中文使用：

```html
<link rel="stylesheet" href="../css/engineering.css?v=1">
```

英文页内导航在 Leverage 与 Ontology 之间加入：

```html
<a href="#engineering">Engineering</a>
```

中文加入：

```html
<a href="#engineering">工程体系</a>
```

- [ ] **步骤 2：在英文 FDE 页面加入摘要章节**

必须位于 `id="leverage"` 章节之后、`id="ontology"` 之前：

```html
<section class="fde-section" id="engineering">
  <div class="container">
    <header class="fde-section-header">
      <span class="fde-section-label">05 · Engineering System</span>
      <h2 class="fde-section-title">Harness × Loop × Living SDD</h2>
      <p class="fde-section-subtitle">Engineering is the system that turns field intent into repeatable execution, reviewed increments, traceable evidence, and reusable assets.</p>
    </header>
    <div class="fde-engineering-summary">
      <article class="fde-card"><h3>Harness</h3><p>Business, technical, and product constraints surround an execution environment of agents, tools, tests, deployment, and field telemetry.</p></article>
      <article class="fde-card"><h3>Loop</h3><p>Echo → Delta → Product contains an inner Specify → Implement → Test → Review → Observe → Update SDD loop.</p></article>
      <article class="fde-card"><h3>Living SDD</h3><p>Design intent flows toward implementation; code, tests, deployment, and field evidence flow back to correct the contract.</p></article>
    </div>
    <div style="text-align:center; margin-top:2rem;">
      <a class="btn btn-primary" href="engineering.html">Explore the Engineering System</a>
    </div>
  </div>
</section>
```

后续章节显示编号顺延，但机器 ID 保持 `ontology`、`capabilities`、`evidence` 不变。

- [ ] **步骤 3：加入中文等价摘要**

使用相同 `id="engineering"` 和同构三卡结构，CTA 使用：

```html
<a class="btn btn-primary" href="engineering.html">查看完整工程体系</a>
```

中文必须表达：Harness 是约束与执行环境；外层 FDE Loop 包含内层工程闭环；SDD 是设计意图和实现证据双向校准的活契约。

- [ ] **步骤 4：增加 Portal 首页导航**

英文 `portal/index.html` 的主导航在 FDE 后加入：

```html
<li><a href="engineering.html">Engineering</a></li>
```

中文 `portal/zh/index.html` 在 FDE 后加入：

```html
<li><a href="engineering.html">工程体系</a></li>
```

不得修改首页其他卡片、内容、样式或版本参数。

- [ ] **步骤 5：运行完整 Engineering 契约测试**

运行：

```bash
python3 portal/tests/test_engineering_pages.py -v
python3 portal/tests/test_fde_pages.py -v
```

预期：两个测试文件全部 PASS。

- [ ] **步骤 6：提交集成改动**

```bash
git add portal/fde.html portal/zh/fde.html portal/index.html portal/zh/index.html
git commit -m "feat: connect FDE to Engineering System"
```

---

### 任务 6：内容、可访问性和本地站点验收

**文件：**
- 修改（仅发现问题时）：`portal/engineering.html`
- 修改（仅发现问题时）：`portal/zh/engineering.html`
- 修改（仅发现问题时）：`portal/css/engineering.css`
- 修改（仅发现问题时）：`portal/fde.html`
- 修改（仅发现问题时）：`portal/zh/fde.html`
- 修改（仅测试缺陷时）：`portal/tests/test_engineering_pages.py`

- [ ] **步骤 1：运行 LSP 和综合诊断**

运行工具：

```text
lsp_diagnostics(paths=[
  "portal/engineering.html",
  "portal/zh/engineering.html",
  "portal/css/engineering.css",
  "portal/fde.html",
  "portal/zh/fde.html",
  "portal/tests/test_engineering_pages.py"
], severity="all", serverScope="all")

lens_diagnostics(mode="full", paths=[
  "portal/engineering.html",
  "portal/zh/engineering.html",
  "portal/css/engineering.css",
  "portal/fde.html",
  "portal/zh/fde.html",
  "portal/tests/test_engineering_pages.py"
], severity="all", refreshRunners="cheap")
```

预期：无本次变更引入的 blocking error 或未处理 warning。

- [ ] **步骤 2：运行事实与反模式扫描**

运行：

```bash
rg -n '439|633|SDD V1.8|P0 PTT|PCB' portal/engineering.html portal/zh/engineering.html
rg -n 'Business Harness|Technical Harness|Product Harness|Specify|Implement|Update SDD' portal/engineering.html portal/zh/engineering.html
rg -n 'planned|implemented|tested|bench-verified|field-verified|released|deferred|known-issue' portal/engineering.html portal/zh/engineering.html
```

预期：两种语言均包含事实口径、双层 Harness、内层 Loop 与完整机器状态。

- [ ] **步骤 3：运行完整测试和差异检查**

运行：

```bash
python3 portal/tests/test_engineering_pages.py -v
python3 portal/tests/test_fde_pages.py -v
git diff --check 5f6f13f..HEAD
git diff --name-only 5f6f13f..HEAD | grep -v '^docs/superpowers/plans/2026-08-27-harness-loop-sdd-engineering.md$'
```

预期：全部测试 PASS；空白检查无输出；排除计划文档后，实现差异只包含规格所列的八个页面/样式/测试文件。

- [ ] **步骤 4：运行本地 HTTP smoke test**

运行：

```bash
python3 -m http.server 8765 --directory portal >/tmp/vlsc-engineering-http.log 2>&1 &
server_pid=$!
trap 'kill "$server_pid" 2>/dev/null || true' EXIT
sleep 1
curl -fsS http://127.0.0.1:8765/engineering.html >/dev/null
curl -fsS http://127.0.0.1:8765/zh/engineering.html >/dev/null
curl -fsS http://127.0.0.1:8765/css/engineering.css >/dev/null
curl -fsS http://127.0.0.1:8765/fde.html >/dev/null
curl -fsS http://127.0.0.1:8765/zh/fde.html >/dev/null
kill "$server_pid"
trap - EXIT
```

预期：五个请求均返回 0。

- [ ] **步骤 5：检查桌面与移动结构**

在桌面和约 390px 宽度检查：

- sticky 导航不遮挡 Hero。
- 三层 Harness 卡片和执行链在移动端单列。
- 两层 Loop 的箭头和文字无需颜色也能理解。
- SDD 八状态无截断，状态差异有文字标签。
- 三角协同 SVG 无溢出且包含可访问说明。
- 五产品族矩阵可横向滚动。
- `<details>` 可由键盘操作。
- 中英文切换和 FDE/Engineering 相互链接正确。

- [ ] **步骤 6：提交验收修正**

若步骤 1–5 产生修正：

```bash
git add portal/engineering.html portal/zh/engineering.html portal/css/engineering.css portal/fde.html portal/zh/fde.html portal/tests/test_engineering_pages.py
git commit -m "fix: verify Engineering System content and accessibility"
```

若无修正，不创建空提交。

---

### 任务 7：合并、保护用户修改并选择性发布

**文件：**
- 合并：本计划涉及的八个实现文件。
- 发布：五个 Engineering/FDE HTML/CSS 文件，并对线上两个首页执行幂等导航补丁；不发布测试或本地首页的其他未提交内容。

- [ ] **步骤 1：运行发布前最终验证**

```bash
python3 portal/tests/test_engineering_pages.py -v
python3 portal/tests/test_fde_pages.py -v
git diff --check 5f6f13f..HEAD
git status --short
```

预期：测试全部 PASS，差异检查无输出，feature worktree 无未提交实现文件。

- [ ] **步骤 2：保护主工作区目标文件的用户修改**

在主仓库根目录运行：

```bash
git diff -- portal/index.html portal/zh/index.html > /tmp/vlsc-engineering-index-user.patch
git stash push -m 'pre-merge Engineering target-file edits' -- portal/index.html portal/zh/index.html
```

预期：其他未提交 EFHW、Portal、图片和链接修改仍留在主工作区；stash 只包含两个首页文件。

- [ ] **步骤 3：快进合并 feature 分支**

```bash
git merge --ff-only feature/engineering-system
python3 portal/tests/test_engineering_pages.py -v
python3 portal/tests/test_fde_pages.py -v
```

预期：快进成功且合并后的 main 测试全部 PASS。

- [ ] **步骤 4：恢复首页用户修改并确认无丢失**

```bash
git stash pop
```

若导航附近冲突，保留 feature 分支新增的 Engineering 导航，同时恢复 stash 中所有其他用户内容。随后运行：

```bash
git diff -- portal/index.html portal/zh/index.html
git status --short
```

预期：首页原有用户修改仍为未提交状态；Engineering 导航来自已提交 feature，不应在 diff 中重复出现。将 `/tmp/vlsc-engineering-index-user.patch` 与当前 diff 对比，确认没有丢失非导航改动。

- [ ] **步骤 5：清理 feature worktree**

从主仓库根目录运行：

```bash
git worktree remove .worktrees/engineering-system
git worktree prune
git branch -d feature/engineering-system
```

- [ ] **步骤 6：创建选择性部署包和远端备份**

本地首页包含与本任务无关的用户修改，因此不得打包 `index.html`。只打包五个新建或完整重构的 Engineering/FDE 资源：

```bash
stamp=$(date +%Y%m%d_%H%M%S)
package="/tmp/vlsc_engineering_${stamp}.tar.gz"
backup="/var/www/backups/engineering_${stamp}"
tar -czf "$package" -C portal \
  engineering.html zh/engineering.html css/engineering.css \
  fde.html zh/fde.html
```

远端逐文件备份上述五个文件以及当前 `index.html`、`zh/index.html` 到 `$backup`；不存在的新文件允许跳过。

- [ ] **步骤 7：上传资源并对线上首页执行幂等导航补丁**

上传并解压五个打包文件。随后用远端 Python 对当前线上首页做精确、幂等插入，而不是覆盖整个首页：

```python
from pathlib import Path

updates = {
    Path("/var/www/vlsc.net/index.html"): (
        '<li><a href="fde.html">FDE</a></li>',
        '<li><a href="fde.html">FDE</a></li>\n                <li><a href="engineering.html">Engineering</a></li>',
        'href="engineering.html">Engineering</a>',
    ),
    Path("/var/www/vlsc.net/zh/index.html"): (
        '<li><a href="fde.html">FDE</a></li>',
        '<li><a href="fde.html">FDE</a></li>\n                <li><a href="engineering.html">工程体系</a></li>',
        'href="engineering.html">工程体系</a>',
    ),
}
for path, (anchor, replacement, sentinel) in updates.items():
    source = path.read_text()
    if sentinel not in source:
        if source.count(anchor) != 1:
            raise RuntimeError(f"expected one navigation anchor in {path}")
        path.write_text(source.replace(anchor, replacement, 1))
```

设置七个受影响文件的所有权和 `0644` 权限，运行 `sudo nginx -t`，成功后 `sudo systemctl reload nginx`。任何精确锚点不匹配都必须终止发布，不得模糊替换。

- [ ] **步骤 8：验证生产页面和关键内容**

```bash
stamp=$(date +%s)
curl -fsS "https://www.vlsc.net/engineering.html?verify=$stamp" | rg -q 'Harness. Loop. SDD.'
curl -fsS "https://www.vlsc.net/zh/engineering.html?verify=$stamp" | rg -q 'Harness、Loop、SDD'
curl -fsS "https://www.vlsc.net/fde.html?verify=$stamp" | rg -q 'Engineering System'
curl -fsS "https://www.vlsc.net/zh/fde.html?verify=$stamp" | rg -q '工程体系'
curl -fsS "https://www.vlsc.net/index.html?verify=$stamp" | rg -q 'href="engineering.html">Engineering</a>'
curl -fsS "https://www.vlsc.net/zh/index.html?verify=$stamp" | rg -q 'href="engineering.html">工程体系</a>'
```

下载五个打包生产文件，与本地文件逐一 `cmp -s`。预期：5/5 字节一致；两个首页分别通过导航哨兵检查且其他线上内容未被本地文件覆盖。报告远端备份目录以便回滚。

---

## 最终验收清单

- [ ] Engineering 是总框架，Harness、Loop、SDD 是三根支柱。
- [ ] 外层 Business/Technical/Product 与内层执行 Harness 都完整出现。
- [ ] 外层 FDE Loop 和内层 Engineering Loop 明确嵌套。
- [ ] SDD 是双向 Living Contract，八状态完整且不构成自动升级链。
- [ ] 五产品族矩阵口径与 FDE 页面一致。
- [ ] FDE 摘要位于 leverage 和 ontology 之间。
- [ ] EN/ZH 页面结构、机器属性和事实一致。
- [ ] 无新增运行时 JavaScript、框架或构建步骤。
- [ ] 主工作区原有未提交修改未被误提交或丢失。
- [ ] 自动化测试、诊断、本地 HTTP 和生产验证均通过。
