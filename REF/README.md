# 过程记录

本目录记录 2026-09-27 两项工作的完整过程：① 无线机历史博物馆网站镜像存档；② ICOM IC-R9000 与 JRC NRD-535 的深度调研。

## 任务一：RIG 目录镜像存档

**目标**：把 http://www.seidensha-ltd.co.jp/~seiden/rekishi.html（日本收藏家 JA4FUQ 的"无线机历史博物馆"）的信息逐台设备保存到本地。

**过程**：

1. 直接抓取页面发现乱码——原站为 Shift_JIS/CP932 编码，文本提取器按错误编码解码。
2. 改用 `curl` 下载原始字节，以 CP932 转 UTF-8（`iconv -c` 丢弃个别无法转换的字节）。
3. 解析主页 HTML，提取出 **220 个本地设备/专题页面链接**（按"年代 × 接收机/收发信机/发射机"表格组织，另有电键、功率计等番外篇）。
4. 编写 `RIG/_mirror.py`（Python，支持断点续传、0.2–0.3 秒间隔礼貌抓取）：下载全部 220 个页面并转码，再从所有页面中收集图片引用，下载 **2,137 张图片**到 `RIG/gif/`。首次运行 600 秒超时被终止，续传后完成，零失败。
5. 修正所有页面的 `<meta charset>` 声明（Shift_JIS → UTF-8），保证离线浏览不乱码。
6. 编写 `RIG/_make_index.py` 解析主页表格，生成中文索引 `RIG/README.md`（含 ☆ 实使用标注、本地相对链接）。
7. 抽查验证：页面文字正常、图片为有效 JPEG。

**产出**：`RIG/` 共 59 MB——221 个 HTML 页面 + 2,136 张图片 + 中文索引，完全离线可用。

## 任务二：IC-R9000 / NRD-535 深度调研

**目标**：针对用户持有的 ICOM IC-R9000 与 JRC NRD-535（非 D 版）做全网深度研究，含 YouTube 视频等一切资料。

**方法**：派出 **8 个并行调研代理**，每个负责一个独立方向，要求所有结论基于实际抓取的网页、关键数字必须附来源 URL：

| # | 方向 | 原始记录 |
|---|---|---|
| 1 | IC-R9000 技术规格、架构、版本、竞品对比 | [01-ICR9000-技术与历史.md](01-ICR9000-技术与历史.md) |
| 2 | IC-R9000 通病、维修、改装、备件 | [02-ICR9000-通病与维修.md](02-ICR9000-通病与维修.md) |
| 3 | IC-R9000 YouTube/Bilibili 视频档案 | [03-ICR9000-视频资料.md](03-ICR9000-视频资料.md) |
| 4 | IC-R9000 日文资料 + 本地存档 JA4FUQ 报告解读 | [04-ICR9000-日文资料.md](04-ICR9000-日文资料.md) |
| 5 | NRD-535 技术规格、与 535D 区别、BWC/ECSS | [05-NRD535-技术与历史.md](05-NRD535-技术与历史.md) |
| 6 | NRD-535 通病、维修、改装 | [06-NRD535-通病与维修.md](06-NRD535-通病与维修.md) |
| 7 | NRD-535 YouTube/Bilibili 视频档案 | [07-NRD535-视频资料.md](07-NRD535-视频资料.md) |
| 8 | NRD-535 日文资料 + 本地存档解读 | [08-NRD535-日文资料.md](08-NRD535-日文资料.md) |

8 个代理全部完成，合计覆盖 60+ 个独立来源。随后人工汇总为两份最终报告：

- [IC-R9000-最终报告.md](IC-R9000-最终报告.md)（同步存于 `RIG/research/IC-R9000.md`）
- [NRD-535-最终报告.md](NRD-535-最终报告.md)（同步存于 `RIG/research/NRD-535.md`）

**调研中的资料局限（如实记录）**：eHam 部分页面被 Cloudflare 拦截（改用 web.archive.org 存档读取）；groups.io 两个 JRC 群组有 JS 验证墙（仅能引用搜索摘要）；antiqueradios.com 返回 403；IC-R9000 的产量数字与按序列号划分的硬件改版记录在所有公开来源中均不存在，未杜撰。

## 任务三：IC-R9000 现代化改造深度研究（同日第二轮）

**目标**：研究如何把 IC-R9000 提升、改造、现代化到现代旗舰机水平。

**方法**：再派 **5 个并行调研代理**，基于第一轮已建立的背景知识（通病、Sherwood 基准数据）深入：

| # | 方向 | 原始记录 |
|---|---|---|
| 9 | 已有改装全集（mods.dk/Sherwood/LCD/滤波器/SE-3/CI-V） | [09-ICR9000-已有改装全集.md](09-ICR9000-已有改装全集.md) |
| 10 | 现代旗舰基准对比（Sherwood 同实验室数据量化差距） | [10-现代旗舰基准对比.md](10-现代旗舰基准对比.md) |
| 11 | SDR 结合（IF tap/panadapter/OmniRig 联动/卫星玩法） | [11-ICR9000-SDR结合.md](11-ICR9000-SDR结合.md) |
| 12 | 硬核深度改造案例（散热/recap/荷兰 RCD 官方改造/相噪与 roofing 空白确认） | [12-ICR9000-硬核改造案例.md](12-ICR9000-硬核改造案例.md) |
| 13 | 老接收机嫁接数字解调/DSP 的可行性与代价 | [13-老接收机嫁接DSP.md](13-老接收机嫁接DSP.md) |

汇总报告：[IC-R9000-现代化改造-最终报告.md](IC-R9000-现代化改造-最终报告.md)（同步存于 `RIG/research/IC-R9000-现代化改造.md`）。

**核心结论**：射频链硬指标（窄间隔 DR 71 dB、相噪 128 dBc/Hz）受 1989 年架构所限，全球无人做成过本振/roofing 改造，追不上现代旗舰；但**功能与体验可通过"IF→SDR 外挂"全面达到甚至超越现代旗舰**（全景瀑布、ECSS 同步检波、任意带宽数字滤波、降噪、录音、数字模式解码），加上散热/电容/LCD 翻新，DIY 总成本约 $400。正确定位：R9000 做 VHF/UHF/频谱监测/卫星 + 情怀旗舰，HF 极限 DX 交给 Airspy HF+ 级现代 SDR，两者协同。

## 任务四：portal 新增 RIG 专栏（同日）

**目标**：在 portal（www.vlsc.net）上新增 RIG 专栏，IC-R9000 作为系列第一篇设备深度文章。

**产出**：
- `portal/rig/index.html` + `portal/rig/zh/index.html` — 专栏落地页（中英双语），含第 1 篇（IC-R9000）卡片与第 2 篇（NRD-535）预告卡片
- `portal/rig/ic-r9000/index.html` + `portal/rig/ic-r9000/zh/index.html` — 长文《ICOM IC-R9000: Anatomy of a 1989 Flagship — and How to Modernize It》，端到端：定位与历史 → 架构 → Sherwood 实测对比 → 老化故障图谱（现象/根因/修法）→ 翻新基线 → SDR 嫁接架构 → 无人做成的前沿（roofing/相噪/GPSDO）→ 结论与预算 → 来源。沿用 blog 文章的 house style（ba-tldr 事实/论点标签、锚点导航、来源清单）
- 全站导航：14 个 portal 页面（en×7 + zh×7）的 navbar 与页脚 Blog 链接后统一插入 RIG 链接
- `portal/make_sitemap.py` 重新生成 sitemap.xml（自动发现 4 个新 URL）
- `portal/deploy.sh`：chmod 规范化目录清单加入 `rig`

**验证**：`pytest portal/tests/` 100 通过 / 1 失败（test_analytics_coverage 对 mrrc 子站旧页面的既有失败，git stash 验证与本次改动无关，新 rig 页面均加载 global-nav.js）；本地链接检查全部可解析；本地 HTTP 服务 4 个新页面均 200。

**部署**：`portal/deploy.sh` 为整目录打包，rig/ 自动包含；本次未执行部署，由用户运行。

## 任务五：NRD-535 第二轮深度研究 + RIG 专栏第 2 篇（同日）

**目标**：对 NRD-535 做与 IC-R9000 同规格的"提升/改造/现代化"研究，并产出专栏第 2 篇。

**方法变化（如实记录）**：原计划再派 5 个并行调研代理，但**子代理池与 WebSearch 均返回 403 配额限制**（5 小时窗口用尽）。改为主线程用 `curl` 直接抓取 + 本地解析完成同等深度的调研；搜索引擎改用 DuckDuckGo Lite 的 HTML 端点（curl 可达），必要时用 Wayback CDX 查历史快照。

**本轮新增的一手材料**：

| # | 方向 | 原始记录 |
|---|---|---|
| 14 | 改装史与一手史料（Paul Lannuier／JRC 前美国销售经理笔记：设计评审内幕、JRC↔NDK 滤波器对照表、Db 序列号改版、NRD-535GS 配方；Nilsson 改装全文；Fenu-Radio Kiwa 评价；ZCM 档案） | [14-NRD535-改装史与一手史料.md](14-NRD535-改装史与一手史料.md) |
| 15 | 与现代旗舰的实测基准（Sherwood 表原始行：JRC 515/525/535/545/93 + R9000/R8600/Perseus/7760/7300/FTdx-101D，含列定义与脚注） | [15-NRD535-基准对比.md](15-NRD535-基准对比.md) |
| 16 | 数字化与 SDR 嫁接（TSP IFace 在 70.455 MHz 的取点、drmrx.org DRM 改装全文、RXCommander/rxcontrol.org/CAT 协议） | [16-NRD535-数字化与SDR嫁接.md](16-NRD535-数字化与SDR嫁接.md) |
| 17 | 显示通病与备件市场实查（VFD 无修法、CSY&SON 备件库存已售罄、Universal Radio 板件价目、TBHD 案例、维修资料清单） | [17-NRD535-显示通病与备件市场.md](17-NRD535-显示通病与备件市场.md) |
| 18 | 现代定位与评价（Patrick Canler 四机对比全文要点：535 排名第一；Fenu/ZCM/dxer.ca/N9EWO） | [18-NRD535-现代定位与评价.md](18-NRD535-现代定位与评价.md) |

**关键新发现**：
- NRD-535 本振相位噪声 **117 dBc/Hz**，比 IC-R9000 的 128 还差 11 dB，比现代旗舰差 27–39 dB；且 JRC 全家族（515/525/535/545）都卡在同一天花板
- 但 **底噪 −135 dBm、灵敏度 0.1 µV 是全表最优级**，今天依然第一梯队
- **NRD-515 的邻近动态范围（77 dB@2kHz）反而优于 535（70 dB@5kHz）**——0.8 倍频程前端 + 80 dB 滤波器极限胜过跟踪预选器
- 滤波器是 535 唯一能真正改到现代水平的一项：**Lannuier 的 JRC↔NDK 对照表**（CFL-251=YF455EB 等）+ **Sherwood 至今在售的 Collins 455 kHz 机械滤波器与 JRC 转接板（$129）**
- **NRD-535GS**（Gilfer × Kiwa，1995–97，$1,659.95）是被商业验证过的完整升级配方，可逐项复刻
- 显示单元 CDE-705 **同时承载调谐编码器接口（PG1/IC7）**——任何替代屏方案必须连编码器逻辑一起做，这是全球尚无人做成的空白
- 欧洲最后一批原厂备件库存（含 2 块 CDE-705）已确认售罄

**产出**：
- 汇总报告 `RIG/research/NRD-535-现代化改造.md`（含 REF 副本）
- portal RIG 专栏第 2 篇：`portal/rig/nrd-535/index.html` + `zh/`（英文主笔，中文由子代理翻译并逐项校验 id/class/锚点一致）
- 落地页中英双语第 2 张卡片由"筹备中"改为正式文章；第 1 篇文章页脚补上第 2 篇链接
- **首页新增 RIG 专栏区块**（`portal/index.html` + `portal/zh/index.html`，插在 Engineering Metrics 与 CTA 之间），此前 RIG 只在导航里、首页正文没有入口
- sitemap 重新生成（83 条 URL，含 6 条 rig 路径）

**验证**：HTML 解析通过；本地 HTTP 服务 `/`、`/zh/`、`/rig/`、`/rig/nrd-535/`、`/rig/nrd-535/zh/` 均 200；首页中英各含 1 个 `id="rig"` 区块；本地链接检查无死链；`pytest portal/tests/` 100 通过 / 1 失败（mrrc 子站旧页面的既有失败，与本次无关）。

## 任务六：Yaesu FT-710 深度研究与专题页（2026-09-28）

**目标**：对 Yaesu FT-710 做与 IC-R9000／NRD-535 同规格的全面深入研究，并在 portal 上生成一个专题页。

**方法**：5 路并行调研代理（配额窗口已恢复）→ 覆盖 60+ 独立来源（Yaesu 日/美官方页与 4 份官方手册、Sherwood 长报告原始 PDF、ARRL QST 2023-08 原始 PDF、RadCom G3SJX 深度评测、ab4oj 与 DC4KU 两份独立实验室报告、经销商规格与价格、eHam 78 条评价/QRZ/Reddit/groups.io）。原始输出 12.6 万字符，由子代理按 subagent 边界稳健切分归档。

| # | 方向 | 原始记录 |
|---|---|---|
| 19 | 规格与架构（含两处前提纠错） | [19-FT710-规格与架构.md](19-FT710-规格与架构.md) |
| 20 | 实测基准（Sherwood 完整行 + 横向对比 + IP+/dither 可比性规则） | [20-FT710-实测基准.md](20-FT710-实测基准.md) |
| 21 | 固件历史（V01-06→V01-12）与已知问题 | [21-FT710-固件与已知问题.md](21-FT710-固件与已知问题.md) |
| 22 | 远程控制与软件生态（CAT 考据、SCU-LAN10、软件矩阵） | [22-FT710-远程控制与软件生态.md](22-FT710-远程控制与软件生态.md) |
| 23 | 选购、配件与口碑 | [23-FT710-选购配件与口碑.md](23-FT710-选购配件与口碑.md) |

汇总报告：[FT-710-最终报告.md](FT-710-最终报告.md)（同步存于 `RIG/research/FT-710.md`，9 章 + 2 附录，含 23 条来源矛盾判定表与"措辞纪律"清单）。

**必须纠正的两处流传错误**（专题页开篇即写）：屏幕是 **4.3 英寸电阻触摸屏**（不是 10.1 英寸；疑为把 10.9 cm 对角线误读成英寸）；频谱跨度是 **1 kHz–1 MHz、30 FPS、100 dB**（不是 300 kHz，那是 FTDX10/101 的指标）。

**关键结论**：① 2 kHz 邻近动态范围 **107 dB**（ARRL 106 dB），Sherwood 全表第 3，是 1,100 美元以下唯一破 100 dB 的机器，且从 20 kHz 到 2 kHz 只掉 0.5 dB（纯直采无顶滤波器的结构性优势；IC-7300 同条件掉 9 dB）；② 弱项是**阻塞 129 dB**（被 ADC 过载保护硬性封顶，>+1 dBm ≈ S9+74 dB 触发）、**IPO 底噪 −127 dBm**（比 IC-7300 差 6 dB，开 P1 后 −135 反超）、**AGC 阈值 4.0 µV 全组最高且不可调**；③ 本振相噪 150 dBc/Hz@10 kHz 是真强项（无 50 kHz 数据，因超过 −154 后保护电路触发）；④ AESS 与 Field 是同一台机器，只差附件；⑤ 固件停在 **V01-12（2024-02-29）**，两年半无更新；⑥ 无任何官方召回/维修公告；⑦ ARRL 的样机曾查出 **SDR 板缺陷元件**、换板后才达标（引用其数据须带此前提）；⑧ 对比 Icom 数据时必须统一用 `ab`（IP+ ON）口径，混用会得出相反结论。

**与本站既有资产的关系**：`portal/blog/ft710-usb-remote-control/` 已把 FT4222 SPI 频谱通道逆向写透（4096 字节帧、850 bin、~30 fps），专题页只做一句话内链并升华为"本站是官方未文档化通道的独立第二来源"；MRRC Modern 作为"免硬件、跨平台、开源"的远程路径，与 SCU-LAN10（$299.95、Windows-only、FT8 官方不支持）正面对照。子代理发现并修正了一处失效链接：`/mrrc_ft710/` 单机站已于 2026-09-12 归档、301 至 `/mrrc_modern/`。

**产出**：
- `portal/ft710.html`（英文专题页，10 节：纠错 → 版本 → 架构 → 实测 → vs FTDX10 → 固件 → 已知问题 → 控制接口 → 软件生态 → 选购）+ `portal/zh/ft710.html`（中文，子代理翻译）
- 站内入口：首页中英 RIG 区块各加一张"配套专题"卡片；FT-710 USB 博客中英两版的延伸阅读各加一条链接；专题页自身 navbar 含 FT-710 项
- sitemap 重新生成（88 条 URL）

**验证**：`pytest portal/tests/` 100 通过 / 1 失败（mrrc 子站既有失败，与本次无关）；中文版完成后补做链接与 HTTP 200 校验。

**收尾（同日）**：
- `portal/zh/ft710.html` 生成（61,812 字节 / 469 行，与英文版行数一致）。子代理逐项校验：id 11/11、class 多重集 155/155、全部标签多重集 1049/1049、`<pre>` 1/1、`<table>` 14/14、`data-claim-type` 6/6；带单位量值 218/218、固件版本号 25/25、ISO 日期 30/30、金额 78/78 完全一致；错误译法（混音器/接收者/屋顶滤波器）0 处；`10.1 英寸` 与 `300 kHz` 仅出现在"讹传"引号内与辟谣句中
- **修复了英文版的一个真实缺陷**：`portal/ft710.html` 漏写 `<title>`（子代理发现），中英两版均已补上
- 品牌译名统一：`portal/blog/ft710-usb-remote-control/zh/index.html` 中 5 处"雅马哈"改为 Yaesu，与新页面一致
- 中文页正文内链保持指向英文版（与 `rig/*/zh` 系列既有做法一致，目标页均带语言切换）；navbar 按 7 个既有 `portal/zh/*.html` 的写法（`/blog/` + `/rig/zh/`）
- sitemap 重新生成：**89 条 URL**，含 `/ft710.html` 与 `/zh/ft710.html`
- 最终校验：6 个相关页面 HTML 解析通过；本地 HTTP `/ft710.html`、`/zh/ft710.html`、`/`、`/zh/`、`/rig/`、`/rig/nrd-535/`、`/blog/ft710-usb-remote-control/zh/` 全部 200；站内链接无死链（`/mrrc*/`、`/efhw/`、`/sunmrrc/` 等子站路径已确认在仓库根存在，由 nginx alias 提供）

**迁移到 RIG 专栏下（同日，应用户要求）**：专题页原挂在站点根目录，已迁入专栏目录，与 `rig/ic-r9000/`、`rig/nrd-535/` 同构。上文提到的 `portal/ft710.html` / `portal/zh/ft710.html` 现在是**跳转占位页**，正文位置为：
- `portal/rig/ft710/index.html` → https://www.vlsc.net/rig/ft710/
- `portal/rig/ft710/zh/index.html` → https://www.vlsc.net/rig/ft710/zh/

配套处理：
- 旧 URL 在 **nginx 层做 301**（`nginx/vlsc.net.conf` 加两条 `location =`，与 `from-intent-to-delivery` 同一处先例），根目录与 `zh/` 下另留 meta-refresh + `noindex` 占位页兜底；占位页仍加载 global-nav.js 以满足 `test_analytics_coverage` 的全站约束
- `portal/make_sitemap.py` 的 `EXCLUDE_PREFIXES` 加入两个占位页（sitemap 必须等于生成器输出，不能手改）；sitemap 仍为 89 条，其中 rig 相关 8 条，`ft710.html` 零残留
- 全站引用改到新地址：首页中英卡片、博客中英延伸阅读；`portal/rig/index.html` 与 `zh/` 各新增一张 **"配套专题 / Companion"** 卡片（不编为第 3 期，因为 FT-710 是在产现代机而非传奇老机）
- **顺带修掉一批中文页指向英文页的链接**：FT-710 中文页 navbar（`/zh/`、`/zh/#projects`、`/zh/agentic.html`、`/zh/engineering.html`、`/rig/ft710/zh/`），以及 `rig/ic-r9000/zh` 与 `rig/nrd-535/zh` 的面包屑与页脚（`/zh/`、`/rig/zh/`、`/rig/ic-r9000/zh/`）
- 迁移前后结构逐项比对一致：id 11/11、class 多重集 155/155、`<table>` 14/14、`<pre>` 1/1、`data-claim-type` 6/6、数字与型号 token（英文 860、中文 857）完全相同；变化的 36 处属性全部是路径与 canonical
- **发现并规避了一个部署风险**：仓库里的 `nginx/vlsc.net.conf` 与线上配置**已漂移**——线上用 `resolver` + 变量式 `proxy_pass`（按 DNS 名回源，家庭 IPv6 变更无需 reload），仓库副本仍是硬编码 IPv6 地址。因此**没有整份覆盖线上配置**，而是在本地副本与线上文件上做同一处精准插入（线上先备份为 `vlsc.net.bak-ft710-301-20260928202700`，`nginx -t` 通过后 reload）。仓库副本仍落后于线上，需要单独同步

**线上验证**：`/rig/ft710/`、`/rig/ft710/zh/`、`/rig/`、`/rig/zh/`、两篇老文章中文版全部 200；`/ft710.html` 与 `/zh/ft710.html` 均 **301** 到对应新地址；sitemap 89 条且无 `ft710.html`；首页中英卡片、RIG 落地页（4 处引用）、博客中文版延伸阅读均已指向新地址。备份：`/var/www/backups/landing_20260928_202725.tgz`。

## 核心结论速查

**IC-R9000（1989–98）**：通病根因是散热——REG/DC-DC 电解电容批量干涸、CRT 烧屏且官方停修（只能第三方 LCD 改装）。保养三板斧：加风扇、预防性换 105°C 电容、记忆电池不断电更换。

**NRD-535（非 D 版）**：与 535D 主机相同，只差 ECSS（CMF-78）/BWC（CFL-243W）/1 kHz 滤波器（CFL-233）三块选件板；最大通病是 VFD 荧光屏变暗熄灭（无备件，可试换显示板 4 只高压电容）；AGC 过冲有官方/第三方修法。
