"""Sitemap contract tests.

Why this file exists: sub-site identity pages were once added by hand-editing
sitemap.xml. The next `python3 make_sitemap.py` run rewrote the artifact from
the generator and silently dropped them — a green file with missing URLs.
These tests pin the two halves of that trap: the generator must enumerate
sub-site pages, and the committed artifact must equal generator output.
"""
import os
import re
import subprocess
import sys

PORTAL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(PORTAL)
BASE = "https://www.vlsc.net"
ARTIFACT = os.path.join(PORTAL, "sitemap.xml")


def _urls(text):
    return set(re.findall(r"<loc>([^<]+)</loc>", text))


def _fresh_urls():
    """URL set from a throwaway regeneration (committed artifact untouched)."""
    out = os.path.join(PORTAL, ".sitemap_check.xml")
    src = open(os.path.join(PORTAL, "make_sitemap.py")).read()
    open(out, "w").write(src.replace(
        "with open(os.path.join(ROOT, 'sitemap.xml'), 'w') as f:",
        "with open(os.path.join(ROOT, '.sitemap_check.xml'), 'w') as f:"))
    try:
        subprocess.run([sys.executable, out], cwd=PORTAL, check=True,
                       capture_output=True)
        return _urls(open(out).read())
    finally:
        if os.path.exists(out):
            os.remove(out)


def test_artifact_matches_generator_output():
    """No hand edits: the committed file is exactly what the generator emits."""
    assert _urls(open(ARTIFACT).read()) == _fresh_urls(), (
        "sitemap.xml is not generator output — fix make_sitemap.py, never the artifact")


def test_all_subsite_pages_are_indexed():
    """Every depth-1 sub-site HTML page must be enumerated.

    Expectations come from the filesystem, never from a hardcoded URL list: a
    hardcoded entry for a page that does not exist can only pass by accident,
    and here it hid a false assertion (mrrc_ft710/engineering.html was never
    created).
    """
    have = _urls(open(ARTIFACT).read())
    src = open(os.path.join(PORTAL, "make_sitemap.py")).read()
    listed = re.findall(r"SUBSITES = \[(.*?)\]", src, re.S)[0]
    seen, missing = 0, []
    for site in re.findall(r"'([^']+)'", listed):
        base = os.path.join(REPO, site.strip("/"))
        if not os.path.isdir(base):
            continue
        for sub in ("", "zh"):
            d = os.path.join(base, sub)
            if not os.path.isdir(d):
                continue
            for fn in sorted(os.listdir(d)):
                if not fn.endswith(".html") or fn.startswith("."):
                    continue
                if fn == "index.html":
                    loc = BASE + site + (sub + "/" if sub else "")
                else:
                    loc = BASE + site + (sub + "/" if sub else "") + fn
                if loc in have:
                    seen += 1
                else:
                    missing.append(loc)
    assert not missing, "未收录的深度 1 页面: " + ", ".join(missing[:6])
    assert seen >= 25, "只匹配到 %d 页，目录遍历可能失效" % seen


def test_new_efhw_baluns_pages_are_indexed():
    """The topic page added this round must be discoverable in both languages."""
    have = _urls(open(ARTIFACT).read())
    for loc in (BASE + "/efhw/baluns.html", BASE + "/efhw/zh/baluns.html"):
        assert loc in have, "未收录 " + loc


def test_all_subsite_roots_present():
    have = _urls(open(ARTIFACT).read())
    src = open(os.path.join(PORTAL, "make_sitemap.py")).read()
    listed = re.findall(r"SUBSITES = \[(.*?)\]", src, re.S)[0]
    for site in re.findall(r"'([^']+)'", listed):
        assert BASE + site in have, f"子站根未收录 {site}"
