"""Redirect-stub contract tests for the merged-away from-intent-to-delivery article.

2026-09-06: the two long-form articles were merged into one
(/blog/seven-billion-tokens/). from-intent-to-delivery keeps only minimal
meta-refresh stubs so old links and the published canonical keep working.
These tests pin the stub shape: they must redirect, must not be indexable,
and must never grow article body content again.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

PORTAL = Path(__file__).resolve().parents[1]
SLUG = "from-intent-to-delivery"
MERGED_SLUG = "seven-billion-tokens"
PAGES = {
    "en": PORTAL / "blog" / SLUG / "index.html",
    "zh": PORTAL / "blog" / SLUG / "zh" / "index.html",
}
TARGET = {
    "en": f"https://www.vlsc.net/blog/{MERGED_SLUG}/",
    "zh": f"https://www.vlsc.net/blog/{MERGED_SLUG}/zh/",
}
RELATIVE_TARGET = {
    "en": f"/blog/{MERGED_SLUG}/",
    "zh": f"/blog/{MERGED_SLUG}/zh/",
}
BLOG_INDEX = PORTAL / "blog" / "index.html"
SITEMAP = PORTAL / "sitemap.xml"

# Body-content probes from the old full article: a stub must contain none of
# these. If one reappears, the stub has grown back into an article and the
# two copies will drift from the merged canonical.
OLD_ARTICLE_PROBES = (
    "Four Dimensions",
    "四个维度",
    "data-volume",
    "data-claim-type",
    "application/ld+json",
)


class FromIntentRedirectTests(unittest.TestCase):
    def test_stub_pages_exist_and_nothing_else(self) -> None:
        for language, path in PAGES.items():
            self.assertTrue(path.exists(), f"{language}: {path}")
        # Only the two stubs may live in the directory: no orphaned
        # article.css / images that nothing references any more.
        files = sorted(
            str(p.relative_to(PAGES["en"].parent))
            for p in PAGES["en"].parent.rglob("*")
            if p.is_file()
        )
        self.assertEqual(["index.html", "zh/index.html"], files)

    def test_canonical_points_at_merged_article(self) -> None:
        for language, path in PAGES.items():
            source = path.read_text(encoding="utf-8")
            canonicals = re.findall(
                r'<link rel="canonical" href="([^"]+)"', source)
            self.assertEqual([TARGET[language]], canonicals, language)

    def test_meta_refresh_redirects_to_merged_article(self) -> None:
        for language, path in PAGES.items():
            source = path.read_text(encoding="utf-8")
            refreshes = re.findall(
                r'<meta http-equiv="refresh" content="0;\s*url=([^"]+)"',
                source,
            )
            self.assertEqual([RELATIVE_TARGET[language]], refreshes, language)

    def test_stubs_are_noindex(self) -> None:
        for language, path in PAGES.items():
            source = path.read_text(encoding="utf-8")
            self.assertIn('<meta name="robots" content="noindex"', source,
                          language)

    def test_stubs_link_both_languages_and_the_merged_article(self) -> None:
        en = PAGES["en"].read_text(encoding="utf-8")
        zh = PAGES["zh"].read_text(encoding="utf-8")
        # bilingual interlinks survive the merge
        self.assertIn('href="zh/"', en)
        self.assertIn('href="../"', zh)
        # an explicit human-clickable link to the merged article
        self.assertIn(f'href="{RELATIVE_TARGET["en"]}"', en)
        self.assertIn(f'href="{RELATIVE_TARGET["zh"]}"', zh)

    def test_stubs_contain_no_article_body(self) -> None:
        for language, path in PAGES.items():
            source = path.read_text(encoding="utf-8")
            for probe in OLD_ARTICLE_PROBES:
                self.assertNotIn(probe, source, f"{language}: {probe}")
            # a stub is a header and a link, not prose
            self.assertLess(len(source), 4000, language)

    def test_blog_index_no_longer_lists_stub(self) -> None:
        source = BLOG_INDEX.read_text(encoding="utf-8")
        self.assertNotIn(SLUG, source)
        self.assertIn(f"/blog/{MERGED_SLUG}/", source)

    def test_sitemap_excludes_stub_and_keeps_merged_article(self) -> None:
        source = SITEMAP.read_text(encoding="utf-8")
        self.assertNotIn(SLUG, source)
        self.assertIn(TARGET["en"], source)
        self.assertIn(TARGET["zh"], source)


if __name__ == "__main__":
    unittest.main()
