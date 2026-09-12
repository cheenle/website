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
CANONICAL = {
    "en": f"https://www.vlsc.net/blog/{SLUG}/",
    "zh": f"https://www.vlsc.net/blog/{SLUG}/zh/",
}

# 2026-09-12 restructure: the main article keeps only the causal chain.
# 15 sections in 6 volumes + one unvolumed prologue. The token ledger, the
# model almanac and the practitioner playbook moved to three companion pages
# (/ledger/, /almanac/, /playbook/) — see tests/test_seven_billion_tokens_companions.py.
REQUIRED_SECTIONS = {
    # 开篇（不属卷）
    "ledger-shrank",
    # 卷 I · 意图
    "intents",
    "control-group",
    # 卷 II · 过程
    "intervention",
    "unit-cost",
    "rework",
    "cadence",
    # 卷 III · 方法
    "method-timeline",
    "incident-chains",
    "evidence-ledgers",
    # 卷 IV · 模型
    "model-shift",
    # 卷 V · 归因
    "attribution",
    "advice",
    "closing",
    # 卷 VI · 四维度
    "four-dimensions",
}

# Grading discipline: measured/test-run results are fact, attribution and
# trend judgments are inference, methodology claims are thesis.
REQUIRED_CLAIM_TYPES = {"fact", "inference", "thesis"}

VOLUMES = (
    ("intent", ("intents", "control-group")),
    ("process", ("intervention", "unit-cost", "rework", "cadence")),
    ("method", ("method-timeline", "incident-chains", "evidence-ledgers")),
    ("models", ("model-shift",)),
    ("verdict", ("attribution", "advice", "closing")),
    ("dimensions", ("four-dimensions",)),
)
UNVOLUMED_SECTIONS = ("ledger-shrank",)

VOLUME_TITLES = {
    "en": {
        "intent": "Intent never starts with",
        "process": "From round-trips to right-first-time",
        "method": "What the harness and the SDD did at each stage",
        "models": "The model is not the long-term variable",
        "verdict": "Where the efficiency actually came from",
        "dimensions": "Separate judgment from execution",
    },
    "zh": {
        "intent": "意图从不以",
        "process": "从「来来回回」到「一次做对」",
        "method": "harness 与 SDD 在各阶段的作用",
        "models": "模型不是长期变量",
        "verdict": "效率究竟从哪里来",
        "dimensions": "把判断从执行中分离",
    },
}

EN_TITLE = "Seven Billion Tokens, Dissected: The Ledger That Shrank"
ZH_TITLE = "七十亿 token 的全程拆解：一本会倒退的账"

# Every one of these strings must appear verbatim in BOTH languages.
# Only values that genuinely belong to the MAIN article live here — the full
# ledger table, the measurement boundaries and the model almanac now belong to
# the companion pages and are asserted there.
LEDGER_CONSTANTS = {
    # 三层误差：虚高 / 虚低 / 漂移
    "published_line_census": "7,007,437,567",
    "recomputed_line_census": "7,404,583,808",
    "recomputed_dedup_census": "5,695,506,675",
    "delta_vs_published": "397,146,241",
    "claude_dedup_census": "818,520,401",
    "hermes_tokens": "485,213,348",
    "codex_tokens": "547,796,667",
    "last_cleanup": "2026-09-07T13:13:57Z",
    "observer_effect_delta": "51,427,037",
    # 对照期（不变）
    "iflow_turns": "37,202",
    "iflow_sessions": "185",
    "glm5_peak_week_turns": "10,420",
    # 过程（历史 + 上周）
    "intervention_drop": "17.1 → 0.3",
    "ft8_peak_unit_cost": "75.5",
    "ft8_maintenance_unit_cost": "0.9",
    "modern_week_human_per_commit": "0.73",
    "modern_week_megatokens_per_commit": "5.95",
    "mrrc_week_human_per_commit": "6.00",
    "mrrc_week_megatokens_per_commit": "47.07",
    "modern_week_commits": "41",
    "modern_week_fix_share": "41%",
    "modern_week_fix_count": "17",
    "red_green_median_minutes": "19",
    # 方法
    "constraints_total": "52",
    "constraints_split": "ft710 17 / modern 21 / ft8 14",
    "incident_ft710_days": "13",
    "incident_backup_days": "7",
    # 产品（2026-09-12 实跑，与 /agentic.html#evidence 同值）
    "tests_ft710": "439",
    "tests_modern": "724",
    "tests_ft8": "935",
    "modern_version_early": "v1.14.0",
    "modern_version_late": "v1.14.3",
    # 模型
    "claude_top_model": "qwen3.8-max-0902",
    "claude_top_model_calls": "3,883",
    "pi_new_model": "glm-5.3-flash",
    "pi_new_model_calls": "745",
    # 缓存经济
    "cache_read_share": "93.7%",
    # 日期
    "census_date": "2026-09-12",
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
        "由智能体建造",
        "AI 打造",
        "智能体建造了",
        "沉淀地",
    ),
}

# R2: a pre-edit-gate claim may only sit near the three repos that own one.
GATE_OWNERS = ("mrrc_ft710", "mrrc_modern", "ft8", "FT-710", "Modern", "MRRC-FT8")
GATE_FORBIDDEN_NEIGHBOURS = ("SunMRRC", "SunsdrMobile", "EFHW", "MRRC Universal")

# R7: the estimate and the recorded ledger must never be merged.
NO_MERGE_PHRASE = {"en": "must not be merged", "zh": "不合并"}
# R8: the ledger moves in both directions — that has to be stated, not hidden.
BOTH_DIRECTIONS = {
    "en": ("overstated", "understated"),
    "zh": ("虚高", "虚低"),
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

    def test_no_unlabelled_estimate(self) -> None:
        """R7: any approximate FIGURE must sit next to an estimate label.

        只约束三位以上数字（量级数字），不约束 `~30 min read` 这类时长表述。
        """
        labels = {
            "en": ("estimate", "estimated", "not recorded", "unrecorded", "lower bound"),
            "zh": ("估算", "未记录", "工具记 0", "下界"),
        }
        for language, path in ARTICLES.items():
            source, _ = load(path)
            for match in re.finditer(r"[≈~]\s?\d[\d,]{2,}", source):
                window = source[max(0, match.start() - 900): match.start() + 900].lower()
                self.assertTrue(
                    any(label in window for label in labels[language]),
                    f"{language}: unlabelled estimate {match.group(0)!r} at {match.start()}",
                )

    def test_recorded_and_estimated_ledgers_are_not_merged(self) -> None:
        for language, path in ARTICLES.items():
            source, _ = load(path)
            self.assertIn(NO_MERGE_PHRASE[language], source, language)

    def test_both_error_directions_are_stated(self) -> None:
        """R8: 已发表值是虚高且虚低——两个方向都必须写出来，不得只说一边。"""
        for language, path in ARTICLES.items():
            source, _ = load(path)
            for word in BOTH_DIRECTIONS[language]:
                self.assertIn(word, source, f"{language}: {word}")

    def test_gate_claims_only_near_owning_repos(self) -> None:
        pattern = re.compile(r"pre-edit gate|编辑前门禁|编辑前拦截|PreToolUse")
        for language, path in ARTICLES.items():
            source, _ = load(path)
            for match in pattern.finditer(source):
                window = source[max(0, match.start() - 700): match.start() + 700]
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

    def test_distillation_layer_is_present(self) -> None:
        for language, path in ARTICLES.items():
            source, _parser = load(path)
            # TL;DR card: five tagged findings + a reading path into the article
            self.assertIn('class="ba-tldr"', source, language)
            self.assertEqual(5, source.count('class="ba-tldr-tag"'), language)
            self.assertIn('href="#four-dimensions"', source, language)
            # one takeaway per narrative volume; the distillation volume has none
            self.assertEqual(5, source.count('class="volume-takeaway"'), language)

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

    def test_main_article_owns_no_ledger_tables(self) -> None:
        """R5: 账本表唯一主人是分册 A；主文只许引结论句。"""
        for language, path in ARTICLES.items():
            source, _ = load(path)
            for token in (
                LEDGER_CONSTANTS["published_line_census"],
                LEDGER_CONSTANTS["recomputed_line_census"],
                LEDGER_CONSTANTS["recomputed_dedup_census"],
            ):
                self.assertIn(token, source, f"{language}: {token}")
            self.assertLess(
                source.count("<table"), 8,
                f"{language}: 主文表格过多，账本/年鉴应外链",
            )

    def test_series_navigation_is_present(self) -> None:
        """主文必须挂上三册分册，否则读者找不到被移出的内容。"""
        for language, path in ARTICLES.items():
            source, _ = load(path)
            for slug in ("ledger/", "almanac/", "playbook/"):
                self.assertIn(slug, source, f"{language}: {slug}")

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
            self.assertEqual("2026-09-12", article_data[0]["dateModified"], language)
            self.assertEqual("Intelligence", article_data[0]["articleSection"], language)

    def test_links_to_thesis_and_mechanism_pages(self) -> None:
        for language, path in ARTICLES.items():
            source, _ = load(path)
            self.assertIn("/agentic.html", source, language)
            self.assertIn("/engineering.html", source, language)


if __name__ == "__main__":
    unittest.main()
