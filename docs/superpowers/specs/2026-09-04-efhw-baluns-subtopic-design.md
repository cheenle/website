# EFHW 巴伦子专题页 — 设计规格

日期：2026-09-04 · 站点：`efhw/` · 语言：EN + CN · 方案：1（单页四段式）

## 1. 目标与定位

在 EFHW 产品站新增巴伦子专题页，覆盖类型、制作、最佳实践、工程优化。

定位是差异化互补。MRRC 研究站 `mrrc/efhw/index.html` 已拥有该主题的理论与实测
（49:1 vs 64:1 Transformer Design、Turns Ratio Showdown 2:14 vs 3:21、Ferrite Core Selection、
Winding Methods & W8JI Measurement Corrections、Common-Mode Choke In-Depth Analysis、
49:1 Real Performance & Loss Measurements、Back-to-Back Measurement Myth），另有独立深页
`mrrc/efhw/t200-2-guide.html`（837 行）。EFHW 首页 `#research` 节正把这些链过去。

本页只拥有「决策与动手」；一切“为什么”与实测数值外链，不复制。

### 归属划分

| 主题 | 拥有方 | 本页处理 |
| --- | --- | --- |
| 巴伦类型谱系、选型决策路径 | 本页 | 原创 |
| 制作工艺、失败模式、物料 | 本页 | 原创 |
| 装机最佳实践、工程优化目标 | 本页 | 原创 + 出处 |
| 49:1 vs 64:1 论证、匝比之争 | MRRC 研究站 | 一句话结论 + 链接 |
| 磁芯对比实测（Fair-Rite vs FT240-43） | MRRC 研究站 | 选型建议 + 链接 |
| 插损 / 温升等本站未亲测的数值 | 无 | 留 `—`，不得猜（§4） |
| 跨项目可比数字（版本、测试数、发布状态） | portal 证据账本 | 本页不得自述 |

## 2. 文件与 URL 契约

- `efhw/baluns.html` → <https://www.vlsc.net/efhw/baluns.html>
- `efhw/zh/baluns.html` → <https://www.vlsc.net/efhw/zh/baluns.html>

EFHW 站此前只有 `index.html` 与 `zh/index.html`，本页**开出子页先例**（改动面见 §5）。

零新增样式与脚本文件：复用 `css/octen.css?v=6`、`css/efhw.css`（emerald 10b981）、
`js/global-nav.js`（附带 AdSense 注入与全站导航）。页面专属样式追加进既有 `efhw.css`
并升版本号，两页同步。

禁止引入 portal 的 `ag-*` 类 —— EFHW 样式表无这些定义，用了会静默失效（任务 13 同类坑）。

结构约定：单一 `h1`；`hreflang` en / zh-CN 互链；沿用 octen 深色变量；
Font Awesome 6.4 图标；正文不用 emoji。

## 3. 信息架构

sticky 页内锚点条（5 锚）→ 01 → 02 → 03 → 04 → Evidence & Sources → 回链区。

### 01 Taxonomy 类型学

速查表，每类一行：器件 / 一句话原理 / 典型频段 / 适合 / **别用**。
家族宽于 EFHW 单相视角，至少含：49:1 与 64:1 电压变换器（unun）、Guanella 型电流巴伦、
1:1 电流巴伦 + 冷地、CMC 共模磁环、LTA 分布式变换器，以及作为对照的偶极子方案。
表下每类一张小卡，只写结构与适用边界，不含实测数值。

### 02 Selection 选型决策

纯 HTML 决策树：功率等级 → 波段数 → 是否长期户外 → 预算 → 磁芯与材料
（Ni-Zn / Mn-Zn / 粉铁）。每个叶子给一句“为什么”并链 MRRC 对应章。
决策树用嵌套列表实现，不引入 JS。

### 03 Build 制作工艺

编号步骤，每步配失败模式：匝线张力与均匀性、匝间电容控制、分区绕法、
浸漆与真空灌注、防水装配、连接器与冷地排、toroid 装配应力。
含物料清单（BOM）表。

### 04 Field & Optimization

装机最佳实践（冷地、共模陷阱位置、counterpoise 取舍、馈线走线）+
工程优化目标表：插损、温升、磁通密度饱和裕度、自谐振点排布、功率降额。
明确写“什么时候该放弃巴伦改用偶极子”。

### Evidence & Sources

页尾固定节，汇总本页全部出处；MRRC 站内深页逐条列出。

## 4. 事实与引用纪律（本页最高风险项）

每条量化说法必须带两级标签之一：

- `[C]` 工程通识且有出处 → 内联引用原始文献（Guanella 1948、Guggenbühll 1958、
  W8JI、Chew《RF Transmission Line Transformers》、PA3HHO），并链 MRRC 对应章
- `[M]` 本站实测 → **仅当仓库内存在原始数据文件时才允许写**，并在脚注给出数据路径

没有数据支撑的行一律填破折号并注明“未测，见 /mrrc/efhw/”。
禁止为凑表格而生成看似专业的数值（如随手写“插入损耗 0.2 dB”）。
本页不得自述跨项目可比数字（版本、测试数、发布状态），需要时链 portal 证据账本。
不得声称本产品系列由 AI/Agent 建造。

## 5. 改动面（本页开出 EFHW 子页先例）

| 文件 | 改动 |
| --- | --- |
| `efhw/baluns.html`、`efhw/zh/baluns.html` | 新建（EN + CN） |
| `efhw/index.html`、`efhw/zh/index.html` | 导航加“Baluns / 巴伦”入口与返回链；`#research` 节补一句分工说明（理论与实测在 MRRC，选型与动手在站内本页） |
| `efhw/css/efhw.css` | 追加本页组件样式，版本号 `efhw.css?v=1` → `v=2`（两页同步升版） |
| `efhw/deploy.sh` | required-files 校验补两个新页 |
| `portal/make_sitemap.py` | 收录两个新 URL（脚本生成，禁止手编 `sitemap.xml`） |

nginx 无需改动：`location /efhw/` 已用 alias 覆盖整个目录。

## 6. 验证关卡（发布前硬性步骤，不得跳过）

1. 两页 div 配平、单一 h1、锚点 id 双语一一对应
2. CN 页英文残留扫描（连续英文句段）—— 防 #36 复发
3. 每个 `[M]` 行都能指到仓库内原始数据文件，否则必须是破折号
4. 断链检查：页内全部站内/跨站链接逐个 200（含 `../mrrc/efhw/…`）
5. 本地 `python3 -m http.server` 冒烟
6. **人眼与键盘关卡**：窄屏断点布局、Tab 顺序可达性、暗色对比度 —— 由用户在真机核验；
   未经核验前不得声称视觉正确（对应上一轮 3b 的教训）
7. 部署：`cd efhw && ./deploy.sh`（脚本内含 nginx reload）；随后线上 curl 回验两个新 URL

## 7. 范围外（YAGNI）

- 不新建 CSS/JS 文件，不引入框架，不做构建步骤
- 不做交互式计算器（方案 3 的取舍，留待有真实需求时再加）
- 不复制 MRRC 的实测数值与图表；不做 17 章理论的镜像
- 不为本页新建测试框架（EFHW 站无 pytest 基础设施）；核验用第 6 节脚本清单

## 8. 未决问题

- 页面标题与 slug 用 `baluns.html`（复数）还是 `balun-guide.html`：倾向复数，短且与导航词一致
- 是否给本页配产品图/绕线过程图（`efhw/images/` 现有素材是否够用，需实施时盘点；无图则以 SVG 示意图代替，不占位假图）

## 9. 实施前发现：sitemap 生成器缺陷（阻塞 §5 的 sitemap 步骤）

实测（2026-09-04）：`HEAD` == 工作区，`portal/sitemap.xml` = 26 个 URL，其中 `agentic.html`
仅 2 条（portal 自身的 EN/CN），`fde.html` 0 条；`portal/make_sitemap.py` 中**不存在** `SITE_PAGES`。

根因：`find_html(ROOT)` 的 `ROOT` 是 **portal 目录本身**，子站只通过 `SUBSITES` 列表加入**根路径**
（`/efhw/`），因此**任何子站的二级页都不可能被子站之外的机制收录**。
后果：此前手工补录的六站 `agentic.html` / `engineering.html` 共 6 条**已回归丢失** ——
因为改的是产物 `sitemap.xml` 而非生成器，一次重新生成就冲掉了（正是计划里我自己警告过的陷阱）。

因此 §5 的 sitemap 步骤修正为：**先修生成器**（遍历 `$SITES` 各站目录、或显式维护子页清单），
再 `python3 portal/make_sitemap.py` 重生成，验证六站页 + 本页两个新 URL 均在列；
**禁止手编 `sitemap.xml`**。§6 关卡补一条：`sitemap.xml` 的 URL 集合必须是
`make_sitemap.py` 的输出（重跑一次应字节相同），否则视为手工改动混入。
