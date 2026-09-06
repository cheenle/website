from __future__ import annotations

import json
import re
import unittest
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

PORTAL = Path(__file__).resolve().parents[1]
SLUG = "from-intent-to-delivery"
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

# Opening thesis + four dimensions (one volume each) + closing + four data
# appendices. The id set must be identical in both languages; thesis, closing
# and the appendices sit OUTSIDE every volume.
REQUIRED_SECTIONS = {
    "thesis",
    "dim-abstraction",
    "dim-knowledge",
    "dim-economics",
    "dim-responsibility",
    "closing",
    "appendix-repos",
    "appendix-tools",
    "appendix-timeline",
    "appendix-limits",
}
# Grading discipline: measured/test-run results are fact, caliber reasoning is
# inference, methodology claims are thesis. This article uses exactly these.
REQUIRED_CLAIM_TYPES = {"fact", "inference", "thesis"}

VOLUMES = (
    ("abstraction", ("dim-abstraction",)),
    ("knowledge", ("dim-knowledge",)),
    ("economics", ("dim-economics",)),
    ("responsibility", ("dim-responsibility",)),
)
UNVOLUMED_SECTIONS = (
    "thesis",
    "closing",
    "appendix-repos",
    "appendix-tools",
    "appendix-timeline",
    "appendix-limits",
)
VOLUME_TITLES = {
    "en": {"abstraction": "The Abstraction Ladder",
           "knowledge": "The Carrier Decides How Long Knowledge Lives",
           "economics": "Tokens Are the Price of Uncertainty",
           "responsibility": "Two Ledgers"},
    "zh": {"abstraction": "抽象阶梯",
           "knowledge": "知识的载体决定知识的寿命",
           "economics": "不确定性的价格",
           "responsibility": "两本账"},
}
EN_TITLE = "One USB Cable: Seven Months of a Business Intent, and the Four Dimensions of Agentic Engineering"
ZH_TITLE = "从一根 USB 线说起：一个业务意图的七个月，与 Agentic 工程的四个维度"

# Hard numbers and commit hashes from the approved story. Every one of these
# strings must appear verbatim in BOTH languages.
LEDGER_CONSTANTS = {
    "tokens_total_recorded": "7,123,689,610",
    "tokens_total_dedup": "5,091,596,244",
    "claude_line_caliber": "3,207,496,620",
    "claude_dedup_caliber": "1,175,403,254",
    "pi_tokens": "1,633,493,477",
    "kimi_tokens": "1,203,639,664",
    "codex_tokens": "547,796,667",
    "mulerun_tokens": "499,992,587",
    "cursor_tokens": "27,079,705",
    "opencode_tokens": "4,190,890",
    "constraints_ft710": "17",
    "constraints_modern": "21",
    "constraints_ft8": "14",
    "constraints_total": "52",
    "tests_ft710": "439",
    "tests_modern": "682",
    "tests_ft8_collected": "937",
    "commits_mrrc": "181",
    "commits_ft710": "162",
    "commits_modern": "244",
    "commits_ft8": "253",
    "commits_sunsdr": "67",
    "commits_sunsdrmobile": "9",
    "commits_website": "102",
    "claude_api_responses": "7,519",
    "shared_commits_ft710_modern": "149",
    "iflow_turns": "37,202",
    "census_date": "2026-09-05",
    "commit_72fd6f0": "72fd6f0",
    "commit_bb128ff": "bb128ff",
    "commit_2498ec2": "2498ec2",
    "commit_d4a7a32": "d4a7a32",
    "commit_c545d69": "c545d69",
    "commit_9403e2e": "9403e2e",
    "commit_7cfefec": "7cfefec",
    "commit_067f565": "067f565",
    "commit_58aa675": "58aa675",
    "commit_88f519f": "88f519f",
    "commit_625779f": "625779f",
    "cache_read_share": "95.2",
    "ft8_tokens_per_line": "26,800",
    "wfview_tokens_per_line": "136",
    "line_caliber_inflation": "2.7",
}

# Red lines: never claim a product family was built by AI.
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
        "AI 打造",
        "由智能体建造",
    ),
}

# R2: a pre-edit-gate claim may only sit near the three repos that own one.
GATE_OWNERS = ("mrrc_ft710", "mrrc_modern", "ft8", "FT-710", "Modern", "MRRC-FT8")
GATE_FORBIDDEN_NEIGHBOURS = ("SunMRRC", "SunsdrMobile", "EFHW", "MRRC Universal")

# Estimates must be visibly labelled near the estimate figure.
ESTIMATE_PROBES = {
    "en": ("234 million",),
    "zh": ("2.34 亿",),
}
ESTIMATE_LABELS = {
    "en": ("estimate", "not recorded", "unrecorded"),
    "zh": ("估算", "未记录", "工具记 0"),
}
# The recorded vs estimated columns must never be merged.
NO_MERGE_PHRASE = {"en": "must not be merged", "zh": "不合并"}

# Appendix D: the seven measurement boundaries. Key strings per language.
LIMITS_ANCHORS = {
    "en": ("time-window", "line caliber", "message.id", "lower bounds",
           "149", "±10%", "self-reported"),
    "zh": ("时间窗口", "行口径", "message.id", "下限",
           "149", "±10%", "自记"),
}
# claude-code dual caliber: both columns side by side, plus the note that the
# published census used the line caliber.
DUAL_CALIBER_NOTE = {
    "en": "published census used the line caliber",
    "zh": "已发表 census 用行口径",
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


def section_body(source: str, section_id: str, language: str) -> str:
    start = source.find(f'<section id="{section_id}"')
    assert start != -1, f"{language}: section {section_id}"
    end = source.find("</section>", start)
    assert end != -1, f"{language}: unclosed {section_id}"
    return source[start:end]


class FromIntentToDeliveryArticleTests(unittest.TestCase):
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

    def test_estimates_are_labelled(self) -> None:
        for language, path in ARTICLES.items():
            source, _ = load(path)
            for value in ESTIMATE_PROBES[language]:
                index = source.find(value)
                self.assertNotEqual(-1, index, f"{language}: {value}")
                window = source[max(0, index - 900) : index + 900].lower()
                self.assertTrue(
                    any(label in window for label in ESTIMATE_LABELS[language]),
                    f"{language}: {value} needs an estimate/unrecorded label nearby",
                )

    def test_recorded_and_estimated_ledgers_are_not_merged(self) -> None:
        for language, path in ARTICLES.items():
            source, _ = load(path)
            self.assertIn(NO_MERGE_PHRASE[language], source, language)

    def test_dual_caliber_is_presented_side_by_side(self) -> None:
        for language, path in ARTICLES.items():
            source, _ = load(path)
            body = section_body(source, "appendix-tools", language)
            self.assertIn(LEDGER_CONSTANTS["claude_line_caliber"], body, language)
            self.assertIn(LEDGER_CONSTANTS["claude_dedup_caliber"], body, language)
            self.assertIn("message.id", body, language)
            self.assertIn(DUAL_CALIBER_NOTE[language], source, language)

    def test_appendix_limits_cover_seven_boundaries(self) -> None:
        for language, path in ARTICLES.items():
            source, _ = load(path)
            body = section_body(source, "appendix-limits", language)
            items = re.findall(r"<li>", body)
            self.assertGreaterEqual(len(items), 7, f"{language}: boundary count")
            for anchor in LIMITS_ANCHORS[language]:
                self.assertIn(anchor, body, f"{language}: {anchor}")

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
        # The two frames never blur into one.
        self.assertNotIn(ZH_TITLE, en_source)
        self.assertNotIn(EN_TITLE, zh_source)
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
            self.assertEqual("2026-09-06", article_data[0]["dateModified"], language)
            self.assertEqual("Intelligence", article_data[0]["articleSection"], language)

    def test_links_to_thesis_mechanism_and_ledger_pages(self) -> None:
        for language, path in ARTICLES.items():
            source, _ = load(path)
            self.assertIn("/agentic.html", source, language)
            self.assertIn("/engineering.html", source, language)
            self.assertIn("/blog/seven-billion-tokens/", source, language)

    def test_blog_index_lists_article(self) -> None:
        source = BLOG_INDEX.read_text(encoding="utf-8")
        self.assertIn(f"/blog/{SLUG}/", source)
        self.assertIn('data-cat="intelligence"', source)
        self.assertIn("One USB Cable", source)
        self.assertIn("Sep 5, 2026", source)

    def test_sitemap_lists_both_languages(self) -> None:
        source = SITEMAP.read_text(encoding="utf-8")
        self.assertIn(CANONICAL["en"], source)
        self.assertIn(CANONICAL["zh"], source)


if __name__ == "__main__":
    unittest.main()
