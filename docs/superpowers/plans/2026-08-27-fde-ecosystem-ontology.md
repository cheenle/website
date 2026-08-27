# FDE 生态与领域本体页面实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 将现有三项目 FDE 页面升级为中英文一致的“三条工程轨道、五个产品族（five product families）”案例页，并加入证据驱动的轻量远程业余无线电领域本体。

**架构：** 保留 Portal 的纯静态 HTML/CSS 架构；新增一个 FDE 专用样式文件，完整重构英文和中文 FDE 页面。FDE 交付循环与本体工程循环并列呈现；产品族、客户端、协议绑定和证据成熟度严格分层。使用原生 `<details>` 实现可访问的附录，不增加 JavaScript 或构建依赖。

**技术栈：** HTML5、CSS3、内联 SVG、Python 3 标准库 `unittest`/`html.parser`、现有 `octen.css` 与 `global-nav.js`。

---

## 文件结构

- 创建：`portal/css/fde.css` — FDE 页面专用布局、图表、产品族卡片、本体卡片、证据徽章、响应式规则。
- 创建：`portal/tests/test_fde_pages.py` — 中英文结构一致性、产品归属、旧口径清理、可访问性和本地资源检查。
- 修改：`portal/fde.html` — 英文 FDE 页面完整内容。
- 修改：`portal/zh/fde.html` — 中文 FDE 页面，与英文保持相同信息架构和事实口径。

不修改 `portal/css/octen.css`、`portal/js/global-nav.js` 或各产品子站。当前工作区已在 FDE 页面上包含 `octen.css?v=6` 与 `global-nav.js?v=6` 的未提交调整，实施时必须保留这两处版本值。

---

### 任务 1：建立静态页面契约测试

**文件：**
- 创建：`portal/tests/test_fde_pages.py`
- 检查：`portal/fde.html`
- 检查：`portal/zh/fde.html`

- [ ] **步骤 1：记录当前未提交差异，确认只保留现有缓存版本修改**

运行：

```bash
git diff -- portal/fde.html portal/zh/fde.html
```

预期：两个页面当前只包含 `octen.css?v=6` 和 `global-nav.js?v=6` 的修改。若出现其他用户修改，先记录并在后续重写中逐项保留，不得直接覆盖。

- [ ] **步骤 2：创建失败的页面契约测试**

创建 `portal/tests/test_fde_pages.py`：

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
    "en": PORTAL / "fde.html",
    "zh": PORTAL / "zh" / "fde.html",
}
REQUIRED_SECTIONS = {
    "method",
    "tracks",
    "families",
    "leverage",
    "ontology",
    "capabilities",
    "evidence",
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
        self.local_refs: list[str] = []
        self.svg_stack: list[dict[str, bool]] = []
        self.svg_results: list[dict[str, bool]] = []
        self.details_count = 0
        self.summary_count = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.append(values["id"])
        if tag == "section" and values.get("id"):
            self.section_ids.add(values["id"])
        if tag in {"a", "link", "script", "img"}:
            ref = values.get("href") or values.get("src")
            if ref:
                self.local_refs.append(ref)
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
    source = path.read_text(encoding="utf-8")
    parser = AuditParser()
    parser.feed(source)
    return source, parser


class FdePageTests(unittest.TestCase):
    def test_required_sections_and_families_exist_in_both_languages(self) -> None:
        for language, path in PAGES.items():
            source, parser = load_page(path)
            self.assertTrue(REQUIRED_SECTIONS <= parser.section_ids, language)
            families = set(re.findall(r'data-family="([^"]+)"', source))
            self.assertEqual(REQUIRED_FAMILIES, families, language)

    def test_product_family_nesting_is_explicit(self) -> None:
        for language, path in PAGES.items():
            source, _ = load_page(path)
            sun = re.search(
                r'data-family="sunmrrc"[\s\S]*?data-family-end="sunmrrc"', source
            )
            direct = re.search(
                r'data-family="mrrc-direct-usb"[\s\S]*?data-family-end="mrrc-direct-usb"',
                source,
            )
            self.assertIsNotNone(sun, language)
            self.assertIsNotNone(direct, language)
            self.assertIn('data-client="sunsdrmobile"', sun.group(0))
            self.assertIn('data-client="ios"', direct.group(0))
            self.assertIn('data-client="android"', direct.group(0))

    def test_obsolete_top_level_counts_are_removed(self) -> None:
        forbidden = (
            "FDE Across Three Projects",
            "One Methodology<br><span class=\"gradient\">Three Products",
            "跨三项目的 FDE 实战",
            "一套方法论<br><span class=\"gradient\">三款产品",
        )
        for language, path in PAGES.items():
            source, _ = load_page(path)
            for phrase in forbidden:
                self.assertNotIn(phrase, source, f"{language}: {phrase}")

    def test_ontology_and_evidence_vocabulary_is_present(self) -> None:
        required_tokens = {
            "en": ("Domain Ontology", "CommandIntent", "Actuation", "Observation", "Field verified"),
            "zh": ("领域本体", "控制意图", "执行活动", "观测", "现场验证"),
        }
        for language, path in PAGES.items():
            source, _ = load_page(path)
            for token in required_tokens[language]:
                self.assertIn(token, source, f"{language}: {token}")

    def test_ids_are_unique_and_section_parity_is_preserved(self) -> None:
        parsed = {language: load_page(path)[1] for language, path in PAGES.items()}
        for language, parser in parsed.items():
            duplicates = [item for item, count in Counter(parser.ids).items() if count > 1]
            self.assertEqual([], duplicates, language)
        self.assertEqual(parsed["en"].section_ids, parsed["zh"].section_ids)

    def test_svg_and_details_are_accessible(self) -> None:
        for language, path in PAGES.items():
            _, parser = load_page(path)
            self.assertTrue(parser.svg_results, language)
            self.assertTrue(all(item["title"] and item["desc"] for item in parser.svg_results), language)
            self.assertGreater(parser.details_count, 0, language)
            self.assertEqual(parser.details_count, parser.summary_count, language)

    def test_relative_assets_exist(self) -> None:
        for language, path in PAGES.items():
            _, parser = load_page(path)
            for ref in parser.local_refs:
                parsed = urlparse(ref)
                if parsed.scheme or ref.startswith(("/", "#", "data:", "mailto:")):
                    continue
                target = (path.parent / parsed.path).resolve()
                self.assertTrue(target.exists(), f"{language}: missing {ref}")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **步骤 3：运行测试并确认针对旧页面失败**

运行：

```bash
python3 portal/tests/test_fde_pages.py -v
```

预期：至少 `test_required_sections_and_families_exist_in_both_languages`、`test_obsolete_top_level_counts_are_removed`、`test_ontology_and_evidence_vocabulary_is_present` 失败；失败原因是旧页面仍采用三项目口径。

- [ ] **步骤 4：提交测试契约**

```bash
git add portal/tests/test_fde_pages.py
git commit -m "test: define FDE ecosystem page contract"
```

---

### 任务 2：提取 FDE 专用视觉系统

**文件：**
- 创建：`portal/css/fde.css`
- 修改：`portal/fde.html` 的 `<head>`
- 修改：`portal/zh/fde.html` 的 `<head>`

- [ ] **步骤 1：创建专用 CSS 文件**

`portal/css/fde.css` 至少定义以下组件，全部使用现有 Octen 变量：

```css
:root {
  --fde-control: #22d3ee;
  --fde-sdr: #f59e0b;
  --fde-edge: #a78bfa;
  --fde-safe: #22c55e;
  --fde-warning: #fbbf24;
}

.fde-hero { padding: 10rem 2rem 5rem; text-align: center; }
.fde-section { padding: 6rem 2rem; }
.fde-section:nth-of-type(even) { background: var(--bg-secondary); }
.fde-section-header { max-width: 760px; margin: 0 auto 3rem; text-align: center; }
.fde-anchor-nav { display: flex; gap: .75rem; overflow-x: auto; padding: 1rem 0; }
.fde-anchor-nav a { white-space: nowrap; }
.fde-track-grid,
.fde-family-grid,
.fde-module-grid,
.fde-evidence-grid { display: grid; gap: 1.25rem; }
.fde-track-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.fde-family-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.fde-module-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.fde-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 1rem; padding: 1.5rem; }
.fde-card[data-track="control"] { border-top: 3px solid var(--fde-control); }
.fde-card[data-track="sdr"] { border-top: 3px solid var(--fde-sdr); }
.fde-card[data-track="edge"] { border-top: 3px solid var(--fde-edge); }
.fde-client-list { display: flex; flex-wrap: wrap; gap: .5rem; margin-top: 1rem; }
.fde-client { border: 1px solid var(--border); border-radius: 999px; padding: .35rem .7rem; font-size: .8rem; }
.fde-relation { font-family: var(--font-mono); color: var(--accent); }
.fde-status { display: inline-flex; border-radius: 999px; padding: .25rem .55rem; font-size: .72rem; font-weight: 600; }
.fde-status--field { color: var(--fde-safe); border: 1px solid currentColor; }
.fde-status--tested { color: var(--fde-control); border: 1px solid currentColor; }
.fde-status--pending { color: var(--fde-warning); border: 1px solid currentColor; }
.fde-table-wrap { overflow-x: auto; }
.fde-table { min-width: 860px; width: 100%; border-collapse: collapse; }
.fde-details { background: var(--bg-card); border: 1px solid var(--border); border-radius: .75rem; margin-bottom: .75rem; }
.fde-details summary { cursor: pointer; padding: 1rem 1.25rem; font-weight: 600; }
.fde-details-body { padding: 0 1.25rem 1.25rem; }
.fde-svg { width: 100%; height: auto; display: block; }

@media (max-width: 900px) {
  .fde-track-grid,
  .fde-family-grid,
  .fde-module-grid { grid-template-columns: 1fr; }
  .fde-hero { padding: 8rem 1.25rem 4rem; }
  .fde-section { padding: 4rem 1.25rem; }
}

@media (prefers-reduced-motion: reduce) {
  .fde-card { transition: none; }
}
```

Add any narrowly required selectors for ontology diagrams, field rows, maturity legends, and mobile stacking. Do not copy global navbar/footer rules from `octen.css`.

- [ ] **步骤 2：link the stylesheet from both pages**

English head:

```html
<link rel="stylesheet" href="css/octen.css?v=6">
<link rel="stylesheet" href="css/sunsdrmobile.css?v=1">
<link rel="stylesheet" href="css/fde.css?v=1">
```

Chinese head:

```html
<link rel="stylesheet" href="../css/octen.css?v=6">
<link rel="stylesheet" href="../css/sunsdrmobile.css?v=1">
<link rel="stylesheet" href="../css/fde.css?v=1">
```

Remove the old large inline FDE `<style>` block after the replacement pages use `fde.css`.

- [ ] **步骤 3：运行资源测试**

运行：

```bash
python3 portal/tests/test_fde_pages.py FdePageTests.test_relative_assets_exist -v
```

预期：PASS；其他内容测试仍可失败。

- [ ] **步骤 4：提交样式基础**

```bash
git add portal/css/fde.css portal/fde.html portal/zh/fde.html
git commit -m "style: add FDE ecosystem page components"
```

---

### 任务 3：重构英文 FDE 页面

**文件：**
- 修改：`portal/fde.html`
- 参考：`docs/superpowers/specs/2026-08-27-fde-ecosystem-ontology-design.md`

- [ ] **步骤 1：更新元数据和 Hero**

使用下列口径：

```html
<title>FDE in Practice — VLSC Remote Radio Engineering</title>
<meta name="description" content="How five VLSC product families turn field problems into reusable remote-radio architecture, safety patterns, and a shared domain ontology.">
```

Hero 必须包含：

```html
<section class="fde-hero">
  <div class="hero-badge">Forward Deployed Engineering · Field Knowledge System</div>
  <h1>One Field. Three Tracks.<br><span class="gradient">Five Product Families.</span></h1>
  <p>...</p>
</section>
```

不得出现 “Three Projects” 或把 SunsdrMobile 计作独立产品族的表述。

- [ ] **步骤 2：实现双循环和三轨总览**

创建带固定 ID 的章节：

```html
<section class="fde-section" id="method">...</section>
<section class="fde-section" id="tracks">...</section>
```

`method` 中并列展示：

```text
FDE Delivery: Echo -> Delta -> Product
Ontology Engineering: Scope -> Terms -> Relations -> Constraints -> Validate
```

`tracks` 中展示：

- Radio Control：MRRC Universal；MRRC FT-710 -> MRRC Modern。
- Direct-IQ SDR：SunMRRC，内含 Web 与 SunsdrMobile。
- Workflow / RF Edge：MRRC-FT8 与 EFHW。

所有 SVG 都使用：

```html
<svg class="fde-svg" role="img" aria-labelledby="unique-title unique-desc">
  <title id="unique-title">...</title>
  <desc id="unique-desc">...</desc>
  ...
</svg>
```

- [ ] **步骤 3：实现五个产品族深度分析**

创建：

```html
<section class="fde-section" id="families">
```

每个 `<article class="fde-card">` 使用唯一 `data-family`：

```text
mrrc-universal
mrrc-direct-usb
sunmrrc
mrrc-ft8
efhw
```

每张卡按固定顺序包含：Field Problem、Echo Evidence、Delta Breakthrough、Product Boundary、Reused Assets、New Assets、Ontology Contribution、Maturity/Evidence。

在 Direct USB 卡内部包含：

```html
<span data-client="web-pwa">Web / PWA</span>
<span data-client="ios">FT710Mobile · iOS</span>
<span data-client="android">FT710Android · Android</span>
<span data-family-end="mrrc-direct-usb"></span>
```

在 SunMRRC 卡内部包含：

```html
<span data-client="web">SunMRRC Web</span>
<span data-client="sunsdrmobile">SunsdrMobile · iOS</span>
<span data-family-end="sunmrrc"></span>
```

Direct USB 卡必须说明 FT-710 是垂直验证、Modern 是平台化结果。不得宣称 iOS 和 Android 客户端成熟度相同。

- [ ] **步骤 4：实现杠杆图和复用语义**

创建：

```html
<section class="fde-section" id="leverage">
```

展示六个共享平面：Control、Media、Device、Safety、Workflow、Experience。关系图只使用以下定义过的谓词：

```text
inherits
consumes
implements
inspired-by
```

所有关系旁必须显示文字，不能只靠颜色或箭头表示。

- [ ] **步骤 5：实现轻量模块化领域本体**

创建：

```html
<section class="fde-section" id="ontology">
```

先解释本体不是第四个 FDE 阶段，再展示：

```text
Agent
Physical Entity
Software System
Activity / Process
Information Object
Capability / Function
Policy / Constraint
Evidence / Provenance Record
```

模块卡覆盖：Identity/Authority、Station/Equipment、Function/Service、Command/Actuation/Observation、Protocol/Transport、Signal/Media/Measurement、Time/Workflow、Safety/Reliability、Evidence/Provenance。

正文必须明确出现：

```text
CommandIntent -> requests -> Actuation -> changes -> DeviceState
Observation -> yields -> StateReport
RF Signal -> Sample/Stream -> Frame
```

并给出安全不变量：单一权威状态所有者、TX 必须有授权和安全上下文、断线/超时收敛到 RX、命令不等于确认状态、不可检测故障不得声称已检测。

- [ ] **步骤 6：实现能力矩阵与证据层**

创建：

```html
<section class="fde-section" id="capabilities">...</section>
<section class="fde-section" id="evidence">...</section>
```

能力矩阵按五个产品族列出设备、控制协议、媒体、频谱源、DSP、工作流、RF 执行、客户端和安全模型。

证据成熟度固定为：

```text
Design target
Simulation result
Automated test
Bench verified
Field verified
Released / operational
Deferred / known issue
```

必须准确记录：

- MRRC FT-710 源码 v1.8.1；v1.8.0 Windows 发布包；439 项测试。
- MRRC Modern v1.12.0；FT-710、IC-7300、IC-7300MK2；633 项测试；IC 实机验收单列。
- MRRC-FT8 公开发布版本与 SDD V1.8 现场演进分开。
- EFHW V3.0 是设计/固件完成，PCB 和台架验证待完成。
- FT710Mobile 的 P0 PTT 安全问题明确为已知问题，不能标为安全完成。

- [ ] **步骤 7：实现原生可折叠附录、CTA 和页脚**

每个附录使用原生结构：

```html
<details class="fde-details">
  <summary>Evidence ledger</summary>
  <div class="fde-details-body">...</div>
</details>
```

附录包含版本/证据账本、术语表、12 个 competency questions、经证据支持的时间线、标准参考链接。CTA 和页脚按五产品族更新，不再输出三项目口径。

- [ ] **步骤 8：运行英文相关测试**

运行：

```bash
python3 portal/tests/test_fde_pages.py \
  FdePageTests.test_obsolete_top_level_counts_are_removed \
  FdePageTests.test_ontology_and_evidence_vocabulary_is_present \
  FdePageTests.test_product_family_nesting_is_explicit -v
```

预期：英文断言通过；若测试同时遍历中文，中文仍失败是预期，暂不放宽测试。

- [ ] **步骤 9：提交英文页面**

```bash
git add portal/fde.html
git commit -m "feat: rebuild English FDE ecosystem page"
```

---

### 任务 4：实现中文等价页面

**文件：**
- 修改：`portal/zh/fde.html`
- 对照：`portal/fde.html`

- [ ] **步骤 1：按英文页面逐节建立中文结构**

必须复用完全相同的 section IDs：

```text
method
tracks
families
leverage
ontology
capabilities
evidence
```

`data-family`、`data-client`、`data-family-end` 使用与英文相同的机器可读值，标题、说明、SVG `title/desc` 和表格内容翻译为中文。

- [ ] **步骤 2：统一关键中文术语**

采用以下固定译法：

```text
Product Family = 产品族
Domain Ontology = 领域本体
CommandIntent = 控制意图
Actuation = 执行活动
Observation = 观测活动
StateReport = 状态报告
DeviceAdapter = 设备适配器
Protocol Binding = 协议绑定
Control Lease = 控制租约
Field verified = 现场验证
Evidence provenance = 证据溯源
```

首次出现时保留英文括注，后续可使用中文简称。产品和协议专名不翻译。

- [ ] **步骤 3：同步产品归属和成熟度说明**

中文页面必须明确：

- SunsdrMobile 是 SunMRRC 的 iOS 客户端。
- FT710Mobile 和 FT710Android 是 Direct USB 产品族客户端。
- MRRC FT-710 -> MRRC Modern 是垂直验证到平台化的演化关系。
- 客户端实现状态、自动化测试、真机验收分别标注。

- [ ] **步骤 4：运行完整页面契约测试**

运行：

```bash
python3 portal/tests/test_fde_pages.py -v
```

预期：全部测试 PASS。

- [ ] **步骤 5：提交中文页面**

```bash
git add portal/zh/fde.html
git commit -m "feat: add Chinese FDE ecosystem ontology page"
```

---

### 任务 5：内容、可访问性和本地站点验证

**文件：**
- 修改（仅发现问题时）：`portal/fde.html`
- 修改（仅发现问题时）：`portal/zh/fde.html`
- 修改（仅发现问题时）：`portal/css/fde.css`
- 修改（仅测试需要修正时）：`portal/tests/test_fde_pages.py`

- [ ] **步骤 1：运行 LSP 与项目诊断**

运行工具：

```text
lsp_diagnostics(paths=[
  "portal/fde.html",
  "portal/zh/fde.html",
  "portal/css/fde.css",
  "portal/tests/test_fde_pages.py"
], severity="all")

lens_diagnostics(mode="all", paths=[
  "portal/fde.html",
  "portal/zh/fde.html",
  "portal/css/fde.css",
  "portal/tests/test_fde_pages.py"
])
```

预期：无 blocking error；修复本次变更引入的 warning。

- [ ] **步骤 2：检查旧口径、危险断言和语言结构漂移**

运行：

```bash
rg -n 'Three Projects|Three Products|跨三项目|三款产品|seven projects|七个项目' \
  portal/fde.html portal/zh/fde.html
rg -n 'SunsdrMobile' portal/fde.html portal/zh/fde.html
rg -n 'FT710Mobile|FT710Android|iOS|Android' portal/fde.html portal/zh/fde.html
python3 portal/tests/test_fde_pages.py -v
```

预期：第一条无匹配；后两条只在对应产品族和证据说明中出现；测试全部 PASS。

- [ ] **步骤 3：启动本地 HTTP 服务并检查响应**

运行：

```bash
python3 -m http.server 8765 --directory portal >/tmp/vlsc-fde-http.log 2>&1 &
server_pid=$!
trap 'kill "$server_pid" 2>/dev/null || true' EXIT
sleep 1
curl -fsS http://127.0.0.1:8765/fde.html >/dev/null
curl -fsS http://127.0.0.1:8765/zh/fde.html >/dev/null
curl -fsS http://127.0.0.1:8765/css/fde.css >/dev/null
kill "$server_pid"
trap - EXIT
```

预期：三个 `curl` 命令均返回 0。

- [ ] **步骤 4：浏览器人工检查**

在桌面宽度和约 390px 移动宽度检查：

- 导航不遮挡 Hero。
- 三轨图在移动端正确堆叠。
- Direct USB 与 SunMRRC 的客户端嵌套清晰。
- 本体图文字不溢出，关系不依赖颜色理解。
- 能力矩阵可以横向滚动。
- 所有 `<details>` 可用鼠标和键盘打开。
- 中英文语言切换路径正确。
- 所有本地链接和 GitHub 外链正确。

- [ ] **步骤 5：检查最终差异只包含本任务文件**

运行：

```bash
git diff --check
git status --short
git diff -- portal/fde.html portal/zh/fde.html portal/css/fde.css portal/tests/test_fde_pages.py
```

预期：`git diff --check` 无输出。不要暂存或提交工作区中原有的 EFHW、Portal 其他页面、图片或 `mrrc_modern` 链接变更。

- [ ] **步骤 6：提交验证修正**

若步骤 1–4 产生修正：

```bash
git add portal/fde.html portal/zh/fde.html portal/css/fde.css portal/tests/test_fde_pages.py
git commit -m "fix: verify FDE ontology page content and accessibility"
```

若无修正，不创建空提交。

---

### 任务 6：最终验收

**文件：**
- 验证：`portal/fde.html`
- 验证：`portal/zh/fde.html`
- 验证：`portal/css/fde.css`
- 验证：`portal/tests/test_fde_pages.py`

- [ ] **步骤 1：运行最终自动化验证**

```bash
python3 portal/tests/test_fde_pages.py -v
git diff --check c8d64f9..HEAD
```

预期：全部页面测试 PASS，diff whitespace 检查无输出。

- [ ] **步骤 2：运行最终诊断**

```text
lens_diagnostics(mode="all", paths=[
  "portal/fde.html",
  "portal/zh/fde.html",
  "portal/css/fde.css",
  "portal/tests/test_fde_pages.py"
])
```

预期：没有本次变更引入的 blocking errors 或未处理 warnings。

- [ ] **步骤 3：核对规格覆盖**

逐项对照 `docs/superpowers/specs/2026-08-27-fde-ecosystem-ontology-design.md`，确认：

- 五个产品族全部出现且归属正确。
- SunsdrMobile、FT710Mobile、FT710Android 均作为客户端出现。
- FDE 与本体是双循环，不是四阶段流水线。
- 领域本体包含类、关系、约束、Profiles 和 competency questions。
- 证据成熟度与能力矩阵分离。
- EN/ZH 信息结构一致。
- 无新增运行时依赖或构建步骤。

- [ ] **步骤 4：记录最终提交范围**

运行：

```bash
git log --oneline --decorate -6
git status --short
```

预期：本任务提交只涉及计划列出的四个实现文件；原有未提交工作保持原状。
