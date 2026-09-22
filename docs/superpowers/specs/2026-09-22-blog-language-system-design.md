# 全站编辑性正文的语言体系（Language System）设计

- 日期：2026-09-22
- 状态：已获用户批准（范围 D · 双语镜像 A · 三档文体 B · 规范+测试 C · 方案二样板先行 · 分册豁免 TL;DR · 本次不发版）
- 归属仓库：`/Users/cheenle/HAM/website`（`portal/` 与 `docs/` 均为真实目录，非 symlink）
- 施工面：约 48 个文件（17 个英文页 + 12 个已有中文页 + 4 个新写中文页 + 2 个索引 + `sitemap.xml` + 4 个总纲页 + 8 个 landing 页术语核对）

---

## 1. 问题

1. **假镜像。** 2026-09-19 ~ 09-21 的**八次** `style(zh)` 提交只重写了中文侧，英文侧未同步。实测：`blog/coda/zh/` 有王阳明、左传、司马迁、老子、天问、张载六处经典引用，`blog/coda/` 用 `grep -o "Wang Yangming|Zuo Zhuan|Sima Qian|Zhang Zai|Laozi|Qu Yuan"` 得 **0 处**。结构镜像还在（测试断言 section id 相等），内容镜像已经不成立。
2. **四篇孤儿。** `ft710-usb-remote-control`、`efhw-esp32s3-auto-tuner`、`opus-vs-pcm-remote-audio`、`psk-reporter-dxcc-hunting` 停在旧版式（`ba-prose` / `citation` / `ba-tags`，无提炼层、无锚点导航、无 claim 分级），且**完全没有中文**——中文索引只能把它们标成「英文」并直连英文页。
3. **体系不可执行。** 文风与结构只存在于提交历史和写作者记忆里。没有约束，下一轮写作就会再漂移一次，于是需要第三次重写。这是本次要解决的根本问题。

## 2. 决策记录

| 决策 | 选择 | 理由 |
| --- | --- | --- |
| 范围 | portal 编辑性正文：blog 全系列 + `agentic.html` / `engineering.html`（EN+ZH）。landing/about/contact/privacy 只做术语与导航核对 | CLAUDE.md 规定 portal 是事实总账，子站不得自我报可比数字；文风该跟着账走 |
| 双语关系 | **逐节真镜像**：每节双语一一对应，经典引用两侧都出现；中文用原文，英文用可核对译本 + 括注原文 | 符合站点纪律（可核对、可复现），且现有测试本就断言结构相等 |
| 文体 | **三档**：论说文 / 实操文 / 总纲 | 标题引经据典已全站化，正文引经典目前只属论说文；一刀切会让引文变装饰 |
| 落地 | 规范文档 + `tests/test_blog_language.py` | 上次更新之所以必要，就是因为没留下可执行约束 |
| 推进 | 样板先行 → 定规范 → 分档批量（方案二） | 体系须由真实页面反推，不能先验规定 |
| 分册 | `almanac` / `ledger` / `playbook` 归实操文，**豁免 TL;DR**（仍强制 claim-box 与镜像） | 三本附录通篇即提炼表，加 TL;DR 属形式主义 |
| 发版 | 本次不发版 | 部署改生产站点，由用户决定时机 |

## 3. 语言体系

### 3.1 档位判据

| 档 | 怎么认定 | 结构 | 引文 | 语体阈值 |
| --- | --- | --- | --- | --- |
| **论说文** | 目的是立论（提出并辩护主张） | hero（badge + 渐变大标题 + 摘要 + pill 摘要 + meta）+ TL;DR ≥4 条（每条带 `fact/inference/thesis`）+ 锚点导航 + ≥3 节，每节有 label/标题/副标题 | 经典引用 **≥3 处**，每处必须支撑所在节的一条 claim；中文用原文，英文用译本 + 原文括注 | 均句长 ≤ **40 字**；`——` ≤ **6‰** |
| **实操文** | 目的是交付可复现的做法或数据 | 同上，TL;DR ≥3 条（fact 为主） | **禁止经典引用**；允许的"经"＝工程文献（RFC、论文、数据手册）+ 项目自身证据（事故、答复页、版本行、测试数字） | 均句长 ≤ **55 字**；`——` ≤ **6‰** |
| **总纲** | 站级立论页（`agentic.html` / `engineering.html`） | hero + 锚点导航 + 术语中英对照（`ag-term-grid`）；不设 TL;DR 卡 | 经典与工程文献并用，必须挂在具体章节的论点上 | 书面定义式，不口语化 |

阈值取"防倒退"而非"逐字锁死"：目标是锁住统计形态与结构，不锁句子。

**「引文」的可测定义**：指通过 `ba-quote` 结构呈现的引用块（见 §4）。文章标题、章节副标题与行文中的典故化用**不计入统计**——标题引经据典是全站性的，实操文标题允许用典（《三板斧》《闻过则喜》即为此类）。

### 3.2 度量算法（规范与测试共用，必须一致）

- 正文 = `<main class="ba-main">` 内可见文本（剔除 `<script>` / `<style>`，去标签后 unescape）
- 汉字数 `N` = `[\u4e00-\u9fff]` 计数
- 句数 `S` = `。！？` 计数；**均句长 = N / S**
- **破折号密度 = (`——` 出现次数 / N) × 1000**，单位 ‰

> **实现陷阱（已实测）：** 不能用 `HTMLParser` 拼接 `handle_data` 取正文。相邻表格单元格里的两个「—」（`<td>…—</td><td>—…</td>`）拼接后会变成「——」，使 `seven-billion-tokens/ledger` 从 5.75‰ 虚高到 6.71‰，凭空多出一篇超标。必须“标签替换为空格后再 unescape”。测试与计划中的 `body_text()` 即按此实现，已用真实站点验证。

### 3.3 基线（2026-09-22 实测，同一算法）

| 文章（中文） | 汉字 N | 句数 S | 均句长 | `——` | ‰ | 档 | 判定 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| coda | 3477 | 140 | 24.8 | 15 | 4.3 | 论说文 | ✅ |
| faculties | 4863 | 152 | 32.0 | 35 | **7.2** | 论说文 | ❌ 破折号 |
| ming-li-dao-tian | 2869 | 96 | 29.9 | 34 | **11.9** | 论说文 | ❌ 破折号 |
| only-imagination | 4276 | 133 | 32.2 | 21 | 4.9 | 论说文 | ✅ |
| connections-recursive-intelligence | 6293 | 176 | 35.8 | 8 | 1.3 | 论说文 | ✅ |
| solo-loop | 5097 | 121 | 42.1 | 12 | 2.4 | 实操文 | ✅ |
| support-loop | 7806 | 219 | 35.6 | 49 | **6.3** | 实操文 | ❌ 破折号 |
| three-axes | 6270 | 142 | 44.2 | 32 | 5.1 | 实操文 | ✅ |
| seven-billion-tokens（主文） | 5658 | 175 | 32.3 | 46 | **8.1** | 实操文 | ❌ 破折号 |
| seven-billion-tokens/almanac | 1285 | 32 | 40.2 | 14 | **10.9** | 实操文 | ❌ 破折号 |
| seven-billion-tokens/ledger | 2087 | 70 | 29.8 | 12 | 5.7 | 实操文 | ✅ |
| seven-billion-tokens/playbook | 2328 | 65 | 35.8 | 8 | 3.4 | 实操文 | ✅ |

**超标清单（施工时必须降到 ≤6‰）**：`faculties` 7.2、`ming-li-dao-tian` 11.9、`support-loop` 6.3、`seven-billion-tokens` 8.1、`almanac` 10.9。共 5 篇。

> 更正说明：方案讨论阶段曾报"两篇超标"，那是用另一套分母（含 ASCII 的字符数）算出的口径。本表用 3.2 的最终算法，超标为 5 篇。

### 3.4 引文规则（四条，三档共用）

1. **完整引用、不截断**；标出处（篇名 + 作者/时代）。
2. **中文保持原文**，异体字/通假不改；白话只做句读与桥接（规则来源：提交 `511242e`）。
3. **英文用可核对的译本**；自译标 `trans.`，并括注原文。不冒充公版译本。
4. **去重**：同一句原文不在多篇反复堆砌；再次出现必须为新论点服务。

### 3.5 术语表（首版）

| 中文 | 英文 |
| --- | --- |
| 现场 | field |
| 裁决归人 | judgment stays human |
| 两本账 | two ledgers |
| 意图 · 边界 · 裁决 | intent · boundary · verdict |
| 智能体工程 | agentic engineering |
| 前沿部署工程（FDE） | Forward Deployed Engineering |
| 执行可被委托，判断不能 | execution can be delegated, judgment cannot |
| 约束清单 | constraint registry |
| 版本记录 | version record |

### 3.6 禁用词（双语同时生效）

- **翻译腔**：「被用来」「这是一个可以…的…」（模板式长定语）
- **AI 腔**：「值得注意的是」「在当今时代」「让我们」「深入探讨」「综上所述」
- **已否决项**：「代理式工程」（必须是「智能体工程」）、「三款产品」、「由 Agent 写成」、`written by AI`
- **标点**：中文正文内的引号统一为 `「」`；半角直引号 `"` 与弯引号 `“ ”` 均不允许（排除 `<code>` / `<pre>`）
- **术语方向**：出现 `agentic engineering` 时中文侧必须是「智能体工程」，反之亦然

### 3.7 档位归属表

| slug / 页面 | 档 | 备注 |
| --- | --- | --- |
| `coda` `faculties` `ming-li-dao-tian` `only-imagination` `connections-recursive-intelligence` | 论说文 | |
| `solo-loop` `support-loop` `three-axes` | 实操文 | |
| `seven-billion-tokens` + `almanac` `ledger` `playbook` | 实操文 | 三本分册豁免 TL;DR |
| `ft710-usb-remote-control` `efhw-esp32s3-auto-tuner` `opus-vs-pcm-remote-audio` `psk-reporter-dxcc-hunting` | 实操文 | 老 4 篇：EN 升骨架 + 新写中文 |
| `agentic.html` `engineering.html`（EN + `zh/`） | 总纲 | |
| `juekun` | **原文档案** | 作者自标「对话沉淀，非论述文」。豁免镜像与 TL;DR；仍受术语、禁用词、阈值约束 |
| `from-intent-to-delivery/{,zh/}` | **跳转壳** | `meta refresh → /blog/seven-billion-tokens/`。豁免全部内容断言，仅断言 canonical 与无正文 |

## 4. 新组件 `ba-quote`

引文必须先成为机器可识别的结构，"镜像"才可断言。现有中文引文是裸文本（`<p>` 里的「志不立，天下无可成之事。」），无法配对。

```html
<blockquote class="ba-quote" data-quote-id="wang-yangming-lichang" data-quote-kind="classic"
            data-quote-cite="王阳明《教条示龙场诸生》">
  <p class="ba-quote-orig" lang="zh">志不立，天下无可成之事。</p>
  <p class="ba-quote-trans" lang="en">Without resolve, nothing in the world can be accomplished.
    <span class="ba-quote-by">trans.</span></p>
</blockquote>
```

- `data-quote-kind`：`classic`（中国经典）/ `engineering`（工程文献、数据手册、论文）/ `project`（项目自身证据：事故、答复页、版本行）
- `data-quote-id`：全篇唯一，**EN 与 ZH 必须同名**——这就是镜像断言的锚
- 两侧都必须有 `ba-quote-orig` 与 `ba-quote-trans`（原文与可读译本）
- 无障碍：语义用 `<blockquote>`，出处用 `data-quote-cite` 并在视觉上以 `.ba-quote-cite` 呈现
- CSS 落在 `css/blog-article.css`，版本 `?v=3 → ?v=4`（引用该 CSS 的页面同步 bump）

用显式 `data-quote-kind` 而非正则猜"哪些算经典"：测试稳定，新增引用不需要维护白名单。

## 5. 可执行约束 `tests/test_blog_language.py`

沿用现有测试风格（`unittest` + 标准库 `HTMLParser`，不引新依赖）。档位由显式清单常量驱动（slug → 档），测试不猜、不靠启发式判断。度量只对有 `<main class="ba-main">` 的页面生效（`juekun` 有，跳转壳没有）。

**结构与镜像（全部文章 ×2 语）**

- `ba-article` / 面包屑 / hero（h1 + 摘要 + meta）/ 尾栏三段齐备
- `ba-tldr` 存在：论说文 ≥4 条、实操文 ≥3 条；每条有 `data-claim-type ∈ {fact, inference, thesis, analogy}`
  （自检补充：`analogy`（工程类比）已在 `connections` ×2 语使用 4 处，且 `blog-article.css` 已有其配色，因此保留为第四种合法类型，不移除）
- `ag-anchor-nav` 每个锚点指向真实存在的 section id（零死锚）
- `ag-section` ≥3
- section id 集合、TL;DR 条数、claim-type 集合、`data-quote-id` 集合：**EN 与 ZH 相等**
- 每个 `ba-quote`：id 全篇唯一、kind 合法、cite 非空、orig 与 trans 齐备

**三档判据**

- 论说文：`kind="classic"` ≥3
- 实操文：`kind="classic"` = 0
- 总纲页：锚点齐备 + `ag-term-grid` 存在

**语体阈值（按 3.2 算法，仅中文本体）**

- 均句长 ≤40 字（论说文）/ ≤55 字（实操文）
- `——` ≤6‰
- 中文正文引号统一为 `「」`（排除 `<code>` / `<pre>`：如 `"FT4222 A"` 这类设备描述符字符串合法）

**术语与禁用词**：3.6 清单，双语同时生效（模式继承 `test_agentic_pages.OBSOLETE_PHRASES`）。§3.5 术语表为写作参考，其中只有「智能体工程 ↔ agentic engineering」的双向一致性进入测试，其余不强制出现

**索引与元数据**

- `/blog/` 与 `/blog/zh/` 卡片集合一致（同 slug、互链）
- 每篇有 `hreflang` `en` / `zh-CN` / `x-default` 与 canonical
- `sitemap.xml` 收录全部文章两语
- 旧版式残留为 0：`ba-prose`（旧正文容器，已被 `ag-section` 取代）与 `ba-tags`（旧标签行，已被 hero pills 取代）——涉及 6 个文件：老 4 篇 + `connections` ×2 语
- **`citation` 不退役**：自检发现它是**脚注引用机制**（`connections` 11 处 ×2 语 + `ft710` 1 处），不是旧版式，且与文末参考区配对。保留，并在本次统一为命名空间的 `ba-` 前缀（`ba-cite-ref`），`ft710` 那 1 处随重排迁移或删除

**豁免机制**：批次 0–1 落地时，未达标项进入带到期批次号的"待清"白名单，**批次 7 清空**，验收时不得残留。白名单分两张，因为两类失败的生命周期不同：

- `PENDING_DASH`（文章 → 批次）：语体阈值类，今天只涉 5 篇，到期批次 2 / 3
- `PENDING_ARTICLES`（(文章, 语言) → 批次）：结构 / 镜像 / 引文 / 标点 / 元数据类，涉 12 篇 ×2 语，跨越批次 0 / 2 / 4 / 9

验收闸门是 `test_pending_entries_are_gone`：两张名单均空才通过。

## 6. 施工批次

| 批次 | 内容 | 文件数 | 产出 |
| --- | --- | --- | --- |
| 0 · 样板 | `coda`（EN 补引文镜像 + ZH 引文改标记，正文不动）；`ft710`（EN 升骨架 + 新写中文） | 4 | 两个方向各一个真实样板；`blog-article.css` 加 `.ba-quote`（v3→v4） |
| 1 · 规范落地 | 本设计文档 + `tests/test_blog_language.py` | 2 | 体系变成可执行约束；测试全绿 |
| 2 · 论说文对齐 | `faculties`、`ming-li-dao-tian`、`only-imagination`、`connections` | 8 | 论说文档达标（含 2 篇破折号超标）；`connections` 额外做结构迁移：`ba-tags` → hero pills、`citation` → `ba-cite-ref`（22 处）、EN 补引文镜像 |
| 3 · 实操文对齐 | `solo-loop`、`support-loop`、`three-axes`、`seven-billion-tokens` 主文 + 三本分册 | 14 | 实操文档达标（含 3 篇破折号超标） |
| 4 · 老 4 篇 | `efhw`、`opus`、`psk`（`ft710` 已在样板做）：EN 升骨架 + 新写中文 ×3 | 6 | 全站每篇都有中文 |
| 5 · 总纲 | `agentic.html`、`engineering.html`（EN + `zh/`） | 4 | 总纲档达标 |
| 6 · 索引与元数据 | `blog/index.html`、`blog/zh/index.html`、`sitemap.xml`；landing 8 页术语/导航核对 | 11 | 索引一致、hreflang 齐备 |
| 7 · 收尾 | 清空"待清"白名单 → 全站测试复检 | — | 无豁免状态 |

**提交粒度**：每篇一个 commit，**EN+ZH 必须同一 commit**（镜像断言要求同步）。沿用既有格式：`style(zh):` / `docs(blog):` / `feat(blog):`。每批结束跑一次全量测试。

## 7. 明确不做

- **不进子站**：`mrrc/` `mrrc_modern/` `sunmrrc/` `efhw/` `mrrc_ft8/` 是独立仓库、独立部署，各自 commit
- **不动 SDD 生成页**：`build_sdd.py` 输出的是构建产物，改模板不属于本次
- **不新增构建步骤**：仓库无构建步骤，全部手写 HTML
- **不重写 landing 页文风**：`index/about/contact/privacy` 仅术语与导航核对
- **不做新视觉设计**：沿用 `agentic.css` + `blog-article.css` 既有系统，只加 `.ba-quote`
- **不重写 `juekun` 正文**：作者原话，按原意理顺的文字不动
- **不引新字体/新框架/新依赖**

## 8. 验收

1. `python3 -m unittest discover portal/tests -v` 全绿（现有 78 个 + 新增断言）
2. "待清"白名单无残留
3. 全部文章 EN/ZH 的 `data-quote-id` 集合相等
4. 5 篇超标破折号降到 ≤6‰
5. 4 篇老文各自的 `zh/` 上线，并进入 `/blog/zh/` 索引与 `sitemap.xml`

## 9. 风险与缓解

| 风险 | 缓解 |
| --- | --- |
| 英文侧引文译本质量 | 自译标 `trans.` + 括注原文；不冒充公版译本；出处可核对 |
| 阈值断言锁死文笔 | 只锁统计量与结构，不锁句子；阈值取防倒退水平 |
| 48 文件改动难回溯 | 每篇一 commit，EN+ZH 同 commit；每批跑全量测试 |
| 中文新写偏离作者声音 | 批次 0 先用 `ft710` 样板验收，后续按样板对齐 |
| 引文标记工作量大 | 显式 `data-quote-*` 属性，无需维护经典白名单 |
