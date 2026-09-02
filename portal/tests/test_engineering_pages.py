from __future__ import annotations

import re
import unittest
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

PORTAL = Path(__file__).resolve().parents[1]
PAGES = {
    "en": PORTAL / "engineering.html",
    "zh": PORTAL / "zh" / "engineering.html",
}
AGENTIC_PAGES = {
    "en": PORTAL / "agentic.html",
    "zh": PORTAL / "zh" / "agentic.html",
}
INDEX_PAGES = {
    "en": PORTAL / "index.html",
    "zh": PORTAL / "zh" / "index.html",
}
REQUIRED_SECTIONS = {
    "overview",
    "harness",
    "loop",
    "sdd",
    "integration",
    "evidence",
    "maturity",
}
REQUIRED_HARNESSES = {"business", "technical", "product"}
REQUIRED_EXECUTION_STAGES = {
    "agents",
    "repository",
    "tools",
    "tests-review",
    "deployment",
    "field-evidence",
}
REQUIRED_STATES = {
    "planned",
    "implemented",
    "tested",
    "bench-verified",
    "field-verified",
    "released",
    "deferred",
    "known-issue",
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
        self.refs: list[str] = []
        self.local_scripts: list[str] = []
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
                self.refs.append(ref)
                parsed = urlparse(ref)
                if tag == "script" and not parsed.scheme and not ref.startswith("/"):
                    self.local_scripts.append(parsed.path)
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
    if not path.exists():
        raise unittest.SkipTest(f"not created yet: {path}")
    source = path.read_text(encoding="utf-8")
    parser = AuditParser()
    parser.feed(source)
    return source, parser


class EngineeringPageTests(unittest.TestCase):
    def test_engineering_pages_exist(self) -> None:
        for language, path in PAGES.items():
            self.assertTrue(path.exists(), language)

    def test_required_sections_and_language_parity(self) -> None:
        parsed = {language: load_page(path)[1] for language, path in PAGES.items()}
        for language, parser in parsed.items():
            self.assertTrue(REQUIRED_SECTIONS <= parser.section_ids, language)
        self.assertEqual(parsed["en"].section_ids, parsed["zh"].section_ids)

    def test_dual_layer_harness_is_explicit(self) -> None:
        for language, path in PAGES.items():
            source, _ = load_page(path)
            harnesses = set(re.findall(r'data-harness="([^"]+)"', source))
            stages = set(re.findall(r'data-execution-stage="([^"]+)"', source))
            self.assertEqual(REQUIRED_HARNESSES, harnesses, language)
            self.assertEqual(REQUIRED_EXECUTION_STAGES, stages, language)

    def test_nested_loops_are_explicit(self) -> None:
        for language, path in PAGES.items():
            source, _ = load_page(path)
            self.assertIn('data-loop="fde"', source, language)
            self.assertIn('data-loop="engineering"', source, language)
            for token in (
                "Echo",
                "Delta",
                "Product",
                "Specify",
                "Implement",
                "Test",
                "Review",
                "Update SDD",
            ):
                self.assertIn(token, source, f"{language}: {token}")

    def test_sdd_lifecycle_states_are_complete(self) -> None:
        for language, path in PAGES.items():
            source, _ = load_page(path)
            states = set(re.findall(r'data-sdd-state="([^"]+)"', source))
            self.assertEqual(REQUIRED_STATES, states, language)

    def test_five_family_evidence_matrix_is_complete(self) -> None:
        for language, path in PAGES.items():
            source, _ = load_page(path)
            families = set(
                re.findall(r'data-engineering-family="([^"]+)"', source)
            )
            self.assertEqual(REQUIRED_FAMILIES, families, language)

    def test_agentic_summary_precedes_ontology_and_links_to_engineering(self) -> None:
        # 注：本节断言的 "engineering" 节在任务 3/4 改名为 "harness"，届时同步更新。
        for language, path in AGENTIC_PAGES.items():
            source, parser = load_page(path)
            self.assertIn("engineering", parser.section_ids, language)
            self.assertLess(
                source.index('id="leverage"'), source.index('id="engineering"')
            )
            self.assertLess(
                source.index('id="engineering"'), source.index('id="ontology"')
            )
            self.assertIn('href="engineering.html"', source, language)

    def test_portal_navigation_links_to_engineering(self) -> None:
        for language, path in INDEX_PAGES.items():
            source, _ = load_page(path)
            self.assertIn('href="engineering.html"', source, language)

    def test_ids_svg_details_and_scripts_are_accessible(self) -> None:
        for language, path in PAGES.items():
            _, parser = load_page(path)
            duplicates = [
                item for item, count in Counter(parser.ids).items() if count > 1
            ]
            self.assertEqual([], duplicates, language)
            self.assertTrue(parser.svg_results, language)
            self.assertTrue(
                all(item["title"] and item["desc"] for item in parser.svg_results),
                language,
            )
            self.assertGreater(parser.details_count, 0, language)
            self.assertEqual(parser.details_count, parser.summary_count, language)
            expected_script = (
                "js/global-nav.js" if language == "en" else "../js/global-nav.js"
            )
            self.assertEqual([expected_script], parser.local_scripts, language)

    def test_relative_assets_exist(self) -> None:
        for group_name, pages in (("engineering", PAGES), ("agentic", AGENTIC_PAGES)):
            for language, path in pages.items():
                _, parser = load_page(path)
                for ref in parser.refs:
                    parsed = urlparse(ref)
                    if parsed.scheme or ref.startswith(
                        ("/", "#", "data:", "mailto:")
                    ):
                        continue
                    target = (path.parent / parsed.path).resolve()
                    self.assertTrue(
                        target.exists(), f"{group_name}/{language}: missing {ref}"
                    )


if __name__ == "__main__":
    unittest.main()
