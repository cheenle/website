#!/usr/bin/env python3
"""eval_run.py — 易占 AI 解读的黄金用例评测（持续提升闭环的量化环节）。

用法（服务器或本地带 LLM_AUTH_TOKEN 的环境）：
    python3 eval_run.py [cases.json 路径]

流程：每个用例 → build_payload → 上游模型 → 硬校验（must 子串、四段结构、字数上限）
→ 评审模型按四维打分（象数运用/经文引用/事理贴合/行动可执行，各 1–5）。
结果写入 $LLM_LOG_DIR/eval_runs/<时间>_<PROMPT_VERSION>.json 并打印汇总表；
任一硬校验失败则退出码 1。

迭代提示词时：改 llm_proxy.SYSTEM_PROMPT → 升 PROMPT_VERSION → 跑本脚本 →
与上一版 run 文件对比硬校验与均分 → 达标才发布（deploy.sh + systemctl restart）。
"""
import json
import os
import re
import urllib.error
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import llm_proxy  # noqa: E402

MAX_CHARS = 480
JUDGE_PROMPT = (
    "你是易学文本评审。下面是一条 AI 易经解读及其输入事实。按四个维度各打 1–5 分："
    "xiangshu（是否真用了爻位/互错综等象数事实而非泛谈）、jingwen（引经是否准确且服务于论证）、"
    "shili（事理是否贴合所问类别、具体不空泛）、xingdong（建议是否可执行、忌是否明确）。"
    "回复的第一个字符必须是 {，只输出 JSON：{\"xiangshu\":n,\"jingwen\":n,\"shili\":n,\"xingdong\":n,\"comment\":\"20字内\"}，禁止任何解释性文字"
)


def hard_check(case, text):
    problems = []
    for m in case["must"]:
        if m.startswith("re:"):
            if not re.search(m[3:], text):
                problems.append("缺必备要素(正则)：%s" % m[3:])
        elif m not in text:
            problems.append("缺必备要素：%s" % m)
    if len(re.sub(r"\s", "", text)) > MAX_CHARS:
        problems.append("超过 %d 字" % MAX_CHARS)
    return problems


def judge(case, text):
    payload = {
        "model": os.environ.get("LLM_MODEL", llm_proxy.DEFAULT_MODEL),
        "max_tokens": 1200,
        "thinking": {"type": "enabled", "budget_tokens": 256},
        "messages": [{"role": "user", "content": JUDGE_PROMPT + "\n\n【输入事实】\n" +
                      case["req"].get("question", "") + " / " + case["category"] +
                      "\n\n【被评审解读】\n" + text}],
    }
    raw = llm_proxy.extract_text(llm_proxy.call_upstream(payload))
    m = re.search(r"\{.*\}", raw, re.S)
    if m:
        try:
            return json.loads(m.group(0))
        except ValueError:
            pass
    out = {}
    for k in ("xiangshu", "jingwen", "shili", "xingdong"):
        km = re.search(k + r"""["'\s]*[:：]\s*(\d)""", raw)
        if km:
            out[k] = int(km.group(1))
    return out or None


def main():
    cases_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent / "eval_cases.json"
    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    results = []
    for case in cases:
        t0 = time.time()
        try:
            text = ""
            for _a in range(2):  # 上游偶发 400/空回复，重试一次
                text = llm_proxy.extract_text(llm_proxy.call_upstream(llm_proxy.build_payload(case["req"])))
                if text:
                    break
            problems = hard_check(case, text)
        except urllib.error.HTTPError as he:
            body = ""
            try:
                body = he.read().decode("utf-8", "replace")
            except Exception:
                pass
            if he.code == 400 and "DataInspection" in body:
                # 上游内容审查误拦：记 skip，不计入硬校验分母
                results.append({"id": case["id"], "category": case["category"],
                                "hard_pass": None, "problems": ["skip: 上游内容审查误拦"],
                                "scores": None, "chars": 0, "ms": 0, "text": ""})
                print("%-16s SKIP 上游内容审查误拦" % case["id"])
                continue
            text, problems = "", ["上游调用失败：HTTPError %d" % he.code]
        except Exception as e:  # 单用例上游故障记 FAIL，不中断整轮
            text, problems = "", ["上游调用失败：%s" % type(e).__name__]
        scores = None if problems else judge(case, text)
        results.append({
            "id": case["id"], "category": case["category"],
            "hard_pass": not problems, "problems": problems,
            "scores": scores, "chars": len(re.sub(r"\s", "", text)),
            "ms": int((time.time() - t0) * 1000), "text": text,
        })
        flag = "PASS" if not problems else "FAIL"
        sc = scores or {}
        print("%-16s %s 字=%3d %s 象数%s 经文%s 事理%s 行动%s %s" % (
            case["id"], flag, results[-1]["chars"],
            ("%4ds" % (results[-1]["ms"] // 1000)),
            sc.get("xiangshu", "-"), sc.get("jingwen", "-"),
            sc.get("shili", "-"), sc.get("xingdong", "-"),
            "; ".join(problems)))

    scored = [r for r in results if r["scores"]]
    mean = {}
    for k in ("xiangshu", "jingwen", "shili", "xingdong"):
        vals = [r["scores"][k] for r in scored if isinstance(r["scores"].get(k), (int, float))]
        mean[k] = round(sum(vals) / len(vals), 2) if vals else None
    judged = [r for r in results if r["hard_pass"] is not None]
    summary = {
        "version": llm_proxy.PROMPT_VERSION,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "hard_pass": sum(1 for r in judged if r["hard_pass"]),
        "total": len(judged),
        "mean_scores": mean,
        "results": results,
    }
    out_dir = Path(os.environ.get("LLM_LOG_DIR", llm_proxy.DEFAULT_LOG_DIR)) / "eval_runs"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / ("%s_%s.json" % (summary["ts"].replace(":", ""), llm_proxy.PROMPT_VERSION))
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    skipped = len(results) - len(judged)
    print("\n版本 %s：硬校验 %d/%d（skip %d），均分 %s" % (summary["version"], summary["hard_pass"], summary["total"], skipped, mean))
    print("run 文件：%s" % out)
    sys.exit(0 if summary["hard_pass"] == summary["total"] else 1)


if __name__ == "__main__":
    main()
