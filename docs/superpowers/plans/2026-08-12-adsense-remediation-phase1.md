# AdSense 整改阶段 1 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建成门户 `/blog/` 技术博客（3 篇旗舰文章 + 列表页 + 样式）、中英双语信任页（About/Contact/Privacy）、导航与死链整改、sitemap/robots，让 www.vlsc.net 具备 AdSense 审核所需的长内容与信任信号。

**Architecture:** 纯静态 HTML/CSS/JS，无构建步骤。文章为 `/blog/<slug>/index.html` 自包含页面，复用 `octen.css` + 新增 `blog.css`。信任页仿 `fde.html` 子页模式。`global-nav.js` 注入全局导航，共 7 份独立副本需同步。

**Tech Stack:** HTML5 语义化标签、CSS 自定义属性、原生 JS（TOC 生成、分类过滤、滚动揭示）、JSON-LD（Article/Blog schema）、Python3（`make_sitemap.py` 生成 sitemap）。

## Global Constraints

- 纯静态、无构建工具、无 npm、无框架 —— 与仓库哲学一致。
- 博客文章**纯英文**；信任页**中英双语**（`zh/` 镜像）。
- 博客文章必须预留用户补充个人 HAM 实操经历/截图的位置（`<figure>` 插图位、blockquote 经验提示）。
- 联系方式使用 GitHub `cheenle` + 预留邮箱占位 `contact@vlsc.net`。
- 站点根为 `www.vlsc.net`，门户部署在 DocumentRoot；文章正文交叉链接到对应项目站绝对路径（`/mrrc_ft710/`、`/efhw/` 等）。
- 所有页面 `<body data-site="portal">` 以启用 `global-nav.js`；页面底部加载 `<script src="js/global-nav.js?v=N" defer data-gn="1"></script>`（相对路径随目录层级变化）。
- 死链整改目标：`radio.vlsc.net:8877` 与 `:8889` 不再直接指向死端口（2026-08-12 实测不可达）；`:9988` 保留（可达，HTTP 302）。
- 无 git 仓库，不做提交；以文件落盘为完成标准。

---

## 文件结构

```
portal/
├── css/blog.css                      # 新增：文章排版、TOC、作者盒、相关文章、列表页卡片
├── blog/
│   ├── index.html                    # 新增：博客列表页
│   └── <slug>/index.html ×3          # 新增：3 篇旗舰文章
├── about.html                        # 新增（EN）
├── contact.html                      # 新增（EN）
├── privacy.html                      # 新增（EN）
├── zh/about.html                     # 新增（CN）
├── zh/contact.html                   # 新增（CN）
├── zh/privacy.html                   # 新增（CN）
├── make_sitemap.py                   # 新增：扫 blog/ 生成 sitemap.xml
├── sitemap.xml                       # 生成产物
├── robots.txt                        # 新增
├── index.html                        # 修改：navbar/footer 加链接
├── zh/index.html                     # 修改：navbar/footer 加链接
├── fde.html                          # 修改：footer 加链接
├── zh/fde.html                       # 修改：footer 加链接
└── js/global-nav.js                  # 修改：顶部导航加 Blog
```
另同步修改其余 6 份 `global-nav.js`（见 Task 8）。

---

### Task 1: `blog.css` — 博客设计系统

**Files:**
- Create: `portal/css/blog.css`

**Interfaces:**
- Consumes: `octen.css` 自定义属性（`--accent:#22d3ee`、`--bg-primary/--bg-secondary/--bg-card`、`--text-primary/--text-secondary/--text-muted`、`--border`、`--font-sans`、`--font-mono`、`--gn-h`）。
- Produces: 类名 `.blog-breadcrumb` `.blog-header` `.blog-cat-badge` `.blog-subtitle` `.blog-meta` `.blog-tags` `.blog-toc` `.blog-content` `.blog-author` `.blog-related` `.blog-prevnext` `.blog-card` `.blog-cat-filter` `.blog-list-hero` —— 供 Task 3–7 使用。

- [ ] **Step 1: 写基础排版与组件样式**

```css
/* portal/css/blog.css — VLSC Blog design system (dark octen theme) */
/* Article page layout */
.blog-article { max-width: 820px; margin: 0 auto; padding: calc(var(--gn-h) + var(--nav-h) + 48px) 2rem 96px; }
.blog-breadcrumb { font-size: 0.82rem; color: var(--text-muted); margin-bottom: 28px; }
.blog-breadcrumb a { color: var(--text-secondary); text-decoration: none; }
.blog-breadcrumb a:hover { color: var(--accent); }
.blog-header { margin-bottom: 40px; }
.blog-cat-badge { display:inline-block; font-size:0.75rem; font-weight:600; letter-spacing:0.08em;
  text-transform:uppercase; color:var(--accent); background:var(--accent-glow);
  border:1px solid var(--border-hover); padding:4px 12px; border-radius:999px; margin-bottom:16px; }
.blog-header h1 { font-size:2.4rem; font-weight:700; letter-spacing:-0.03em; line-height:1.15; margin-bottom:14px; }
.blog-subtitle { color:var(--text-secondary); font-size:1.12rem; line-height:1.6; max-width:70ch; }
.blog-meta { color:var(--text-muted); font-size:0.88rem; margin:16px 0 0; }
.blog-tags { display:flex; flex-wrap:wrap; gap:8px; list-style:none; padding:0; margin:18px 0 0; }
.blog-tags li a { font-size:0.78rem; color:var(--text-secondary); border:1px solid var(--border);
  padding:3px 10px; border-radius:999px; text-decoration:none; transition:all 0.2s; }
.blog-tags li a:hover { color:var(--accent); border-color:var(--border-hover); }

/* TOC */
.blog-toc { border:1px solid var(--border); border-radius:12px; padding:20px 24px; margin:8px 0 40px;
  background:var(--bg-card); }
.blog-toc-title { font-size:0.75rem; text-transform:uppercase; letter-spacing:0.1em; color:var(--text-muted); margin-bottom:12px; }
.blog-toc ol { list-style:none; margin:0; padding:0; }
.blog-toc li { margin:0 0 6px; }
.blog-toc a { color:var(--text-secondary); text-decoration:none; font-size:0.9rem; }
.blog-toc a:hover { color:var(--accent); }
.blog-toc .toc-h3 { padding-left:18px; }

/* Article body typography */
.blog-content { font-size:1.02rem; line-height:1.85; color:var(--text-primary); }
.blog-content h2 { font-size:1.6rem; font-weight:700; letter-spacing:-0.02em; margin:48px 0 16px;
  padding-top:8px; }
.blog-content h2::before { content:''; display:block; width:40px; height:3px; border-radius:2px;
  background:var(--accent); margin-bottom:14px; }
.blog-content h3 { font-size:1.22rem; font-weight:600; margin:32px 0 12px; }
.blog-content p { margin:0 0 20px; }
.blog-content a { color:var(--accent); text-decoration:none; }
.blog-content a:hover { text-decoration:underline; }
.blog-content strong { color:var(--text-primary); font-weight:600; }
.blog-content ul, .blog-content ol { margin:0 0 20px; padding-left:22px; }
.blog-content li { margin-bottom:8px; }
.blog-content li::marker { color:var(--accent); }
.blog-content code { font-family:var(--font-mono); font-size:0.88em; background:var(--bg-tertiary);
  border:1px solid var(--border); padding:2px 6px; border-radius:4px; color:#7dd3fc; }
.blog-content pre { background:#0a0f16; border:1px solid var(--border); border-radius:12px;
  padding:18px 20px; overflow-x:auto; margin:0 0 22px; }
.blog-content pre code { background:none; border:none; padding:0; color:#c9d1d9; font-size:0.86rem; line-height:1.7; }
.blog-content blockquote { border-left:3px solid var(--accent); background:var(--accent-glow);
  margin:24px 0; padding:14px 20px; border-radius:0 10px 10px 0; color:var(--text-secondary); }
.blog-content blockquote p { margin:0; }
.blog-content figure { margin:28px 0; }
.blog-content figure img, .blog-content figure svg { width:100%; border-radius:12px; border:1px solid var(--border); }
.blog-content figcaption { text-align:center; color:var(--text-muted); font-size:0.82rem; margin-top:10px; }
.blog-content table { width:100%; border-collapse:collapse; margin:0 0 22px; font-size:0.92rem; }
.blog-content th, .blog-content td { text-align:left; padding:10px 14px; border:1px solid var(--border); }
.blog-content th { background:var(--bg-tertiary); color:var(--text-primary); font-weight:600; }

/* Author box, related, prev/next */
.blog-author { display:flex; gap:18px; align-items:flex-start; margin:56px 0 0; padding:24px;
  border:1px solid var(--border); border-radius:14px; background:var(--bg-card); }
.blog-author .ba-icon { width:48px; height:48px; border-radius:50%; display:flex; align-items:center;
  justify-content:center; background:var(--accent-glow); color:var(--accent); font-size:1.3rem; flex-shrink:0; }
.blog-author h3 { font-size:1rem; margin:0 0 6px; }
.blog-author p { color:var(--text-secondary); font-size:0.88rem; margin:0; line-height:1.6; }
.blog-related { margin-top:40px; }
.blog-related h3 { font-size:1.05rem; margin-bottom:16px; }
.blog-related ul { list-style:none; padding:0; margin:0; display:grid; grid-template-columns:repeat(2,1fr); gap:12px; }
.blog-related li a { display:block; padding:14px 16px; border:1px solid var(--border); border-radius:10px;
  text-decoration:none; color:var(--text-primary); font-size:0.92rem; transition:all 0.2s; }
.blog-related li a:hover { border-color:var(--border-hover); color:var(--accent); transform:translateY(-2px); }
.blog-prevnext { display:flex; justify-content:space-between; gap:16px; margin-top:24px; font-size:0.9rem; }
.blog-prevnext a { color:var(--text-secondary); text-decoration:none; }
.blog-prevnext a:hover { color:var(--accent); }

/* Blog list page */
.blog-list-hero { padding: calc(var(--gn-h) + var(--nav-h) + 56px) 2rem 0; text-align:center; }
.blog-list-hero h1 { font-size:2.5rem; font-weight:700; letter-spacing:-0.03em; margin-bottom:12px; }
.blog-list-hero p { color:var(--text-secondary); max-width:640px; margin:0 auto 32px; }
.blog-cat-filter { display:flex; flex-wrap:wrap; gap:10px; justify-content:center; margin-bottom:40px; }
.blog-cat-filter button { font-size:0.82rem; color:var(--text-secondary); background:none;
  border:1px solid var(--border); border-radius:999px; padding:6px 16px; cursor:pointer; transition:all 0.2s; }
.blog-cat-filter button:hover { color:var(--accent); border-color:var(--border-hover); }
.blog-cat-filter button.is-active { color:var(--accent); border-color:var(--accent); background:var(--accent-glow); }
.blog-grid { display:grid; grid-template-columns:repeat(2,1fr); gap:24px; max-width:1080px; margin:0 auto;
  padding:0 2rem 96px; }
.blog-card { border:1px solid var(--border); border-radius:16px; padding:28px; background:var(--bg-card);
  transition:all 0.25s; display:flex; flex-direction:column; }
.blog-card:hover { transform:translateY(-3px); border-color:var(--border-hover); }
.blog-card .bc-cat { font-size:0.72rem; text-transform:uppercase; letter-spacing:0.08em; color:var(--accent); margin-bottom:10px; }
.blog-card h2 { font-size:1.25rem; font-weight:600; line-height:1.4; margin:0 0 10px; }
.blog-card h2 a { color:var(--text-primary); text-decoration:none; }
.blog-card h2 a:hover { color:var(--accent); }
.blog-card .bc-excerpt { color:var(--text-secondary); font-size:0.9rem; line-height:1.65; flex:1; margin-bottom:16px; }
.blog-card .bc-meta { color:var(--text-muted); font-size:0.8rem; }
@media (max-width:768px){
  .blog-article { padding: calc(var(--gn-h) + var(--nav-h) + 24px) 1.25rem 64px; }
  .blog-header h1 { font-size:1.8rem; }
  .blog-grid { grid-template-columns:1fr; padding:0 1.25rem 64px; }
  .blog-related ul { grid-template-columns:1fr; }
  .blog-author { flex-direction:column; }
}
```

- [ ] **Step 2: 验证 CSS 无语法错误**

Run: `node -e "new (require('css').Parser)?.(0)" 2>/dev/null || python3 - <<'EOF'
import re
css=open('/Users/cheenle/HAM/website/portal/css/blog.css').read()
# naive brace balance check
opens=css.count('{'); closes=css.count('}')
print(f'braces {opens} open / {closes} close ->', 'OK' if opens==closes else 'MISMATCH')
EOF`
Expected: `braces N open / N close -> OK`

---

### Task 2: 文章页模板样板（首篇 `ft710-usb-remote-control`）

**Files:**
- Create: `portal/blog/ft710-usb-remote-control/index.html`

**Interfaces:**
- Consumes: Task 1 的 `blog.css` 类；`global-nav.js`（页面底部相对路径 `../../js/global-nav.js`）。
- Produces: 文章页完整模板（head/SEO/JSON-LD/TOC 脚本/作者盒/相关文章结构），作为 Task 3、4 的文章页蓝本。

- [ ] **Step 1: 建立文章页完整骨架**（先建空 `blog/ft710-usb-remote-control/` 目录与完整 head/nav/JSON-LD/结构骨架，正文填充见 Step 3）

模板要点（全文内容以真实技术事实撰写，见下方"技术事实"）：
- `<title>Remote-Controlling a Yaesu FT-710 with Just a USB Cable — VLSC Blog</title>`
- `meta description`（≤160 字符，含关键词）
- canonical `https://www.vlsc.net/blog/ft710-usb-remote-control/`
- JSON-LD `Article`：headline/description/author(BG1SB)/publisher(VLSC)/datePublished/dateModified/keywords/articleSection=FT-710
- 页面结构：面包屑 → 文章头（分类徽章 FT-710 + 标题 + 副标题 + 元信息）→ TOC 容器 → `.blog-content`（≥1000 词，h2/h3）→ 作者盒 → 相关文章 → 上一篇/下一篇
- 内联 TOC 脚本：抓取 `.blog-content` 中 h2/h3，生成 `.blog-toc` 链接并加 `.toc-h3` 缩进
- 预留 `<figure>` 插图位（`<!-- PLACEHOLDER: add your test screenshot here -->`）

- [ ] **Step 2: 页面引用的 CSS/JS 相对路径核对**

Run: `ls /Users/cheenle/HAM/website/portal/blog/ft710-usb-remote-control/../../css/blog.css` 应存在
（即 `<link href="../../css/blog.css">`、`<link href="../../css/octen.css">`、`<script src="../../js/global-nav.js">` 三个相对路径均指向 portal 根下的真实文件）

- [ ] **Step 3: 撰写正文**（≥1000 词；结构见下方"技术事实"，所有数字必须来自该清单，不得虚构；正文链接 `/mrrc_ft710/`）

**技术事实（写作素材，来自 `/Users/cheenle/HAM/mrrc_ft710/` 源码与 SDD，不可改动）:**

文章 h2 结构与每节必写要点：

1. **Introduction** — 一根 USB 线同时暴露三路接口：CP210x Enhanced COM Port（CAT 命令）、FTDI FT4222 SPI 桥（频谱/瀑布流数据）、C-Media USB 音频编解码器（收发音频）。对比官方案：SCU-LAN10 需额外硬件、闭源。
2. **Anatomy of the USB port** — 三接口表格：
   | 接口 | USB 端点 | 用途 |
   |---|---|---|
   | Enhanced COM Port | CP210x UART | CAT 命令，38400 波特 |
   | FT4222 SPI Bridge | FTDI D2XX | 850 点 FFT 频谱 @~30fps |
   | USB Audio Codec | C-Media | 44.1kHz 接收 + 发送 |
3. **The FT4222 SPI bridge** — 芯片在 FT-710 主板上，通常被前面板或 SCU-LAN10 占用；项目经 D2XX 驱动按描述符 "FT4222 A" 打开。SPI 配置：`SPI_IO_SINGLE`、`SYS_CLK_24`/`CLK_DIV_64` = **375 kHz**、CPOL 高/CPHA 前沿、片选 0x01、每次读 **4096 字节**。关键点：这是**预计算的幅度 bin（已处理频谱），不是原始 IQ 样本**——FFT 由电台内部引擎完成（与 KiwiSDR/RX888 不同）。
4. **The 4096-byte scope frame** — 帧布局表（`scope_frame.py`）：
   | 偏移 | 大小 | 内容 |
   |---|---|---|
   | 0–849 | 850B | WF1 频谱（反相，`~b & 0xFF` 校正） |
   | 850–1699 | 850B | WF2 频谱（第二接收机） |
   | 1700–2899 | 1200B | 保留 |
   | 2900–3049 | 150B | 元数据块 |
   | 4092–4095 | 4B | 同步尾 `0xFF 0x01 0xEE 0x01` |
   元数据块含：scope mode、preamp(bit0-1)/attenuator(bit2-3)、span、mode、VFO-A 频率（5 字节 BCD 与 4 字节大端）、S-meter 原始值、scope 起始频率。帧率约 **30fps**。
5. **CAT over the Enhanced COM Port** — 原生 Yaesu CAT（非 Hamlib；SDD AD-002 明确避开 rigctld），格式 `[2字母命令][参数];`，例 `FA014200000;` 设 VFO-A 14.200MHz。38400 baud 8N1，无流控。连接时先发 `AI0;` 关闭自动信息流，改主动轮询。命令间 **20ms 延时**（对齐 Hamlib `post_write_delay`）。初始化频谱需 EX 命令：`EX040101`（FT4222 输出频谱）、`EX040200`（CENTER 模式）。PTT/TUNE 用 `send_priority_set_command()` 抢占轮询。
6. **From SPI to browser: the pipeline** — 三段式：`scope_pipe.py` **独立子进程**读 FT4222（隔离阻塞的 D2XX ctypes 调用，崩溃自动重启）；长度前缀帧（4 字节大端）经 stdout 传给 server；server 以 **1701 字节二进制帧**（1B 版本 + 850B WF1 + 850B WF2）经 `/WSspectrum` WebSocket 以 **5fps**（200ms）广播；浏览器渲染瀑布流（120 行历史、6 种 colormap）。
7. **Handling transmit** — 发射时 FT-710 频谱流会损坏：server 发 `TX:1\n` 暂停 SPI 读取，松开 PTT 后关闭/稳定/重开设备重新同步，避免 `too_many_reinits` 崩溃循环。
8. **Graceful degradation** — FT4222 不可用时 `ScopeHandler.update_from_radio_state()` 用 S-meter 生成高斯形状合成频谱，同 5fps 下发。
9. **What this means vs the SCU-LAN10** — 对比表：无需额外硬件 / 开源可审计 / 浏览器即客户端 / 双模式频谱（SCU-LAN10 无等效降级）/ 数据路径无网络层无专有编码。
10. **Field notes（个人经历区）** — 预留 blockquote "My experience:" 提示用户填写实测（何时第一次跑通、踩过的坑、SPI 时钟分频器 `FT710_FT4222_CLK_DIV` 环境变量的调试等）。

关键数字（必须准确引用）：38400 baud、20ms 命令延时、375kHz SPI、4096B 帧、850 bins×2、30fps SPI/5fps 网页、1701B WebSocket 帧、S-meter 0–255 校准到 -54~+60 dBm、Opus 64kbps、网页默认端口 8888。

- [ ] **Step 4: 验证页面结构完整**

Run: `python3 - <<'EOF'
import re
html=open('/Users/cheenle/HAM/website/portal/blog/ft710-usb-remote-control/index.html').read()
checks={
 'title': '<title>' in html, 'canonical': 'rel="canonical"' in html,
 'jsonld': 'application/ld+json' in html, 'toc': 'blog-toc' in html,
 'authorbox': 'blog-author' in html, 'lang=en': 'lang="en"' in html,
}
assert all(checks.values()), [k for k,v in checks.items() if not v]
import json
m=re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
json.loads(m.group(1))  # must parse
words=len(re.sub(r'<[^>]+>',' ',html.split('<div class="blog-content">')[1]).split())
print('words in .blog-content:', words)
EOF`
Expected: 全部 checks 通过，JSON-LD 可解析，words ≥ 1000

---

### Task 3: 第二篇旗舰文章 `efhw-esp32s3-auto-tuner`

**Files:**
- Create: `portal/blog/efhw-esp32s3-auto-tuner/index.html`

**Interfaces:**
- Consumes: 与 Task 2 相同的文章页模板；`blog.css` 类。
- Produces: 文章页，cross-link 到 `/efhw/` 与 `/mrrc/efhw/`。

- [ ] **Step 1: 复刻 Task 2 文章骨架**，替换 head/JSON-LD/正文

- [ ] **Step 2: 撰写正文**（≥1000 词；结构见下方"技术事实"，数字必须准确；cross-link `/efhw/` 与 `/mrrc/efhw/`）

**技术事实（写作素材，来自 `/Users/cheenle/HAM/efhw-knowledge/auto-efhw-tuner/`，不可虚构）:**

文章 h2 结构与必写要点：

1. **Introduction** — 自动天线调谐器（ATU）解决什么：野外换频时手调 EFHW 匹配网络繁琐。Fuchs ATU V3.0 = ESP32-S3 伺服驱动电容调谐。成本约 **430 元**。
2. **Hardware platform** — 硬件平台表格：ESP32-S3-WROOM-1（Xtensa LX7 双核 240MHz / 512KB SRAM / 16MB Flash）、ESP-IDF v5.x 原生 C（非 Arduino）+ FreeRTOS、MG996R 伺服（6V、10kg·cm、0.17s/60°）、伺服 PWM 用 LEDC（GPIO1，50Hz，500–2500µs ↔ 0–180°）、GPIO2→2N2222A→IRF9540 P-MOSFET 控制伺服 6V 供电、Bias-T 电压监测（GPIO5 ADC1_CH4，47k+10k 分压 5.7:1）。供电链：同轴 Bias-T 13.8V → LM2940CT-12 → DC-DC 6V（伺服）+ AMS1117 3.3V（ESP32）。
3. **The matching network** — 匹配网络：单一 T200-6 羰基铁粉芯磁环（Type 6，µ=8，OD 50.8mm/ID 31.8mm/高 14mm，AL≈10.5nH/N²），**2T:14T** 匝比 → 阻抗比 (14/2)²=**49:1**，50Ω→约 2450Ω；发信机级空气可变电容 10–500pF（≥5kV 或极板间距 ≥1.5mm）；伺服经 3:1–6:1 齿轮减速耦合。实测调谐范围 f_max 35.1MHz（10pF）～ f_min 4.96MHz（500pF），覆盖 40m–10m 含全部 WARC 频段。B_peak @100W/7.1MHz = 12.7mT vs 600mT 饱和 = **47 倍裕量**。
4. **SWR sensing: where it actually lives** — 关键架构（AD-003）：**ATU 上没有 SWR 桥**。数据流 `ATR1000 → MRRC → WebSocket → ESP32-S3 → tune_engine_feed_swr()`。好处：BOM 去掉 SWR 桥、减少故障点；代价：断网时无法调谐。
5. **The tuning algorithm** — 四阶段（`tune_engine.c` 头注释）：
   ① **缓存命中**：NVS 按 `"f"+freq_khz` 键查 ±50kHz 模糊匹配，约 2000 条记录/24KB 分区；命中直接移到位并上报，**<1s** 完成。
   ② **粗扫**：0–180° 每 5° 一步（36 步），每步发 `tune_progress` 后等 WebSocket 的 `swr_update`；全程跟踪 best_swr/best_pos。SWR<1.05 提前退出。
   ③ **细扫**（best_swr>1.5 才执行）：best 附近 ±15° 每 1° 一步（30 步）。
   ④ **锁定**：移到 best_pos、SWR<2.0 才写 NVS、**关闭伺服 MOSFET 供电**、发 `tune_done {cap_pct, swr_final, elapsed_ms}`。
   时间：每步 80ms（伺服移动）+ ~100ms（SWR 网络往返）≈180ms；全粗扫 ≈6.5s；粗+细最坏 ≈12s（SDD 目标 <10s）；缓存命中 <1s。
6. **Safety and fault detection** — 安全门：`feed_swr()` 时前向功率 >15W 中止 `TUNE_ERR_OVERPOWER`、<0.5W 中止 `TUNE_ERR_NORF`；SWR≥2.0 无匹配报错。固件可检：Bias-T 电压越界（10–15V 外）、核心温度 >80°C、WiFi 断连每 10s 重连、WebSocket 断连每 3s 重连、畸形 JSON 静默丢弃、NVS 损坏自动重建、5s 任务看门狗。**固件无法检**（无传感器）：伺服机械堵转、扫齿/联轴器打滑、MOSFET 开路/短路、电容打火、磁环过热、进水。
7. **FreeRTOS architecture** — 三任务：`ws_client_task`（pri 3 / 8KB 栈）、`tune_engine_task`（pri 2 / 4KB）、`health_mon_task`（pri 1 / 3KB）。通信：ws→tune 直接函数调用 `tune_engine_feed_swr()`；tune→ws 经 FreeRTOS Queue（深 16、512B 消息）。
8. **JSON protocol** — 5 命令（`tune_start{freq_hz,swr,fwd_pwr_w}`/`swr_update{swr,fwd_pwr_w}`/`tune_abort`/`set_bypass`/`get_status`）、5 事件（`tune_progress`/`tune_done`/`tune_error`（ok/overpower/no_rf/no_match/servo_stall/timeout/ws_disconnect）/`status_report`/`health_alert`）。
9. **Field notes（个人经历区）** — 预留 blockquote "My experience:"：野外首次架设、用 ATR1000 联调、某个频段调不上的排查等。

- [ ] **Step 3: 运行 Task 2 Step 4 的验证脚本**（路径换为本文）并确认通过

---

### Task 4: 第三篇旗舰文章 `opus-vs-pcm-remote-audio`

**Files:**
- Create: `portal/blog/opus-vs-pcm-remote-audio/index.html`

**Interfaces:**
- Consumes: 与 Task 2 相同的文章页模板；`blog.css` 类。
- Produces: 文章页，cross-link 到 `/sunmrrc/`、`/sunsdrmobile/`、`/mrrc/`。

- [ ] **Step 1: 复刻 Task 2 文章骨架**，替换 head/JSON-LD/正文

- [ ] **Step 2: 撰写正文**（≥1000 词；结构见下方"技术事实"，数字必须准确；cross-link `/sunmrrc/`、`/sunsdrmobile/`、`/mrrc/`）

**技术事实（写作素材，来自 `/Users/cheenle/HAM/sunsdr/web_control/` 与 SunMRRC SDD，不可虚构）:**

文章 h2 结构与必写要点：

1. **Introduction** — 远程电台的音频链路：接收 48kHz 单声道、发射 16kHz 单声道；无压缩 PCM 在移动网络下会卡顿（underrun），用 Opus 获得 >10 倍带宽压缩。
2. **The bandwidth math (why PCM fails on mobile)** — 表格：
   | 链路 | PCM 带宽 | Opus 带宽 | 压缩比 |
   |---|---|---|---|
   | RX 音频 | ~768 kbit/s（48kHz 16-bit 单声道） | ~18–24 kbit/s（64kbps 目标） | >10x |
   | TX 上行 | ~256 kbit/s（16kHz） | ~18–24 kbit/s | >10x |
   代码注释引用：64kbps 是"远程 WFM 收听甜点：广播音乐近透明，且仅为 768kbps Int16 PCM 的 1/12"。
3. **Opus encoder settings** — 参数（`opus_rx.py`）：RX 48kHz/单声道、TX 16kHz/单声道、**20ms 帧**（48kHz 下 960 采样）、默认 **64kbps**（范围 8–128kbps）、**`OPUS_APPLICATION_AUDIO`(2049)** 而非 VOIP(2048)——为全带宽音频调优（WFM 广播 + 清晰 SSB）。`MAX_PACKET_BYTES=4000`、`TX_MAX_FRAME_SAMPLES=5760`（120ms 最坏帧）。
4. **A real-world ctypes quirk (variadic ABI)** — 有趣实战细节：`opus_encoder_ctl` 是 C 可变参函数，arm64（Apple Silicon）上变参 ABI 把尾参压栈，但 ctypes 固定 argtypes 走寄存器 → 每次 SET 都返回 `OPUS_BAD_ARG`，位率控制静默失效。绕过：改用 `opus_encode` 的 `max_data_bytes` 限幅（`cap = min(4000, bitrate*20//1000//8)`；64kbps → **160 字节/帧**；实测 40B≈13kbps、60B≈20kbps 可干净解码往返）。
5. **PCM ↔ Opus switching without a handshake** — 双编解码传输（AD-004）：每个 `/WSaudioRX` 帧前缀 **1 字节 codec tag**（`0x00`=PCM、`0x01`=Opus），客户端看 tag 决定解码 → 流中可无握手切换。启动默认 Opus；libopus 缺失时自动回退 Int16 PCM；前端 "Audio Codec" 菜单可运行时切换（`setOpus:`/`setOpusBitrate:` 16–128kbps）。
6. **Latency budget** — 时序表：Opus 帧 20ms；WebSocket 抖动缓冲 prime **10 帧（200ms）**、max 60 帧（1200ms）；TX 麦克风抖动缓冲 prime 60 包（~307ms）、重 prime 8 包（41ms）；稳态队列 ~80 包（~410ms）；TX 调制前 17 个零 IQ 包预调谐（~87ms）、线性淡入 200 采样（~5.1ms）。远程操作主观延迟来自缓冲而非 Opus 本身。
7. **The WebSocket audio transport** — 4 端点：`/WSCTRX`（控制，PING/PONG 测往返）、`/WSaudioRX`（服务→客户端，tag+payload）、`/WSaudioTX`（客户端→服务端）、`/WSspectrum`（512 字节 uint8 行，可配 1–38fps）。**AD-014**：TX 路径用 `SharedArrayBuffer` 无锁环形缓冲（16384 float32 @16kHz = 1.024s）在 AudioWorklet 与 Web Worker 间传递，主线程不碰音频采样，避免 GC 停顿卡顿；需 `Cross-Origin-Opener-Policy: same-origin` + `Cross-Origin-Embedder-Policy: credentialless` 响应头。
8. **Sample rates & signal path** — SunSDR2 DX IQ 采样率是 5^7=78125Hz 的倍数（39k/78k/156k/312k，24-bit IQ），基率 39062.5Hz 提供 ~19.5kHz Nyquist 供 WFM，解调后用 Catmull-Rom 三次插值重采样到 48kHz 供 Opus/浏览器。TX 处理链：16kHz 麦克风 → Opus WASM（Worker 内）→ `/WSaudioTX` → 服务端 `TxOpusDecoder` → **300Hz 四阶 Butterworth HPF**（AD-015，把 <300Hz 包络功率占比从 30.4% 降到 3.7%，96% PA 功率落入 300–2800Hz SSB 话音带）→ DC 阻断 → 上采样 + Hilbert 解析信号（overlap-save，256 采样边距）→ 80 音频采样→200 IQ 采样 @39063Hz → `TX_DRIVE_GAIN=2.8` → tanh 软限幅（`TX_IQ_PEAK=1.0`）→ 线性淡入 → 24-bit IQ 1200B 载荷 0xFFFD UDP 包 @5.12ms。
9. **Field notes（个人经历区）** — 预留 blockquote "My experience:"：何时发现 PCM 卡顿、切 Opus 后的体验、Apple Silicon 变参 bug 的排查、某个网络下的延迟表现。

- [ ] **Step 3: 运行 Task 2 Step 4 的验证脚本**（路径换为本文）并确认通过

---

### Task 5: 博客列表页 `blog/index.html`

**Files:**
- Create: `portal/blog/index.html`

**Interfaces:**
- Consumes: Task 1 `blog.css`（`.blog-list-hero`/`.blog-cat-filter`/`.blog-grid`/`.blog-card`）；三篇文章 slug。
- Produces: 列表页；`/blog/` 目录入口；JSON-LD `Blog`；分类过滤 JS。

- [ ] **Step 1: 编写列表页**：hero（标题+简介）、分类过滤按钮（All / MRRC / FT-710 / EFHW / SunSDR / Audio / Deployment）、三张文章卡片（分类、标题、摘要、日期、阅读时长）、JSON-LD `Blog` schema、加载 `../css/blog.css` 与 `../js/global-nav.js`

- [ ] **Step 2: 客户端分类过滤脚本**（内联）：`data-cat` 与按钮 `data-filter` 匹配，隐藏非匹配 `.blog-card`

- [ ] **Step 3: 验证三篇文章链接路径正确**

Run: `grep -o 'href="[^"]*"' /Users/cheenle/HAM/website/portal/blog/index.html`
Expected: 每个 href 指向存在文件（`./ft710-usb-remote-control/`、`./efhw-esp32s3-auto-tuner/`、`./opus-vs-pcm-remote-audio/`）

---

### Task 6: 信任页（EN + CN 双语）

**Files:**
- Create: `portal/about.html`, `portal/contact.html`, `portal/privacy.html`
- Create: `portal/zh/about.html`, `portal/zh/contact.html`, `portal/zh/privacy.html`

**Interfaces:**
- Consumes: `fde.html` 子页模式（page-hero + section）；`octen.css`/`sunsdrmobile.css`；`js/global-nav.js`（EN 页 `js/global-nav.js`，zh 页 `../js/global-nav.js`）。
- Produces: 全站信任信号页。

- [ ] **Step 1: `about.html`（EN）**：仿 fde.html 头尾结构。内容：VLSC 简介、BG1SB 呼号、技术背景（HAM、逆向工程 SunSDR2 DX、FDE 方法论）、项目群创建初衷、六个项目一句话说明、GitHub/CQ 社群链接。加 JSON-LD `AboutPage`。

- [ ] **Step 2: `contact.html`（EN）**：GitHub `https://github.com/cheenle`、预留邮箱 `contact@vlsc.net`、按项目分流 GitHub Issues（/mrrc/、/mrrc_ft710/ 等六个 repo）、无线电社群占位。加 JSON-LD `ContactPage`。

- [ ] **Step 3: `privacy.html`（EN）**：必需声明：① 网站不设 Cookie 无追踪；② **Google AdSense 第三方广告可能使用 Cookie/网络存储**（链接 https://policies.google.com/privacy 与 ads.google.com 设置）；③ nginx 访问日志记录标准 IP/User-Agent（用于安全与统计）；④ 无用户注册/无表单收集；⑤ 外部链接（GitHub、Font Awesome CDN、Google Fonts）；⑥ 联系渠道 contact@vlsc.net；⑦ Last updated 日期。加 JSON-LD `WebPage`。

- [ ] **Step 4: 三个中文镜像**：复制结构，文案译为中文，链接改 `../` 前缀，`<html lang="zh-CN">`。

- [ ] **Step 5: 验证双语 6 页均可访问且无 404 链接**

Run: `python3 -m http.server 8100 --directory /Users/cheenle/HAM/website/portal >/dev/null 2>&1 & sleep 1; for p in about contact privacy zh/about zh/contact zh/privacy; do echo "$p -> $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8100/$p.html)"; done; kill %1`
Expected: 6 个页面均 200

---

### Task 7: 导航与页脚更新（portal 内 4 个页面）

**Files:**
- Modify: `portal/index.html`（navbar + footer）
- Modify: `portal/zh/index.html`（navbar + footer）
- Modify: `portal/fde.html`（footer）
- Modify: `portal/zh/fde.html`（footer）

**Interfaces:**
- Consumes: 既有 navbar/footer 结构。
- Produces: 全站可发现的 Blog/About/Contact/Privacy 入口。

- [ ] **Step 1: `index.html` navbar**：在 `<li><a href="/fde.html">FDE</a></li>` 后插入 `<li><a href="/blog/">Blog</a></li>`

- [ ] **Step 2: `index.html` footer**：Resources 区顶部加 Blog 链接；新增 Site 区（About/Contact/Privacy）或并入现有区（About→`about.html`、Contact→`contact.html`、Privacy→`privacy.html`）；footer-bottom 加三页链接

- [ ] **Step 3: `zh/index.html` navbar**：FDE 后插入 `<li><a href="/blog/">博客</a></li>`；footer 同 Step 2（链接指 `about.html`/`contact.html`/`privacy.html` 或 `../about.html` 视路径而定）

- [ ] **Step 4: `fde.html` 与 `zh/fde.html` footer**：Resources 加 Blog；footer-bottom 加 About/Contact/Privacy

- [ ] **Step 5: 验证**：4 个文件均含 `/blog/`、`about.html`、`contact.html`、`privacy.html` 链接

Run: `for f in index zh/index fde zh/fde; do grep -c 'blog\|about\|contact\|privacy' /Users/cheenle/HAM/website/portal/$f.html; done`
Expected: 每个文件 grep 计数 ≥ 3

---

### Task 8: `global-nav.js` 顶部导航加 Blog（7 份副本）

**Files:**
- Modify: `portal/js/global-nav.js`
- Modify: `efhw/js/global-nav.js`
- Modify: `mrrc_ft710/website/js/global-nav.js`
- Modify: `/Users/cheenle/UHRR/MRRC/website/js/global-nav.js`
- Modify: `/Users/cheenle/HAM/sunsdr/sunmrrc/website/js/global-nav.js`
- Modify: `/Users/cheenle/HAM/sunsdr/SunsdrMobile/website/js/global-nav.js`
- Modify: `/Users/cheenle/HAM/ft8/website/js/global-nav.js`

**Interfaces:**
- Consumes: 各副本现有 `siteLink('…', '…')` 调用序列（副本各自独立、内容不全相同，需逐个读取后再编辑）。
- Produces: 全站顶部导航出现 Blog 入口（指向 `/blog/`）。

- [ ] **Step 1: 读取 portal 副本**，在 `<nav class="vlsc-gn-links">` 内最后一个 `siteLink(...)` 后插入 `siteLink('blog', 'Blog')`

- [ ] **Step 2: 在 `PATHS` 对象加** `blog: '/blog/'`（portal 副本）

- [ ] **Step 3: 逐个读取其余 6 份副本**，确认其 `PATHS` 与 nav 结构（副本有差异），应用同样两处修改（`PATHS.blog` + `siteLink('blog','Blog')`）

- [ ] **Step 4: 验证**：`grep -l "siteLink('blog'"` 覆盖全部 7 份

Run: `for f in $(find /Users/cheenle/HAM/website /Users/cheenle/UHRR/MRRC/website /Users/cheenle/HAM/sunsdr /Users/cheenle/HAM/mrrc_ft710/website /Users/cheenle/HAM/ft8/website -name global-nav.js 2>/dev/null); do grep -q "siteLink('blog'" "$f" && echo "OK $f" || echo "MISSING $f"; done`
Expected: 7 行全为 OK

---

### Task 9: 死链整改（Demo 状态徽章）

**Files:**
- Modify: `portal/index.html`（两处 Live Demo 链接：`:8877` 行、`:8889` 行）

**Interfaces:**
- Consumes: 既有 demo 卡片结构。
- Produces: 消除指向死端口的空链接。

- [ ] **Step 1: 将 8877（SunsdrMobile）与 8889（SunMRRC）的 `<a href="https://radio.vlsc.net:8877/...">` 与 `<a href="https://radio.vlsc.net:8889">` 替换为**：状态徽章（红色/灰点 + "Demo Offline"）+ 指向对应项目站部署文档或项目站本身的链接（保留可点击且有价值的去向）

- [ ] **Step 2: 9988（MRRC-FT8）保留**，可加绿色状态点 "Demo Online"

- [ ] **Step 3: 验证无死端口 href 残留**

Run: `grep -n "radio.vlsc.net" /Users/cheenle/HAM/website/portal/index.html`
Expected: 仅剩 `:9988`（或明确的状态文字），`:8877`/`:8889` 不再作为可点击 href 目标

---

### Task 10: `sitemap.xml` + `robots.txt` + `make_sitemap.py`

**Files:**
- Create: `portal/make_sitemap.py`
- Create: `portal/sitemap.xml`（生成产物）
- Create: `portal/robots.txt`

**Interfaces:**
- Produces: Google 可抓取的站点地图与爬虫指令。

- [ ] **Step 1: 写 `make_sitemap.py`**（标准库 os/re，无第三方依赖）：

```python
#!/usr/bin/env python3
"""Generate sitemap.xml for www.vlsc.net from the portal directory tree."""
import os, re, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = "https://www.vlsc.net"

def find_html(base):
    pages = []
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if not d.startswith('.')]
        for fn in filenames:
            if fn.endswith('.html') and not fn.startswith('.'):
                full = os.path.join(dirpath, fn)
                if fn == 'index.html':
                    url = os.path.relpath(dirpath, base) + '/'
                else:
                    url = os.path.relpath(full, base)
                pages.append((url.replace(os.sep, '/'), full))
    return pages

def lastmod(path):
    ts = os.path.getmtime(path)
    return datetime.date.fromtimestamp(ts).isoformat()

pages = find_html(ROOT)
# sub-site roots (deployed as nginx aliases under the same domain)
SUBSITES = ['/mrrc/', '/mrrc_ft710/', '/mrrc_ft8/', '/sunmrrc/', '/sunsdrmobile/', '/efhw/']

urls = []
urls.append(f'<url><loc>{BASE}/</loc><changefreq>weekly</changefreq></url>')
for url, path in sorted(pages):
    if url.startswith('zh/'):
        loc = f'{BASE}/zh/{url[3:]}'
    else:
        loc = f'{BASE}/{url}'
    urls.append(f'<url><loc>{loc}</loc><lastmod>{lastmod(path)}</lastmod></url>')
for s in SUBSITES:
    urls.append(f'<url><loc>{BASE}{s}</loc><changefreq>weekly</changefreq></url>')

sitemap = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           + '\n'.join(urls) + '\n</urlset>\n')
with open(os.path.join(ROOT, 'sitemap.xml'), 'w') as f:
    f.write(sitemap)
print(f"wrote sitemap.xml with {len(urls)} URLs")
```

- [ ] **Step 2: 运行脚本生成 sitemap.xml**

Run: `cd /Users/cheenle/HAM/website/portal && python3 make_sitemap.py`
Expected: `wrote sitemap.xml with N URLs`；N ≥ 12（含 3 篇文章 + 6 子站根 + 门户页）

- [ ] **Step 3: 写 `robots.txt`**

```
User-agent: *
Allow: /

Sitemap: https://www.vlsc.net/sitemap.xml
```

- [ ] **Step 4: 验证 sitemap 为合法 XML 且含三篇文章 URL**

Run: `python3 -c "import xml.etree.ElementTree as ET; r=ET.parse('/Users/cheenle/HAM/website/portal/sitemap.xml').getroot(); u=[e[0].text for e in r]; print(len(u)); print([x for x in u if '/blog/' in x])"`
Expected: 打印 URL 总数 + 3 个 `/blog/` 文章 URL

---

### Task 11: 全站终检

**Files:**
- 无（验证任务）

- [ ] **Step 1: 本地起服务，全站爬取验证 200 / 404**

Run: `cd /Users/cheenle/HAM/website/portal && python3 -m http.server 8101 >/dev/null 2>&1 & sleep 1; python3 - <<'EOF'
import re, urllib.request, os
base='http://localhost:8101'
paths=['/','/blog/','/blog/ft710-usb-remote-control/','/blog/efhw-esp32s3-auto-tuner/','/blog/opus-vs-pcm-remote-audio/','/about.html','/contact.html','/privacy.html','/zh/about.html','/zh/contact.html','/zh/privacy.html']
bad=[]
for p in paths:
    try:
        code=urllib.request.urlopen(base+p).status
        if code!=200: bad.append((p,code))
    except Exception as e: bad.append((p,e))
print('bad:', bad if bad else 'NONE — all 200')
EOF
kill %1 2>/dev/null`
Expected: `bad: NONE — all 200`

- [ ] **Step 2: JSON-LD 三篇均语法合法**（复用 Task 2 Step 4 的 json 解析，对三篇文章分别跑）

- [ ] **Step 3: 汇总交付**：向用户报告改动清单、遗留占位（contact@vlsc.net 邮箱、每篇文章的实测截图位、global-nav 其余副本待部署），并给出阶段 2（余下 17 篇）清单

---

## 自审（spec 对照）

- Spec A（文件结构）→ Task 1–10 覆盖全部新文件。
- Spec B（文章模板 SEO/JSON-LD/TOC/作者盒）→ Task 2 骨架 + Task 2–4 正文。
- Spec C（列表页过滤/tag/JSON-LD）→ Task 5。
- Spec D（信任页双语 + AdSense Cookie 声明）→ Task 6。
- Spec E（导航改动 4 页 + global-nav 同步）→ Task 7 + Task 8。
- Spec F（3 篇旗舰选题 4/7/13）→ Task 2/3/4。
- Spec G（死链整改 + sitemap/robots）→ Task 9 + Task 10。
- Spec H（阶段 1 范围）→ 全部任务；阶段 2 不在本计划。
- 验收标准：Task 11 全站终检覆盖。
