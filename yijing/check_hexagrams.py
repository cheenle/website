#!/usr/bin/env python3
"""check_hexagrams.py — yijing/ 数据完整性验证门。

校验八卦与 64 卦数据：卦数、卦画编码、上下经卦一致性、爻题、用九用六、
白话与问事要点字段齐备。默认严格模式要求 64 卦齐备；
批次撰写期间设 ALLOW_PARTIAL=1 时只校验已有卦的字段结构。
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CATEGORIES = ["综合", "事业", "财运", "感情", "健康", "出行"]


def extract_const(path, name):
    """从 JS 文件中提取 JSON 严格字面量常量（配对括号扫描，跳过字符串）。"""
    text = path.read_text(encoding="utf-8")
    m = re.search(re.escape(name) + r"\s*=\s*", text)
    if not m:
        raise SystemExit(f"FAIL: {path} 中找不到常量 {name}")
    start = m.end()
    opener = text[start]
    closer = "]" if opener == "[" else "}"
    depth = 0
    in_str = False
    esc = False
    i = start
    while i < len(text):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == opener:
                depth += 1
            elif ch == closer:
                depth -= 1
                if depth == 0:
                    return json.loads(text[start:i + 1])
        i += 1
    raise SystemExit(f"FAIL: {path} 中 {name} 字面量未闭合")


def yao_title(i, yang):
    pos = ["初", "二", "三", "四", "五", "上"][i]
    num = "九" if yang else "六"
    return pos + num if i in (0, 5) else num + pos


def main():
    strict = os.environ.get("ALLOW_PARTIAL") != "1"
    trigrams = extract_const(ROOT / "js/data/trigrams.js", "TRIGRAMS")
    hexes = extract_const(ROOT / "js/data/hexagrams.js", "HEXAGRAMS")
    errors = []

    if len(trigrams) != 8:
        errors.append(f"八卦数量 {len(trigrams)} != 8")
    symbols = [t["symbol"] for t in trigrams.values()]
    if len(set(symbols)) != 8 or any(not re.fullmatch(r"[01]{3}", s) for s in symbols):
        errors.append("八卦卦符不唯一或不合法")

    if strict and len(hexes) != 64:
        errors.append(f"卦数 {len(hexes)} != 64")
    if strict and sorted(h["id"] for h in hexes) != list(range(1, 65)):
        errors.append("卦序 id 不是 1..64")

    seen_lines = set()
    for h in hexes:
        hid = h.get("id", "?")
        hname = h.get("name", "?")
        lines = h["lines"]
        if not re.fullmatch(r"[01]{6}", lines):
            errors.append(f"#{hid} {hname}: lines 非法 {lines!r}")
        if lines in seen_lines:
            errors.append(f"#{hid} {hname}: lines 重复 {lines}")
        seen_lines.add(lines)
        if h["lower"] not in trigrams or h["upper"] not in trigrams:
            errors.append(f"#{hid} {hname}: 上下卦名非法")
        else:
            expect = trigrams[h["lower"]]["symbol"] + trigrams[h["upper"]]["symbol"]
            if lines != expect:
                errors.append(f"#{hid} {hname}: lines={lines} 与 {h['lower']}下{h['upper']}上={expect} 不符")
        yaos = h["yaos"]
        if len(yaos) != 6:
            errors.append(f"#{hid} {hname}: 爻数 {len(yaos)} != 6")
        for i, y in enumerate(yaos):
            want = yao_title(i, lines[i] == "1")
            if y["title"] != want:
                errors.append(f"#{hid} {hname}: 第{i+1}爻题 {y['title']} 应为 {want}")
            for f in ("ci", "xiang", "baihua"):
                if not str(y.get(f, "")).strip():
                    errors.append(f"#{hid} {hname} {y.get('title')}: {f} 为空")
        if h["id"] in (1, 2):
            yong = h.get("yong")
            if not yong or not all(str(yong.get(f, "")).strip() for f in ("ci", "xiang", "baihua")):
                errors.append(f"#{hid}: 乾坤须有完整用九/用六")
        elif h.get("yong") is not None:
            errors.append(f"#{hid} {hname}: 非乾坤不得有 yong 字段")
        for f in ("guaci", "tuan", "xiang", "guaciBaihua"):
            if not str(h.get(f, "")).strip():
                errors.append(f"#{hid} {hname}: {f} 为空")
        advice = h.get("advice") or {}
        for c in CATEGORIES:
            if not str(advice.get(c, "")).strip():
                errors.append(f"#{hid} {hname}: advice[{c}] 为空")

    if errors:
        for e in errors:
            print("FAIL:", e)
        print(f"\n共 {len(errors)} 处问题")
        sys.exit(1)
    mode = "strict" if strict else f"partial（{len(hexes)} 卦）"
    print(f"OK: 数据校验通过（{mode}）")


if __name__ == "__main__":
    main()
