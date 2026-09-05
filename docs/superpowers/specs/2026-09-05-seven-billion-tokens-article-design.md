# 《Seven Billion Tokens, One Field Incident》— 端到端 Agentic Engineering 长文 + 全站数字校正

- 日期：2026-09-05
- 类型：portal/blog 长文（EN + zh）＋ 门户数字校正
- 归属仓库：`/Users/cheenle/HAM/website`（portal 为真实目录，非 symlink）
- 叙事骨架：**C 台账先行**（用户已选定）
- 交付形式：`portal/blog/<slug>/`（用户已选定）

---

## 1. 目的

给"要用 AI 做业务 / 要用 agent 改变自身能力"的人一篇**可复核**的端到端叙事：从一个真实业务诉求（用一根 USB 线替代 Yaesu SCU-LAN10），到最终交付、使用与持续优化，中间那套机器（Harness × Loop × Living SDD）到底做了什么、花了什么、拦住了什么、以及**哪些事情人没有交出去**。

文章本身必须满足它自己所描述的标准：每个数字带溯源与局限，每个断言标明认识论类型，全过程可复现。

## 2. 核心命题

> **执行可以委托，判断不能。**
> 让 agent 花掉七十亿 token 而不出事，靠的不是模型更强，而是：约束可被机器读取、每次声明带溯源、事故被固化成规则、以及人保留 Intent / Boundaries / Judgment 三样东西。

三条支撑论断（均对应站内已有口径，不新造品牌）：

1. **账单的形状就是 harness 的形状。** 7.0B token 里 95.2% 是 cache-read —— 每一轮都重新加载契约。"本体在 agent 打字之前被加载"在账单上可见。
2. **一条链是可复现的。** 现场事故 → SDD 裁决 → 机器可读约束 → 编辑落地前被拦截。这条链能跑出 `exit 2`。
3. **两条阶梯不相交。** 过程约束（B1–B4）永远不提升产品成熟度（A 级）；52 条约束不会让一块 PCB 少一次台架验证。

## 3. 全站口径红线（逐条自检）

| # | 红线 | 本文如何遵守 |
|---|---|---|
| R1 | **绝不声称某个产品族是 AI / agent 建造的** | 全文只说"agent 在内环执行"，产品成熟度单独分级；`playbook` 节明确写"过程证据不等于产品成熟度" |
| R2 | **无 `.agents/skills/sdd-guardian/` 的仓库不得描述 pre-edit gate** | 只有 `mrrc_ft710`(17) / `mrrc_modern`(21) / `ft8`(14) 可称 gate；MRRC、sunsdr、efhw 明确写"无约束注册表，因此不声称拦截门" |
| R3 | **FDE 留在 Lineage 内，不得重新提升为顶层品牌** | FDE 只作为外环 Echo→Delta→Product 出现；顶层品牌是 Agentic Engineering / 智能体工程 |
| R4 | **中文术语**：智能体工程（禁用"代理式工程"）；FDE = 前沿部署工程 | zh 版逐词校验，契约测试断言禁句不出现 |
| R5 | **事实只有一个主人**：跨项目可比数字归 `/agentic.html#evidence` | 本文引用台账并链接；本文新增的 token 台账**写入本文自己的 `references` 节并标注 census 日期**，不散落到子站 |
| R6 | **每条声明带最小证据记录** | `Claim · Source artifact · Version/commit · Environment · Verification method · Result · Limitations · Date` |
| R7 | **不夸大测量** | 估算值（iFlow ~234M）与未记录值（Hermes）必须显式标注为估算/缺失，不并入"已记录"合计 |

## 4. 台账（census 2026-09-05，本文第 1 节的数据源）

### 4.1 已记录（7 个 harness，语义已逐工具校正）

| 工具 | tokens | 轮次 | 会话 | 溯源文件 | 语义要点 |
|---|---|---|---|---|---|
| Claude Code | 3,129,411,481 | 21,648 | 194 | `~/.claude/projects/**/*.jsonl` → `message.usage` | Anthropic 四桶互斥可加：`input/output/cache_read/cache_creation` |
| Pi | 1,625,562,962 | 8,719 | 60 | `~/.pi/agent/sessions/**/*.jsonl` → `usage.totalTokens` | **必须用 `totalTokens`**；`input` 不含 `cacheRead`；另记 `cost` |
| Kimi Code | 1,201,837,537 | 9,769 | 229 | `~/.kimi-code/sessions/**/wire.jsonl` → `usage.record` | 仅取 `usageScope=="turn"`；`inputOther` 为非缓存输入 |
| Codex | 547,796,667 | 717 | 116 | `~/.codex/{sessions,archived_sessions}/**/*.jsonl` → `token_count.info.total_token_usage` | **`cached_input_tokens` 是 `input_tokens` 的子集**，不可另加 |
| MuleRun | 471,558,325 | 181 | 181 | `~/.mulerun/agent-data/opencode/opencode/opencode.db` → `session.tokens_*` | 含 `tokens_reasoning` |
| Cursor | 27,079,705 | 217 | 96 | `~/Library/Application Support/Cursor/User/globalStorage/state.vscdb` → `cursorDiskKV` `bubbleId:*` | **Qoder 是严格子集（0 条独有），已去重** |
| opencode | 4,190,890 | 6 | 6 | `~/.local/share/opencode/opencode.db` → `session.tokens_*` | 与 MuleRun 会话 ID 零重叠 |
| **小计** | **7,007,437,567** | **41,257** | **882** | | |

### 4.2 未记录 / 估算（不得并入 4.1 合计）

| 工具 | 处置 | 依据 | 局限 |
|---|---|---|---|
| iFlow | **~234,247,399（估算）** | 195 份 jsonl / 63,602 条记录 / 843,290,639 字符 ÷ 3.6 | `usage.input_tokens`/`output_tokens` **全部为 0**，工具未记录；区间 187M(÷4.5)–281M(÷3.0)；37,202 轮 assistant 为实测 |
| Hermes | **未记录** | `~/.hermes/state.db`：292 会话 / 9,121 消息 / 4,336 工具调用 | `messages.token_count` 列 9,121 行全为 0；存量文本 14,975,356 字符 ≈ 4.2M token 仅为**地板值**（不含每轮重发的 ~36KB system prompt 与工具 schema） |
| Qoder | **0（已去重）** | 588 个 bubble 全部与 Cursor 共享 key，独有 token = 0 | Cursor 分支，导入而非独立产生 |
| Cursor ai-tracking | **0** | `~/.cursor/ai-tracking/ai-code-tracking.db` 6 张表 5 张空 | 未启用 |

### 4.3 合计与结构

- **已记录：7,007,437,567 tokens / 41,257 轮 / 882 会话**
- **含估算与未记录工具：~7,241,684,966 tokens / 87,580 次交互 / 1,359 会话**
- **fresh（非 cache-read）：336,661,475 = 4.8%**；**cache-read：6,670,776,092 = 95.2%**；模型输出：30,061,161
- **Pi 记录了成本：$15.1135 / 1,625,562,962 tokens = $9.30 per billion**（`cost.total` 与各分量之和一致，不重复相加）
- 时间跨度：**2025-10-20（iFlow 最早）→ 2026-09-05**

### 4.4 按仓库（跨全部工具，已合并别名 `mrrc`→`MRRC`、`mrrc_ic7300`→`mrrc_modern`）

| 仓库 | tokens |
|---|---|
| ft8 | 1,875,258,566 |
| mrrc_ft710 | 1,275,611,389 |
| mrrc_modern | 1,260,804,213 |
| MRRC | 1,150,197,250 |
| website | 819,343,926 |
| sunsdr | 64,490,898 |
| pskreporter | 54,409,498 |
| efhw-knowledge | 45,949,584 |
| wfview | 23,459,822 |
| 未归属 / 其他 | 410,832,716 |
| **无线电生态小计** | **6,491,655,826** |
| **按仓库可归属合计** | **6,980,357,862** |

**校验**：6,980,357,862 + Cursor 27,079,705 = 7,007,437,567（与 §4.1 小计精确相等）。Cursor 的 `state.vscdb` 不记录 cwd，因此其 27,079,705 tokens **无法按仓库归属** —— 这是本表的一个明确局限，文中须写明。

归属方法：Claude Code / Codex / Pi 用记录内 `cwd`；Kimi 用 `wd_<name>_<hash>` 工作区名；MuleRun/opencode 用 `session.directory`；iFlow 用项目目录 slug。**从父目录（如 `/Users/cheenle`）发起的会话落入"未归属"，因此按仓库拆分是下限。**

### 4.5 模型与 API 源（多源实证）

| harness | 记录到的模型 |
|---|---|
| Claude Code | deepseek-v4-flash(18,184)、qwen3.8-flash(1,077)、glm-5.2(800)、deepseek-v4-pro(715)、qwen3.8-max(438)、qwen3.8-max-0902(434) |
| Pi | deepseek-v4-flash(61)、deepseek-v4-pro(28)、gpt-5.6(26)、qwen3.8-flash(6)、deepseek-v4-flash-vision-exp(1)；provider = deepseek(90) / mulerun(26) / new-provider(6) |
| Kimi Code | kimi-code/k3(5,463)、kimi-for-coding(2,097)、k3-256k(1,903)、kimi-for-coding-highspeed(306) |
| Codex | gpt-5.5(28)、gpt-5.6-sol(28)、gpt-5.3-codex(4)、deepseek-v4-flash(4)；provider = **api111(106)** / openai(6) / deepseek(4) |
| MuleRun | gpt-5.5(160)、deepseek-v4-flash-free(16)、qwen3.6-plus(2)、gemini-3-pro-preview(1)、gemini-3.1-pro-preview(1)、glm-5.1(1) |
| opencode | big-pickle(3)、gpt-5.5(1)、qwen3.6-plus-free(1) |
| iFlow | glm-5(17,925)、qwen3-coder-plus(6,706)、kimi-k2.5(6,500)、minimax-m2.5(4,315)、glm-4.7(1,080)、iFlow-ROME-30BA3B(673) |
| Hermes | deepseek-v4-flash(230 会话)、deepseek-v4-pro(45)、gpt-5.5(11)、google/gemma-4-12b(1)、google/gemma-4-e4b(1)；**277 份会话文件 base_url 全部为 `https://api.deepseek.com/v1`** |

**表述纪律**：模型标识符是 harness 自己记录的 **fact**；"这些请求实际由哪家 API 服务"是 **inference**（Codex 的 `model_provider='api111'` 与 Pi 的 `provider='mulerun'` 说明存在自建/第三方路由，但我未抓包验证终点）。文中不得把 inference 写成 fact。

### 4.6 Hermes 的三个来源（本文唯一的"非交互"证据）

`~/.hermes/state.db` → `sessions.source`：**cron 201 / cli 68 / weixin 23**。即：agent 曾被定时任务驱动，也曾从微信被驱动。跨度 2026-05-11 → 2026-07-24。这是"agent 不只是交互式编码工具"的直接证据，同时它的 token 未被记录 —— 一个诚实的缺口。

### 4.7 测量自纠错（本文第 2 节的素材，必须如实写）

首轮统计得 5,380,941,148，**错在两个方向**：

- **漏计**：Pi(+1.63B)、MuleRun(+471.6M)、Cursor(+27.1M)、opencode(+4.2M) —— 因为只扫了 `~/.claude`、`~/.codex`、`~/.kimi-code`、`~/.iflow`。
- **重复计**：Codex 把 `cached_input_tokens`（`input_tokens` 的子集）另加，虚增 511.9M；Pi 把 `totalTokens` 与其分量一起求和，虚增 ~1.63B；Qoder 与 Cursor 共享全部 bubble key，差点再虚增 1.5M。

**发现方式**：Codex 自己的 `state_5.sqlite → threads.tokens_used = 546,858,767` 与我 JSONL 解析的 1,058,625,328 不一致。一个"看起来被独立数据源佐证"的数字，实际是在报告语义错误。这条写进文章，作为 R6 的自证。

---

## 5. 文章结构（12 节，每节一个 `id`，契约测试锁死）

### 5.0 双标题与三卷结构（2026-09-05 增补）

**双标题**：
- EN：`Seven Billion Tokens, One Field Incident`（保留 —— 台账先行的具体钩子）
- ZH：`格物致知 —— Agentic AI 的思考`

**slug 不变**（`seven-billion-tokens`），因此 canonical / hreflang / sitemap / 测试常量中的 URL 全部不受影响。ZH 标题只出现在 ZH 页的 `<title>`、`<h1>` 与 JSON-LD `headline` 上；**EN 页不得出现 `格物致知` 四字**（契约测试 `test_titles_are_bilingual` 断言 `assertNotIn`）—— 两个框架不互相稀释，EN 读者得具体钩子，ZH 读者得经典框架，两版结构完全相同。

**三卷分组**：13 个 section id 不变，但按《大学》「致知在格物，物格而后知至」与阳明「知行合一」重组为三卷。卷标记用 `<div class="volume" data-volume="...">` 包裹（**不用 `<section>`**，否则 `section_ids` 集合会多出 3 个 id，破坏 `REQUIRED_SECTIONS` 的精确相等断言）。`references` 作为附录留在三卷之外 —— 它是溯源清单，不是乐章。

| 卷 | `data-volume` | 卷题 | 含 section id | 为什么是这一卷 |
|---|---|---|---|---|
| 卷一 | `gewu` | 格物 · Investigating Things | `ledger` `floor` `numbers-lie` `intent` `before` | 到现场去问那个东西：解析本机会话库、跑测试、读 CHANGELOG；以及「不格物」的两种反面 —— 裸调模型的 iFlow 时代（阳明格竹）与把字段相加却不问语义的我自己（5.38B 错值） |
| 卷二 | `zhizhi` | 致知 · Extending Knowledge | `machine` `chain` `scale` | 物格而后知至：一套机器把观测变成契约；一条链把事故变成 `AD-014` 再变成 `cat-no-dn`；52 条约束的积累到本体的「豁然贯通」 |
| 卷三 | `zhixing` | 知行合一 · Unity of Knowing and Acting | `delivery` `drift` `human` `playbook` | 知而不行只是未知：交付是知识遇到世界；漂移是「知」停止行动的失败模式；人保留的签字权是委托的边界 |
| 附录 | —（不包裹） | Provenance | `references` | 溯源清单 |

**卷内必含的具体对应**（写进正文，不是装饰）：

- 卷一 `before` 节必含一个 `data-claim-type="analogy"` 的 claim-box：**阳明格竹七日而病** ↔ iFlow 时代 37,202 轮 / 6 个模型 / 零注册表。对着竹子枯坐不是格物，在循环里调模型也不是。
- 卷一 `numbers-lie` 节必含：**致知在格物，不在台账** —— 我自己的 5,380,941,148 是一次「不格物」，字段相加而未问语义。
- 卷二 `chain` 节必含：**物格而后知至** 的四步链（电台的实际行为 → SDD 裁决 → 机器可读约束 → 运行时拦截）。
- 卷二 `scale` 节必含：朱子「今日格一物，明日格一物，积习既多，然后脱然自有贯通处」↔ 17→21→14 条约束的积累，与 `agentic.html` 原话「本体只在证据跨产品边界出现之后才被固化」。
- 卷三 `human` 节必含：**知而不行，只是未知** ↔ 一条不会 block 的约束等于没有这条约束（`PreToolUse → hook`，退出码 2）。

**表述纪律**：经典引文只作为 `analogy` 或 `thesis` 出现，**不得**作为 `fact`。凡引用需给出出处（《大学》、朱熹《大学章句》补传、王阳明《传习录》）。不得把古典概念写成"中国早就有了 agentic engineering"这类目的论断言 —— 那是 R1 的近亲，同样禁止。

### 5.1 节清单

必需 section id 集合（13 个，与三卷分组正交）：
`ledger, floor, numbers-lie, intent, before, machine, chain, scale, delivery, drift, human, playbook, references`

| # | id | 内容要点 | 主要 `data-claim-type` |
|---|---|---|---|
| 0 | hero | 标题 + 副标 + 元信息（BG1SB · Sep 5, 2026 · ~30 min read） | — |
| 1 | `ledger` | **开场即台账**：§4.1 表 + 三个结构数字（95.2% cache-read / $9.30 per B / 87,580 次交互）。每行带溯源文件路径与语义要点。附最小证据记录模板实例 | fact |
| 2 | `floor` | 为什么这是**下限**：iFlow 记 0（估算 234M）、Hermes 未记录、Qoder 去重、Cursor ai-tracking 空、Claude Code 留存仅到 08-05 而 MRRC 始于 03-06、父目录会话未归属 | fact |
| 3 | `numbers-lie` | 数字本身不构成证据。引 engineering.html 六种"看起来像速度的失败模式"（文档替代验证 / 测试数替代证据 / AI 生成替代评审 / 发布替代现场安全 / SDD 停止接收反馈 / 设计目标当成"完成"）。**并交代我自己的 5.38B→7.01B 自纠错（§4.7）** | fact + thesis |
| 4 | `intent` | 业务诉求：FT-710 用户要remote，原厂 SCU-LAN10 是专有配件；诉求是"一根已有的 USB 线"。Echo 观测：USB serial/audio 行为、FT4222 SPI 可出真频谱 | fact |
| 5 | `before` | **对照组**：iFlow 时代 2025-10-20→2026-04-16，185 会话 / 37,202 轮 / 6 个模型 / **零 harness**。其中 `-Users-cheenle-UHRR-MRRC` 13,219 轮、`UHRR_mac` 15,674 轮、pskreporter 3,193 轮。对照成熟度阶梯：1 Ad hoc → 2 Repeatable | fact + inference |
| 6 | `machine` | 一套机器：外层约束 harness（Business WHY·WHO·SUCCESS / Technical HOW·BOUNDARIES·PROOF / Product DELIVERABLE·ACCEPTANCE·REUSE）× 内层执行 harness（Human+AI Agents → Repository+SDD → Tools+Diagnostics → Tests+Review → Deployment → Field Telemetry）；嵌套双环；Living SDD 8 态；最小证据记录 8 字段 | fact |
| 7 | `chain` | **全文证明点**：`DN;` 在 FT-710 上不是 DNR 查询而是 VFO 每次下移 ~20Hz → 每 2 秒轮询造成**实机频漂事故（V1.2）** → SDD 裁决 AD-014 → 约束 `cat-no-dn`（severity=block, scope+patterns）→ `SessionStart→prime` / `PreToolUse(Edit\|Write)→hook` → 复现命令与真实输出（`sdd_context.py check probe_b4_tmp.py` → `[BLOCK] cat-no-dn ...` → `echo $?` = **2**） | fact |
| 8 | `scale` | 台账 × 机器对齐：§4.4 按仓库表映射到 FDE 阶段与 harness 层；52 条约束（17/21/14）随事故生长；**`mrrc_modern` 与 `mrrc_ft710` 共享同一个 initial commit `9403e2e`** —— 谱系在 git 里是字面事实；**`ft8` 的首个提交 `d4a7a32` 同时引入 AGENTS.md + SDD + sdd-guardian** —— 机器被继承而非重新学习；commit `2bc3d30` "SDD V2.23 — record issues I8-I11, expand sdd-guardian harness to 21 rules" | fact + inference |
| 9 | `delivery` | 交付与使用：版本/测试实况（§6.1）；部署脚本机制（校验→打包→远端备份→scp→解包→权限→reload nginx）；**三条安全规则**：远端 heredoc 必须引号化、`tar -x` 不删除、备份按站瘦身轮转（`rsync --exclude downloads/videos`，只留 3 份）、回滚只还自己那一目录；共享 DocumentRoot 禁止整根 `rm -rf`/`chown -R` | fact |
| 10 | `drift` | **自我修正**：我今天现场实跑抓到的漂移（§6）。台账也会过时 → 所以台账需要 owner、census 日期与契约测试。如实说明 Modern 那 1 个 `test_macos_launcher` loader error 是 macOS 上的**导入失败**（Windows 启动器测试），非产品缺陷 | fact |
| 11 | `human` | 人保留 Intent / Boundaries / Judgment；四件不可压缩：Hardware(PCB/bench)、RF safety(PTT)、Live stations、Publication；**FT710Mobile 有未解决的 P0 PTT 安全问题**，服务端自动化测试与其他客户端结果都不能关闭它；EFHW V3.0 只有 B2（spec/plan trail），无台架验证前不得声称 bench/field-verified；**两条阶梯不相交**（A 产品成熟度 / B1–B4 过程约束） | thesis |
| 12 | `playbook` | 给要用 AI 做业务的人的 7 步可迁移做法 + 成熟度 1–5 自评 + engineering.html 的 7 条评审清单 | thesis + analogy |
| 13 | `references` | 完整溯源清单：每个数字的来源路径 / 命令 / 日期；站内链接（`/agentic.html`、`/engineering.html`、五个产品族）；标准引用（Stanford Ontology 101、W3C PROV-O、SOSA/SSN、SKOS、Time、WoT TD、ETSI SAREF、QUDT） | fact |

### 5.2 断言分类纪律

沿用 connections 一文的 `.claim-box[data-claim-type]` 四分类：`fact`（可复核，须给来源）/ `inference`（我的推论）/ `analogy`（类比）/ `thesis`（主张）。**四种类型都必须出现**，契约测试断言。凡 §4.5 表述纪律涉及的"模型标识符 vs 实际 API 终点"，必须分别标 fact 与 inference。

### 5.3 页面骨架（与 connections 一文完全同构）

`<article class="blog-article">` → `.blog-breadcrumb` → `.article-language` → `.blog-header`（`.blog-cat-badge` + `h1` + `.blog-subtitle` + `.blog-meta` + `.blog-tags`）→ `<nav class="blog-toc" id="blog-toc">`（JS 自动填充）→ `.blog-content` → 各 `<section id>` → 作者块 → Related reading。

head 必含：`meta description/keywords/author=BG1SB`、`og:type=article` 全套、`canonical`、三条 `hreflang`（en / zh-CN / x-default）、JSON-LD `Article`（`articleSection: "Intelligence"`、`datePublished/dateModified: 2026-09-05`）。

样式：`../../css/octen.css?v=6` + `../../css/blog.css?v=1` + 本文自带 `article.css?v=1`（`.claim-box` 系列**不在** `blog.css` 里，必须随文携带）。四色规则从 connections 的 `article.css` 原样移植：fact `#22c55e` / inference `#22d3ee` / analogy `#f59e0b` / thesis `#a78bfa`，每型两条规则（`border-left-color` 与 `.claim-label` 的 `color`），基类 `.claim-box` 与 `.claim-label` 一并移植。

## 6. Part 2 — 全站数字校正

### 6.1 现场实测（2026-09-05，本机 macOS）

| 项目 | 权威实测 | `/agentic.html#evidence` 台账（census 09-02） | `portal/index.html` | 处置 |
|---|---|---|---|---|
| MRRC FT-710 | `Ran 439 tests ... OK`（unittest discover） | v1.8.1 · 439 tests ✅ | **V1.0 · 180+ tests** ❌ | index.html 改为与台账一致 |
| MRRC Modern | `Ran 682 tests`，1 个 loader error（`test_macos_launcher`，macOS 导入失败）；SDD README 显示 **v1.12.1** | v1.12.0 · 633 tests ❌ | **v1.10.1 · 593 tests** ❌ | 台账与 index.html 一并更新为 v1.12.1 · 682 tests，并标注该 loader error 的环境局限 |
| MRRC-FT8 | `937 tests collected`（pytest） | 未给测试数 | **v0.1.0 · 40 tests** ❌ | index.html 更新；台账是否补测试数**待确认**（见 §8 Q1） |
| MRRC Universal | 仓库 179 commits，2026-03-06 → 2026-09-04；有 `AGENTS.md`，**无** `.agents/` | Released / operational ✅ | **V5.6.5 · 280+ commits** ⚠️ | commits 数与仓库不符，**查清权威源前不盲改**（见 §8 Q2） |
| SunMRRC / SunsdrMobile | `sunsdr` 仓 67 commits（2026-06-21 → 2026-09-03），仓库同时含两者 | Field evidence by scenario ✅ | **V1.0 · 40+ commits** / **V1.0 · 3 commits** ⚠️ | 仓库边界 ≠ 产品边界，**查清前不盲改**（见 §8 Q3） |

### 6.2 改动清单

1. `portal/index.html` + `portal/zh/index.html`：项目卡数字与台账对齐；凡台账未拥有的可比数字，改为链接台账而非自报（R5）。
2. `portal/agentic.html` + `portal/zh/agentic.html`：`#evidence` 台账 Modern 行 633→682、v1.12.0→v1.12.1；census 日期 2026-09-02 → 2026-09-05；`#families` 内 Modern 卡片同步。
3. `portal/engineering.html` + `portal/zh/engineering.html`：`#sdd` 节 "633 automated tests do not prove..." 与 `#evidence` 族表 "FT-710: 439 tests; Modern: 633 tests" 同步为 682。
4. 跨站普查：按 CLAUDE.md 规矩显式列出站点目录（每个带尾斜杠）grep 自报可比数字，确认子站未违反 R5。

```bash
SITES="portal/ mrrc/ mrrc_ft710/ mrrc_modern/ sunmrrc/ SunsdrMobile/ mrrc_ft8/ efhw/"
grep -Rn "439 tests\|633 tests\|593 tests\|180+ tests\|40 tests\|v1\.10\.1\|v1\.12\.0" $SITES
```

5. `portal/sitemap.xml`：由 `make_sitemap.py` 重新生成（该脚本 `os.walk`，会自动收录新 blog 目录）；**不得**手工编辑后遗留不一致。

### 6.3 部署边界（不得违反）

`make_sitemap.py`、`tests/`、`.pytest_cache`、`IMG_*` 已被 `portal/deploy.sh` 排除，且脚本内含对历史误发布的远端 `rm -rf`。**本次不得改动 deploy.sh 的排除清单**；新文章目录必须落在 `blog/` 下以被正常打包。

## 7. 验证

### 7.1 新增契约测试 `portal/tests/test_seven_billion_tokens_article.py`

对齐 `test_connections_article.py` 的写法，断言：

1. EN 与 ZH 两个文件都存在且可解析。
2. `REQUIRED_SECTIONS` 13 个 id 全部存在（EN/ZH 各自）。
3. `REQUIRED_CLAIM_TYPES = {fact, inference, analogy, thesis}` 四种都至少出现一次。
4. **禁句断言（R1/R3/R4）**：EN 不得出现 `built by AI` / `built by agents` / `AI-built`；ZH 不得出现 `代理式工程`；两版都不得把 FDE 作为顶层品牌表述。
5. **gate 归属断言（R2）**：文中出现 `pre-edit gate` / `编辑前拦截` 的句子，其上下文必须属于 ft710 / modern / ft8 三者之一；不得与 MRRC / SunMRRC / EFHW 同句。
6. **数字一致性断言**：文中出现的 `7,007,437,567`、`95.2%`、`336,661,475`、`$15.11`、`439`、`682`、`937`、`52` 必须与台账常量一致；`439/682/937` 三数不得出现旧值 `180+/593/40`。
7. **估算标注断言（R7）**：`234,247,399` 与 Hermes 相关句子必须带"估算/未记录"标记词。
8. `blog/index.html` 含指向本文的卡片，`data-cat="intelligence"`，且卡片日期与 JSON-LD `datePublished` 一致。
9. `sitemap.xml` 含 EN 与 zh 两条 URL。
10. head 必含三条 hreflang + canonical + JSON-LD Article。
11. 所有站内链接可解析（沿用 connections 测试的链接检查逻辑）。

### 7.2 既有测试不得变红

`portal/tests/` 现有 4 个测试文件（agentic / engineering / connections / sitemap）必须继续通过。§6.2 改动 `agentic.html` 与 `engineering.html` 的数字后，需同步检查 `test_agentic_pages.py` / `test_engineering_pages.py` 是否硬编码了 633/439 等值 —— **若硬编码，先改测试再改页面，并把这次修改单独 commit（红→绿可追溯）**。

### 7.3 人工验证

- 本地 `python3 -m http.server` 打开 EN/ZH，检查 TOC 自动生成、claim-box 四色、移动端宽度、语言切换互链。
- `grep` 复查 R1–R7 逐条。

## 8. 待确认问题（每条都带默认处置，不阻塞执行）

- **Q1**：台账（`/agentic.html#evidence`）当前**不给** FT8 测试数。实测 937 collected 是否要补进台账？补则要定义口径（collected ≠ passed；且 ft8 用 pytest 而非 unittest）。
  **默认处置**：**不补进台账**，只在本文 `drift` 节以 "937 collected (pytest, 2026-09-05)" 的形式出现并标注 collected≠passed；同时把 index.html 的 "40 tests" 改为与本文一致的口径。若你要补台账，需要先跑一次 `pytest -q` 拿到 passed 数再定。
- **Q2**：index.html 写 MRRC "280+ commits"，但 `/Users/cheenle/HAM/MRRC` 只有 179 条（2026-03-06 起）。是否存在更早的仓库/迁移前历史？
  **默认处置**：**不盲改**。B5 普查时用 `git log --all --oneline | wc -l`、`git count-objects`、以及 iFlow 时代 `-Users-cheenle-UHRR-MRRC`（13,219 轮）作为线索判断是否有迁移前历史；查不清就在 index.html 保留原值但去掉精确数字改为不可比表述，或在台账标注局限。**绝不允许我为了让数字好看而选一个来源。**
- **Q3**：`sunsdr` 一个仓库同时承载 SunMRRC 与 SunsdrMobile（67 commits），index.html 却分别写 "40+ commits" 与 "3 commits"。仓库边界 ≠ 产品边界。
  **默认处置**：**不盲改**。改为按台账口径表述（"Field evidence by scenario"），commit 数这种仓库级指标不再按产品拆分自报；若必须保留数字，则标注"census 日期 + 仓库路径"，让口径可见。
- **Q4**：`~/.mulerun/vendor/mulerouter` 与 Codex 的 `model_provider='api111'` 指向自建/第三方路由。文中是否点名？
  **默认处置**：**不点名供应商**。只写 fact（`model_provider` / `provider` 字段的字面值与计数），把"存在多源路由"写成 inference，不推断具体供应商或终点 —— 我没有抓包验证。

## 9. 范围外

- 不改任何子站的产品架构文案、SDD 内容、约束注册表。
- 不动 `deploy.sh`（除 §6.3 明确禁止的改动外，本次完全不碰）。
- 不做 nginx 配置变更。
- 不部署 —— 本次只到"本地验证通过 + 分仓提交"，部署由用户另行触发。
- 不修复 Modern 的 `test_macos_launcher` loader error（属产品仓库问题，非本次范围；文中如实标注为环境局限）。
- 不新增 blog 类目 chip（复用已存在的 `intelligence`）。

## 10. 分批执行顺序

| 批次 | 内容 | 交付判据 |
|---|---|---|
| B0 | 契约测试先行：新建 `test_seven_billion_tokens_article.py`，**先让它红** | 测试运行失败，失败原因正是"文件尚不存在" |
| B1 | EN 文章 `portal/blog/seven-billion-tokens/index.html` + `article.css` | §7.1 中 EN 相关断言转绿 |
| B2 | ZH 文章 `.../zh/index.html` | EN/ZH 结构对等断言转绿；R4 术语校验通过 |
| B3 | `blog/index.html` 卡片 + `make_sitemap.py` 重生成 sitemap | 卡片与 sitemap 断言转绿 |
| B4 | Part 2 数字校正（§6.2 第 1–3 项），**先改被硬编码的既有测试** | 既有 4 个测试 + 新测试全绿 |
| B5 | 跨站普查（§6.2 第 4 项）+ R1–R7 逐条 grep 复查 | 普查无违规命中 |
| B6 | 分仓提交（website 仓一次或多次 scoped commit） | `git log` 可读，红测试单独一次 commit |

## 11. 文件清单

**新增**
- `portal/blog/seven-billion-tokens/index.html`
- `portal/blog/seven-billion-tokens/article.css`
- `portal/blog/seven-billion-tokens/zh/index.html`
- `portal/tests/test_seven_billion_tokens_article.py`

**修改**
- `portal/blog/index.html`（卡片）
- `portal/sitemap.xml`（重生成）
- `portal/index.html` + `portal/zh/index.html`（数字校正）
- `portal/agentic.html` + `portal/zh/agentic.html`（台账 + families）
- `portal/engineering.html` + `portal/zh/engineering.html`（633 → 682）
- 可能：`portal/tests/test_agentic_pages.py`、`portal/tests/test_engineering_pages.py`（若硬编码旧数字）

**不发布**（已被 deploy.sh 排除）：`portal/tests/`、`portal/make_sitemap.py`、`.pytest_cache`
