"""GA4 injection contract tests.

Why this file exists: the analytics snippet ships inside a shared script
(scope.js / global-nav.js), not pasted into 122 pages. Two failures are
possible and neither looks broken in a browser:

  1. one shared-script copy loses the block (a rebuild, a hand-edit), and an
     entire site silently stops reporting;
  2. a new page ships without either shared script, so it is never counted.

Both are green-tree failures. These tests pin them.
"""
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GA_ID = "G-JQLSKV1MCT"

# The 7 shared-script copies carrying the snippet, across 5 repositories.
SCRIPTS = [
    "portal/js/global-nav.js",
    "efhw/js/global-nav.js",
    "mrrc/js/global-nav.js",
    "mrrc_modern/js/scope.js",
    "mrrc_modern/js/global-nav.js",
    "sunmrrc/js/scope.js",
    "mrrc_ft8/js/scope.js",
]

# Every HTML page under these sites must load one of the shared scripts.
SITES = ["portal", "efhw", "mrrc", "mrrc_modern", "sunmrrc", "mrrc_ft8"]
SHARED = ("scope.js", "global-nav.js")

# Canary, calibrated 2026-09-13: 29+4+25+23+20+21 = 122 pages. Retiring a
# sub-site legitimately lowers this; do not lower it to make a walk failure pass.
MIN_PAGES = 120


def _read(rel):
    with open(os.path.join(REPO, rel), encoding="utf-8") as f:
        return f.read()


def _html_pages(site):
    for dirpath, _, filenames in os.walk(os.path.join(REPO, site)):
        for fn in sorted(filenames):
            if fn.endswith(".html"):
                yield os.path.join(dirpath, fn)


def _guard_regex(text):
    """Lift the shipped host guard out of the file: test the artifact, not a copy."""
    m = re.search(
        r"if \(/(.+?)/\.test\(location\.hostname\) && !window\.dataLayer\)", text)
    assert m, "GA 守卫语句缺失"
    return re.compile(m.group(1))


def test_every_shared_script_carries_the_ga_block():
    for rel in SCRIPTS:
        text = _read(rel)
        assert GA_ID in text, f"{rel} 缺 GA 测量 ID"
        assert f"googletagmanager.com/gtag/js?id={GA_ID}" in text, f"{rel} 缺 gtag.js 地址"
        assert f"window.gtag('config', '{GA_ID}')" in text, f"{rel} 缺 config 调用"
        assert "window.gtag('js', new Date())" in text, f"{rel} 缺 js 调用"
        # dataLayer 必须先于 gtag.js 挂载定义，否则与 async 加载竞态。
        assert text.index("window.dataLayer = window.dataLayer || []") < text.index(
            f"googletagmanager.com/gtag/js?id={GA_ID}"), f"{rel} dataLayer 定义晚于脚本挂载"


def test_guard_regex_accepts_only_vlsc_hosts():
    for rel in SCRIPTS:
        guard = _guard_regex(_read(rel))
        assert guard.search("www.vlsc.net"), f"{rel} 未放行 www.vlsc.net"
        assert guard.search("vlsc.net"), f"{rel} 未放行 vlsc.net"
        for host in ("localhost", "", "127.0.0.1", "evil-vlsc.net", "vlsc.net.evil.com"):
            assert not guard.search(host), f"{rel} 误放行 {host!r}"


def test_ga_block_is_idempotent_by_construction():
    for rel in SCRIPTS:
        assert "!window.dataLayer" in _read(rel), f"{rel} 缺幂等守卫"


def test_every_page_loads_a_shared_script():
    orphans, total = [], 0
    for site in SITES:
        for page in _html_pages(site):
            total += 1
            with open(page, encoding="utf-8", errors="replace") as f:
                text = f.read()
            if not any(s in text for s in SHARED):
                orphans.append(os.path.relpath(page, REPO))
    assert total >= MIN_PAGES, f"只遍历到 {total} 页，目录遍历可能失效"
    assert not orphans, "未加载共享脚本（将不被统计）: " + ", ".join(sorted(orphans))
