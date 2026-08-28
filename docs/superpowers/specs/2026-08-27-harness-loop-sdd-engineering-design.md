# Harness、Loop 与 SDD Engineering System 设计规格

## 1. 目标

在 VLSC Portal 中建立一个独立的双语 Engineering System 主题，并在现有 FDE 页面增加摘要入口。Engineering 是总框架，Harness、Loop 与 SDD 是三根协同支柱，用于解释五个产品族背后的工程约束、执行环境、反馈循环、设计契约与证据纪律。

本设计不改变“三条工程轨道、五个产品族”的生态口径。Harness、Loop、SDD 和 Engineering 都不是产品族。

## 2. 范围

### 2.1 新增

- `portal/engineering.html`：英文完整 Engineering System 页面。
- `portal/zh/engineering.html`：中文等价页面。
- `portal/css/engineering.css`：Engineering 页面及 FDE 摘要的专用样式。
- `portal/tests/test_engineering_pages.py`：双语结构、语义、资源和可访问性契约测试。

### 2.2 修改

- `portal/fde.html`：在 `leverage` 与 `ontology` 之间加入 Engineering System 摘要章节。
- `portal/zh/fde.html`：同步中文摘要章节。
- `portal/index.html`：导航增加 Engineering。
- `portal/zh/index.html`：导航增加“工程体系”。

### 2.3 不在范围内

- 不修改各产品子站或其 SDD。
- 不引入 JavaScript、框架、构建系统、RDF/OWL 运行时或知识图数据库。
- 不把自动化测试描述为台架或现场验证。
- 不把 AI Agent 描述为能够绕过审查、安全约束或验收的自主权威。
- 不重新定义已经批准的五产品族领域本体。

## 3. 核心定位

Engineering System 是持续产生可信产品的系统：

```text
Field Problem
     ↓
ENGINEERING SYSTEM
├── Harness：约束与可重复执行环境
├── Loop：嵌套反馈循环
└── SDD：双向 Living Contract
     ↓
Code + Tests + Evidence + Product + Reusable Assets
```

三者的职责不可互换：

- Harness 约束并承载工程执行。
- Loop 产生增量、验证和反馈。
- SDD 保存设计意图、实现事实、证据与偏差。

## 4. 信息架构

### 4.1 FDE 页面摘要

在 `leverage` 与 `ontology` 之间新增固定 ID：

```html
<section class="fde-section" id="engineering">...</section>
```

摘要只回答：

1. 为什么产品迭代能够重复执行？
2. 设计、代码、测试和现场证据如何闭环？
3. SDD 如何成为工程契约，而不是静态文档？

摘要包含 Harness、Loop、SDD 三项卡片、简化协同图、五产品族工程证据概述及独立页面 CTA。

FDE 页内锚点导航增加 `Engineering / 工程体系`。

### 4.2 独立页面

英文路径 `/engineering.html`，中文路径 `/zh/engineering.html`。两页使用相同的固定章节 ID：

```text
overview
harness
loop
sdd
integration
evidence
maturity
```

页面顺序：

1. Hero — Engineering Is the Product-Making System
2. Engineering System Overview
3. Dual-Layer Harness
4. Nested Engineering Loops
5. SDD as a Living Contract
6. Harness × Loop × SDD Integration
7. Five-Family Evidence Matrix
8. Engineering Maturity & Failure Modes
9. SDD Chapter Map / Evidence Appendices

## 5. 双层 Harness

Harness 指让工程活动可以被约束、执行、验证和重复的完整环境，不局限于 AI 编码工具或文档模板。

### 5.1 外层约束 Harness

#### Business Harness

回答“为什么做、为谁做、什么算成功”：

- 用户与现场问题
- 业务价值和范围
- 成功标准
- 法规、资源和运行限制

#### Technical Harness

回答“如何实现、如何证明正确”：

- 领域模型与架构决策
- 接口、协议与组件边界
- 性能、可靠性和安全不变量
- 部署、可观测性和恢复模型

#### Product Harness

回答“实际交付什么、成熟到什么程度”：

- 交付物与验收条件
- 版本和发布状态
- 已知问题与延期项
- 可复用资产与产品 Profile

### 5.2 内层执行 Harness

```text
Human + AI Agents
        ↓
Repository + SDD
        ↓
Tools + Diagnostics
        ↓
Tests + Review
        ↓
Deployment
        ↓
Field Telemetry + Evidence
```

约束：

1. Harness 必须让失败可见，而不是只提高生成速度。
2. 工具输出必须可追溯到代码版本和运行环境。
3. 自动化测试不能替代台架或现场验证。
4. 部署和遥测属于 Engineering。
5. Human 与 AI Agent 接受相同的规格、审查和安全边界。
6. Harness 产物可以更新 SDD，但不能自动提升证据成熟度。

## 6. 嵌套 Engineering Loop

### 6.1 外层 FDE 交付循环

```text
Echo → Delta → Product → 新的现场 Echo
```

- Echo：观察现场、采集故障、确认真实约束。
- Delta：验证最高风险假设，形成可运行垂直切片。
- Product：稳定边界、完成验收、发布并提炼复用资产。

### 6.2 内层 Engineering Loop

每个外层阶段内部运行：

```text
Specify → Implement → Test → Review → Deploy / Observe → Update SDD
    ↑                                                              ↓
    └──────────────────────── 下一轮 ──────────────────────────────┘
```

- Specify：声明目标、约束、接口、验收条件和证据要求。
- Implement：实现最小可验证增量。
- Test：执行适合当前主张的自动化、模拟、台架或现场测试。
- Review：检查规格符合性、质量、安全边界和事实口径。
- Deploy / Observe：进入运行环境并采集行为、性能和故障证据。
- Update SDD：同步决策、实现、验证状态、偏差和已知问题。

外层 Loop 决定产品风险如何降低；内层 Loop 决定每个增量如何可靠实现和验证。该模型不是瀑布流程，任何阶段都可以因新证据返回 Specify。

## 7. SDD 作为双向 Living Contract

SDD 同时表达设计方向和实现事实：

```text
Intent / Constraints / Decisions
              ↓
             SDD
              ↑
Code / Tests / Deployment / Field Evidence
```

### 7.1 状态词汇

- `planned`：已规划，尚未实现。
- `implemented`：已实现，尚未充分验证。
- `tested`：已通过明确范围的自动化或模拟测试。
- `bench-verified`：已通过实物台架验证。
- `field-verified`：已在真实运行环境验证。
- `released`：已公开发布或投入生产运行。
- `deferred`：明确延期。
- `known-issue`：已知问题，不得包装为完成。

状态不构成自动升级链。服务端测试不能替代客户端验收，测试数量不能替代实机验证，固件完成不能替代 PCB 或 RF 台架验证。

### 7.2 SDD 语义映射

Business Harness：Executive Direction、System Context、Non-functional Requirements、Use Cases、Feasibility。

Technical Harness：Subject Area / Domain Model、Architecture Decisions、Architecture Overview、Service Model、Component Model、Operational Model。

Product Harness：Project Definition、Acceptance Criteria、Version / Evidence History、Known Issues、Reusable Asset Catalog。

项目不必使用完全相同的章节编号；统一的是语义职责、状态词汇和证据字段。

### 7.3 最小证据记录

```text
Claim
Source artifact
Version / commit
Environment
Verification method
Result
Limitations
Date
```

## 8. 三者协同模型

```text
                    HARNESS
          约束、执行环境、质量门禁
                 /          \
                ↓            ↓
             LOOP ←────────→ SDD
        产生增量与反馈     保存意图与证据
                 \          /
                  ↓        ↓
        Product + Evidence + Reusable Assets
```

页面必须明确展示以下失败模式：

- Harness 没有 Loop：只有工具和规则，没有学习。
- Loop 没有 Harness：迭代快但不可重复、不可审计。
- SDD 没有现场 Loop：成为过期的事前设计。
- Loop 没有 SDD：经验停留在个人或聊天记录。
- Harness 没有 SDD：Agent、测试与部署缺乏共享语义和验收依据。

## 9. 五产品族证据矩阵

| 产品族 | Harness 重点 | Loop 突破 | SDD 作用 | Engineering 证据 |
|---|---|---|---|---|
| MRRC Universal | Hamlib、服务端状态、Web/PWA | 现场网络与状态漂移反复校准 | 固化通用电台边界 | 发布与现场运行 |
| MRRC Direct USB | USB、机型后端、客户端安全门禁 | FT-710 垂直验证到 Modern 平台化 | 提炼 Backend/Capabilities | 439/633 测试与实机验收分离 |
| SunMRRC | 抓包、DSP、媒体诊断、原生客户端 | 未知协议到 Direct-IQ 产品 | 协议、媒体、安全契约持续同步 | 服务端与客户端分别取证 |
| MRRC-FT8 | 时钟、音频、工作流状态 | 现场 QSO 周期驱动状态机演化 | 分离公开发布与 SDD V1.8 演进 | 发布与现场演进分离 |
| EFHW | 固件、传感器、舵机、RF 台架 | 测量—执行有界搜索 | 区分设计、固件、PCB、台架状态 | 当前不得越级为现场验证 |

矩阵用于展示同一 Engineering System 在不同边界下的应用，不用于产品排名。

## 10. 成熟度与反模式

页面包含 Engineering 成熟度模型：

1. Ad hoc：知识主要存在于个人操作和临时记录。
2. Repeatable：已有基础 Harness 和可重复步骤。
3. Traceable：规格、代码、测试、发布和证据可以关联。
4. Evidence-driven：成熟度主张带有来源、环境和限制。
5. Reusable：经过验证的架构、约束和资产能够跨产品迁移。

成熟度不是产品优劣排名，也不允许仅凭文档数量或测试数量升级。

反模式包括：文档代替验证、测试数量代替证据、AI 生成代替审查、发布代替现场安全、SDD 长期不回写、把设计目标写成已实现事实。

## 11. 视觉与响应式设计

- 复用 Octen 深色设计系统和现有 FDE 色彩。
- Harness 使用三层卡片与内层执行链。
- Loop 使用两个嵌套环或明确的外层/内层流程图，关系必须有文字。
- SDD 使用双向流图和状态徽章。
- Integration 使用可访问 SVG，必须包含唯一的 `title` 和 `desc`。
- 五产品族矩阵在窄屏允许横向滚动。
- 所有附录使用原生 `<details>/<summary>`。
- 移动端卡片单列，图中文字不得依赖颜色理解。
- 支持 `prefers-reduced-motion`。

## 12. 导航

以下中英文页面增加 Engineering 导航：

- Portal 首页
- FDE 页面
- Engineering 页面

英文标签为 `Engineering`，中文标签为 `工程体系`。FDE 页内锚点增加 Engineering。语言切换必须在对应页面之间切换。

## 13. 测试与验收

静态契约测试必须验证：

- 英文和中文 Engineering 页面固定章节 ID 完全一致。
- FDE 中英文页面都存在 `engineering` 摘要章节和独立页面链接。
- 外层 Business / Technical / Product Harness 与内层执行 Harness 均出现。
- 外层 FDE Loop 和内层 Engineering Loop 均出现。
- SDD 的八个状态词汇存在且中英文事实一致。
- 五个产品族在证据矩阵中各出现一次。
- 所有 ID 唯一。
- SVG 包含 `title` 和 `desc`。
- `<details>` 与 `<summary>` 数量一致。
- 本地 CSS、页面和脚本资源存在。
- 不新增 Engineering 运行时 JavaScript。

最终验证包括：契约测试、LSP、`git diff --check`、本地 HTTP smoke test、桌面/移动结构检查，以及线上发布后的文件和关键内容核验。

## 14. 发布策略

由于主工作区含有其他未提交修改，实现必须在隔离 worktree 中完成。合并时保护目标文件上的现有修改。发布采用选择性备份和上传，只部署：

- `portal/engineering.html`
- `portal/zh/engineering.html`
- `portal/css/engineering.css`
- `portal/fde.html`
- `portal/zh/fde.html`
- `portal/index.html`
- `portal/zh/index.html`

测试文件不部署。远端部署前备份对应文件，执行 `nginx -t`，重载 nginx，并验证生产文件与本地发布文件一致。
