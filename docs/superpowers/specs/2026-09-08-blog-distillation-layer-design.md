# 设计：博客 Intelligence 系列文章的提炼层（Distillation Layer）

日期：2026-09-08
状态：已获用户批准（方案一 + 组件①②③④ 全选 + 四维度并入《七十亿 token》）

## 背景与问题

博客最近三篇 Intelligence 长文（《七十亿 token 的全程拆解》《连接支配》，及已合并的
`from-intent-to-delivery`）信息密度高但缺少提炼层：无 TL;DR、无卷/节小结、
《七十亿 token》的合并把四维度提炼（工程史/认识论/经济学/责任）的框架本体丢了
（只存活了收束句与零星观点）。读者必须读满 24–28 分钟才能自行提炼。

## 目标

不读全文的人 3 分钟拿到骨架；读全文的人每卷/每节有一句话收束；
四维度提炼以「卷六」回归《七十亿 token》。

## 方案（已批准：方案一）

直接编辑 4 个 HTML（两篇 × EN/zh）+ 扩展契约测试 + 更新 blog 首页卡片摘要，
沿用现有设计系统（claim-box / volume / ag-card），CSS 新增 3 组类。

### 组件

1. **TL;DR 结论卡** `.ba-tldr` > `.ba-tldr-card`：置于 lede（7B）或 main 开头
   （Connections）之后、正文第一节之前。每条结论带 `.ba-tldr-tag`
   （复用 claim 类型语义：fact/inference/thesis）；卡底 `.ba-readpath`
   速读路径锚点 chips。
2. **卷小结** `.volume-takeaway`（7B，×5，卷六不加）／**节小结**
   `.section-takeaway`（Connections，×7）：位于卷 div 末尾／节 container 末尾，
   不新增 section id（Connections 的 REQUIRED_SECTIONS 保持不变）。
3. **卷六 · 四个维度**（7B）：`<div class="volume" data-volume="dimensions">`，
   单 section `id="four-dimensions"`，位于卷五之后、附录之前。总纲 thesis 卡 +
   四张 ag-card（工程史/认识论/经济学/责任）+ 四条纪律 thesis 卡。
   内容源：`2026-09-05-agentic-e2e-story.md`（压缩为提炼层，不重复卷一–卷五证据）。
   章节编号顺延为 16。
4. **速读路径**：TL;DR 卡内一行 chips。7B：§3 介入轮次 → §8 事故链 → §13 归因 →
   卷六；Connections：connectome → limits 六性质 → recursion。

### 文案要点

- 7B TL;DR 5 条：效率曲线真实（17.1→0.3，三曲线同向）【fact】；token 服从
  不确定性密度（~26,800 vs 136 tok/行）【fact】；同模型 ±方法差一个量级，
  模型定上限、方法定兑现比例【inference】；事故转化率 13 天/7 天【fact】；
  先问沉淀在哪里【thesis】。
- Connections TL;DR 4 条：数字果蝇证明结构产出可检验预测【fact】；连接是骨架
  非器官本体【inference】；稀缺的是连接质量六性质【inference】；治理层竞争
  【thesis】。recursion 节末尾（参考文献前）加 "If you remember three things" 收束块。
- 每卷/每节小结一句话 + 半句过渡；EN/zh 严格镜像（zh 用「」引号、CJK 排版既有规范）。

### 数值与元数据

- 阅读时长：7B ~28→~30 min（zh 约 25→27）；Connections ~24→~26（zh 同步）。
- `dateModified` → 2026-09-08（两篇文章页 JSON-LD、zh `<time>`、blog index JSON-LD）。
- blog index 两卡 `bc-excerpt` 重写为提炼后结论；标题/日期字符串不动（测试断言依赖）。

## 测试联动

- `test_seven_billion_tokens_article.py`：REQUIRED_SECTIONS + `four-dimensions`；
  VOLUMES 追加 `("dimensions", ["four-dimensions"])`（verdict 之后）；
  VOLUME_TITLES 两语言补卷六；新增断言：TL;DR 卡存在、速读路径锚点有效、
  volume-takeaway 计数 = 5。
- `test_connections_article.py`：REQUIRED_SECTIONS 不变；新增断言：TL;DR 卡存在、
  section-takeaway 计数 = 7、收束块存在。
- `from-intent-to-delivery` 测试不动（跳转壳保持无正文）。
- sitemap：URL 无变化，不动。

## 明确不做

- 不做三篇互链/系列导流（用户明确只要单篇提炼层）。
- 不动根目录 markdown 源稿（不在构建管线，方案一不要求同步）。
- 不动 `from-intent-to-delivery` 跳转壳。
- 不引入新 CSS 框架；新增类全部落在 `blog-article.css`（bump ?v=1→v=2）。

## 验收

1. `python3 -m unittest discover portal/tests -v` 全绿。
2. 4 个页面 TL;DR/小结/卷六在浏览器中层级清晰（静态检查 + 测试结构断言）。
3. 双语结构一致性由测试守护（既有镜像断言 + 新增断言）。
