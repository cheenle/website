#!/usr/bin/env python3
"""llm_proxy.py — 易占的 LLM 进一步解读代理（Python 标准库，无第三方依赖）。

浏览器绝不接触密钥：前端 POST /yijing/api/interpret → nginx → 本服务（仅监听
127.0.0.1）→ Anthropic 兼容端点（DashScope）。密钥经环境变量/EnvironmentFile 注入。

持续提升闭环：
  - 每次解读写 JSONL 日志（含 PROMPT_VERSION、请求事实、回复全文、耗时）；
  - 前端 👍/ 经 POST /yijing/api/feedback 回传同目录 feedback.jsonl；
  - eval_run.py 用黄金用例 + 评审模型打分，对比各 PROMPT_VERSION 后迭代提示词。

环境变量：
  LLM_BASE_URL    默认 https://dashscope.aliyuncs.com/apps/anthropic
  LLM_AUTH_TOKEN  必填，缺失时服务拒绝启动
  LLM_MODEL       默认 qwen3.8-max-0902
  LLM_PORT        默认 8100
  LLM_LOG_DIR     默认 /home/cheenle/yijing-llm-logs
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DEFAULT_BASE = "https://dashscope.aliyuncs.com/apps/anthropic"
DEFAULT_MODEL = "qwen3.8-max-0902"
DEFAULT_LOG_DIR = "/home/cheenle/yijing-llm-logs"
MAX_BODY = 64 * 1024
UPSTREAM_TIMEOUT = 90
PROMPT_VERSION = "2026-09-25.v5"

SYSTEM_PROMPT = (
    "你是兼通象数与义理的易学解读者，熟稔《周易》经传与朱熹《易学启蒙》断法。"
    "用户给出一次铜钱起卦的完整事实：本卦与之卦、互卦/错卦/综卦、动爻及其爻位事实"
    "（当位失正、中、应、乘承顺逆）、断法所取断辞原文与白话、问事类别。\n"
    "写作要求：\n"
    "1. 结构固定为四段，段首用【卦象大势】【爻位细析】【事理推断】【行动建议】；\n"
    "2. 【卦象大势】首句须点明本卦全称（如「乾为天」「水火既济」），并结合上下经卦取象与互卦所示内情、错综所示反面与换位视角，说明局势；\n"
    "3. 【爻位细析】只析所给动爻（不逐爻泛论），须使用所给爻位事实论证（如失正而居中、有应而乘刚），并引用所给动爻"
    "爻辞或小象原句至少一处，引文用「」标出；\n"
    "4. 【事理推断】针对所问类别，把卦爻之意落到具体事理，不得空泛；每段至多三句；\n"
    "5. 【行动建议】给二至四条可执行建议，最后一条必须以「忌：」开头写忌讳，不得省略；\n"
    "6. 全文不超过四百五十字（含标点），宁简勿冗；只用所给经文，不得编造或引用未提供的卦爻辞；\n"
    "7. 不使用「总的来说」「综上所述」之类套话；结尾另起一行写：占断仅供参考，事在人为。"
)


def build_payload(req):
    """由前端请求体构造上游 Messages 请求（纯函数，便于测试）。"""
    ben = req.get("ben") or {}
    zhi = req.get("zhi")
    moving = req.get("moving") or []
    duanci = req.get("duanci") or []
    lines = ["所问之事：%s" % (req.get("question") or "心中默念"),
             "问事类别：%s" % req.get("category", "综合"),
             "本卦：%s" % ben.get("fullName", "?")]
    if ben.get("tuan"):
        lines.append("本卦彖传：%s" % ben["tuan"])
    if ben.get("xiang"):
        lines.append("本卦大象：%s" % ben["xiang"])
    lines.append("之卦：%s" % (zhi.get("fullName") if zhi else "无（六爻安静）"))
    lines.append("互卦：%s　错卦：%s　综卦：%s" % (req.get("hu") or "?", req.get("cuo") or "?", req.get("zong") or "?"))
    if moving:
        lines.append("动爻爻位事实：")
        for m in moving:
            one = "- %s：%s" % (m.get("title", "?"), m.get("facts", ""))
            if m.get("xiang"):
                one += "　小象：%s" % m["xiang"]
            lines.append(one)
    else:
        lines.append("动爻：无")
    lines.append("断法：%s" % req.get("rule", "?"))
    lines.append("断辞：")
    for e in duanci:
        lines.append("- %s：%s（白话：%s）" % (e.get("source", "?"), e.get("ci", ""), e.get("baihua", "")))
    return {
        "model": os.environ.get("LLM_MODEL", DEFAULT_MODEL),
        "max_tokens": 2048,
        # 思考型模型：给 thinking 设预算，避免思考吃满额度/超时导致正文为空
        "thinking": {"type": "enabled", "budget_tokens": 1024},
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": "\n".join(lines)}],
    }


def extract_text(resp):
    """从 Messages 响应中取出 text 块拼接（thinking 块忽略）。"""
    parts = [b.get("text", "") for b in resp.get("content", []) if b.get("type") == "text"]
    return "\n".join(p for p in parts if p).strip()


def call_upstream(payload):
    base = os.environ.get("LLM_BASE_URL", DEFAULT_BASE).rstrip("/")
    token = os.environ.get("LLM_AUTH_TOKEN", "")
    if not token:
        raise RuntimeError("LLM_AUTH_TOKEN 未配置")
    rq = urllib.request.Request(
        base + "/v1/messages",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "x-api-key": token,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(rq, timeout=UPSTREAM_TIMEOUT) as rp:
        return json.loads(rp.read().decode("utf-8"))


def log_event(kind, obj):
    d = os.environ.get("LLM_LOG_DIR", DEFAULT_LOG_DIR)
    try:
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "%s.jsonl" % kind), "a", encoding="utf-8") as f:
            rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "version": PROMPT_VERSION}
            rec.update(obj)
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError:
        pass  # 日志失败不阻断解读


class Handler(BaseHTTPRequestHandler):
    server_version = "YijingLLMProxy/2.0"

    def _send(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > MAX_BODY:
            return None
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return None

    def do_POST(self):
        if self.path == "/interpret":
            self._interpret()
        elif self.path == "/feedback":
            self._feedback()
        else:
            self._send(404, {"ok": False, "error": "not found"})

    def _interpret(self):
        req = self._read_json()
        if req is None:
            self._send(400, {"ok": False, "error": "bad json"})
            return
        rid = uuid.uuid4().hex[:16]
        log_event("interpret_req", {"id": rid, "req": req})
        t0 = time.time()
        text = ""
        try:
            # 思考型模型偶发把额度耗在 thinking 上导致正文为空，重试一次
            for _attempt in range(2):
                resp = call_upstream(build_payload(req))
                text = extract_text(resp)
                if text:
                    break
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8", "replace")
            except Exception:
                pass
            if e.code == 400 and "DataInspection" in body:
                log_event("interpret_err", {"id": rid, "error": "content-inspection"})
                self._send(409, {"ok": False, "error": "content-inspection"})
                return
            log_event("interpret_err", {"id": rid, "error": "upstream %d" % e.code})
            self._send(502, {"ok": False, "error": "upstream %d" % e.code})
            return
        except Exception as e:
            log_event("interpret_err", {"id": rid, "error": type(e).__name__})
            self._send(502, {"ok": False, "error": "upstream error: %s" % type(e).__name__})
            return
        if not text:
            log_event("interpret_err", {"id": rid, "error": "empty completion"})
            self._send(502, {"ok": False, "error": "empty completion"})
            return
        log_event("interpret_res", {"id": rid, "ms": int((time.time() - t0) * 1000), "text": text})
        self._send(200, {"ok": True, "text": text, "id": rid, "version": PROMPT_VERSION})

    def _feedback(self):
        body = self._read_json()
        if not isinstance(body, dict) or body.get("rating") not in (1, -1):
            self._send(400, {"ok": False, "error": "rating must be 1 or -1"})
            return
        log_event("feedback", {
            "id": body.get("id"),
            "rating": body["rating"],
            "question": body.get("question", ""),
            "category": body.get("category", ""),
        })
        self._send(200, {"ok": True})

    def do_GET(self):
        self._send(405, {"ok": False, "error": "method not allowed"})

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main():
    if not os.environ.get("LLM_AUTH_TOKEN"):
        sys.exit("LLM_AUTH_TOKEN 未配置，拒绝启动")
    port = int(os.environ.get("LLM_PORT", "8100"))
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    sys.stderr.write("yijing llm proxy %s on 127.0.0.1:%d\n" % (PROMPT_VERSION, port))
    srv.serve_forever()


if __name__ == "__main__":
    main()
