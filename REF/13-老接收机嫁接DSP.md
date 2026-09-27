# 调研原始记录：给老接收机嫁接数字解调/DSP

> 调研任务：调研在模拟接收机中频或音频级嫁接现代 DSP 的通用方案（10.7 MHz/455 kHz IF 接 SDR 做数字解调、外置音频 DSP bhi/Timewave、SDR 软件能补齐哪些功能短板）。重点回答：IC-R9000 缺的同步检波、数字降噪、可变滤波能否通过外挂补齐，代价是什么。
>
> 执行：并行调研代理（agent-31），2026-09-27。

---

**核心结论：同步检波、数字降噪、可变滤波三大短板，通过"10.7 MHz IF → SDR"外挂可以接近完整补齐，且 R9000 恰好是这类改装最容易的机型之一（自带 10.7 MHz IF 输出、IF 频率全波段恒定）。但外挂补不了前端动态范围、本振噪声和互调——这些在信号进入 IF 之前就已经定型了；代价是需要一台常开 PC、音频延迟、以及 R9000 的模拟 AGC 仍然先于 SDR 起作用。**

## 1. IC-R9000 的先天条件：IF 嫁接的"理想宿主"

- **后背板自带 10.7 MHz IF OUT（RCA 插座）**。荷兰无线电监测局（RCD/AT）当年把约 20 套 R9000 接入 PAN-2000 FFT 拦截系统时，就是取这个 10.7 MHz 口；其改装档案记录了原厂输出的两个缺陷：RCA（CINCH）插座不适合射频、且走线位置会拾取杂散和噪声，他们的做法是改到 BNC、换特氟龙同轴直接焊在 IF 单元上（[Crypto Museum: IC-R9000 modifications](https://www.cryptomuseum.com/df/icom/icr9000/mod.htm)）。这提示：做 SDR 嫁接时换 BNC/优质同轴是有官方先例的"标准动作"。
- **10.7 MHz 第二中频全波段恒定**。TSP（意大利 IFace 缓冲板厂商）的 R9000 专用教程指出：R9000 有多个混频器，但**第二混频器之后 IF 恒为 10.7 MHz，与接收频段无关**，因此只需在 IF UNIT 上取一个点即可覆盖 0.1–2000 MHz 全频段，不需要 PTT（[TSP: IC-R9000 with SDR panadapter](https://www.tspelettronica.com/en/2020/06/29/panadapter-sdr-per-ic-r9000/)）。
- **注意频谱反转**。RadioReference 论坛实测帖确认：**R9000 的 IF 输出频谱是反转的**，接数字解码器（AOR AR-DV1）时必须把其 "IF DIR" 设为 REV 才能正确解码；改好后"set and forget"。另一个实测教训：IF OUT 电平偏低时，先换优质 BNC 同轴（旧 RCA 视频线在 10.7 MHz 损耗大）而不是加放大器（[IC-R9000 & digital modes](http://forums.radioreference.com/threads/ic-r9000-digital-modes.475682/)）。

## 2. 取 IF 接 SDR 的通用做法与关键工程问题

- **取样点与带宽的取舍**：取在混频器之后、滤波器之前 → SDR 看到数 MHz 宽的频谱（全景显示），但不能当独立第二接收机用；取在滤波器之后（R9000 原厂 IF OUT 即属此类）→ 只剩中频滤波器带宽内的信号，适合"数字化解调当前频道"而非宽带监视。KV5R 的 IC-7100 IF tap 教程（取点在第一混频器后、roofing 滤波器前）对此有清晰论述，并强调取点处有 DC 偏置需隔直电容（5 pF），且从取点起"就是两台独立的收音机"（[KV5R: 7100 Panadapter](https://kv5r.com/ham-radio/2018-projects/7100-panadapter/)）。
- **必须缓冲，否则会把主机"吸哑"**。Drake R-4B 加装 panadapter 的实录：直接把 Clifton Labs Z10000 缓冲板（低阻输入设计）接到电子管机第一混频器，"把信号全吸走了，收音机几乎哑掉"，最后改用高阻 JFET 源极跟随器（10 pF 耦合）才解决——"50 Ω 的常规放大器会把老收音机彻底加载"（[smbaker.com: Panadapter for Drake R-4B](https://www.smbaker.com/adding-a-panadapter-to-a-drake-r-4b-ham-radio-receiver)）。R9000 是固态机，加载问题小得多（原厂 IF OUT 已是缓冲输出），但若在机内新增取点仍需高阻缓冲或 IFace 类成品板。
- **SDR 硬件选择**：10.7 MHz 恰在 RTL-SDR 直采范围之上，KV5R 建议选带 TCXO 的 RTL-SDR V3（约 $23）即可胜任 IF 监视；若要兼顾"第二接收机"和低噪声，上 14 bit 的 SDRplay RSP1A（约 $120，带 11 组带通滤波）。他特别警告廉价 $15 DVB 棒"无屏蔽、无保护、振荡器不稳"（[KV5R](https://kv5r.com/ham-radio/2018-projects/7100-panadapter/)）。
- **校准**：HDSDR 提供 ExtIO 的 IF/变频器频率选项与 PPM 校准，配合 OmniRig/CAT 与主机联动；KV5R 给出用 WWV 10 MHz 把主机与 SDR 都校到 ±1 Hz 级的具体流程（[KV5R](https://kv5r.com/ham-radio/2018-projects/7100-panadapter/)）。HDSDR 官方更新日志还确认有专门的 **S-meter 校准**（Options/Misc Options）与频率校准入口（[HDSDR What's new](http://www.hdsdr.de/wnew.html)）。

## 3. 同步检波：外挂能否补齐——能，而且要管理预期

- **HDSDR 原生支持 ECSS**（AM、ECSS、FM、SSB、CW 解调，另有降噪、噪声消隐、可调带通、自动陷波 + 最多 10 个手动陷波）（[HDSDR 官网](https://www.hdsdr.de/)）。所谓 ECSS 就是用 SSB 模式零拍 AM 载波，等效于可选边带的同步检波。
- **同步检波解决什么**：选择性衰落使载波相对边带衰落 10–20 dB，等效过调制，包络检波产生刺耳失真；同步检波在机内再生一个稳定的本地载波，消除这类失真，且乘积检波无包络检波的小信号阈值问题，还能任选边带避开邻频干扰（[fallows.ca: Understanding Synchronous Detection](https://play.fallows.ca/wp/radio/shortwave-radio/understanding-synchronous-detection/)）。
- **预期管理（非常重要）**：SWLing Post 的"同步检波速成课"用双机录音对照证明：同步检波**只对选择性衰落失真有效，对普通衰落（那是 AGC 的事）无能为力**；"救活极弱台"是营销话术，成功率方差很大——载波一旦跌入噪声底，真同步检波会失锁啸叫，伪同步检波（载波限幅再生式，如 Belka、NRD-525/535 的 AM 模式）只是静音。其价值是"让中等强度以上的节目长时间可听"，即消疲劳而非创造奇迹（[SWLing: sync detector crash course](https://swling.com/blog/2021/09/guest-post-a-synchronous-detector-crash-course/)）。
- **对 R9000 的意义**：R9000 是包络检波 AM（无同步、无 ECSS 便利——虽然有 SSB 可手动零拍，但模拟机频率稳定度/调谐步进让 ECSS 操作繁琐）。经 IF 接 SDR 后，HDSDR 的 ECSS + AFC 自动锁载波，等于免费获得"自动版同步检波"，这是**补齐最彻底的一项**。

## 4. 外置音频 DSP：bhi 与 Timewave DSP-599zx 的实际水平

- **bhi（英国）**：官方/渠道标称 NES10-2 MK4 可消除**最多 40 dB 噪声、8 级可调（8–40 dB），外加最多 65 dB 单音消除**（[Comtek: NES10-2 MK4](https://comtekradio.com.au/nes10-2-mk4-amplified-dsp-noise-eliminating-speaker/)）；另一渠道给出模块级指标"降噪 9–35 dB、8 级"（[Andrews Communications](http://www.andrewscom.com.au/site-content-section-01-speakers.htm)）。SWLing Post 实测 Compact In-Line（约 $260）：在太阳耀斑导致的恶劣噪声下"噪声消失"，AM/FM/SSB/气象频道全部受益、显著降低听觉疲劳；**局限：消不干净时仍剩底噪、强度调太高会使语音失真并干扰 SSB 调谐、有"流水声"数字伪影**（[SWLing: bhi Compact In-Line 评测](https://swling.com/blog/2021/11/jock-reviews-the-bhi-compact-in-line-noise-eliminating-module/)）。eHam 有用户认为 bhi 的音频 DSP 优于 FT-710 内置 DNR（[eHam 评测](https://www.eham.net/reviews/detail/12414)，页面本体 403，结论摘自搜索摘要）。
- **Timewave DSP-599zx**：官方数据页给出硬指标——随机降噪**最多 20 dB**（随噪声特性浮动），自动多重陷波消差拍**最多 50 dB**，延迟：降噪/陷波 5 ms、语音滤波 21 ms、CW 窄滤波 34–58 ms；语音高低通 100–1000 Hz / 1000–5000 Hz（10 Hz 步进，带外 180 Hz 处 60 dB）、CW 带宽 5–600 Hz（5 Hz 步进）；AGC 语音 36 dB / CW 18 dB；16 bit ADSP-2181。安装就是串在电台与音箱之间（[Timewave DSP-599zx 官方数据](http://old.timewave.com/support/DSP-599/599data.html)）。eHam 评价摘要："对大气/电气随机噪声的降噪有效，高低切滤波好用"（[eHam: DSP-599zx 评测](https://www.eham.net/reviews/detail/209)，取自摘要）。
- **横向判断**：外置音频 DSP 只拿到检波后的音频——**无法恢复已被中频滤波器挡掉的邻频干扰、无法做同步检波、无法提供频谱**。它能补"数字降噪"这一项（bhi 的 40 dB 甚至强于多数 SDR 软件的 NR），但补不了另外两项。相反，SDR 软件的 NR/NB/ANF 作用在 I/Q 上，信息更全。

## 5. SDR 软件到底能给 R9000 补齐什么（功能清单对照）

经 HDSDR + IF 链路可获得（[HDSDR 官网](https://www.hdsdr.de/)）：
- **同步 AM / ECSS + AFC** —— R9000 完全没有，补齐；
- **可变带宽数字滤波**（任意拖带宽，另有多达 10 个手动陷波 + 自动陷波）—— R9000 只有固定几档机械/陶瓷滤波器，补齐且超越；
- **数字降噪、噪声消隐** —— 补齐（性能大致相当于中高档音频 DSP，视算法而定）；
- **校准过的 S 表（dBm/S 值）**—— R9000 的模拟 S 表精度一般，HDSDR 提供 S 表校准（[更新日志](http://www.hdsdr.de/wnew.html)）；
- **频谱/瀑布、录音（RF/IF/AF WAV）、数字模式解码**——经 10.7 MHz IF 接 AR-DV1 之类的硬件解码器甚至无需 PC 即可解 DMR/D-STAR/C4FM/TETRA（[RadioReference 实测](http://forums.radioreference.com/threads/ic-r9000-digital-modes.475682/)）。

**补不了的（关键代价）**：
1. **前端动态范围与互调**：窄间隔 DR 71 dB@5 kHz、本振相位噪声 128 dBc/Hz 是 R9000 模拟前端在混频前就定型的，SDR 收到的是已经"带伤"的 IF 信号。外挂方案做的是"解调链现代化"，不是"射频链现代化"。
2. **AGC 次序**：若取原厂 IF OUT（滤波后、AGC 后），强台引起的模拟 AGC 压缩先于 SDR 发生，SDR 端无法再恢复瞬时动态；用混频器后取点可绕开，但失去中频滤波的选择性保护。
3. **操作形态改变**：需要常开 PC、软件延迟（SDR 软件缓冲通常数十 ms 级；音频 DSP 硬件仅 5–58 ms，见 Timewave 数据）、调谐变成"R9000 旋钮 + 鼠标"双界面；CI-V 可经 OmniRig 联动缓解。
4. **杂散与屏蔽**：原厂 RCA IF 口会拾取杂散（Crypto Museum 记录），接 PC 还引入 USB/地环路噪声风险（KV5R 建议 USB 线加 FT-140 磁环）。

## 6. 给改造方案的直接建议（基于上述证据）

- **优先路线：机内第二混频器后高阻缓冲取 10.7 MHz（IFace 或自制 JFET 跟随器）→ 带 TCXO 的 RTL-SDR/SDRplay → HDSDR（ECSS+NR+可变滤波+校准 S 表）**。这一条同时补齐三大短板，成本 $25–120 + 缓冲板，且有针对 R9000 的现成商业化教程（TSP）。
- **无 PC 场景的补充**：bhi Compact In-Line / NES10-2 MK4（降噪这一项的最强即插即用方案，$260 级）或二手 DSP-599zx（滤波 + 陷波 + 降噪 + RTTY 调制解调一体）。
- **数字模式**：AR-DV1 接 IF OUT，记得设 IF DIR = REV、用优质 BNC 线。
- **射频性能不要再投入**：71 dB 的窄间隔动态靠外挂无解，如确实需要，只能在一中频前加滤波/衰减器等前端手段，超出"嫁接 DSP"范畴。

**来源汇总**（正文已内联）：Crypto Museum（R9000 官方改装档案）、TSP IFace R9000 教程、KV5R IC-7100 panadapter 长文、smbaker.com Drake R-4B、HDSDR 官网及更新日志、fallows.ca 同步检波原理、SWLing Post 同步检波速成课与 bhi 评测、Timewave 官方数据页、Comtek/Andrews bhi 指标、RadioReference R9000 数字模式实测帖、eHam 评测摘要。
