#!/usr/bin/env python3
"""llm_proxy.py — 易占的 LLM 进一步解读代理（Python 标准库，无第三方依赖）。

浏览器绝不接触密钥：前端 POST /yijing/api/interpret → nginx → 本服务（仅监听
127.0.0.1）→ Anthropic 兼容端点（DashScope）。密钥经环境变量/EnvironmentFile 注入。

环境变量：
  LLM_BASE_URL    默认 https://dashscope.aliyuncs.com/apps/anthropic
  LLM_AUTH_TOKEN  必填，缺失时服务拒绝启动
  LLM_MODEL       默认 qwen3.8-max-0902
  LLM_PORT        默认 8100
"""
import json
import os
import sys
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DEFAULT_BASE = "https://dashscope.aliyuncs.com/apps/anthropic"
DEFAULT_MODEL = "qwen3.8-max-0902"
MAX_BODY = 64 * 1024
UPSTREAM_TIMEOUT = 90

SYSTEM_PROMPT = (
    "你是通晓《周易》经传的解读者。用户给出一次铜钱起卦的结果：本卦、之卦、动爻、"
    "朱熹断法所取断辞（原文与白话）与问事类别。请在此基础上作进一步解读：\n"
    "1.「卦象」：结合上下经卦取象与动爻位置，说明卦象所示之势；\n"
    "2.「事理」：针对所问类别，把断辞之意落到具体事理；\n"
    "3.「行动」：给出二至三条可执行的建议与忌讳。\n"
    "全文三百字以内，白话，不堆砌术语；结尾须附一句：占断仅供参考，事在人为。"
)


def build_payload(req):
    """由前端请求体构造上游 Messages 请求（纯函数，便于测试）。"""
    ben = req.get("ben") or {}
    zhi = req.get("zhi")
    duanci = req.get("duanci") or []
    lines = ["所问之事：%s" % (req.get("question") or "心中默念"),
             "问事类别：%s" % req.get("category", "综合"),
             "本卦：%s" % ben.get("fullName", "?"),
             "之卦：%s" % (zhi.get("fullName") if zhi else "无（六爻安静）"),
             "动爻：%s" % ("、".join(req.get("movingTitles") or []) or "无"),
             "断法：%s" % req.get("rule", "?"),
             "断辞："]
    for e in duanci:
        lines.append("- %s：%s（白话：%s）" % (e.get("source", "?"), e.get("ci", ""), e.get("baihua", "")))
    user = "\n".join(lines)
    return {
        "model": os.environ.get("LLM_MODEL", DEFAULT_MODEL),
        "max_tokens": 900,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": user}],
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


class Handler(BaseHTTPRequestHandler):
    server_version = "YijingLLMProxy/1.0"

    def _send(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/interpret":
            self._send(404, {"ok": False, "error": "not found"})
            return
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > MAX_BODY:
            self._send(413, {"ok": False, "error": "body too large"})
            return
        try:
            req = json.loads(self.rfile.read(length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self._send(400, {"ok": False, "error": "bad json"})
            return
        try:
            resp = call_upstream(build_payload(req))
            text = extract_text(resp)
        except urllib.error.HTTPError as e:
            self._send(502, {"ok": False, "error": "upstream %d" % e.code})
            return
        except Exception as e:  # 网络/超时/配置
            self._send(502, {"ok": False, "error": "upstream error: %s" % type(e).__name__})
            return
        if not text:
            self._send(502, {"ok": False, "error": "empty completion"})
            return
        self._send(200, {"ok": True, "text": text})

    def do_GET(self):
        self._send(405, {"ok": False, "error": "method not allowed"})

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main():
    if not os.environ.get("LLM_AUTH_TOKEN"):
        sys.exit("LLM_AUTH_TOKEN 未配置，拒绝启动")
    port = int(os.environ.get("LLM_PORT", "8100"))
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    sys.stderr.write("yijing llm proxy on 127.0.0.1:%d\n" % port)
    srv.serve_forever()


if __name__ == "__main__":
    main()
