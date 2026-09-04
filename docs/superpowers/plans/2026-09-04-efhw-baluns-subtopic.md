# EFHW 巴伦子专题页 实现计划

> **面向 AI 代理的工作者：** 必需子技能：superpowers:executing-plans 逐任务实现。
> 规格：`docs/superpowers/specs/2026-09-04-efhw-baluns-subtopic-design.md`

**目标：** 在 EFHW 站新增巴伦专题（类型/制作/最佳实践/工程优化），EN + CN 双语子页。

**架构：** 单页四段式（01 Taxonomy / 02 Selection / 03 Build / 04 Field & Optimization）

+ 页尾 Evidence & Sources。零新 CSS/JS 文件；复用 octen.css 组件类 + efhw.css 品牌层。

**技术栈：** 纯静态 HTML/CSS；核验用单文件 `python3` 脚本（exit code 表达结论）。

## 全局纪律（每个任务都适用，违反即返工）

1. `efhw/` 是 website 仓库里的**真实目录**（非软链），commit 进 website 仓库。
   但**禁止 `git add -A`**（工作区含你既有 WIP）。一律显式路径。
2. **一轮一个写者操作**。同一文件不得在同一轮里被 heredoc 与 write/edit 同时写
   （规格 §2 曾因此整节丢失）。
3. 每条量化说法必须带 `[C]`（工程通识 + 原始文献出处）或 `[M]`（本站实测，
   须指向仓库内原始数据文件）。**没有数据就填 `—`，禁止编造数值。**
4. 不引入 portal 的 `ag-*` 类（efhw.css 无定义，会静默失效）。
5. 站点级 grep 必须显式列目录并带尾斜杠：`SITES="portal/ mrrc/ mrrc_ft710/ mrrc_modern/ sunmrrc/ SunsdrMobile/ mrrc_ft8/ efhw/"`。
6. `git commit -F -` 之后**不得**在同一命令链里再接任何内容（会吞掉后续 heredoc）。
7. 验证脚本必须用 `sys.exit(1)` 表达失败，不能只 print。

## 文件结构

| 文件 | 职责 | 动作 |
| --- | --- | --- |
| `efhw/check_baluns.py` | 本页发布关卡（结构/双语/[M] 纪律/断链），一条命令出结论 | 新建 |
| `efhw/baluns.html` | EN 专题页（四段 + Evidence） | 新建 |
| `efhw/zh/baluns.html` | CN 专题页，结构与 EN 逐节对齐 | 新建 |
| `efhw/css/efhw.css` | 追加本页组件类，版本 v1→v2 | 修改 |
| `efhw/index.html` | 导航入口 + #research 分工句 + 页脚链 | 修改 |
| `efhw/zh/index.html` | 同上（CN，注意其链回 EN 的相对路径 `../`） | 修改 |
| `efhw/deploy.sh:22` | required-files 增加两个新页 | 修改 |
| `portal/make_sitemap.py` | **先修生成器**：收录子站二级页（规格 §9） | 修改 |

---

## 阶段 A：sitemap 生成器修复（前置，阻塞步骤 7）

### 任务 1：让生成器真正收录子站二级页

**文件：** 修改 `portal/make_sitemap.py`

+ [ ] **步骤 1：复现缺陷**

```bash
cd portal && python3 make_sitemap.py && grep -c '<loc>' sitemap.xml
# 预期 26，且 grep -c 'mrrc[a-z_0-9]*/agentic.html' → 0（子站二级页无收录）
```

+ [ ] **步骤 2：加子站二级页枚举**

在 `SUBSITES` 之后插入（`REPO = os.path.dirname(ROOT)`，ROOT 已存在）：

```python
# Second-level pages of sub-sites live outside ROOT (symlinks into their own
# repos). Enumerate them
```

> ⚠️ **本计划文件在此处被截断（写作者上下文耗尽）。任务 1 之后的内容尚未写。**
> 未完成前**不得**照此执行。续写点：任务 1 步骤 2（子站二级页枚举）→ 任务 2 EN 页 →
> 任务 3 CN 页 → 任务 4 efhw.css → 任务 5 两首页导航 → 任务 6 deploy.sh →
> 任务 7 关卡+部署+线上回验。规格 §1–§9 已完整、可直接依赖。

---

## 断点快照（2026-09-04，作者上下文耗尽）

**已完成并上线**：sitemap 生成器修复 `7d31b40`（44 URL，六站 agentic/engineering +
`mrrc_modern` 根已入列，`portal/tests/test_sitemap.py` 三用例锁死）。

**EFHW 巴伦页进度**：EN 页写到 §01 表格第 6 行（198 行，含 head/nav/subnav/hero/
label-disclosure/表头+5.5 行），**已移出部署路径**到 `.wip/efhw-baluns.en.html`
（`efhw/deploy.sh` 是 `tar czf … efhw/`，半成品留在站内会被下次部署一起推上线）。

**已落未提交**：`efhw/css/efhw.css` 追加了本页组件类（.subnav/.spec-table/.tag-c/.tag-m/
.tree/.calc），随本次 WIP 一起提交。

**续写清单**（按序，每块 ≤ ~70 行输出，否则会被截断）：

1. `.wip/efhw-baluns.en.html`：补完表格最后一行（Dipole + 1:1 对照）+ `</tbody></table>`
   + 每类小卡 → §02 决策树（`.tree` 嵌套列表，功率→波段→户外→预算→磁芯）→
   §03 制作工艺（编号步 + 每步失败模式 + BOM 表 + `<pre>` 手绘绕线示意，不放假图）→
   §04 现场实践 + 优化目标表（目标/推导式/本站值 `[M]` 或 `—`）+ 何时放弃巴伦 →
   `#evidence` → footer（照 index.html 的 .footer-grid 结构）→ 末尾 script（nav 滚动 +
   `js/global-nav.js?v=6 data-gn="1"`）
2. 从 EN 页生成 CN 页 `efhw/zh/baluns.html`：结构逐节对齐、锚点 id 相同、
   相对路径加 `../`，**中文页不得残留英文段落**（#36）
3. **CSS 版本一致性**：新页引用 `efhw.css?v=2`，但 `index.html`/`zh/index.html` 仍是
   `?v=1` —— 三处必须统一到 `v=2`，否则同一 CSS 两份缓存版本
4. `efhw/index.html` + `zh/index.html` 导航加 “Baluns / 巴伦” 入口（EN 用 `baluns.html`，
   CN 用 `../baluns.html` 注意其现有写法是 `../index.html#xxx`）+ `#research` 节分工句
5. `efhw/deploy.sh:22` required-files 补 `"baluns.html" "zh/baluns.html"`
6. `efhw/check_baluns.py`（规格 §6 七条关卡，exit code 表达结论，defect #30）
7. 跑关卡 → **用户在真机核验窄屏/键盘/对比度（§6 关卡 6，不得代签）** → 页面放回
   `efhw/` → `cd efhw && yes | ./deploy.sh`（macOS 无 `timeout`，用 `gtimeout` 或工具超时）
   → 线上 curl 回验两个新 URL + sitemap 含之

---

## 断点快照（2026-09-04，作者上下文耗尽）

已完成并上线：sitemap 生成器修复 7d31b40 —— 44 URL，六站 agentic/engineering 与
mrrc_modern 根均已入列；portal/tests/test_sitemap.py 三用例锁死"改产物不改生成器"陷阱。

EFHW 巴伦页进度：EN 页写到 01 节表格第 6 行（198 行，含 head / nav / subnav / hero /
标签纪律块 / 表头 + 5.5 行数据）。已移出部署路径至 .wip/efhw-baluns.en.html，理由：
efhw/deploy.sh 打包整个 efhw/ 目录，未闭合的表格若留在站内会被下一次部署一起推上线。

已落未提交：efhw/css/efhw.css 追加了本页组件类（subnav / spec-table / tag-c / tag-m /
tree / calc）。

续写清单（按序，每块输出不超过约 70 行，否则会被截断）：

1. 补完 .wip/efhw-baluns.en.html：表格最后一行（Dipole + 1:1 对照）与收尾标签，
   每类小卡；02 决策树（tree 嵌套列表：功率 → 波段 → 是否长期户外 → 预算 → 磁芯材料）；
   03 制作工艺（编号步骤 + 每步失败模式 + BOM 表 + pre 手绘绕线示意，不放假图）；
   04 现场实践与优化目标表（目标 / 推导式 / 本站值用 M 标签或填破折号）+
   何时该放弃巴伦改用偶极子；evidence 节；footer（照 index.html 的 footer-grid 结构）；
   末尾 script（nav 滚动 + js/global-nav.js?v=6 data-gn="1"）。
2. 由 EN 页生成 CN 页 efhw/zh/baluns.html：锚点 id 与分节顺序逐节一致，相对路径加 ../，
   中文页不得残留英文段落（缺陷 #36 的成因）。
3. CSS 版本一致性：新页引用 efhw.css?v=2，而 index.html 与 zh/index.html 仍是 v=1。
   三处必须统一到同一版本，否则同一份 CSS 存在两个缓存版本。
4. efhw/index.html 与 zh/index.html 导航加 Baluns / 巴伦 入口（EN 指 baluns.html，
   CN 指 ../baluns.html；注意 CN 现有条目写法是 ../index.html#xxx）+ 01 research 节
   补一句分工说明：理论与实测在 MRRC，选型与动手在站内本页。
5. efhw/deploy.sh 第 22 行 required-files 增加 baluns.html 与 zh/baluns.html 两项。
6. 新建 efhw/check_baluns.py 落实规格第 6 节七条关卡，结论必须走 exit code（缺陷 #30）。
7. 跑关卡 → 由用户在真机核验窄屏断点 / 键盘可达性 / 暗色对比度（规格 6 关卡 6，不得代签）
   → 页面放回 efhw/ → cd efhw && yes | ./deploy.sh → 线上 curl 回验两个新 URL 且 sitemap 含之。

操作环境提醒：macOS 无 timeout 命令（只有 gtimeout）；上一轮 portal 部署曾因
timeout: command not found 实际未执行，是线上 curl 仍显示 26 URL 才揭穿的 ——
部署结论一律以线上取异为准，不以退出码为准。

## 断点 2：EN 页已成稿（.wip/efhw-baluns.en.html，418 行）

01 表格 7 行齐 + 标签纪律块；02 决策树 Q1-Q4；03 工艺 8 步（含每步失败模式）；
03b BOM 表；04 四项现场实践 + 优化目标表（5 行全填破折号并指向研究站）+ 放弃判据；
Evidence（6 位作者名，无杜撰 URL）+ 回链区 + footer + script。
结构校验：`<tr>`/`</tr>` 各 23、单 h1、无未闭合块、`tag-m` 零使用（本页无自测值，符合 §4）。
修掉 3 处截断伤：LTA 行缺 `</tr>`、一处未闭合 calc 残块、以及两次被 awk/切片
显示误导的**假缺陷**（我据被裁剪的输出断定有错，实际文本是好的）。

余下待办：① CN 整页翻译（同锚点 id、路径加 ../、无英文残留）② efhw.css 三处版本统一
v2（新页已引用 v2，两首页仍 v1）③ 两首页导航入口 + #research 分工句
④ deploy.sh required-files ⑤ check_baluns.py 关卡 ⑥ 页面放回 efhw/ + 部署 + 线上回验。

## 断点 3：两页落地 efhw/ 并集成完成（未部署）

关卡 `python3 efhw/check_baluns.py` → OK。本轮自造并抓回的缺陷：

 1. **`bash -c` 尾部语法错误 ≠ 整条未执行**。上一轮我据 exit=2 判定"一个字都没写"并重发同一块
    heredoc，导致 CN 页出现**两个 `id="selection"`**（重复 88 行）。bash 是逐条读取执行的，
    只在读到残缺行时才报错，之前的完整命令已落盘。判据只能看文件系统。
 2. **同文件并行调用再次违规 ×3**：两首页 double edit（幸而原子回滚，未产生重复 Modern 项）、
    check_baluns.py 两次补尾造成 `IndentationError line 96`、引号修复与 grep 竞态读到旧内容。
 3. **排版修复误伤 `<script>`**：把 ASCII `"` 换成中文 `“”` 的脚本以 `<[^>]*>` 切分文本节点，
    而 `<script>` 体不是标签也不是文本节点 —— 内联 JS 的 22 处字符串字面量被改成弯引号，
    语法即坏。上线前必须把 script/style 区一并排除在中文标点替换之外。
 4. **`wc` 不给文件名会读空 stdin** 返回 `0 0 0`，被误读为"文件被清空"。
 5. 关卡自身两条误报（`ag-` 是 `tag-c` 的子串；反面引语 `"0.2 dB, trust us"` 命中 dB 断言）。
    处理方式是**收紧判据**（词边界 + 引语语境双条件），不是放宽放行。
另：文件被 HTML formatter 重排过（124→444 行），**行号不可作为定位锚点**，一律用 id/label。
