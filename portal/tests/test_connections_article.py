from __future__ import annotations

import json
import re
import unittest
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

PORTAL = Path(__file__).resolve().parents[1]
ARTICLES = {
    "en": PORTAL / "blog" / "connections-recursive-intelligence" / "index.html",
    "zh": PORTAL
    / "blog"
    / "connections-recursive-intelligence"
    / "zh"
    / "index.html",
}
BLOG_INDEX = PORTAL / "blog" / "index.html"
REQUIRED_SECTIONS = {
    "premise",
    "neuron",
    "connectome",
    "epistemology",
    "civilization",
    "limits",
    "recursion",
    "references",
}
REQUIRED_CLAIM_TYPES = {"fact", "inference", "analogy", "thesis"}
REQUIRED_DOIS = {
    "10.1038/s41586-024-07558-y",
    "10.1038/s41586-024-07763-9",
    "10.1038/s41592-022-01466-7",
    "10.1126/science.adh1174",
    "10.1038/s41586-019-1424-8",
    "10.1038/s41586-021-03819-2",
    "10.1126/science.ade9097",
    "10.1038/s41586-021-03506-2",
}


class ArticleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.section_ids: set[str] = set()
        self.refs: list[str] = []
        self.svg_stack: list[dict[str, bool]] = []
        self.svg_results: list[dict[str, bool]] = []
        self.canonicals: list[str] = []
        self.hreflangs: set[str] = set()
        self.json_ld: list[dict[str, object]] = []
        self._json_buffer: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        element_id = values.get("id")
        if element_id:
            self.ids.append(element_id)
        if tag == "section" and element_id:
            self.section_ids.add(element_id)
        if tag in {"a", "link", "script", "img"}:
            ref = values.get("href") or values.get("src")
            if ref:
                self.refs.append(ref)
        href = values.get("href")
        if tag == "link" and values.get("rel") == "canonical" and href:
            self.canonicals.append(href)
        hreflang = values.get("hreflang")
        if tag == "link" and values.get("rel") == "alternate" and hreflang:
            self.hreflangs.add(hreflang)
        if tag == "svg":
            self.svg_stack.append({"title": False, "desc": False})
        elif tag in {"title", "desc"} and self.svg_stack:
            self.svg_stack[-1][tag] = True
        if tag == "script" and values.get("type") == "application/ld+json":
            self._json_buffer = []

    def handle_data(self, data: str) -> None:
        if self._json_buffer is not None:
            self._json_buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "svg" and self.svg_stack:
            self.svg_results.append(self.svg_stack.pop())
        if tag == "script" and self._json_buffer is not None:
            self.json_ld.append(json.loads("".join(self._json_buffer)))
            self._json_buffer = None


def load(path: Path) -> tuple[str, ArticleParser]:
    if not path.exists():
        raise unittest.SkipTest(f"not created yet: {path}")
    source = path.read_text(encoding="utf-8")
    parser = ArticleParser()
    parser.feed(source)
    return source, parser


class ConnectionsArticleTests(unittest.TestCase):
    def test_articles_exist(self) -> None:
        for language, path in ARTICLES.items():
            self.assertTrue(path.exists(), language)

    def test_sections_and_claim_types_match(self) -> None:
        parsed = {language: load(path) for language, path in ARTICLES.items()}
        for language, (source, parser) in parsed.items():
            self.assertEqual(REQUIRED_SECTIONS, parser.section_ids, language)
            claim_types = set(re.findall(r'data-claim-type="([^"]+)"', source))
            self.assertEqual(REQUIRED_CLAIM_TYPES, claim_types, language)
        self.assertEqual(parsed["en"][1].section_ids, parsed["zh"][1].section_ids)

    def test_connectome_facts_and_boundaries_are_present(self) -> None:
        required = {
            "en": ("139,255", "50 million", "not sufficient", "neuromodulation"),
            "zh": ("139,255", "5×10", "并不充分", "神经调质"),
        }
        forbidden = {
            "en": (
                "connectome alone produces complete autonomous intelligence",
                "human participant controlled a robotic arm",
            ),
            "zh": (
                "连接组本身产生完整自主智能",
                "人体试验患者用意念控制机械臂",
            ),
        }
        for language, path in ARTICLES.items():
            source, _ = load(path)
            for token in required[language]:
                self.assertIn(token, source, f"{language}: {token}")
            for phrase in forbidden[language]:
                self.assertNotIn(phrase, source, f"{language}: {phrase}")

    def test_citations_and_primary_source_sets_match(self) -> None:
        doi_sets: dict[str, set[str]] = {}
        for language, path in ARTICLES.items():
            source, _ = load(path)
            cited = set(re.findall(r'class="citation" href="#ref-(\d+)"', source))
            listed = set(re.findall(r'<li id="ref-(\d+)"', source))
            self.assertEqual(cited, listed, language)
            self.assertGreaterEqual(len(cited), 12, language)
            dois = {
                doi.lower() for doi in re.findall(r'doi\.org/([^"<]+)', source)
            }
            self.assertTrue(REQUIRED_DOIS <= dois, language)
            doi_sets[language] = dois
        self.assertEqual(doi_sets["en"], doi_sets["zh"])

    def test_ids_svg_and_local_assets_are_valid(self) -> None:
        for language, path in ARTICLES.items():
            _, parser = load(path)
            duplicates = [
                item for item, count in Counter(parser.ids).items() if count > 1
            ]
            self.assertEqual([], duplicates, language)
            self.assertTrue(parser.svg_results, language)
            self.assertTrue(
                all(item["title"] and item["desc"] for item in parser.svg_results),
                language,
            )
            for ref in parser.refs:
                parsed = urlparse(ref)
                if parsed.scheme or ref.startswith(("/", "#", "data:", "mailto:")):
                    continue
                self.assertTrue(
                    (path.parent / parsed.path).resolve().exists(), f"{language}: {ref}"
                )

    def test_seo_language_links_and_json_ld_are_complete(self) -> None:
        for language, path in ARTICLES.items():
            source, parser = load(path)
            self.assertEqual(1, len(parser.canonicals), language)
            self.assertEqual({"en", "zh-CN", "x-default"}, parser.hreflangs, language)
            self.assertIn('property="og:type" content="article"', source)
            article_data = [
                item for item in parser.json_ld if item.get("@type") == "Article"
            ]
            self.assertEqual(1, len(article_data), language)
            for field in (
                "headline",
                "description",
                "author",
                "publisher",
                "datePublished",
                "dateModified",
                "mainEntityOfPage",
            ):
                self.assertIn(field, article_data[0], f"{language}: {field}")

    def test_blog_index_lists_article_and_category(self) -> None:
        source = BLOG_INDEX.read_text(encoding="utf-8")
        self.assertIn('data-filter="intelligence"', source)
        self.assertIn('data-cat="intelligence"', source)
        self.assertIn("/blog/connections-recursive-intelligence/", source)
        self.assertIn("Connections Rule", source)


if __name__ == "__main__":
    unittest.main()
