# 把 FDE 整体重构成 Agentic Engineering（全站）

**日期：** 2026-09-02
**状态：** 设计已逐节确认，待规格审查
**范围：** portal + 6 个可改子站（`mrrc` 本轮除外，见 §10）
**决定链：** 全站重构(C) → FDE 分层保留(B) → 命题 A+B 合一(C) → 双层页面 IA(C) → 子站深度＝术语层＋分工小节(B) → 本体升为 Agent 运行时底座(B)

## 1. 目的

把「Agentic Engineering（智能体工程）」提升为 VLSC 全站的工程总纲，同时保留 Forward Deployed
Engineering（FDE）作为它的一个交付环节与前史，使既有三份资产——产品族证据、领域本体、
Engineering System（Harness × Loop × Living SDD）——成为同一主张的可核查支撑，而不是三套并列说法。

本轮同时修复一项真实技术债：全站存在三份互相矛盾的 FDE 事实（§8）。

## 2. 核心命题

> **EN** — Agentic engineering is the discipline of building environments where an agent can be
> trusted to execute, and where a human remains the only one who can decide.
> **ZH** — 智能体工程的纪律，是构建一个「智能体可被信任去执行、而人保留唯一裁决权」的工程环境。

三段支撑（括号内为承载节次）：

1. **角色重构（`roles`）** — Agent 接管内环 Specify → Implement → Test → Review → Observe →
   Update SDD；人保留三样：**意图（Why）**、**边界（约束与安全不变量）**、**裁决（证据是否足以宣称完成）**。
2. **为什么现在才成立（`ontology`）** — Agent 真的会读契约。`AGENTS.md`、Living SDD、领域本体从
   「写给人看的交付物」变成「每次执行前被加载的运行时上下文」；约束从口头约定变成可执行物件。
3. **FDE 的位置（`lineage`）** — Echo → Delta → Product 不被否定：现场纪律产出了值得被复用的契约，
   并提供不可压缩的关口（PCB、台架、RF 安全）——Agent 无权对这些自行签字。

主张的可反驳形式（页面论证主干，不作口号使用）：

```text
现场事故 (Echo) → SDD 裁决 (AD-xxx / NFR-xxx) → 机器可读约束 (constraints.json)
                → Agent 越界阻断 (PreToolUse hook)
```

任何「本体即运行时」的表述必须能落到这条链上；落不到就不写。

## 3. 全站口径红线（逐页校验规则）

| 禁止 | 必须 |
| --- | --- |
| 「五个产品族由 Agent 写成」 | 「产品族在 FDE 纪律下由人主导产出；Agentic Engineering 描述其后续迭代、验证与本体维护如何交给 Agent 内环」 |
| 「Agent 通过测试 ⇒ 硬件可用」 | 沿用既有分离：automated test ≠ bench ≠ field；§8.3 新增的阶梯 B 位于其下，不得向上互推 |
| 让 FDE 一词消失 | FDE 保留为术语条目、历史环节，中文统一为「前沿部署工程」 |
| 「AI 赋能」「智慧工程」等无指称表述 | 只写具体工件名：`AGENTS.md`、`.agents/skills/sdd-guardian/`、`constraints.json`、`harness/index.json`、SDD 章节号、capability profile、Control Lease、PTT invariant |
| 声称某族有它其实没有的工件 | 逐仓如实标注（普查 2026-09-02）：**有 `AGENTS.md` + `constraints.json` 注册表** = ft710(17) / modern(21) / ft8(14)；**有 `AGENTS.md` 但无注册表** = mrrc、sunsdr(sunmrrc)；**仅 `CLAUDE.md`** = SunsdrMobile；**EFHW** = `efhw-knowledge/` 知识库 + workspace `CLAUDE.md`，无固件约束注册表。无注册表者不得声称「编辑前门禁」 |
| 把 EFHW 的 PCB/台架 pending 写成缺陷 | 写成「Agent 不得自行裁决、必须由人签字的关口」的示例 |
| 子站自述跨站可比数字（测试数 / 版本 / cycle 数） | 一律链接到 portal 事实账本（§8） |

## 4. 页面与 URL 架构（纲 / 目）

```text
/agentic.html            总纲（由 portal/fde.html 演化）＝命题 + 生态证据 + 本体底座
/engineering.html        机制分册（保留文件名）＝双层 Harness / 内外环 / Living SDD
/agentic/ontology.html   本期不建（仅保留锚点 #ontology）；搬迁路径见 §6.4
```

`engineering.html` 文件名与 URL 不动：它已有外链，且 `css/engineering.css` 的 `eng-*`
类依赖该页。纲 / 目父子关系由**导航与页内面包屑**表达，不靠目录结构。

### 4.1 重定向（集中在 `nginx/vlsc.net.conf`）

```nginx
location = /fde.html                 { return 301 /agentic.html; }
location = /zh/fde.html              { return 301 /zh/agentic.html; }
location = /mrrc_modern/fde.html     { return 301 /mrrc_modern/agentic.html; }
location = /mrrc_ft710/fde.html      { return 301 /mrrc_ft710/agentic.html; }
location = /mrrc/fde.html            { return 301 /mrrc/agentic.html; }
location = /mrrc/zh/fde.html         { return 301 /mrrc/zh/agentic.html; }
```

exact-match（`=`）优先于既有的 `location ~* \.html$`，无需调整原块顺序。

### 4.2 导航统一

* 各站 navbar `FDE` 项 → `Agentic`，指向 `/agentic.html`。
* `js/global-nav.js`：`SITE` 判定正则 `/\/fde\.html/` → `/\/(fde|agentic)\.html/`；
  路由表 `fde: '/fde.html'` → `agentic: '/agentic.html'`；`siteLink('fde','FDE')` →
  `siteLink('agentic','Agentic')`。`js/scope.js` 同步（子站共 5 处）。
* 页面 `data-site="fde"` → `data-site="agentic"`。

### 4.3 术语约定

| 英文 | 中文 | 备注 |
| --- | --- | --- |
| Agentic Engineering | 智能体工程 | 首次出现括注 `Agentic Engineering`；中文 AI 语境 agent 通行译法为「智能体」，「代理式」易被读成 proxy |
| Forward Deployed Engineering (FDE) | 前沿部署工程 | 作为历史环节名词条。**中文译名现状本身不一致**：`portal/zh/fde.html` 用「前沿部署工程」×2、`portal/zh/about.html` 用「前置部署工程」×1。取定义该术语的主页所用者，全站统一为「前沿部署工程」，`zh/about.html` 的一处随任务 5 改掉 |
| Agent | 智能体 | 与本体顶层分区 `Agent`（operator or software agent）区分：涉及人的授权时写「操作者 / Operator」 |
| Harness | 约束环境（Harness） | 中文页首次出现保留英文 |
| Living SDD | 活体 SDD（Living SDD） | 与 engineering.html 现有用词一致 |
| Constraint registry | 约束注册表 | 指 `harness/constraints.json` |

### 4.4 CSS 改名范围（普查已完成）

`css/fde.css` → `css/agentic.css`（153 行 / 100 条选择器），类前缀 `.fde-` → `.ag-`。
使用侧刚好四个文件（已核）：

| 文件 | 唯一 `.fde-*` 类数 | 备注 |
| --- | --- | --- |
| `portal/fde.html` | 47 | → `agentic.html` |
| `portal/zh/fde.html` | 47 | → `zh/agentic.html` |
| `portal/engineering.html` | 1（`fde-client-list`） | 仅一个类，跟改 |
| `portal/zh/engineering.html` | 1 | 同上 |

另有 `css/engineering.css` 内 2 处 `.fde-engineering-summary` 定义需同步改名。
重命名是一次机械 `sed`，作于 portal 范围内；子站各自的 CSS 不受影响。

注意：`engineering.html` 链接了 `css/fde.css`（仅为了 `fde-client-list`），改名后改链
`css/agentic.css`，并提升 `?v=` 缓存版本号。

## 5. `/agentic.html` 内容结构

沿用 octen 现有组件（按 §4.4 改名后的 `.ag-card` / `.ag-flow` / `.ag-table` / `.ag-details`），
无新框架、无新 CSS 体系。编号九节 = **10 个 `section id`**（`capabilities` 与 `evidence` 同属编号 09）；
`section id` 是契约测试断言对象，故给出新旧映射。

| # | id | 内容 | 来源 |
| --- | --- | --- | --- |
| 01 | `thesis` | 命题（§2 主张句 + 三段论）。Hero 承载于此 | 新写 |
| 02 | `roles` | 人与 Agent 的分工：左栏 Agent 接管的内环六步，右栏人保留的意图 / 边界 / 裁决。收尾一条边界声明：**「Agent 承担执行，不承担责任」**——责任始终在签字的人身上 | 新写（内环六步复用 engineering.html 表述） |
| 03 | `lineage` | FDE → Agentic：保留原 `method` 双环图（Echo→Delta→Product ＋ Scope→Terms→Relations→Constraints→Validate），叙事改为「现场纪律产出值得被复用的契约」，并列出不可压缩关口 | 改自 `method` |
| 04 | `harness` | 机制摘要：双层 Harness / Living SDD 三卡 + `Explore the Engineering System` → `/engineering.html`。保持「摘要 + 跳转」，细节不在总纲展开 | 保留原 `engineering` 节 |
| 05 | `tracks` | 三赛道 + SVG 生态图 | 原样保留 |
| 06 | `families` | 五产品族 deep dive | 保留 + 新增 2 字段（§5.2） |
| 07 | `leverage` | 六个 plane + `inherits / consumes / implements / inspired-by` 复用语义 | 原样保留（该语义正是 agentic 复用判断的地基） |
| 08 | `ontology` | 本体作为 Agent 运行时底座 + 新增「概念 → 消费方」映射（§6） | 改写 + 新增 |
| 09 | `capabilities` / `evidence` | 能力矩阵 + 证据纪律（§8 新分级）+ 折叠附录 | 保留，evidence 节扩充 |

Hero 文案改为 **`Human Intent. Agentic Execution. Field Evidence.`**，副标用 §2 主张句。
原 Hero 的「One Field. Three Tracks. Five Product Families.」下移到 `tracks` / `families` 两节承担，
使 Hero 表达主张而非数字。

锚点导航 8 项：`thesis` / `roles` / `lineage` / `harness` / `tracks` / `families` /
`ontology` / `evidence`（`leverage` 与 `capabilities` 从锚点导航移除以控制宽度，仍保留 id 供外链）。

### 5.1 契约测试同步

`portal/tests/test_fde_pages.py` → `test_agentic_pages.py`，`REQUIRED_SECTIONS` 更新为
`{thesis, roles, lineage, harness, tracks, families, leverage, ontology, capabilities, evidence}`；
`REQUIRED_FAMILIES` 不变；`test_obsolete_top_level_counts_are_removed` 的禁句清单追加
「Built Through Forward Deployed Engineering」（portal 首页旧标题）与旧 Hero 标题串。

### 5.2 产品族卡片新增字段（全站统一模板，同时是子站那一节的模板）

原 8 字段顺序不变，追加：

* **`Agent Execution` / 智能体承担环节** — 该族内环的哪些步骤实际由 Agent 执行、依据哪份入口文件。
  只写「哪几步」，不写「多少代码」。
* **`Human Retained Judgment` / 人保留裁决** — 该族中 Agent 不得自行签字的项目
  （EFHW：PCB 与台架验收；FT-710：PTT 安全路径真机确认；Modern：IC 系列物理接受度）。
  末尾并入 **`Contract Left Behind` / 沉淀契约**：该族新产出、可被下一个 Agent 加载的工件。

`Maturity / Evidence` 字段原位、原徽章不变——它是既有可信度来源，不能被新叙事稀释。

## 6. 本体新核心：概念 → 消费方映射

本期唯一的新设计内容。把「本体不只是文档」变成可核查的东西。

### 6.1 已核实的实装（三仓库共 52 条机器可读约束）

| 仓库 | `constraints.json` 规则数 | `sdd_version` | 路由索引 |
| --- | --- | --- | --- |
| `mrrc_ft710` | 17 | V1.7 | 15 章 / 15 主题 |
| `mrrc_modern` | 21 | V2.27 | 15 章 / 16 主题 |
| `mrrc_ft8` | 14 | V1.0 | 15 章 |

每条规则带 `severity`（`block` / `warn` / `info`）、`sdd_ref`（指回 AD-xxx / NFR-xxx / 具体事故）、
`scope` glob、`patterns` 正则、`message`。`context_map` 按文件 glob 映射到 SDD 条目。

执行入口：`harness/sdd_context.py` 提供 `prime` / `brief` / `sdd` / `context` / `check` / `hook`；
`hooks.snippet.toml` + `install_hooks.py` 注册 `SessionStart → prime`（会话开局注入）与
`PreToolUse(Edit|Write) → hook`（改前阻断）。`SKILL.md` 定义 Phase 0–6 生命周期
（brief → design → implement → test → verify → doc-sync → commit）。

**同一份语义在三处被消费**：Agent 上下文（`prime` / `brief`）、运行时阻断（`check` / `hook`）、
人裁决（`review` checklist + `docs-sync`）。这就是 agentic 工程相对「口头约定」的真实增量。

### 6.2 页面表格（概念 → 消费方 → 真实锚点）

| 本体概念 / 公理 | 消费方 | 真实锚点 |
| --- | --- | --- |
| `Policy/Constraint`：单一权威状态持有者、Serial 独占 | Agent 运行时硬阻断 | ft8 `no-direct-serial`「rigctld is the sole serial owner」[AD-008]；ft710 / modern `cat-direct-serial-io` [AD-002] |
| `Safety`：TX 授权与 PTT 所有权 | Agent 运行时硬阻断 | ft8 `ptt-authority`「PTT controlled only by rig and safety components」[AD-007; NFR-050; Ch15] |
| `CommandIntent ≠ Actuation` | Agent 侧 `info` 提示 | ft710 `ptt-release-no-verify`「TX0 is fire-and-forget」[AD-007; Ch15; V1.2] |
| `Observation`：陈旧读不得污染状态 | `info` 约束 + 单测 | ft710 / modern `poll-stale-guard` [AD-009; §9.6; V1.7 filter race fix] |
| `Protocol Binding ≠ Capability` | 代码事实 + 约束特化 | Modern `audio-pyaudio-rate` 由 FT-710 固定 44.1k 改为「rate comes from backend capabilities」[AD-011 amended V2.9/V2.14] |
| `Evidence/Provenance`：知识不得过时 | 路由索引不存内容 | `harness/index.json`「holds no content — refs are sliced live from `SDD/*.md`, so it never goes stale」 |
| `Information Object`：变更即文档同步 | 生命周期强制 | `SKILL.md` Phase 0–6；`docs-sync` 规则 [§14] |
| 事故 → 约束的因果链 | 领域记忆 | `cat-no-dn` [AD-014; SDD V1.2 freq-drift incident]、`audio-16k-rate` [AD-011; V1.1 crackling incident]、`cat-sh-format` [§10.4; commit a07bb49] |

### 6.3 每行必须可点开

表格三列全部来自仓库实际文件。规则：

* 锚点必须能在对应仓库内 grep 到（规则 ID 或原文子串）。
* 无法核实的行直接删除，不写「预计」「将会」。
* 表格下方标注普查日期（as-of）与仓库范围，沿用 portal 既有规矩：
  「historical counts are only stated with repository scope and as-of date」。

### 6.4 后续可选搬迁

若单页过长，把 `#ontology` 整节平移至 `/agentic/ontology.html`。搬迁成本低：契约测试按
section id 断言，拆页时同步 `REQUIRED_SECTIONS` 与 nginx 锚点即可。本期不做。

## 7. 逐站改动清单

深度＝术语层 + 每族「分工与资产」小节（§5.2 模板）。

| 站点 | 术语层改动 | 页面动作 | 重定向 |
| --- | --- | --- | --- |
| `portal/` | 导航 `FDE→Agentic`；`js/global-nav.js`；`index.html:316` 方法论节重写；`index.html:283`「Four Approaches, One Vision」口径核对；about / contact / privacy + 全部 `zh/` | `fde.html → agentic.html`（§5 九节）；`engineering.html` 标题与定位改为机制分册，`OUTER · FDE DELIVERY` 标签改为「外层 · FDE 交付环（agentic 环的外层）」 | `/fde.html`、`/zh/fde.html` |
| `mrrc_modern/` | `index.html:932`、`js/global-nav.js:34`、`js/scope.js:12`、`zh/index.html` | `fde.html → agentic.html`：保留技术内容，套 §5.2 两字段，按 §8 处理过时数字 | `/mrrc_modern/fde.html` |
| `mrrc_ft710/` | `index.html:55`、`js/global-nav.js:35`、`js/scope.js:12`、`zh/index.html` | 同上 | `/mrrc_ft710/fde.html` |
| `efhw/` | `index.html:560`、`js/global-nav.js:109`、`js/scope.js:46`、`zh/index.html` | 无 FDE 页；新增一节「本族分工与资产」（PCB / 台架为人的签字位） | — |
| `sunmrrc/` | `js/scope.js` | 新增一节「本族分工与资产」：仓库根 `/Users/cheenle/HAM/sunsdr` 有 `AGENTS.md` + `CLAUDE.md` + `SDD/`，**无** `.agents` 约束注册表 → 只声明 B1 以下证据 | — |
| `SunsdrMobile/` | `js/scope.js` | 同上（该族有 `CLAUDE.md`，无约束注册表） | — |
| `mrrc_ft8/` | `js/scope.js` | 新增一节「本族分工与资产」（14 条约束，含 vendor 只读、rigctld 独占、PTT 权威） | — |
| `mrrc/` | 改名 + 术语层 + 数字口径（**不重做页面设计**） | `fde.html → agentic.html`、23 文件 28 处导航链接 | 原「软链断裂」判断有误：仓库在 `/Users/cheenle/HAM/mrrc`，只是 `website/mrrc` 指向已搬走的旧路径。已重指向 |

中文对等：本期**不为子站新建** `zh/agentic.html`（两张子站 FDE 页本就无中文版），只更新
既有 `zh/index.html` 的链接文案。portal 保持 EN/ZH 完全对等（§9.1 断言）。子站中文页若将来
要补，属独立一轮工作。

## 8. 事实单一来源与过时数字修复

### 8.1 现状（本轮普查结果）

| 声称位置 | 页面写的 | 仓库实际 | 结论 |
| --- | --- | --- | --- |
| `mrrc_modern/fde.html` | 「12 FDE Cycles (Git-Verified)」、「V1.0 to V2.1」 | SDD `V2.30`、约束注册表 `sdd_version V2.27` | 落后约 9 个版本，且 cycle 数无 as-of 范围 |
| `mrrc_ft710/fde.html` | 「262 tests」、V1.0→V1.9 | portal 账本：439 tests、source v1.8.1；注册表 `V1.7` | 测试数与版本双重不一致 |
| `portal/fde.html` | 439 / 633 tests、v1.8.1、v1.12.0 | 与仓库一致 | 唯一可信来源 |

**根因**：跨站可比数字（测试数、版本号、cycle 数）在三个地方各自手写，无单一来源。
任何只做术语替换的重构都会把这三份矛盾改名后继续存在。

### 8.2 规则

1. `portal` 的 Evidence 节 = 全站唯一事实账本（版本、测试数、发布状态、已知缺陷）。
2. 子站删除自述的跨站可比数字，改为指向账本的链接 + 一句本族专有说明。
3. 子站保留：本族架构、模块表、协议细节（这些与各仓库一致，属各站专长）。
4. 无法核实的 legacy 数字按既有规矩「删除或显式标为 historical estimate」处理。
   本轮决定：`mrrc_modern/fde.html` 的「12 FDE Cycles (Git-Verified)」**整节标题与计数删除**，
   改为定性描述（「每次现场信号触发一次版本推进」）+ 指向 portal 账本的链接。理由：该数字既无
   as-of 范围、又已落后约 9 个版本，标为 historical estimate 反而制造第二个事实源。
5. 该规则写进 `CLAUDE.md`，作为后续新增子站的约束。

### 8.3 证据分级：两条独立阶梯（禁止互推）

**阶梯 A · 产品行为成熟度**（portal 既有，不变）：设计目标 → 仿真结果 → 自动化测试 →
台架验证 → 现场验证 → 已发布/运行 → 已知缺陷/延期。

**阶梯 B · 工程过程证据**（本轮新增，只用于支撑 agentic 主张）：

```text
B1 约束注册表条目   constraints.json 里有规则 + severity + sdd_ref
B2 spec / plan 留痕  docs/superpowers/specs 与 plans/ 存在对应文档
B3 会话内强制执行    hooks 已安装（SessionStart prime + PreToolUse hook）
B4 阻断被验证        check --staged 对越界改动实际返回 exit 2
```

**互推禁令**：B 级证据只说明「工程过程被约束」，不提升任何产品能力声明；A 级证据不因
B 存在而自动升级。页面徽章分两色族：A 用现有徽章改名后的 `ag-status--*`，B 用新增
`ag-proc--*` 样式（两者前缀与 §4.4 的类改名一致）。

## 9. 验证

1. `portal/tests/test_agentic_pages.py` 全绿：九节存在、EN/ZH section id 集合相等、
   五产品族 `data-family` 集合不变、产品族嵌套（sunsdrmobile 在 sunmrrc 内、iOS/Android 在
   direct-usb 内）、SVG 含 `title`/`desc`、`details`/`summary` 配对、本地资源存在、id 唯一。
2. 新增断言：`thesis` 节含主张句；`ontology` 节含「概念 → 消费方」表且每行含规则 ID；
   禁句清单含「由 Agent 写成」类表述。
3. 全站术语普查：**逐个显式列出站点目录并带尾斜杠**（`grep -Rn PAT portal/ mrrc/ …`）。
   实测 macOS BSD grep 的 `-r` 与 `-R` **都**不进入符号链接子站，从 `.` 扫会漏掉全部子站却报干净
   （假绿）；裸符号链接名作参数同样返回 0，带尾斜杠才生效。据此确认无残留
   「Built Through Forward Deployed Engineering」；`FDE` 仅以历史环节/术语条目形式出现。
4. 链接检查：各站 `fde.html` 引用全部改尽；重定向路径拼写与 §4.1 一致；`nginx -t` 通过。
5. 数字一致性：全站不再存在第二处版本 / 测试数声明（§8.2 规则 2）。
6. 视觉回归：1280 / 390 视口检查 Hero、锚点导航换行、宽表横向滚动；键盘操作
   `details` 并确认 `aria-expanded` 更新。
7. CSS 改名后无孤儿类：`grep -o 'ag-[a-z-]*' *.html zh/*.html` 的集合 ⊆
   `css/agentic.css` 的类选择器集合，且 portal 内 `grep -R "fde-"` 归零。
8. 本地 HTTP 冒烟 + `lens_diagnostics mode=all` 无阻塞错误。
9. 部署：各站 `deploy.sh` 逐个跑（先 portal，再子站）；`portal/deploy.sh` 的
   `REQUIRED_FILES` 若含 `fde.html` 需同步为 `agentic.html`。
10. 部署后线上抽查：`/fde.html` 返回 301 → `/agentic.html`；各子站旧路径同理。

## 10. 范围外与已知风险

* **不做**：OWL/RDF/JSON-LD/SHACL/三元组库/自动推理；新框架或构建系统；重写各产品 SDD；
  修复内容研究中暴露的产品实现缺陷（如 FT710Mobile P0）；页面运行时抓项目指标。
* **软链曾指向失效路径**：`website/mrrc` 原指 `/Users/cheenle/UHRR/MRRC/website`（该路径已不存在），
  真实仓库在 `/Users/cheenle/HAM/mrrc`。已重指向并把 MRRC 纳入本轮。
  教训：软链断裂不等于仓库丢失，下轮起普查前先 `readlink` + `ls` 目标父目录。
* **MRRC 的 FDE 页不做重写**：`mrrc/website/fde.html` 是 748 行的独立 Tailwind 设计，与 portal
  的 octen 组件体系不同源。本轮只做改名、导航术语与 §8.2 数字口径；套 §5 九节模板另立一轮。
* **`engineering.html` 与总纲的重叠**：内外环描述在两页都出现。约定：总纲只保留一步概括 +
  跳转，环的细节（含 `Specify → … → Update SDD` 的解释段）以 `engineering.html` 为权威。
* **叙事风险**：Agentic Engineering 是当下热词，页面容易滑向行业通稿。防线＝§3 口径红线 +
  §6.3「每行必须可点开」+ §8.3 禁止互推。

## 11. 分批执行顺序

| 批次 | 内容 | 可独立发布 |
| --- | --- | --- |
| B0 | 测试先行：`test_agentic_pages.py` 契约（含 §9.2 新断言），先红后绿 | 否 |
| B1 | `portal/fde.html` → `agentic.html` + `zh/`（用 `git mv` 保留文件历史）；`css/fde.css` → `agentic.css`（类前缀 `.fde-` → `.ag-` 机械重命名）；导航与 `global-nav.js` | 是 |
| B2 | `portal/engineering.html` + `zh/engineering.html` 重定位为机制分册；`index.html` 方法论节重写 | 是 |
| B3 | `nginx/vlsc.net.conf` 四条 301 + `nginx -t` | 与 B1 同批发布 |
| B3.5 | `mrrc`：软链重指向 + `fde.html → agentic.html`（EN/ZH）+ 23 文件导航术语 + §8.2 数字口径 + 两条 301 | 是 |
| B4 | `mrrc_modern` / `mrrc_ft710`：`fde.html → agentic.html`（套 §5.2 字段、按 §8.2 删数字）+ 术语层 + 301 | 是 |
| B5 | `efhw` / `sunmrrc` / `SunsdrMobile` / `mrrc_ft8`：术语层 + 各加一节「分工与资产」 | 是 |
| B6 | `CLAUDE.md` 更新（事实单一来源规则、符号链接普查约定、新 URL 结构）+ `sitemap.xml` / `make_sitemap.py` + 全站复查 | 是 |

B1 与 B3 必须同批发布，否则旧链接 404。每批独立 commit。
