from __future__ import annotations

import re
import unittest
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

PORTAL = Path(__file__).resolve().parents[1]
PAGES = {
    "en": PORTAL / "agentic.html",
    "zh": PORTAL / "zh" / "agentic.html",
}
REQUIRED_SECTIONS = {
    "thesis",
    "roles",
    "lineage",
    "harness",
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


class AgenticPageTests(unittest.TestCase):
    def test_agentic_thesis_and_role_split_are_stated(self) -> None:
        required = {
            "en": (
                "Agentic engineering is the discipline",
                "Intent",
                "Boundaries",
                "Judgment",
            ),
            "zh": ("智能体工程", "意图", "边界", "裁决"),
        }
        for language, path in PAGES.items():
            source, _ = load_page(path)
            for token in required[language]:
                self.assertIn(token, source, f"{language}: {token}")

    def test_ontology_consumers_cite_real_constraint_rule_ids(self) -> None:
        rule_ids = (
            "ptt-authority",
            "no-direct-serial",
            "cat-no-dn",
            "poll-stale-guard",
            "vendor-readonly",
        )
        for language, path in PAGES.items():
            source, _ = load_page(path)
            cited = [r for r in rule_ids if r in source]
            self.assertGreaterEqual(len(cited), 4, language)

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
            "One Field. Three Tracks.",
            "Built Through Forward Deployed Engineering",
            "由 Agent 写成",
            "written by AI",
        )
        for language, path in PAGES.items():
            source, _ = load_page(path)
            for phrase in forbidden:
                self.assertNotIn(phrase, source, f"{language}: {phrase}")

    def test_page_metadata_leads_with_new_umbrella(self) -> None:
        """`<title>` / description / keywords 是搜索结果与链接预览里**唯一可见的文案**。

        正文全改了而 meta 没改，所有结构断言（节 id / class / 锚点）依旧全绿——
        执行任务 4 时就是这样漏掉两页 meta 的（计划补正 #10），故固定成契约。
        FDE 作为前史保留在关键词里，但不得再是首位。
        """

        def grab(pattern: str, source: str, label: str, language: str) -> str:
            # 用断言而非直接 .group()：标签缺失时要报清哪个标签，而不是 AttributeError。
            # （用 assert 语句而不是 assertIsNotNone：后者不会为类型检查器收窄。）
            match = re.search(pattern, source, re.S)
            assert match is not None, f"{language}: 找不到 {label}"
            return match.group(1)

        umbrella = {"en": "Agentic Engineering", "zh": "智能体工程"}
        for language, path in PAGES.items():
            source, _ = load_page(path)
            title = grab(r"<title>(.*?)</title>", source, "<title>", language)
            desc = grab(
                r'<meta name="description" content="(.*?)"', source, "description", language
            )
            keywords = grab(
                r'<meta name="keywords" content="(.*?)"', source, "keywords", language
            )
            needle = umbrella[language].lower()
            # 大小写不敏感：<title> 是 Title Case，而 description 是散文、句首小写属正常。
            # 本契约要卡的是「术语在不在」，不是它怎么大写。
            self.assertIn(needle, title.lower(), f"{language}: <title> 未含新伞形术语 → {title}")
            self.assertIn(needle, desc.lower(), f"{language}: description 未含新伞形术语")
            first = keywords.split(",")[0].strip().lower()
            self.assertIn(
                needle.lower(), first, f"{language}: 首位关键词仍是 {first!r}"
            )

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
