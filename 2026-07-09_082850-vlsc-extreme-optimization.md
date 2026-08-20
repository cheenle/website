# VLSC 2026 极致优化总方案（核验版）

> 文档更新时间：2026-07-09 09:25 (Asia/Shanghai)  
> 核验窗口：2026-07-09 08:43-09:08 (Asia/Shanghai)  
> 目标：把 VLSC 从“项目展示页”升级为“高可信、强转化、可传播的开源 HAM Remote Control 官网”。

---

## 1. 执行摘要（先做什么）

先做 5 件事，收益最大：

1. 首页首屏直接回答“我该用哪个项目”。
2. 四项目卡片改为稳定 2x2 布局（桌面）+ 1 列（移动端）。
3. Demo 区加状态门禁（在线/维护），避免用户点击即失败。
4. Trust Metrics 改为“自动拉取数据”，不用手写数字。
5. 把 FDE 提升到首页核心模块，建立工程可信度而不是只讲功能。

---

## 2. 事实基线（已核验，不凭感觉）

### 2.1 站点与 Demo 可达性快照

| 项目 | 结果 | 细节 | 结论 |
|---|---|---|---|
| `https://www.vlsc.net` | 可达 | HTTP 200；`server: nginx/1.28.3`; `last-modified: Wed, 08 Jul 2026 05:02:24 GMT` | 主站在线 |
| `https://radio.vlsc.net:8877/mobile_modern.html` | 不可达 | 连接失败（port 8877） | Demo 入口存在可达性风险 |
| `https://radio.vlsc.net:8889/` | 不可达 | 连接失败（port 8889） | Demo 入口存在可达性风险 |

说明：以上是 2026-07-09 的实时探测结果；Demo 端口可能随维护窗口变化，应做自动状态展示，避免首页误导。

### 2.2 仓库元数据快照（GitHub API）

| Repo | Stars | Forks | License (API识别) | 最近 Push (UTC) | Commit 总量（main） |
|---|---:|---:|---|---|---:|
| `cheenle/UHRR_mac` | 7 | 2 | GPL-3.0 | 2026-06-19 14:18:23 | 119 |
| `cheenle/mrrc_ft710` | 0 | 0 | 未识别 | 2026-07-08 22:53:15 | 40 |
| `cheenle/sunsdr` | 1 | 0 | 未识别 | 2026-07-04 12:06:45 | 61 |
| `cheenle/SunsdrMobile` | 1 | 0 | 未识别 | 2026-07-04 10:24:56 | 4 |

关键结论：

- 主页若宣称统一许可证（如“GPLv3/MIT”）需谨慎；目前 API 仅明确识别 `UHRR_mac`。其余仓库建议补标准 `LICENSE` 文件并保持 SPDX 可识别。
- 可信度数字应改为自动拉取，避免“发布后 1 周即过时”。

---

## 3. 定位升级（5 秒内让用户懂）

### 3.1 一句话定位（英文）

`Open-source remote radio control ecosystem for modern HAM operators.`

### 3.2 一句话定位（中文）

`面向现代业余无线电操作的开源远程控制生态。`

### 3.3 Hero 副标题（建议替换现文案）

英文：

`Control HF and SDR radios from anywhere — browser, phone, or native iOS app.`

中文：

`用浏览器、手机或 iOS 原生 App，在任何地方安全控制你的 HF/SDR 电台。`

---

## 4. 首页信息架构（最终建议顺序）

1. Hero：定位 + 三个 CTA（Find Your Project / GitHub / Demo）。
2. Which Project Should I Use?：用户选择表（必须在首屏下）。
3. Four Projects：四卡 2x2。
4. Live Demo：入口 + 在线状态 + 维护说明。
5. Three Architectures, One Vision：架构差异可视化。
6. Built Through FDE：工程演化与复用能力。
7. Trust Metrics：自动同步数字。
8. Final CTA：Repo / Docs / Deployment。

---

## 5. 最高优先级改造（P0）

### P0-1：增加“Which Project Should I Use?”

```markdown
## Which Project Should I Use?

| I have... | Use | Why |
|---|---|---|
| Any HF radio with CAT | MRRC | Universal remote control via Hamlib/rigctld |
| Yaesu FT-710 | MRRC FT-710 | Software SCU-LAN10 replacement via one USB cable |
| SunSDR2 DX | SunMRRC | SDR server with UDP IQ demodulation and real-time waterfall |
| iPhone + SunSDR2 DX | SunsdrMobile | Native iOS client for SunMRRC |
```

### P0-2：项目卡片布局固定为 2x2

```css
.features-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 24px;
}

@media (max-width: 900px) {
  .features-grid {
    grid-template-columns: 1fr;
  }
}
```

### P0-3：Live Demo 状态门禁

```html
<div class="demo-status demo-status--offline">● Demo Currently Unavailable</div>
<p class="demo-note">Demo station may be under maintenance. Source code and setup guide are always available.</p>
```

规则：

- 状态为 Offline 时，不隐藏 Demo，而是弱化按钮 + 给出备用路径（GitHub/Docs）。
- 状态文案必须中英双语一致。

### P0-4：把“不可验证指标”改为“可证据指标”

不再直接写死 `<100ms`、`15-20dB` 等数字，除非给出测试条件和测量方法。建议模板：

- 指标值
- 测试环境（本地/公网，设备型号）
- 测试日期（绝对日期）
- 测试方法（脚本/命令）

---

## 6. P1（7天内）与 P2（后续）

### P1（7天内）

1. FDE 模块上移到首页中部（项目之后，Trust 之前）。
2. 项目页统一结构：Hero / Who it is for / Architecture / Demo / Install / Safety / FAQ。
3. Open Graph 与社媒缩略图上线（1200x630）。
4. 中英文页面内容对齐并校验链接一致性。

### P2（后续）

1. Demo 状态 API 化（而非手写）。
2. 增加架构图和 20-30 秒短视频（产品级传播素材）。
3. 实装 Lighthouse/可访问性门槛，接入 CI 检查。

---

## 7. Trust Metrics 自动化（强烈建议落地）

目标：首页数字每日自动刷新，避免信息陈旧。

### 7.1 数据源

- GitHub API：stars/forks/pushed_at/commit_count/license。
- Demo health endpoint：8877/8889 可达状态。

### 7.2 最小可行实现（建议）

1. 每天定时任务抓取四个 Repo 数据。
2. 生成 `metrics.json`。
3. 首页前端读取 `metrics.json` 展示。
4. Demo 状态每 1-5 分钟刷新一次（服务端缓存）。

### 7.3 需要展示的字段

- `repo_name`
- `stars`
- `forks`
- `license`
- `last_push_utc`
- `commit_count_main`
- `demo_8877_status`
- `demo_8889_status`

---

## 8. Image/视频内容生产（可直接喂模型）

你要求“最佳效果最优展示”，这里给出可直接执行的媒体资产清单与提示词。

### 8.1 必做视觉资产（Image）

1. `og-vlsc-projects-1200x630.png`（社媒分享图）
2. `hero-spectrum-bg-2560x1440.png`（首屏背景）
3. `architecture-flow-1920x1080.png`（三架构流向图）

#### Image Prompt（英文，通用高质量模型）

```text
Create a premium technical hero image for an open-source amateur radio remote control ecosystem.
Style: dark engineering aesthetic, precise signal-flow lines, subtle spectrum waterfall texture, high contrast, clean typography zones.
Color palette: near-black background, amber accent (#f59e0b), cool gray text tones.
Include abstract motifs for radio transceiver, server, browser, and mobile device connected through low-latency signal paths.
No logos of third-party brands, no clutter, no fake UI text.
Output: ultra-clean, production website quality.
```

### 8.2 必做传播资产（Video）

1. `vlsc-ecosystem-teaser-25s-1080p.mp4`
2. `vlsc-demo-walkthrough-45s-1080p.mp4`

#### Video Prompt（25 秒 Teaser）

```text
Produce a 25-second cinematic but technical product teaser for an open-source HAM radio remote control ecosystem.
Scene 1 (0-6s): radio hardware in dark lab environment, signal lines activating.
Scene 2 (6-12s): architecture transition showing CAT/Hamlib, Direct USB FT-710, and UDP IQ SDR pipelines.
Scene 3 (12-18s): browser and iOS interfaces receiving real-time spectrum and audio streams.
Scene 4 (18-25s): trust metrics and call-to-action: "Open Source. Real Operation. Built for Modern HAM."
Visual style: premium, sharp, engineering-focused, no hype effects, realistic UI overlays.
```

### 8.3 媒体验收标准

- 首页首屏可读性不被背景图破坏（文本对比度达标）。
- OG 图在社媒小图下仍可读主标题。
- 视频首 3 秒能识别“这是 HAM remote control 生态”。
- 全部素材都有中英文版本的字幕/文案。

---

## 9. 直接可替换的首页文案块

### 9.1 Hero（EN）

```text
VLSC Projects
Open-source remote radio control ecosystem

Control HF and SDR transceivers from anywhere — browser, phone, or native iOS app.

[Find Your Project] [Try Live Demo] [GitHub]
```

### 9.2 Hero（ZH）

```text
VLSC 项目
开源业余无线电远程控制生态

用浏览器、手机或 iOS 原生 App，在任何地方控制你的 HF/SDR 电台。

[选择适合你的项目] [试用在线演示] [GitHub]
```

### 9.3 Trust Block（EN）

```text
Engineering Metrics (auto-updated)
MRRC: 119 commits · 7 stars
MRRC FT-710: 40 commits
SunMRRC: 61 commits
SunsdrMobile: 4 commits
```

### 9.4 Demo Fallback（EN）

```text
Live demo may be temporarily unavailable during maintenance.
You can always access source code and deployment guides.
```

---

## 10. 14 天落地排期（可执行）

### Day 1-2

- 首页新增 Project Selector + 2x2 卡片布局。
- Hero 文案替换为“价值 + 设备覆盖 + 终端覆盖”。

### Day 3-4

- Demo 状态门禁上线（Offline 文案与降级路径）。
- Trust Metrics 区块接入 `metrics.json`。

### Day 5-7

- FDE 模块上移并精简成“可读故事 + 时间线”。
- 中英文页面对齐检查。

### Day 8-10

- OG 图 + Hero 背景图 + 架构图产出并压缩。
- Open Graph 标签与分享测试。

### Day 11-14

- 25 秒 teaser 视频 + 45 秒 walkthrough 视频。
- Lighthouse、移动端、键盘可访问性回归。

---

## 11. 验收标准（Definition of Done）

满足以下条件才算“优化完成”：

1. 用户 10 秒内能完成项目选择（有清晰路径，不靠猜）。
2. 首页所有关键数字来自自动数据源，而非手写。
3. Demo 不可达时页面不会造成“死链挫败”。
4. 社媒分享图、短视频、英文/中文文案全部可发布。
5. Lighthouse（移动端）核心指标达标：
   - LCP < 2.5s
   - CLS < 0.1
   - Performance >= 90
   - Accessibility >= 95

---

## 12. 最终结论

VLSC 已经有真实工程价值，短板不在技术，而在“表达与证据系统”。

这轮优化的本质不是再写更多文案，而是三件事：

1. 让用户立即做出项目选择。  
2. 让所有关键说法都有可验证数据。  
3. 让视觉与视频素材可直接支持传播与转化。  

按本方案执行后，VLSC 的对外认知将从“几个不错的项目”升级为“可持续演进、可验证可信的开源远程电台生态”。
