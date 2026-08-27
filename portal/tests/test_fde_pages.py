from __future__ import annotations

import re
import unittest
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

PORTAL = Path(__file__).resolve().parents[1]
PAGES = {
    "en": PORTAL / "fde.html",
    "zh": PORTAL / "zh" / "fde.html",
}
REQUIRED_SECTIONS = {
    "method",
    "tracks",
    "families",
    "leverage",
    "ontology",
    "capabilities",
    "evidence",
}
REQUIRED_FAMILIES = {
    "mrrc-universal",
    "mrrc-direct-usb",
    "sunmrrc",
    "mrrc-ft8",
    "efhw",
}


class AuditParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.section_ids: set[str] = set()
        self.local_refs: list[str] = []
        self.svg_stack: list[dict[str, bool]] = []
        self.svg_results: list[dict[str, bool]] = []
        self.details_count = 0
        self.summary_count = 0

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
                self.local_refs.append(ref)
        if tag == "svg":
            self.svg_stack.append({"title": False, "desc": False})
        elif tag in {"title", "desc"} and self.svg_stack:
            self.svg_stack[-1][tag] = True
        elif tag == "details":
            self.details_count += 1
        elif tag == "summary":
            self.summary_count += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "svg" and self.svg_stack:
            self.svg_results.append(self.svg_stack.pop())


def load_page(path: Path) -> tuple[str, AuditParser]:
    source = path.read_text(encoding="utf-8")
    parser = AuditParser()
    parser.feed(source)
    return source, parser


class FdePageTests(unittest.TestCase):
    def test_required_sections_and_families_exist_in_both_languages(self) -> None:
        for language, path in PAGES.items():
            source, parser = load_page(path)
            self.assertTrue(REQUIRED_SECTIONS <= parser.section_ids, language)
            families = set(re.findall(r'data-family="([^"]+)"', source))
            self.assertEqual(REQUIRED_FAMILIES, families, language)

    def test_product_family_nesting_is_explicit(self) -> None:
        for language, path in PAGES.items():
            source, _ = load_page(path)
            sun = re.search(
                r'data-family="sunmrrc"[\s\S]*?data-family-end="sunmrrc"', source
            )
            direct = re.search(
                r'data-family="mrrc-direct-usb"[\s\S]*?data-family-end="mrrc-direct-usb"',
                source,
            )
            self.assertIsNotNone(sun, language)
            self.assertIsNotNone(direct, language)
            assert sun is not None
            assert direct is not None
            self.assertIn('data-client="sunsdrmobile"', sun.group(0))
            self.assertIn('data-client="ios"', direct.group(0))
            self.assertIn('data-client="android"', direct.group(0))

    def test_obsolete_top_level_counts_are_removed(self) -> None:
        forbidden = (
            "FDE Across Three Projects",
            'One Methodology<br><span class="gradient">Three Products',
            "跨三项目的 FDE 实战",
            '一套方法论<br><span class="gradient">三款产品',
        )
        for language, path in PAGES.items():
            source, _ = load_page(path)
            for phrase in forbidden:
                self.assertNotIn(phrase, source, f"{language}: {phrase}")

    def test_ontology_and_evidence_vocabulary_is_present(self) -> None:
        required_tokens = {
            "en": (
                "Domain Ontology",
                "CommandIntent",
                "Actuation",
                "Observation",
                "Field verified",
            ),
            "zh": ("领域本体", "控制意图", "执行活动", "观测", "现场验证"),
        }
        for language, path in PAGES.items():
            source, _ = load_page(path)
            for token in required_tokens[language]:
                self.assertIn(token, source, f"{language}: {token}")

    def test_ids_are_unique_and_section_parity_is_preserved(self) -> None:
        parsed = {language: load_page(path)[1] for language, path in PAGES.items()}
        for language, parser in parsed.items():
            duplicates = [
                item for item, count in Counter(parser.ids).items() if count > 1
            ]
            self.assertEqual([], duplicates, language)
        self.assertEqual(parsed["en"].section_ids, parsed["zh"].section_ids)

    def test_svg_and_details_are_accessible(self) -> None:
        for language, path in PAGES.items():
            _, parser = load_page(path)
            self.assertTrue(parser.svg_results, language)
            self.assertTrue(
                all(item["title"] and item["desc"] for item in parser.svg_results),
                language,
            )
            self.assertGreater(parser.details_count, 0, language)
            self.assertEqual(parser.details_count, parser.summary_count, language)

    def test_relative_assets_exist(self) -> None:
        for language, path in PAGES.items():
            _, parser = load_page(path)
            for ref in parser.local_refs:
                parsed = urlparse(ref)
                if parsed.scheme or ref.startswith(("/", "#", "data:", "mailto:")):
                    continue
                target = (path.parent / parsed.path).resolve()
                self.assertTrue(target.exists(), f"{language}: missing {ref}")


if __name__ == "__main__":
    unittest.main()
