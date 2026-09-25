# AI 解读的持续提升流程（runbook）

闭环四件套：**日志 → 反馈 → 评测 → 提示词版本**。

## 1. 看数据

服务器 `/home/cheenle/yijing-llm-logs/`：

- `interpret_req.jsonl` / `interpret_res.jsonl`：每次解读的输入事实与回复全文，带 `version` 与耗时；
- `feedback.jsonl`：前端 👍/👎 回传（`id` 与解读记录对应），**低分条目是下一轮提示词与用例的第一来源**；
- `eval_runs/<时间>_<版本>.json`：黄金评测结果。

快速看低分：`grep '"rating": -1' feedback.jsonl | tail`。

## 2. 改提示词

1. 编辑 `llm_proxy.py` 的 `SYSTEM_PROMPT`（或 `build_payload` 的事实组织）；
2. **必须**同时升 `PROMPT_VERSION`（格式 `YYYY-MM-DD.vN`），日志与评测都靠它归因；
3. 把暴露问题的真实案例固化进 `eval_cases.json`（用 `/tmp/gen_eval_cases.js` 的方式从卦爻生成 `req`，补 `must` 检查项），让回归可测。

## 3. 评测对比

```bash
python3 yijing/server/eval_run.py            # 需 LLM_AUTH_TOKEN 环境
```

输出每用例硬校验（四段结构、引文标记、忌、免责、字数 ≤400、must 子串）与评审模型四维均分
（象数/经文/事理/行动）。与 `eval_runs/` 中上一版 json 对比：**硬校验全过且均分不降**才发布。

主机已配 systemd timer（`yijing-llm-eval.timer`，每周一 03:17 + 随机延迟，Persistent）自动跑评测留档：
`systemctl list-timers | grep yijing`；手动跑：`sudo systemctl start yijing-llm-eval.service`。

基线记录：v2（结构化四段）硬校验 0/6 → v3（点名本卦/忌不省略）2/6 → v4（450 字上限+评审 thinking 预算）4/6，
均分 象数3/经文4/事理3/行动3 → v5（每段≤三句、只析动爻）。上游内容审查误拦的用例记 skip，不计分母。

## 4. 发布

```bash
cd yijing && ./deploy.sh          # 站点与 server/llm_proxy.py 一起更新
ssh cheenle@www.vlsc.net "sudo systemctl restart yijing-llm"
```

## 红线

- 不在提示词里承诺预测结果；免责句「占断仅供参考，事在人为」是硬校验项，不得移除；
- 不为了提分而放开字数或结构约束；
- 密钥永不进仓库、不进日志（日志只记事实与回复文本）。
