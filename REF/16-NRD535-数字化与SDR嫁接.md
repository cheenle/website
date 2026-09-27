# 调研原始记录：NRD-535 的数字化与 SDR 嫁接

> 执行：主线程直接抓取，2026-09-27。来源：TSP Electronics（IFace 官方 NRD-535 教程）、drmrx.org（DRM 改装文档 V1.02 全文）、rxcontrol.org、HB9RXC RXCommander、N9EWO 链接集。

---

## 一、SDR 全景显示（panadapter）：TSP IFace 官方支持 NRD-535

来源：[TSP Electronics: NRD-535 with SDR panadapter](https://www.tspelettronica.com/en/2020/07/09/panadapter-sdr-per-nrd-535/)（2020-07-09，全文已读）

- TSP 的 **IFace 缓冲接口板**明确支持 NRD-535（与 IC-R9000 同一产品线）。
- **取点与 R9000 不同**：NRD-535 有多个混频器，panadapter 应取 **RX 链的第一个混频器**输出，因为那里的宽带信号围绕**一中频 70.455 MHz**。
- 官方文档给出：整机框图、**RF TUNE 板与 MOTHERBOARD 的原理图取样点**、PCB 实物上的 IF 信号取点与缓冲板供电取点照片。
- **不需要 PTT 信号**（纯接收机）。
- 免责声明：自行安装风险自担。

**工程含义**（与 R9000 的对比）：
- R9000 的 tap 在 10.7 MHz（全波段恒定，普通 RTL-SDR 直采即可）；
- NRD-535 的 tap 在 **70.455 MHz**，需要能覆盖 70 MHz 的 SDR——RTL-SDR 的 R820T2 调谐器模式（24–1766 MHz）可以，SDRplay/Airspy 等更宽裕；直采 HF 模式的 RTL 不行。
- 取点在第一混频后 = 频谱最宽（可显示整个波段），代价是信号未经一中频滤波，强信号环境下 SDR 自身可能过载（可用 SDR 前端衰减缓解）。

## 二、DRM 数字广播解调改装（完整文档）

来源：[Modification of JRC NRD-535 HF Receiver for the reception of DRM signals, V1.02, 11-April-2003（PDF，drmrx.org）](https://www.drmrx.org/mods/NRD_535_V102.pdf)（全文已读；镜像：[radiomanual.info](https://www.radiomanual.info/schemi/RX/JRC_NRD-535_modification_DRM_2003.pdf)）

- 原理：把机内 **455 kHz 中频用 LC 混频器下变频到 12 kHz**，经后面板新装的 3.5 mm 插座送到声卡 line-in，PC 上用 DReaM / TU-Darmstadt 软件解码。
- **LC 混频器板固定在 CFH-36A IF 滤波板上**（双面胶）。
- **供电**：CFH-36A 板上 **P30 连接器 pin 1 = 10.8 V**（接到混频器的 L8 电感，文档中红线）。
- **455 kHz 取点两种方法**：
  - 方法 1：若 CFH-36A 的 FL5 NARR 位装了额外滤波器、FL6 AUX 位空 → 用 AUX 带宽档收 DRM（其他带宽档衰减太大）；455 kHz 在 **P30 pin 22**，地在 **pin 21**。
  - 方法 2（通用）：在 **LC 滤波器（C19 并 L3）之后、FL3–FL6 滤波器之前**取 455 kHz。
- 12 kHz 输出（NF）接后面板 3.5 mm 座，左右声道都接 NF；LC 混频器地接 C4 附近的地。
- 实测（2003 年 4 月，欧洲 10 kHz 宽 DRM 广播，RF-systems GMDSS 天线）：**两种方法都无问题，SNR 高达 30 dB 不罕见**；测试机为 1 GHz Compaq Deskpro EN + 板载声卡 + Win2000。
- 评价原文："NRD-535 已用于许多模拟年头，在灵敏度、选择性和动态范围上始终证明是优质接收机。这些特性在 DRM 时代仍然重要：它们能决定是好接收还是完全收不到。"

**现状说明**：DRM30 广播在 2026 年只剩极少数发射台（主要是印度 AIR），此改装的历史与工程价值大于实用价值；但同一 12 kHz 通路也可用于其他窄带数字模式的声卡解调。

## 三、PC 遥控软件与接口

| 资源 | 内容 | 链接 |
|---|---|---|
| **RXCommander（HB9RXC）** | 瑞士火腿写的 NRD-525/535 遥控软件，"nice and simple"；站点**目前仍可访问**，并提供 **CMH-532 串口接口手册**、**CBO-232 串口接口（F4EZC 设计）图与手册**、**JRC-NRD535 CAT 协议手册** | http://hb9rxc.homeip.net/rxcommander.html |
| **rxcontrol.org NRD-535 软件** | 免费 V1.3.6 完整版：任意本地串口（COM1–8）、控制频率/模式/滤波器/AGC/噪声消隐/衰减器、实时回显所有设置、显示当前波段规划、知名频率识别、**自动选择合适的滤波带宽与检波模式**、导入频率文件、从剪贴板取频率、全键盘操作 | http://rxcontrol.org/Nrd535/index.html |
| **CMH-532** | JRC 官方电脑控制选件（串口接口板） | [Universal Radio NRD-535 附件页](https://www.universal-radio.com/catalog/commrxvr/1535.html) |
| **CBO-232** | 第三方（F4EZC）串口接口，有手册 | 见 RXCommander 页链接 |
| **原厂 RS-232C（DB-25）** | 标配，4800 baud 8/N/1，可遥控 36 项功能并回读 S 表 | [dxing.com 机型页](https://www.dxing.com/rx/nrd535.htm)、[ZCM](https://www.zcm.com.au/nrd535.htm) |
| OmniRig / HDSDR / SDR Console | 通用 CAT 桥；NRD-535 走 RS-232，社区有 ini（本次未取到 ini 文件本体，属待验证项） | — |
| 视频实证 | [JRC NRD 535 und 525 fernsteuern mit RXCommander Remote Control](https://www.youtube.com/watch?v=ze5nNf5d-LM)（德语，约 1.9 万播放） | YouTube |
| 日本自制软件 | まったりDXer's 的 Active Controller（[介绍视频](https://www.youtube.com/watch?v=9ClHzFbMHeU)、[Advanced 版](https://www.youtube.com/watch?v=fTAC-3fmNGQ)） | YouTube |

## 四、与 R9000 方案的差异总结（供改造路线使用）

| 项目 | IC-R9000 | NRD-535 |
|---|---|---|
| panadapter 取点 | 第二混频后 **10.7 MHz**（全波段恒定，滤波前） | 第一混频后 **70.455 MHz**（宽带信号） |
| SDR 要求 | 任何能收 10.7 MHz 的（RTL 直采即可） | 需覆盖 70 MHz（RTL 调谐器模式 / SDRplay / Airspy） |
| 成品缓冲板 | TSP IFace（有专文） | **TSP IFace（有专文）** |
| 频谱是否反转 | 是（需 Swap I/Q / IF DIR=REV） | 文档未提及，需实测确认 |
| 数字解调 | IF OUT → AR-DV1 等硬件解码器（10.7 MHz） | 455 kHz → 12 kHz LC 混频 → 声卡（DRM/窄带数字模式） |
| CAT | CI-V（需 CT-17/USB 转换） | **RS-232C 标配**（DB-25，含 S 表回读） |
| 同步检波 | 无，需 SE-3 外挂或 SDR 软件 ECSS | **有 ECSS 板（CMF-78）**，非 D 版可后加 |
