#!/usr/bin/env python3
"""Parse the era/category table in RIG/rekishi.html and emit RIG/README.md."""
import os, re, html

OUT = "RIG"
main = open(os.path.join(OUT, "rekishi.html"), encoding="utf-8").read()

# isolate the big bordered history table (first table border="1")
m = re.search(r'<table border="1"[^>]*>(.*?)</table>', main, flags=re.I | re.S)
table = m.group(1)

rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table, flags=re.I | re.S)

def cells(row):
    return re.findall(r'<td[^>]*>(.*?)</td>', row, flags=re.I | re.S)

def items(cell):
    """split a cell into (name, link, mark) entries, <br>-separated"""
    cell = re.sub(r'&nbsp;', ' ', cell)
    parts = re.split(r'<br\s*/?>', cell, flags=re.I)
    out = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        lm = re.match(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>(.*)', p, flags=re.I | re.S)
        if lm:
            link, name, rest = lm.groups()
        else:
            link, name, rest = None, p, ""
        name = re.sub(r'<[^>]+>', '', name)
        name = html.unescape(name).strip()
        rest = re.sub(r'<[^>]+>', '', rest)
        mark = ""
        if '☆' in rest: mark = '☆'
        elif '※' in rest: mark = '※'
        if name and name not in ('　',):
            out.append((name, link, mark))
    return out

def fmt(cell):
    its = items(cell)
    if not its:
        return "—"
    res = []
    for name, link, mark in its:
        local = link if (link and ':' not in link and os.path.exists(os.path.join(OUT, link))) else None
        s = f"[{name}]({link})" if local else name
        if mark: s += f" {mark}"
        res.append(s)
    return "<br>".join(res)

lines = []
lines.append("# 无线机历史博物馆（無線機の遍歴）本地存档\n")
lines.append("来源：[無線機の遍歴 - セイデン社](http://www.seidensha-ltd.co.jp/~seiden/rekishi.html)（已转为 UTF-8，页面与图片均保存在本目录，可离线浏览）\n")
lines.append("- `rekishi.html` — 主页完整存档（从此页进入各设备页面）")
lines.append("- 各 `*.html` — 逐台设备的图文介绍页")
lines.append("- `gif/` — 页面引用的图片\n")
lines.append("标注含义：**☆** = 实际使用过（実使用）；**※** = 特别说明。\n")
lines.append("| 年代 | 接收机 | 收发信机 | 发射机・其他 |")
lines.append("|---|---|---|---|")

CATS = ["接收机", "收发信机", "发射机・其他"]
for row in rows:
    cs = cells(row)
    if not cs:
        continue
    first = re.sub(r'<[^>]+>', '', cs[0]).strip()
    first = html.unescape(first)
    era_m = re.match(r'^(１９４０|１９５０|１９６０|１９７０|１９８０|１９９０|２０００)年代', first)
    if not era_m:
        continue
    era = era_m.group(0)
    if era.startswith('１９７０'): era += "（自此无线机＝收发信机）"
    if era.startswith('２０００'): era += "以降"
    cols = cs[1:4]
    while len(cols) < 3: cols.append("")
    lines.append(f"| {era} | {fmt(cols[0])} | {fmt(cols[1])} | {fmt(cols[2])} |")

# special sections
lines.append("\n## 专题・番外\n")
specials = [
    ("1967〜1973年 日本国产 V/UHF 收发信机", "1967-73_vuhf.html"),
    ("年代不明・其他汇总", "rekishi_sonota.html"),
    ("自制音频主放大器 6RA8x2（1970年代）", "6ra8x2.html"),
    ("各式电键（含海外制电键）", "telegraph_key.html"),
    ("通过式功率计", "power_meter.html"),
    ("终端式功率计", "wattmeter.html"),
    ("警察预备队无线机", "keisatuyobi.html"),
    ("TJ4A 套件与高频电源改造、线性放大器", "tj4a_main.html"),
]
for name, f in specials:
    if os.path.exists(os.path.join(OUT, f)):
        lines.append(f"- [{name}]({f})")

lines.append("\n## SDR 时代（主页正文详述）\n")
lines.append("主页正文对以下机型有详细使用报告（无独立页面，见 `rekishi.html`）：")
lines.append("- ICOM IC-7300（2015 下下期，告别超外差，SDR/FPGA）")
lines.append("- ICOM IC-756 / IC-756PRO 系列远程运用（RS-BA1）")
lines.append("- ICOM IC-7610、IC-7760（2024 受注开始）、IC-705\n")

with open(os.path.join(OUT, "README.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("README.md written,", len(lines), "lines")
