from __future__ import annotations

import json
import re
import unittest
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

PORTAL = Path(__file__).resolve().parents[1]
SLUG = "seven-billion-tokens"
ARTICLES = {
    "en": PORTAL / "blog" / SLUG / "index.html",
    "zh": PORTAL / "blog" / SLUG / "zh" / "index.html",
}
ARTICLE_CSS = PORTAL / "css" / "blog-article.css"
BLOG_INDEX = PORTAL / "blog" / "index.html"
SITEMAP = PORTAL / "sitemap.xml"
CANONICAL = {
    "en": f"https://www.vlsc.net/blog/{SLUG}/",
    "zh": f"https://www.vlsc.net/blog/{SLUG}/zh/",
}

REQUIRED_SECTIONS = {
    "ledger",
    "floor",
    "numbers-lie",
    "intent",
    "before",
    "machine",
    "chain",
    "scale",
    "delivery",
    "drift",
    "human",
    "playbook",
    "references",
}
REQUIRED_CLAIM_TYPES = {"fact", "inference", "analogy", "thesis"}

# Three volumes (spec §5.0). Order matters; `references` is an appendix and
# deliberately sits OUTSIDE every volume.
VOLUMES = (
    ("gewu", ("ledger", "floor", "numbers-lie", "intent", "before")),
    ("zhizhi", ("machine", "chain", "scale")),
    ("zhixing", ("delivery", "drift", "human", "playbook")),
)
UNVOLUMED_SECTIONS = ("references",)
VOLUME_TITLES = {
    "en": {"gewu": "Investigating Things", "zhizhi": "Extending Knowledge",
           "zhixing": "Unity of Knowing and Acting"},
    "zh": {"gewu": "格物", "zhizhi": "致知", "zhixing": "知行合一"},
}
ZH_TITLE = "格物致知"
EN_TITLE = "Seven Billion Tokens, One Field Incident"

# Five required classical correspondences (spec §5.0). Anchors are per-language:
# the ZH page carries the classical Chinese; the EN page carries the standard
# English gloss (and MAY additionally carry the Chinese term, but is not forced to).
CLASSICAL_ANCHORS = {
    "before": {
        "zh": ("格竹",),
        "en": ("investigating the bamboo",),
    },
    "numbers-lie": {
        "zh": ("致知在格物",),
        "en": ("investigating things",),
    },
    "chain": {
        "zh": ("物格而后知至",),
        "en": ("things investigated", "knowledge arrives"),
    },
    "scale": {
        "zh": ("豁然贯通",),
        "en": ("sudden thorough comprehension",),
    },
    "human": {
        "zh": ("知而不行",),
        "en": ("knowing and not acting",),
    },
}
# Classical claims must be analogy or thesis, never fact. Terms that mark a
# claim-box as classical, per language.
CLASSICAL_TERMS = {
    "zh": ("格竹", "格物", "致知", "知行", "贯通"),
    "en": ("bamboo", "investigating things", "extending knowledge",
           "unity of knowing", "comprehension"),
}
# At least one source must be named, per language.
CITATION_SOURCES = {
    "zh": ("大学", "传习录", "大学章句"),
    "en": ("Great Learning", "Chuanxi", "Zhu Xi", "Wang Yangming"),
}
# Teleological claims are forbidden (R1's near cousin).
FORBIDDEN_TELEOLOGY = ("早就有了", "already had agentic", "invented agentic")

# Census 2026-09-05. These strings must appear verbatim in BOTH languages.
LEDGER_CONSTANTS = {
    "recorded_tokens": "7,007,437,567",
    "recorded_turns": "41,257",
    "recorded_sessions": "882",
    "with_estimates_tokens": "7,241,684,966",
    "with_estimates_interactions": "87,580",
    "with_estimates_sessions": "1,359",
    "fresh_tokens": "336,661,475",
    "cache_read_tokens": "6,670,776,092",
    "output_tokens": "30,061,161",
    "cache_read_share": "95.2",
    "fresh_share": "4.8",
    "pi_tokens": "1,625,562,962",
    "pi_cost": "15.11",
    "cost_per_billion": "9.30",
    "constraints_total": "52",
    "constraints_ft710": "17",
    "constraints_modern": "21",
    "constraints_ft8": "14",
    "tests_ft710": "439",
    "tests_modern": "682",
    "tests_ft8_collected": "937",
    "iflow_turns": "37,202",
    "iflow_estimate": "234,247,399",
    "hermes_sessions": "292",
    "hermes_messages": "9,121",
    "hermes_toolcalls": "4,336",
    "first_pass_wrong": "5,380,941,148",
    "codex_db_corroboration": "546,858,767",
    "census_date": "2026-09-05",
}

# R1 / R4 red lines.
FORBIDDEN = {
    "en": (
        "built by AI",
        "built by agents",
        "AI-built",
        "AI wrote",
        "agents built",
    ),
    "zh": (
        "代理式工程",
        "由 AI 建造",
        "由智能体建造",
        "AI 打造",
        "智能体建造了",
    ),
}

# Numbers overturned by the 2026-09-05 census. Must NOT appear as current claims.
STALE_NUMBERS = ("180+ tests", "180+ 测试", "593 tests", "593 测试", "v1.10.1")

# R2: a pre-edit-gate claim may only sit near these three repos.
GATE_OWNERS = ("mrrc_ft710", "mrrc_modern", "ft8", "FT-710", "Modern", "MRRC-FT8")
GATE_FORBIDDEN_NEIGHBOURS = ("SunMRRC", "SunsdrMobile", "EFHW", "MRRC Universal")

# R7: estimates must be visibly labelled.
ESTIMATE_LABELS = {
    "en": ("estimate", "not recorded", "unrecorded"),
    "zh": ("估算", "未记录", "工具记 0"),
}


class ArticleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.section_ids: set[str] = set()
        self.refs: list[str] = []
        self.canonicals: list[str] = []
        self.hreflangs: set[str] = set()
        self.json_ld: list[dict[str, object]] = []
        self.section_volume: dict[str, str | None] = {}
        self.volume_order: list[str] = []
        self.div_depth = 0
        self._div_stack: list[str | None] = []
        self._json_buffer: list[str] | None = None

    def _enclosing_volume(self) -> str | None:
        for value in reversed(self._div_stack):
            if value is not None:
                return value
        return None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        element_id = values.get("id")
        if element_id:
            self.ids.append(element_id)
        if tag == "div":
            self.div_depth += 1
            volume = values.get("data-volume")
            self._div_stack.append(volume)
            if volume and volume not in self.volume_order:
                self.volume_order.append(volume)
        if tag == "section" and element_id:
            self.section_ids.add(element_id)
            self.section_volume[element_id] = self._enclosing_volume()
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
        if tag == "script" and values.get("type") == "application/ld+json":
            self._json_buffer = []

    def handle_data(self, data: str) -> None:
        if self._json_buffer is not None:
            self._json_buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "div":
            self.div_depth -= 1
            if self._div_stack:
                self._div_stack.pop()
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


class SevenBillionTokensArticleTests(unittest.TestCase):
    def test_articles_and_css_exist(self) -> None:
        self.assertTrue(ARTICLE_CSS.exists(), "blog-article.css")
        for language, path in ARTICLES.items():
            self.assertTrue(path.exists(), language)

    def test_sections_and_claim_types_match(self) -> None:
        parsed = {language: load(path) for language, path in ARTICLES.items()}
        for language, (source, parser) in parsed.items():
            self.assertEqual(REQUIRED_SECTIONS, parser.section_ids, language)
            claim_types = set(re.findall(r'data-claim-type="([^"]+)"', source))
            self.assertEqual(REQUIRED_CLAIM_TYPES, claim_types, language)
        self.assertEqual(parsed["en"][1].section_ids, parsed["zh"][1].section_ids)

    def test_ledger_constants_appear_verbatim(self) -> None:
        for language, path in ARTICLES.items():
            source, _ = load(path)
            missing = [
                f"{name}={value}"
                for name, value in LEDGER_CONSTANTS.items()
                if value not in source
            ]
            self.assertEqual([], missing, language)

    def test_stale_numbers_are_gone(self) -> None:
        targets = list(ARTICLES.values()) + [
            PORTAL / "index.html",
            PORTAL / "zh" / "index.html",
            PORTAL / "agentic.html",
            PORTAL / "zh" / "agentic.html",
            PORTAL / "engineering.html",
            PORTAL / "zh" / "engineering.html",
        ]
        for path in targets:
            if not path.exists():
                continue
            source = path.read_text(encoding="utf-8")
            # The article's `drift` section must be able to QUOTE a wrong number
            # in order to show it was wrong. Quoted values are wrapped in
            # <del class="stale">…</del> and stripped before the check, so a
            # struck-through citation is allowed but a live claim is not.
            # Tag regexes tolerate line-wrapped markup (`</del\n>`), and the
            # surviving text is whitespace-normalized so a live claim cannot
            # hide behind a line break either.
            live = re.sub(r"<del\s+class=\"stale\">.*?</del\s*>", " ", source, flags=re.S)
            live = re.sub(r"\s+", " ", live)
            hits = [n for n in STALE_NUMBERS if n in live]
            self.assertEqual([], hits, str(path.relative_to(PORTAL)))

    def test_drift_section_quotes_stale_values_as_struck_through(self) -> None:
        # Positive counterpart: the pedagogy must survive the stripping above.
        # Each stale value the article names has to appear inside <del class="stale">.
        for language, path in ARTICLES.items():
            source, _parser = load(path)
            start = source.find('<section id="drift"')
            self.assertNotEqual(-1, start, f"{language}: drift section")
            end = source.find("</section>", start)
            body = source[start:end]
            struck = re.findall(r"<del\s+class=\"stale\">(.*?)</del\s*>", body, re.S)
            self.assertGreaterEqual(len(struck), 3, f"{language}: drift quotes")
            joined = " ".join(struck)
            for value in ("180+", "593", "v1.10.1"):
                self.assertIn(value, joined, f"{language}: struck-through {value}")

    def test_estimates_are_labelled(self) -> None:
        for language, path in ARTICLES.items():
            source, _ = load(path)
            for value in (
                LEDGER_CONSTANTS["iflow_estimate"],
                LEDGER_CONSTANTS["first_pass_wrong"],
            ):
                index = source.find(value)
                self.assertNotEqual(-1, index, f"{language}: {value}")
                window = source[max(0, index - 900) : index + 900].lower()
                self.assertTrue(
                    any(label in window for label in ESTIMATE_LABELS[language]),
                    f"{language}: {value} needs an estimate/unrecorded label nearby",
                )

    def test_gate_claims_only_near_owning_repos(self) -> None:
        pattern = re.compile(r"pre-edit gate|编辑前门禁|编辑前拦截|PreToolUse")
        for language, path in ARTICLES.items():
            source, _ = load(path)
            for match in pattern.finditer(source):
                window = source[max(0, match.start() - 700) : match.start() + 700]
                self.assertTrue(
                    any(owner in window for owner in GATE_OWNERS),
                    f"{language}: gate claim at {match.start()} lacks an owning repo",
                )
                for bad in GATE_FORBIDDEN_NEIGHBOURS:
                    if bad in window:
                        self.assertNotIn(
                            bad,
                            window,
                            f"{language}: gate claim near {bad} violates R2",
                        )

    def test_forbidden_phrases_absent(self) -> None:
        for language, path in ARTICLES.items():
            source, _ = load(path)
            for phrase in FORBIDDEN[language]:
                self.assertNotIn(phrase, source, f"{language}: {phrase}")

    def test_zh_uses_mandated_terminology(self) -> None:
        source, _ = load(ARTICLES["zh"])
        self.assertIn("智能体工程", source)
        self.assertIn("前沿部署工程", source)
        self.assertNotIn("代理式工程", source)

    def test_titles_are_bilingual(self) -> None:
        en_source, _ = load(ARTICLES["en"])
        zh_source, _ = load(ARTICLES["zh"])
        self.assertIn(EN_TITLE, en_source)
        self.assertIn(ZH_TITLE, zh_source)
        # The EN page keeps the concrete hook and stays free of the ZH title,
        # so the two frames never blur into one.
        self.assertNotIn(ZH_TITLE, en_source)
        # each page must still offer the other language
        self.assertIn('href="zh/"', en_source)
        self.assertIn('href="../"', zh_source)

    def test_volumes_group_sections_correctly(self) -> None:
        expected = {
            section: volume for volume, sections in VOLUMES for section in sections
        }
        for section in UNVOLUMED_SECTIONS:
            expected[section] = None
        self.assertEqual(REQUIRED_SECTIONS, set(expected))
        for language, path in ARTICLES.items():
            source, parser = load(path)
            self.assertEqual(0, parser.div_depth, f"{language}: unbalanced <div>")
            self.assertEqual(
                [v for v, _ in VOLUMES], parser.volume_order,
                f"{language}: volume order",
            )
            self.assertEqual(expected, parser.section_volume, language)
            for volume, _sections in VOLUMES:
                self.assertIn(VOLUME_TITLES[language][volume], source, language)

    def test_classical_anchors_are_present_in_their_sections(self) -> None:
        for language, path in ARTICLES.items():
            source, _parser = load(path)
            for section, per_language in CLASSICAL_ANCHORS.items():
                start = source.find(f'<section id="{section}"')
                self.assertNotEqual(-1, start, f"{language}: section {section}")
                end = source.find("</section>", start)
                self.assertNotEqual(-1, end, f"{language}: unclosed {section}")
                # Whitespace-normalize: line-wrapped prose ("knowledge\narrives")
                # must still match its anchor phrase.
                body = re.sub(r"\s+", " ", source[start:end])
                for anchor in per_language[language]:
                    self.assertIn(anchor, body, f"{language}: {section} needs {anchor}")

    def test_classical_citations_are_not_graded_as_fact(self) -> None:
        for language, path in ARTICLES.items():
            source, _parser = load(path)
            terms = CLASSICAL_TERMS[language]
            boxes = re.findall(
                r'<div class="claim-box" data-claim-type="([^"]+)">((?:(?!</div>).)*)',
                source,
                re.S,
            )
            self.assertTrue(boxes, f"{language}: no claim-box found")
            for kind, body in boxes:
                if any(term in body for term in terms):
                    self.assertIn(
                        kind,
                        {"analogy", "thesis"},
                        f"{language}: classical claim graded as '{kind}'",
                    )
            self.assertTrue(
                any(name in source for name in CITATION_SOURCES[language]),
                f"{language}: no classical source named",
            )
            lowered = source.lower()
            for phrase in FORBIDDEN_TELEOLOGY:
                self.assertNotIn(phrase.lower(), lowered, f"{language}: {phrase}")

    def test_chain_reproduction_block_is_present(self) -> None:
        required = (
            "sdd_context.py",
            "cat-no-dn",
            "AD-014",
            "DN;",
        )
        for language, path in ARTICLES.items():
            source, _ = load(path)
            for token in required:
                self.assertIn(token, source, f"{language}: {token}")
            self.assertRegex(source, r"exit|退出码|\$\?")
            self.assertIn("2", source)

    def test_ids_and_local_assets_are_valid(self) -> None:
        for language, path in ARTICLES.items():
            _, parser = load(path)
            duplicates = [i for i, c in Counter(parser.ids).items() if c > 1]
            self.assertEqual([], duplicates, language)
            for ref in parser.refs:
                parsed = urlparse(ref)
                if parsed.scheme or ref.startswith(("/", "#", "data:", "mailto:")):
                    continue
                self.assertTrue(
                    (path.parent / parsed.path).resolve().exists(),
                    f"{language}: {ref}",
                )

    def test_seo_language_links_and_json_ld_are_complete(self) -> None:
        for language, path in ARTICLES.items():
            source, parser = load(path)
            self.assertEqual([CANONICAL[language]], parser.canonicals, language)
            self.assertEqual({"en", "zh-CN", "x-default"}, parser.hreflangs, language)
            self.assertIn('property="og:type" content="article"', source)
            article_data = [i for i in parser.json_ld if i.get("@type") == "Article"]
            self.assertEqual(1, len(article_data), language)
            for field in (
                "headline",
                "description",
                "author",
                "publisher",
                "datePublished",
                "dateModified",
                "articleSection",
                "mainEntityOfPage",
            ):
                self.assertIn(field, article_data[0], f"{language}: {field}")
            self.assertEqual("2026-09-05", article_data[0]["datePublished"], language)
            self.assertEqual("Intelligence", article_data[0]["articleSection"], language)

    def test_links_to_thesis_and_mechanism_pages(self) -> None:
        for language, path in ARTICLES.items():
            source, _ = load(path)
            self.assertIn("/agentic.html", source, language)
            self.assertIn("/engineering.html", source, language)

    def test_blog_index_lists_article(self) -> None:
        source = BLOG_INDEX.read_text(encoding="utf-8")
        self.assertIn(f"/blog/{SLUG}/", source)
        self.assertIn('data-cat="intelligence"', source)
        self.assertIn("Seven Billion Tokens", source)
        self.assertIn("Sep 5, 2026", source)

    def test_sitemap_lists_both_languages(self) -> None:
        source = SITEMAP.read_text(encoding="utf-8")
        self.assertIn(CANONICAL["en"], source)
        self.assertIn(CANONICAL["zh"], source)


if __name__ == "__main__":
    unittest.main()
