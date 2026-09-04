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


def test_subsite_identity_pages_are_indexed():
    """Depth-1 sub-site pages must be enumerated, not just site roots."""
    have = _urls(open(ARTIFACT).read())
    for loc in (f"{BASE}/mrrc/agentic.html", f"{BASE}/mrrc/zh/agentic.html",
                f"{BASE}/mrrc_ft710/agentic.html", f"{BASE}/mrrc_modern/agentic.html",
                f"{BASE}/mrrc_ft710/engineering.html", f"{BASE}/efhw/index.html"):
        assert loc in have or loc.replace("index.html", "") in have, f"未收录 {loc}"


def test_all_subsite_roots_present():
    have = _urls(open(ARTIFACT).read())
    src = open(os.path.join(PORTAL, "make_sitemap.py")).read()
    listed = re.findall(r"SUBSITES = \[(.*?)\]", src, re.S)[0]
    for site in re.findall(r"'([^']+)'", listed):
        assert BASE + site in have, f"子站根未收录 {site}"
