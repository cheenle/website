# “链接为王”双语科学随笔设计规格

## 1. 目标

将用户原稿《链接为王：从神经元到文明级智能的递归升级》改写为一篇证据驱动的双语科学随笔，并发布到 VLSC Blog。

文章保留“链接是智能演化的重要元原理”这一核心判断，但必须明确区分已证实事实、合理推论、工程类比和作者判断。不得把神经科学隐喻写成跨尺度机制等同，也不得把公司演示、未来计划或未经核验报道写成既成科学事实。

## 2. 发布形态

### 2.1 页面

- 英文：`portal/blog/connections-recursive-intelligence/index.html`
- 中文：`portal/blog/connections-recursive-intelligence/zh/index.html`
- 文章专用样式：`portal/blog/connections-recursive-intelligence/article.css`
- 静态契约测试：`portal/tests/test_connections_article.py`
- Blog 首页入口：修改 `portal/blog/index.html`

### 2.2 标题

中文：

> 链接为王：从神经元到文明级智能的递归升级

中文副标题：

> 一篇关于连接组、人工智能与文明级网络的证据型思想实验

英文：

> Connections Rule: Recursive Intelligence from Neurons to Civilization

英文副标题：

> An evidence-led thought experiment about connectomes, artificial intelligence, and civilization-scale networks

### 2.3 篇幅

- 中文正文约 6000–8000 字。
- 英文正文约 3500–4500 词。
- 中英文采用相同证据骨架和章节结构，但分别按各自语言习惯写作，不逐句硬译。

## 3. 论证类型

页面必须显式展示四类标签，并在重要段落或事实框中使用：

- `fact` / 已证实事实：一手论文、临床登记或官方技术资料直接支持。
- `inference` / 合理推论：由事实导出的解释，但不是实验直接结论。
- `analogy` / 工程类比：跨尺度解释工具，不主张物理机制等同。
- `thesis` / 作者判断：“链接为王”等价值判断、综合判断和未来展望。

英文使用 `data-claim-type="fact|inference|analogy|thesis"`；中文复用相同机器值。

## 4. 核心证据边界

### 4.1 神经元原理

原稿的“触达—整合—链接”改为更准确的“触达—整合—传递—反馈”：

- 神经元通过化学突触、电突触和感觉输入接收信号。
- 膜电位、细胞动力学与局部回路共同参与整合。
- 动作电位和递质释放是主要传递机制，但不是全部神经通信机制。
- 网络反馈、可塑性、神经调质、身体和环境共同影响功能。

文章可以把该过程作为智能系统类比，但不得声称单个神经元的工作模式完整解释文明或 AI。

### 4.2 果蝇连接组

采用 2024 年 Nature 论文《Neuronal wiring diagram of an adult brain》的数据：成年雌性果蝇全脑连接图包含 139,255 个神经元和约 5×10⁷ 个化学突触。

采用 2024 年 Nature 论文《A Drosophila computational brain model reveals sensorimotor processing》的限定结论：研究者根据连接结构和预测的神经递质身份建立漏积分—发放模型，对部分进食与梳理回路作出可实验检验的预测，并通过光遗传和行为实验验证其中部分预测。

不得写成：

- “仅加载连接图就自然涌现完整自主行为。”
- “连接组证明结构等于功能。”
- “数字果蝇完整复现真实果蝇智能。”

更准确的结论：

> 连接结构约束功能，并能为部分完整感知—运动转换提供可检验模型；但突触权重、神经调质、细胞动力学、身体和环境仍不可缺失。

NeuroMechFly 用于说明神经控制、身体和物理环境必须进入同一闭环，不用来宣称已经完成全脑自主仿真。

### 4.3 神经形态和存内推理

- Intel Loihi 2：描述为事件驱动、脉冲神经网络导向的神经形态研究芯片。
- Tianjic：描述为支持神经科学导向和计算机科学导向模型的混合架构研究芯片。
- IBM NorthPole：描述为受脑启发、将计算和存储在芯片上深度融合的神经推理架构。不得把 NorthPole 与 Loihi 2 归为机制完全相同的脉冲神经形态芯片。

硬件能效数字必须直接来自论文或官方资料，并标明特定工艺、模型和基准环境；正文不使用脱离条件的泛化倍数。

### 4.4 AI 案例

保留：

- AlphaFold：从序列和进化信息预测蛋白质结构的代表案例。
- RAG：模型参数与外部可检索知识源之间的动态链接。
- CICERO：语言模型与战略推理结合的多智能体协作案例。
- 世界模型：区分预测生成、环境动力学建模和行动规划。
- RT-2 原始论文：视觉—语言—行动链接的具身案例。
- 算力互联：作为分布式计算工程类比，不称其为生物神经纤维的机制复制。

删除或降级：

- 不依赖无法稳定核验的 GPT-5、Gemini 2 功能陈述。
- 不把 Sora 等视频模型直接描述为已经理解物理因果的世界模型。
- 不把 AutoGPT 作为成熟多智能体科学证据。

### 4.5 脑机接口

采用 Nature 2021 脑控书写通信论文，以及 Neuralink PRIME 早期可行性研究登记 NCT06429735。

Neuralink 只描述公开支持的外部设备控制研究目标和已公开数字设备/光标控制演示。不得声称人体试验已经完成机械臂控制，除非实施阶段找到正式结果的一手来源。

## 5. 认知姿态章节

原稿“神学 → 哲学 → 科学”的线性高低叙事改为三种建立世界关系模型的认知姿态：

1. 启示与传统：建立意义、规范和共同体关系。
2. 哲学与逻辑：推演概念关系、前提和可能模型。
3. 科学与工程：通过可观测、可证伪、可重复的方法约束模型，并将可靠关系工程化。

必须明确：三者不是严格年代顺序，也不是简单优劣排名；它们今天仍然并存。文章只比较知识主张的验证方式，不评判文化或信仰价值。

## 6. 正文结构

英文和中文使用相同章节 ID：

```text
premise
neuron
connectome
epistemology
civilization
limits
recursion
references
```

### 6.1 `premise` — 链接是必要条件，但不是充分条件

提出限定后的中心论点：智能依赖有结构、有权重、有时序、可塑且嵌入身体和环境的链接。更多链接并不自动意味着更多智能。

### 6.2 `neuron` — 触达、整合、传递、反馈

解释神经元与局部回路，用类比图连接到人工系统，但明确机制差异。

### 6.3 `connectome` — 从连接图到行为预测

按 FlyWire → 全脑计算模型 → NeuroMechFly 的证据阶梯展开。核心是“结构产生可检验约束”，不是“结构独自解释全部功能”。

### 6.4 `epistemology` — 三种关系模型姿态

按启示/传统、哲学/逻辑、科学/工程并列讨论。

### 6.5 `civilization` — 文明尺度的链接递归

使用六层矩阵：

1. 传输链接：通信、互联网、算力互联。
2. 表征链接：深度学习、多模态、RAG。
3. 协作链接：多智能体与人机协作。
4. 因果链接：世界模型与规划。
5. 行动链接：具身智能与控制系统。
6. 生物链接：脑机接口与神经形态计算。

每层列出已实现能力、代表证据和未解决边界。

### 6.6 `limits` — 链接为什么仍不够

覆盖：噪声和错误传播、脆弱性和单点失效、平台权力、群体极化、多智能体不自动产生集体理性、不同“链接”不是同一物理机制。提出链接质量、协议、反馈、治理和可验证性决定系统结果。

### 6.7 `recursion` — 递归闭环与作者宣言

保留宏大闭环，但标记为作者判断：

```text
自然形成神经链接
→ 意识研究链接
→ 文明建造外部链接网络
→ 网络辅助研究和改变自身
→ 人类开始治理链接的演化方向
```

结尾建议：

> 链接是智能的母语之一；治理链接，可能是文明下一阶段的共同工程。

不得把“宇宙意识”描述为科学预测或必然结果。

### 6.8 `references` — 参考文献

数字引用与文末条目一一对应。英文和中文使用相同编号、DOI/官方 URL 和访问边界。

## 7. 核心一手来源

1. Dorkenwald et al. “Neuronal wiring diagram of an adult brain.” Nature (2024). DOI: `10.1038/s41586-024-07558-y`.
2. Shiu et al. “A Drosophila computational brain model reveals sensorimotor processing.” Nature (2024). DOI: `10.1038/s41586-024-07763-9`.
3. Lobato-Rios et al. “NeuroMechFly, a neuromechanical model of adult Drosophila melanogaster.” Nature Methods (2022). DOI: `10.1038/s41592-022-01466-7`.
4. Modha et al. “Neural inference at the frontier of energy, space, and time.” Science (2023). DOI: `10.1126/science.adh1174`.
5. Pei et al. “Towards artificial general intelligence with hybrid Tianjic chip architecture.” Nature (2019). DOI: `10.1038/s41586-019-1424-8`.
6. Jumper et al. “Highly accurate protein structure prediction with AlphaFold.” Nature (2021). DOI: `10.1038/s41586-021-03819-2`.
7. Lewis et al. “Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks.” arXiv: `2005.11401` / NeurIPS 2020.
8. Bakhtin et al. “Human-level play in the game of Diplomacy by combining language models with strategic reasoning.” Science (2022). DOI: `10.1126/science.ade9097`.
9. Driess et al. “PaLM-E: An Embodied Multimodal Language Model.” arXiv: `2303.03378`, and Brohan et al. “RT-2: Vision-Language-Action Models Transfer Web Knowledge to Robotic Control.” arXiv: `2307.15818`. The article uses them only to support documented vision/language/action integration, not general physical reasoning.
10. Willett et al. “High-performance brain-to-text communication via handwriting.” Nature (2021). DOI: `10.1038/s41586-021-03506-2`.
11. ClinicalTrials.gov `NCT06429735`, Neuralink PRIME early feasibility study.
12. Intel Loihi 2 official technology brief; used only for documented architecture and specifications.

No source is cited merely because it repeats a desired conclusion. Secondary summaries may aid discovery but do not support the final factual claims when a primary source exists.

## 8. 视觉与交互

使用现有 `blog.css` 和文章局部 `article.css`。不修改全局 Blog CSS。

新增组件：

- 四类 claim badge 和 callout。
- 可访问的“触达—整合—传递—反馈”内联 SVG。
- 神经元到文明网络的尺度阶梯。
- 六类文明链接矩阵，窄屏可横向滚动。
- 递归闭环 SVG。
- “必要但不充分”约束框。
- 引用列表和 DOI 链接样式。

所有 SVG 必须有唯一 `title` 和 `desc`。视觉不能只依赖颜色表达。支持窄屏和 `prefers-reduced-motion`。

文章沿用 Blog 自动目录脚本和 `global-nav.js`，不增加新的外部运行时库。

## 9. SEO 与结构化数据

两页均包含：

- 独立 title、description、keywords。
- `og:type=article`、标题、描述、URL 和站点名。
- canonical 指向本语言页面。
- `hreflang=en`、`hreflang=zh-CN` 和 `x-default`。
- JSON-LD Article：headline、description、author、publisher、datePublished、dateModified、keywords、articleSection、mainEntityOfPage。
- 语言切换链接。

文章分类为 `Intelligence / 智能系统`。

## 10. Blog 首页集成

`portal/blog/index.html` 增加：

- `Intelligence` 分类按钮。
- 新文章卡片，路径指向英文文章。
- Blog JSON-LD `blogPost` 新条目。

当前 Blog 首页有用户未提交修改。实现必须在隔离 worktree 中提交；合并前仅暂存该目标文件，合并后恢复用户修改。生产发布不得用本地首页覆盖线上首页，而应备份线上文件并执行精确、幂等的分类/卡片/JSON-LD 插入，或在确认线上与目标本地文件完全一致后才允许完整覆盖。

## 11. 测试与验收

创建 `portal/tests/test_connections_article.py`，验证：

- 中英文文章存在且固定章节 ID 一致。
- 四类 `data-claim-type` 均出现。
- 139,255 和约 50 million/5×10⁷ 等连接组关键事实在两种语言中一致，并且只出现在相关语境。
- 禁止出现“连接组本身足以产生完整自主智能”“Neuralink 人体已控制机械臂”等已否定强断言。
- 中英文引用编号和 DOI/官方 URL 集合一致。
- 所有正文引用编号在参考文献中存在，参考文献没有未使用编号。
- section ID 和 HTML ID 唯一。
- SVG 均有 `title` 和 `desc`。
- 本地资源存在。
- canonical、hreflang、Open Graph 和 JSON-LD 完整。
- Blog 首页存在 Intelligence 分类和文章入口。

实施完成后运行：契约测试、现有 Portal 测试、LSP、`git diff --check`、本地 HTTP smoke test。人工检查桌面和约 390px 布局、表格滚动、引用跳转、目录和中英文切换。

## 12. 发布与回滚

选择性发布：

- 英文文章目录。
- 中文文章子目录。
- 文章专用 CSS。
- Blog 首页仅发布本任务相关的幂等补丁。

服务器上先备份所有目标文件。运行 `nginx -t` 后重载。生产验证包括文章文件字节比较、关键事实、参考文献、语言切换、Blog 首页入口和 HTTP 响应。报告备份路径用于回滚。
