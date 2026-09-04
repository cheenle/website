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
