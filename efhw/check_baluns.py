#!/usr/bin/env python3
"""Gate for the EFHW baluns pages: python3 efhw/check_baluns.py"""
import os, re, sys
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
VOID = {"meta", "link", "br", "img", "hr", "input"}
FAIL = []


def chk(ok, msg):
    if not ok:
        FAIL.append(msg)


def load(p):
    try:
        return open(p, encoding="utf-8").read()
    except OSError as e:
        chk(False, f"cannot read {p}: {e}")
        return ""


class Stk(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack, self.bad = [], []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append((tag, self.getpos()[0]))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        names = [x[0] for x in self.stack]
        if names and names[-1] == tag:
            self.stack.pop()
        elif tag in names:
            while self.stack and self.stack[-1][0] != tag:
                self.bad.append(("unclosed", self.stack.pop(), tag))
            self.stack.pop()
        else:
            self.bad.append(("stray", tag, self.getpos()[0]))


CSS = load(os.path.join(HERE, "css/octen.css")) + load(os.path.join(HERE, "css/efhw.css"))
NEEDED = ("subnav spec-table tag-c tag-m tree leaf deny na calc steps step risk "
          "section-cta feature-card card-title tech-stack tech-tag footer-grid "
          "footer-section footer-bottom mobile-menu-toggle nav-actions lang-btn "
          "hero-content hero-badge hero-actions section-header section-label "
          "section-title section-subtitle").split()
for c in NEEDED:
    chk(re.search(r"\." + c + r"[ ,:{]", CSS), f"CSS class .{c} undefined")

sec_ids = {}
for rel in ("baluns.html", "zh/baluns.html"):
    s = load(os.path.join(HERE, rel))
    if not s:
        continue
    base = os.path.dirname(os.path.join(HERE, rel))
    p = Stk()
    p.feed(s)
    chk(not p.bad, f"{rel}: tag mismatch {p.bad[:2]}")
    chk(not p.stack, f"{rel}: unclosed at EOF {p.stack[:3]}")
    chk(s.count("<h1") == 1, f"{rel}: h1 count")
    ids = re.findall(r'id="([\w-]+)"', s)
    chk(not [i for i in set(ids) if ids.count(i) > 1], f"{rel}: duplicate ids")
    chk(not [h for h in re.findall(r'href="#([^"]+)"', s) if h not in ids], f"{rel}: dead anchor")
    chk(re.search(r"(?<![a-z-])ag-[a-z]", s) is None, f"{rel}: forbidden ag-* class")
    chk("mobile-menu-toggle" in s and "function toggleMobileMenu" in s, f"{rel}: mobile menu")
    for h in re.findall(r'href="((?!https?:|#|data:|mailto:|/)[^"]+)"', s):
        t = os.path.normpath(os.path.join(base, h.split("#")[0].split("?")[0]))
        chk(os.path.exists(t), f"{rel}: broken link {h}")
    chk(s.count('class="na"') >= 5, f"{rel}: expected >=5 unmeasured (-) cells")
    chk(s.count("tag-m") <= 1, f"{rel}: [M] on a data row (nothing self-measured)")
    for m in re.finditer(r"[^\n]*\d+(?:\.\d+)?\s*dB[^\n]*", s):
        line = m.group(0)
        illustrative = "builder gets" in line or "\u6709\u4eba" in line
        quoted_denial = ("&ldquo;" in line or "\u201c" in line) and ("trust us" in line
                             or "\u8bf7\u76f8\u4fe1" in line)
        chk(illustrative or quoted_denial,
            f"{rel}: non-illustrative dB claim: {m.group(0)[:60]}")
    sec_ids[rel] = re.findall(r'<section[^>]*id="([\w-]+)"', s)
    if rel.startswith("zh/"):
        for w in ("Decide by", "Failure mode", "Back to", "Bill of materials",
                  "Where the numbers", "Build one"):
            chk(w not in s, f"CN untranslated English: {w}")
    else:
        chk('hreflang="zh-CN"' in s, "EN page missing hreflang=zh-CN")

chk(sec_ids.get("baluns.html") == sec_ids.get("zh/baluns.html"), f"EN/CN anchors differ: {sec_ids}")
for msg in FAIL:
    print("FAIL:", msg)
print("check_baluns:", "FAILED (%d)" % len(FAIL) if FAIL else "OK")
sys.exit(1 if FAIL else 0)
