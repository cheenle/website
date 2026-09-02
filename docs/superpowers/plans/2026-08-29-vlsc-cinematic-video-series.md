# VLSC 电影级视频系列实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 制作 Portal 总片与七个项目片共八部约 30 分钟的中英双语电影级技术宣传片，并交付可恢复、可审计的生成与远程合成管线。

**架构：** 前期由 10 个 GPT-5.5 agent 并行生成互不重叠的事实表、双语脚本、分镜和生产管线；中心审校把来源、术语和能力边界合并为共享契约。后续以 GPT Image 2 生成 4K 参考帧，以 Seedance 2.0 reference/image-to-video 生成镜头候选，大素材同步到 `ham.vlsc.net`，由 ffmpeg 在 4K 时间线上完成合成和 QC。

**技术栈：** MuleRun Studio、GPT-5.5/OpenCode、GPT Image 2、Seedance 2.0、Veo 3.1/Kling V3 Omni、Python 3、JSON Schema、Bash、rsync/SSH、ffmpeg/ffprobe。

---

## 文件结构

- 创建：`promo-videos-long/shared/production-contract.md` — 所有 agent 的统一交付契约。
- 创建：`promo-videos-long/shared/capability-matrix.json` — 跨项目能力与来源矩阵。
- 创建：`promo-videos-long/shared/glossary.json` — 中英术语与发音。
- 创建：`promo-videos-long/shared/visual-bible.md` — 视觉、镜头、颜色、禁用模式。
- 创建：`promo-videos-long/shared/pipeline/generate.py` — 可恢复的 MuleRun 任务队列。
- 创建：`promo-videos-long/shared/pipeline/render.sh` — 远程 ffmpeg 合成入口。
- 创建：`promo-videos-long/shared/pipeline/qc.py` — manifest、媒体与响度检查。
- 创建：`promo-videos-long/shared/schema/storyboard.schema.json` — 分镜清单约束。
- 创建：`promo-videos-long/<site>/facts.json` — 带来源的事实表。
- 创建：`promo-videos-long/<site>/script-en.md`、`script-zh.md` — 双语旁白和画面提示。
- 创建：`promo-videos-long/<site>/storyboard.json` — 逐镜头生产 manifest。
- 创建：`promo-videos-long/<site>/prompts/*.json` — 图像、视频、音频提示。
- 创建：`promo-videos-long/<site>/generated/` — 模型返回 JSON 与下载媒体。
- 创建：`promo-videos-long/<site>/out/` — 4K/1080p 主片、字幕、预告及社媒版。

### 任务 1：冻结生产契约与目录

- [ ] **步骤 1：创建隔离目录**

运行：

```bash
mkdir -p promo-videos-long/{shared/{pipeline,schema,reviews},portal,mrrc,mrrc_ft710,mrrc_ft8,mrrc_modern,sunmrrc,SunsdrMobile,efhw}
for s in portal mrrc mrrc_ft710 mrrc_ft8 mrrc_modern sunmrrc SunsdrMobile efhw; do
  mkdir -p "promo-videos-long/$s"/{research,prompts,refs,generated,audio,intermediate,out}
done
```

预期：八个站点目录均存在，且不修改现有 `promo-videos/`。

- [ ] **步骤 2：写入统一契约**

契约必须要求：28–32 分钟；中英双语；每条事实包含 `source_path` 和 `source_excerpt`；每个镜头包含 ID、章节、时长、类型、画面、旁白、来源、生成模型、参数和状态；模型生成画面禁止承载可读 UI 文本及工程数字。

- [ ] **步骤 3：验证目录和契约**

运行：

```bash
test -f promo-videos-long/shared/production-contract.md
find promo-videos-long -maxdepth 2 -type d | sort
```

预期：命令退出码为 0，出现八个站点目录。

### 任务 2：并行完成八个站点制片包

- [ ] **步骤 1：启动八个 GPT-5.5 agent**

每个 agent 仅写一个 `promo-videos-long/<site>/`，读取对应站点全部 HTML/Markdown/SVG/图片和设计文档，交付：

```text
facts.json
script-en.md
script-zh.md
storyboard.json
prompts/images.json
prompts/videos.json
prompts/audio.json
research/source-index.md
agent-report.md
```

每个 agent 使用：

```bash
mulerun code -a opencode -m openai/gpt-5.5 --effort high -- "<site-specific self-contained prompt>"
```

八条命令后台并发，stdout/stderr 分别写 `promo-videos-long/shared/logs/<site>.log`。

- [ ] **步骤 2：验证八个 agent 的交付完整性**

运行：

```bash
for s in portal mrrc mrrc_ft710 mrrc_ft8 mrrc_modern sunmrrc SunsdrMobile efhw; do
  test -s "promo-videos-long/$s/facts.json"
  test -s "promo-videos-long/$s/script-en.md"
  test -s "promo-videos-long/$s/script-zh.md"
  test -s "promo-videos-long/$s/storyboard.json"
done
```

预期：退出码 0。

### 任务 3：并行完成全局审校与生产管线

- [ ] **步骤 1：启动第九个 GPT-5.5 agent 进行全局事实审校**

该 agent 读取八个站点及其源站文件，写入 `capability-matrix.json`、`glossary.json` 和 `reviews/cross-site-review.md`；报告所有能力串线、来源不足、中文术语不一致和重复段落。

- [ ] **步骤 2：启动第十个 GPT-5.5 agent 实现管线**

该 agent 仅写 `promo-videos-long/shared/pipeline/`、`shared/schema/`、`shared/visual-bible.md` 和测试；必须提供 dry-run、任务持久化、并发上限 10、指数退避、SHA-256 下载校验、SSH/rsync、ffprobe 和响度 QC。

- [ ] **步骤 3：验证管线测试**

运行：

```bash
python3 -m unittest discover -s promo-videos-long/shared/pipeline/tests -v
python3 promo-videos-long/shared/pipeline/generate.py --help
python3 promo-videos-long/shared/pipeline/qc.py --help
```

预期：全部测试通过，两个 CLI 帮助退出码为 0。

### 任务 4：中心整合与脚本质量门

- [ ] **步骤 1：验证 JSON**

运行：

```bash
find promo-videos-long -name '*.json' -print0 | xargs -0 -n1 python3 -m json.tool >/dev/null
```

预期：退出码 0。

- [ ] **步骤 2：验证时长与词数**

`qc.py scripts` 检查每种语言旁白目标 3,600–4,800 英文词等效量，镜头总时长为 1,680–1,920 秒，章节完整且镜头 ID 唯一。

运行：

```bash
python3 promo-videos-long/shared/pipeline/qc.py scripts promo-videos-long
```

预期：八个站点均显示 PASS；任何 FAIL 必须回到对应 agent 修正。

- [ ] **步骤 3：关闭事实审校问题**

中心协调器逐项处理 `cross-site-review.md` 中的 Critical/Major 问题，并将处置写入 `reviews/resolutions.md`。

### 任务 5：生成视觉参考与 2–3 分钟风格样片

- [ ] **步骤 1：为每站点生成关键参考图**

使用 GPT Image 2：

```bash
mulerun studio run openai/gpt-image-2/generation \
  --prompt "<prompt from prompts/images.json>" \
  --quality high --size 3840x2160 --n 2 --format png --json
```

每站点至少生成角色/设备、主环境、章节卡三组参考图；保存请求 JSON、响应 JSON 和图片哈希。

- [ ] **步骤 2：用 Seedance 2.0 生成样片镜头候选**

优先参考图生视频：

```bash
mulerun studio run bytedance/seedance-2.0/image-to-video \
  --image "<reference.png>" --prompt "<motion prompt>" \
  --resolution 1080p --aspect-ratio 16:9 --duration 15 \
  --generate-audio true --json
```

每个关键镜头生成两个候选；英雄镜头生成四个候选。输出不得带水印。

- [ ] **步骤 3：同步到远程服务器**

运行：

```bash
rsync -az --partial --info=progress2 promo-videos-long/ ham.vlsc.net:~/vlsc-video-production/
```

预期：rsync 成功，远程 `find ~/vlsc-video-production -type f` 可见资产。

- [ ] **步骤 4：远程合成样片并 QC**

运行：

```bash
ssh ham.vlsc.net 'cd ~/vlsc-video-production && bash shared/pipeline/render.sh --pilot --all'
ssh ham.vlsc.net 'cd ~/vlsc-video-production && python3 shared/pipeline/qc.py media --all'
```

预期：每站点产生 120–180 秒样片；无黑帧、冻结、损坏媒体、音画不同步和响度超标。

### 任务 6：批量生成全部镜头、配音与音乐

- [ ] **步骤 1：运行全量生成队列**

运行：

```bash
python3 promo-videos-long/shared/pipeline/generate.py enqueue --all --models gpt-image-2,seedance-2.0
python3 promo-videos-long/shared/pipeline/generate.py run --all --concurrency 10 --resume
```

预期：所有任务进入 `succeeded`、`rejected` 或可解释的 `failed` 状态，进程重启不会重复计费任务。

- [ ] **步骤 2：质量淘汰和兜底重生**

对畸变、伪文字、闪烁、错误设备外观和叙事不连续的候选标为 `rejected`。仅对被拒镜头使用 Veo 3.1 或 Kling V3 Omni 生成新候选，直到每个必需镜头至少有一个通过项。

- [ ] **步骤 3：生成双语配音和分段音乐**

每个站点生成独立中英旁白，章节级音频必须与脚本哈希绑定；每部片生成 4–6 段器乐，旁白闪避后混音。专有名词、呼号和型号按 `glossary.json` 发音。

### 任务 7：远程 4K 合成与衍生输出

- [ ] **步骤 1：同步通过审核的资产**

```bash
rsync -az --partial --delete-delay promo-videos-long/ ham.vlsc.net:~/vlsc-video-production/
```

- [ ] **步骤 2：生成中英主片**

```bash
ssh ham.vlsc.net 'cd ~/vlsc-video-production && bash shared/pipeline/render.sh --master --all --languages en,zh'
```

每站点输出 `master-en-4k.mp4`、`master-zh-4k.mp4`、1080p 版本、独立字幕和旁白音轨。

- [ ] **步骤 3：生成预告和社媒版**

```bash
ssh ham.vlsc.net 'cd ~/vlsc-video-production && bash shared/pipeline/render.sh --derivatives --all --formats 16:9,9:16,1:1'
```

每站点至少输出 60–90 秒预告、30 秒和 15 秒切片。

### 任务 8：最终验证与交付索引

- [ ] **步骤 1：运行全量媒体检查**

```bash
ssh ham.vlsc.net 'cd ~/vlsc-video-production && python3 shared/pipeline/qc.py media --all --strict'
```

预期：所有必需输出 PASS；主片时长 1,680–1,920 秒，True Peak ≤ -1 dBTP，目标响度约 -14 LUFS。

- [ ] **步骤 2：生成交付清单**

创建 `promo-videos-long/README.md`，列出每个成片的语言、时长、分辨率、文件大小、SHA-256、远程路径和使用的模型版本。

- [ ] **步骤 3：保留可恢复状态**

确认所有 task ID、请求参数、响应 JSON、下载哈希、审核状态和渲染日志均存在；删除缓存前先验证远程和本地索引一致。
