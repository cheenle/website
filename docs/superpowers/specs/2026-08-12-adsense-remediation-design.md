# AdSense 整改设计文档（VLSC Website）

> 日期：2026-08-12
> 目标：通过补充技术博客、信任信号页面、SEO 架构整改，提升 www.vlsc.net 的 AdSense 审核通过率。
> 状态：已获用户批准（阶段 1 与阶段 2）。

## 背景与决策

| 决策点 | 结论 |
|---|---|
| 博客位置 | 门户下 `/blog/`（集中式知识库，文章链接到相关项目站） |
| 语言范围 | 博客纯英文；信任页（About/Contact/Privacy）中英双语 |
| 创作方式 | Claude 起草 HTML 文章 → 用户审阅补充个人 HAM 实操经历/截图/踩坑过程 |
| 联系方式 | GitHub（cheenle）+ 预留邮箱占位符 `contact@vlsc.net` |
| 博客技术方案 | 方案 A：纯手写 HTML 文章，无构建步骤，复用 octen.css + 新增 blog.css |

### 已核验事实

- 现有 `portal/` 无任何 About / Contact / Privacy / blog 页面（find 全空）。
- Demo 端口实测（2026-08-12）：
  - `radio.vlsc.net:8877`（SunsdrMobile demo）— **不可达**（HTTP 000）
  - `radio.vlsc.net:8889`（SunMRRC demo）— **不可达**（HTTP 000）
  - `radio.vlsc.net:9988`（MRRC-FT8 demo）— 可达（HTTP 302）
- 工作目录非 git 仓库（`git rev-parse` 失败），设计文档不提交 git。
- 全局导航 `js/global-nav.js` 有多个副本（portal/mrrc/sunmrrc 等各站一份），修改需逐个同步。

## A. 博客文件结构

```
portal/
├── blog/
│   ├── index.html              # 博客列表页（分类过滤 + 文章卡片 + tag 云）
│   └── <slug>/
│       └── index.html          # 文章页（自包含，含全部 SEO meta）
├── css/
│   ├── octen.css               # 复用
│   └── blog.css                # 新增：文章排版、代码块、TOC、作者盒、相关文章
├── about.html                  # About（EN）
├── contact.html                # Contact（EN）
├── privacy.html                # Privacy Policy（EN）
├── zh/
│   ├── about.html
│   ├── contact.html
│   └── privacy.html            # 中文镜像
├── sitemap.xml                 # 生成产物
├── robots.txt
└── make_sitemap.py             # 极简脚本：扫 blog/ 生成 sitemap.xml
```

- 文章 URL：`/blog/<slug>/`，语义化 slug。
- 文章页复用 `global-nav.js`（`<body data-site="portal">`），顶部导航自动注入。

## B. 单篇文章页模板

1. **SEO 头部**：自定义 `<title>`、`meta description`、Open Graph、JSON-LD `Article` schema
   （headline、author=BG1SB、datePublished、dateModified、keywords、articleSection、publisher）。
2. **面包屑**：Home › Blog › 分类 › 标题。
3. **文章头**：分类徽章 + 标题 + 副标题 + 元信息行（BG1SB · 日期 · 预估阅读时长 · 标签）。
4. **正文**：语义化 `<article>`，h2/h3 层级、`<code>`/`<pre>` 代码块、`<figure>` 插图
   （预留实测截图位）、表格、`blockquote` 技巧提示。
5. **TOC**：内联 JS 从 h2/h3 自动生成锚点目录（无构建）。
6. **作者盒**：BG1SB / 呼号 / GitHub。
7. **相关文章 + 上一篇/下一篇**。
8. **交叉链接**：正文链接到对应项目站（`/mrrc_ft710/`、`/efhw/` 等）。

## C. 博客列表页

- 简介区 + 文章卡片（分类、日期、摘要、阅读时长）。
- 客户端分类过滤（纯 JS）+ 标签云。
- JSON-LD `Blog` schema。
- 置顶/精选文章位。

## D. 信任页（中英双语）

- **about.html**：VLSC 简介、BG1SB 呼号、技术背景、项目群创建初衷、各项目一句话说明、
  GitHub / CQ 社群链接。
- **contact.html**：GitHub（`github.com/cheenle`）+ 预留邮箱 `contact@vlsc.net`（占位符）
  + 按项目分流到 GitHub Issues 的指引。
- **privacy.html**：明确声明——网站本身无 Cookie 无追踪；**第三方广告（Google AdSense）
  可能使用 Cookie**；nginx 访问日志收集标准 IP/UA；链接到 Google 隐私政策；修改日期。

## E. 导航改动

- 门户 navbar（EN + zh）：加 **Blog** 链接。
- 门户 footer（EN + zh）：加 Blog / About / Contact / Privacy 链接。
- `global-nav.js`：共享顶部导航加 **Blog** 链接；同步更新各站副本。

## F. 20 篇选题清单（映射 6 个项目）

**MRRC**
1. Universal HF remote control with Hamlib/rigctld —— 架构总览
2. CAT protocols under the hood：USB 串口上的 rigctld 与控制
3. 选择正确的电台接口：USB 串口 vs 网络（SCU-LAN10）

**MRRC FT-710**
4. **只用一根 USB 线远程控制 Yaesu FT-710**（FT4222 SPI，绕开 SCU-LAN10）★指南点名
5. FT-710 SPI 频谱数据流是怎么工作的
6. 瀑布流管线：从 FT4222 到浏览器像素

**EFHW**
7. **基于 ESP32-S3 的伺服天线调谐器硬件设计** ★指南点名
8. Fuchs ATU V3.0 调谐算法：匹配网络搜索策略
9. 为什么自动调谐器在野外优于手动 EFHW 调谐

**SunMRRC / SunSDR2 DX**
10. UDP IQ 流式传输与服务端解调（FastAPI + WebSocket）
11. 实时 512-bin FFT 瀑布流：从 IQ 样本到像素
12. 用 Hilbert 变换做 TX SSB 语音调制

**音频 / 编解码**
13. **短波远程控制中的 Opus vs PCM：延迟与质量权衡** ★指南点名
14. WebSocket 上的低延迟音频传输实践

**SunsdrMobile**
15. 用 SwiftUI 构建原生 iOS 电台客户端：架构
16. 从 Web 客户端到原生 iOS App：共享服务端而非 UI

**部署 / 实战**
17. 24/7 远程电台自托管：nginx、HTTPS 与 NAT 穿透
18. 在树莓派上部署电台远程服务器
19. 我的 HF 远程电台间实测报告（纯个人经验）
20. 疑难排错：我踩过的最难坑（协议、音频卡顿、固件）

## G. SEO / 死链 / 索引

- **死链整改**：8877、8889 两个 Demo 已死 → 改为状态徽章"Offline"并链接到对应部署文档；
  保留活的 9988。消除空链接。
- **sitemap.xml**：门户页 + 全部博客文章（+ 子站根路径）。由 `make_sitemap.py` 自动生成。
- **robots.txt**：允许抓取 + 指向 sitemap。
- **内部链接**：博客 ↔ 项目站双向链接（正文链接项目站；门户 footer 加博客入口）。

## H. 排期（两阶段）

- **阶段 1（本次完成，可部署）**：博客基建（列表页 + 模板 + blog.css）+ **3 篇旗舰文章**
  （选题 4、7、13，即指南点名三篇）+ 信任页双语 + 导航/footer + sitemap/robots + 死链整改。
  用户审阅 3 篇并补经历，作为后续 17 篇质量样板。
- **阶段 2（持续）**：按用户补经历速度，逐批起草剩余 17 篇 → 用户审阅补充 → 上线后
  在 Search Console 提交 sitemap → **等待 2-4 周**再考虑重新申请 AdSense。

## 验收标准（阶段 1）

- `/blog/`、`/blog/<slug>/` 三篇文章、`/about.html`、`/contact.html`、`/privacy.html`
  （EN + zh）全部可访问，无 404。
- 全站导航可见 Blog 入口；footer 可见 About/Contact/Privacy。
- 死链 Demo 整改完成：8877/8889 不再直接指向死端口。
- `sitemap.xml` 与 `robots.txt` 就位，`make_sitemap.py` 可重建。
- 三篇文章 JSON-LD 校验通过（Google Rich Results 语法正确）。
