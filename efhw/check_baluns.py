#!/usr/bin/env python3
"""Publish gate for the EFHW content pages: python3 efhw/check_baluns.py

Covers two page pairs (see PAGES below):
  efhw/baluns.html    + efhw/zh/baluns.html    — device taxonomy / selection
  efhw/rx-noise.html  + efhw/zh/rx-noise.html  — receive noise, four-door model

Why a config table instead of two hardcoded paths (2026-10-14): the two pages
are held to different rules. baluns.html is a selection page and carries
unmeasured (") cells and at most one [M] badge; rx-noise.html produces no
self-measured data at all, so a [M] badge there is a defect, not a feature.
A single hardcoded pair could express neither.

Exit code carries the verdict (defect #30): 0 = OK, 1 = any FAIL.
"""
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

# ── Per-page rule sets ────────────────────────────────────────────────────
# Universal rules apply to every page below. Page-specific knobs:
#   min_na             assert at least N "unmeasured" cells (selection pages
#                      have them; pages with no data tables do not)
#   max_tag_m          cap on [M] badges. None = do not check
#   require_tag_m_zero page produces no self-measured data, so ANY [M] is a
#                      defect. Stronger than max_tag_m=0 because it reports
#                      the reason, not just a number.
#   max_labeled_tables cap on data-gate="labeled" tables (see the dB rule)
PAGES = [
    {
        "en": "baluns.html", "zh": "zh/baluns.html",
        "min_na": 5, "max_tag_m": 1, "require_tag_m_zero": False,
        "max_labeled_tables": 0,
        "cn_forbidden": ("Decide by", "Failure mode", "Back to",
                         "Bill of materials", "Where the numbers", "Build one"),
    },
    {
        "en": "rx-noise.html", "zh": "zh/rx-noise.html",
        "min_na": 0, "max_tag_m": None, "require_tag_m_zero": True,
        # Exactly three tables on this page state their own basis and are
        # therefore exempt from the per-line dB rule (not a blank cheque —
        # the cap is the count, and the gate prints how many claims it waived):
        #   §01  BG1SB counter-example  — basis: measurements/…case_study §2.5/2.6
        #   §02  Class B limits + dBuV→dBm conversion — basis: GB/T 9254.1-2021
        #   §03  common-mode divider table — basis: the formula stated above it
        "max_labeled_tables": 3,
        "cn_forbidden": ("Measure first", "Six sources", "The other three",
                         "Prove it worked", "What a choke cannot fix",
                         "Where the noise", "No number on this page"),
    },
]

sec_ids = {}
for spec in PAGES:
  for rel in (spec["en"], spec["zh"]):
    s = load(os.path.join(HERE, rel))
    if not s:
        chk(False, f"missing page: {rel}")
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
    if spec["min_na"]:
        chk(s.count('class="na"') >= spec["min_na"],
            f"{rel}: expected >={spec['min_na']} unmeasured (-) cells")
    n_m = s.count("tag-m")
    if spec["max_tag_m"] is not None:
        chk(n_m <= spec["max_tag_m"],
            f"{rel}: tag-m {n_m} > {spec['max_tag_m']} (nothing self-measured)")
    if spec["require_tag_m_zero"]:
        chk(n_m == 0,
            f"{rel}: tag-m must be 0 — this page has no self-measured data")

    # dB discipline. Default is per-line: a claim must mark itself
    # illustrative in the same line, or quote a denial. Some tables are
    # entirely statements of a recomputable formula or of a named standard's
    # limits, and tagging every cell would make the table unreadable. Those
    # declare their own basis with data-gate="labeled", and the gate then
    # waives claims inside them — but counts them, prints the count, and caps
    # the number of such tables, so a reviewer can see the size of the
    # exemption rather than having to trust it.
    # Note the token regex also matches "56 dBuV", so a limits table needs the
    # exemption too.
    labeled = [(m.start(), m.end()) for m in re.finditer(
        r'<table[^>]*data-gate="labeled".*?</table>', s, re.S)]
    chk(len(labeled) <= spec["max_labeled_tables"],
        f"{rel}: {len(labeled)} data-gate=labeled tables > "
        f"{spec['max_labeled_tables']}")

    def _labeled_at(pos, _spans=labeled):
        return any(a <= pos < b for a, b in _spans)

    waived = 0
    for m in re.finditer(r"\d+(?:\.\d+)?\s*dB", s):
        pos = m.start()
        line = s[s.rfind("\n", 0, pos) + 1: s.find("\n", pos)]
        if _labeled_at(pos):
            waived += 1
            continue
        illustrative = "builder gets" in line or "\u6709\u4eba" in line
        quoted_denial = (("&ldquo;" in line or "\u201c" in line)
                         and ("trust us" in line or "\u8bf7\u76f8\u4fe1" in line))
        chk(illustrative or quoted_denial,
            f"{rel}: non-illustrative dB claim: {line.strip()[:60]}")
    if labeled:
        print(f"note: {rel}: waived {waived} dB claim(s) in "
              f"{len(labeled)} labeled table(s)")

    sec_ids[rel] = re.findall(r'<section[^>]*id="([\w-]+)"', s)
    if rel.startswith("zh/"):
        for w in spec["cn_forbidden"]:
            chk(w not in s, f"{rel}: CN untranslated English: {w}")
    else:
        chk('hreflang="zh-CN"' in s, f"{rel}: EN page missing hreflang=zh-CN")
  chk(sec_ids.get(spec["en"]) == sec_ids.get(spec["zh"]),
      f"EN/CN anchors differ for {spec['en']}: "
      f"{sec_ids.get(spec['en'])} vs {sec_ids.get(spec['zh'])}")

for msg in FAIL:
    print("FAIL:", msg)
print("check_baluns:", "FAILED (%d)" % len(FAIL) if FAIL else "OK")
sys.exit(1 if FAIL else 0)
