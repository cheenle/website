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

## 核心结论速查

**IC-R9000（1989–98）**：通病根因是散热——REG/DC-DC 电解电容批量干涸、CRT 烧屏且官方停修（只能第三方 LCD 改装）。保养三板斧：加风扇、预防性换 105°C 电容、记忆电池不断电更换。

**NRD-535（非 D 版）**：与 535D 主机相同，只差 ECSS（CMF-78）/BWC（CFL-243W）/1 kHz 滤波器（CFL-233）三块选件板；最大通病是 VFD 荧光屏变暗熄灭（无备件，可试换显示板 4 只高压电容）；AGC 过冲有官方/第三方修法。
