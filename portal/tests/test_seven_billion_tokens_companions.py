from __future__ import annotations

import json
import re
import unittest
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

PORTAL = Path(__file__).resolve().parents[1]
SERIES_ROOT = PORTAL / "blog" / "seven-billion-tokens"
BLOG_INDEX = PORTAL / "blog" / "index.html"
SITEMAP = PORTAL / "sitemap.xml"
COMPANION_CSS = PORTAL / "css" / "blog-article.css"

# ArticleParser / load / section_body are copied verbatim from
# tests/test_seven_billion_tokens_article.py — the two files share no module,
# to match this repo's "one article, one test file" convention.
# Keep changes in sync when either copy is edited.

COMPANIONS = {
    "ledger": {
        "sections": {"census", "window", "repos", "boundaries", "verify"},
        "slug": "ledger",
        "title_en": "The Ledger and Its Measurement Boundaries",
        "title_zh": "账本与测量边界",
    },
    "almanac": {
        "sections": {"eras", "shift", "benchmarks", "routing"},
        "slug": "almanac",
        "title_en": "The Model × Harness Almanac",
        "title_zh": "模型 × harness 年鉴",
    },
    "playbook": {
        "sections": {"disciplines", "checklists", "templates", "incidents"},
        "slug": "playbook",
        "title_en": "The Practitioner's Playbook",
        "title_zh": "实践手册",
    },
}


def companion_paths(slug: str):
    """产出 (language, path) 对，EN 在前、ZH 在后。"""
    root = SERIES_ROOT / COMPANIONS[slug]["slug"]
    return (("en", root / "index.html"), ("zh", root / "zh" / "index.html"))


CANONICAL = {
    slug: {
        "en": f"https://www.vlsc.net/blog/seven-billion-tokens/{spec['slug']}/",
        "zh": f"https://www.vlsc.net/blog/seven-billion-tokens/{spec['slug']}/zh/",
    }
    for slug, spec in COMPANIONS.items()
}

# R2：与主文测试同源同值（两文件各自复制一份，改动时两处同步）
GATE_OWNERS = ("mrrc_ft710", "mrrc_modern", "ft8", "FT-710", "Modern", "MRRC-FT8")
GATE_FORBIDDEN_NEIGHBOURS = ("SunMRRC", "SunsdrMobile", "EFHW", "MRRC Universal")
ARTICLES = {
    "en": SERIES_ROOT / "index.html",
    "zh": SERIES_ROOT / "zh" / "index.html",
}

REQUIRED_CLAIM_TYPES = {"fact", "inference", "thesis"}

# 分册 A 专有：完整账本表 + 测量边界（这些值不得出现在主文常量里）
LEDGER_TABLE = {
    "claude_line": "2,527,597,534",
    "claude_dedup": "818,520,401",
    "claude_api_ids": "6,600",
    "claude_window": "2026-08-08 .. 2026-09-08",
    "pi_tokens": "1,926,003,139",
    "kimi_tokens": "1,254,875,254",
    "mulerun_tokens": "537,961,611",
    "hermes_tokens": "485,213,348",
    "hermes_window": "2026-05-15 .. 2026-07-24",
    "agnes_tokens": "82,931,675",
    "agnes_window": "2026-07-13 .. 2026-07-26",
    "cursor_tokens": "27,079,705",
    "dsh_tokens": "10,931,069",
    "opencode_tokens": "4,190,890",
    "iflow_estimate": "247,000,000",
    "last_cleanup": "2026-09-07T13:13:57Z",
    "codex_crosscheck": "546,858,767",
    "observer_effect_delta": "51,427,037",
    "census_cutoff": "2026-09-12T02:40:59Z",
    "line_total": "7,404,583,808",
    "dedup_total": "5,695,506,675",
}
BOUNDARY_CONSTANTS = {
    "mrrc_w25_doubtful": "27.6",
    "commit_class_error": "±10%",
    "census_date": "2026-09-12",
}
NO_MERGE_PHRASE = {"en": "must not be merged", "zh": "不合并"}
DUAL_CALIBER_NOTE = {
    "en": "message.id",
    "zh": "message.id",
}
# 裸日期陷阱：分册 A 必须写出可复制的正确命令
BARE_DATE_FIX = {"en": "2026-09-05T00:00:00+08:00", "zh": "2026-09-05T00:00:00+08:00"}

# 分册 B 专有：模型时代与主力切换（附录 A5）
ALMANAC_TABLE = {
    "era_count": "six",
    "claude_top_model": "qwen3.8-max-0902",
    "claude_top_model_calls": "3,883",
    "claude_former_leader": "deepseek-v4-flash",
    "pi_new_model": "glm-5.3-flash",
    "pi_new_model_calls": "745",
    "codex_leader": "gpt-5.6-sol",
    "kimi_leader": "k3",
}
BENCHMARK_LAYERS = {
    "en": ("Independent measurements", "Vendor claims"),
    "zh": ("独立测评", "厂商口径"),
}
ROUTING_LABELS = ("big-pickle", "code-supernova-1-million", "kimi-for-coding")

# 分册 C：R9 —— 机制内容归 engineering.html，不得在本册重复
R9_BANNED = (
    "Harness × Loop",
    "Living SDD",
    "five engineering boundaries",
    "五种工程边界",
)
INCIDENT_ANCHORS = (
    "cat-no-dn",
    "AD-014",
    "DN;",
    "067f565",
    "2498ec2",
)


class ArticleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.section_ids: set[str] = set()
        self.refs: list[str] = []
        self.canonicals: list[str] = []
        self.hreflangs: set[str] = set()
        self.json_ld: list[dict[str, object]] = []
        self.div_depth = 0
        self._json_buffer: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        element_id = values.get("id")
        if element_id:
            self.ids.append(element_id)
        if tag == "div":
            self.div_depth += 1
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
        if tag == "script" and values.get("type") == "application/ld+json":
            self._json_buffer = []

    def handle_data(self, data: str) -> None:
        if self._json_buffer is not None:
            self._json_buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "div":
            self.div_depth -= 1
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


class CompanionPagesTests(unittest.TestCase):
    def test_all_companions_exist(self) -> None:
        for slug in COMPANIONS:
            for language, path in companion_paths(slug):
                self.assertTrue(path.exists(), f"{slug}/{language}")

    def test_sections_match_the_spec(self) -> None:
        for slug, spec in COMPANIONS.items():
            for language, path in companion_paths(slug):
                _source, parser = load(path)
                self.assertEqual(spec["sections"], parser.section_ids, f"{slug}/{language}")

    def test_claim_types_are_used(self) -> None:
        for slug in COMPANIONS:
            for language, path in companion_paths(slug):
                source, _ = load(path)
                found = set(re.findall(r'data-claim-type="([^"]+)"', source))
                self.assertTrue(
                    found <= REQUIRED_CLAIM_TYPES,
                    f"{slug}/{language}: unknown claim type {found - REQUIRED_CLAIM_TYPES}",
                )
                self.assertEqual(REQUIRED_CLAIM_TYPES, found, f"{slug}/{language}")

    def test_titles_are_bilingual(self) -> None:
        for slug, spec in COMPANIONS.items():
            en_source, _ = load(SERIES_ROOT / spec["slug"] / "index.html")
            zh_source, _ = load(SERIES_ROOT / spec["slug"] / "zh" / "index.html")
            self.assertIn(spec["title_en"], en_source, slug)
            self.assertIn(spec["title_zh"], zh_source, slug)
            self.assertIn('href="zh/"', en_source, slug)
            self.assertIn('href="../"', zh_source, slug)

    def test_ids_and_local_assets_are_valid(self) -> None:
        for slug in COMPANIONS:
            for language, path in companion_paths(slug):
                _, parser = load(path)
                duplicates = [i for i, c in Counter(parser.ids).items() if c > 1]
                self.assertEqual([], duplicates, f"{slug}/{language}")
                for ref in parser.refs:
                    parsed = urlparse(ref)
                    if parsed.scheme or ref.startswith(("/", "#", "data:", "mailto:")):
                        continue
                    self.assertTrue(
                        (path.parent / parsed.path).resolve().exists(),
                        f"{slug}/{language}: {ref}",
                    )

    def test_seo_language_links_and_json_ld_are_complete(self) -> None:
        for slug in COMPANIONS:
            for language, path in companion_paths(slug):
                _source, parser = load(path)
                self.assertEqual([CANONICAL[slug][language]], parser.canonicals,
                                 f"{slug}/{language}")
                self.assertEqual({"en", "zh-CN", "x-default"}, parser.hreflangs,
                                 f"{slug}/{language}")
                data = [i for i in parser.json_ld if i.get("@type") == "Article"]
                self.assertEqual(1, len(data), f"{slug}/{language}")
                for field in ("headline", "description", "author", "publisher",
                              "datePublished", "dateModified", "articleSection",
                              "mainEntityOfPage"):
                    self.assertIn(field, data[0], f"{slug}/{language}: {field}")
                self.assertEqual("2026-09-12", data[0]["dateModified"], f"{slug}/{language}")

    def test_gate_claims_only_near_owning_repos(self) -> None:
        pattern = re.compile(r"pre-edit gate|编辑前门禁|编辑前拦截|PreToolUse")
        for slug in COMPANIONS:
            for language, path in companion_paths(slug):
                source, _ = load(path)
                for match in pattern.finditer(source):
                    window = source[max(0, match.start() - 700): match.start() + 700]
                    self.assertTrue(
                        any(owner in window for owner in GATE_OWNERS),
                        f"{slug}/{language}: gate claim lacks an owning repo",
                    )
                    for bad in GATE_FORBIDDEN_NEIGHBOURS:
                        self.assertNotIn(bad, window, f"{slug}/{language}: R2 — {bad}")

    def test_terminology_bans_hold_series_wide(self) -> None:
        for slug in COMPANIONS:
            for language, path in companion_paths(slug):
                source, _ = load(path)
                self.assertNotIn("代理式工程", source, f"{slug}/{language}")
                self.assertNotIn("沉淀地", source, f"{slug}/{language}")

    # ---------------------------------------------------------- 分册 A 专有
    def test_ledger_owns_the_full_table(self) -> None:
        for language, path in companion_paths("ledger"):
            source, _ = load(path)
            missing = [f"{k}={v}" for k, v in LEDGER_TABLE.items() if v not in source]
            self.assertEqual([], missing, language)
            missing = [f"{k}={v}" for k, v in BOUNDARY_CONSTANTS.items() if v not in source]
            self.assertEqual([], missing, language)

    def test_ledger_presents_dual_caliber_side_by_side(self) -> None:
        for language, path in companion_paths("ledger"):
            source, _ = load(path)
            body = section_body(source, "census", language)
            self.assertIn(LEDGER_TABLE["claude_line"], body, language)
            self.assertIn(LEDGER_TABLE["claude_dedup"], body, language)
            self.assertIn(DUAL_CALIBER_NOTE[language], body, language)
            self.assertIn(NO_MERGE_PHRASE[language], source, language)

    def test_ledger_documents_the_window_mechanics(self) -> None:
        """保留期 + 观察者效应 + 裸日期陷阱，三条都要有可复现证据。"""
        for language, path in companion_paths("ledger"):
            source, _ = load(path)
            body = section_body(source, "window", language)
            self.assertIn(LEDGER_TABLE["last_cleanup"], body, language)
            self.assertIn(LEDGER_TABLE["observer_effect_delta"], body, language)
            self.assertIn(BARE_DATE_FIX[language], body, language)

    def test_ledger_documents_cross_checks(self) -> None:
        for language, path in companion_paths("ledger"):
            source, _ = load(path)
            body = section_body(source, "verify", language)
            self.assertIn(LEDGER_TABLE["codex_crosscheck"], body, language)
            self.assertIn(LEDGER_TABLE["agnes_tokens"], body, language)

    # ---------------------------------------------------------- 分册 B 专有
    def test_almanac_records_the_current_shift(self) -> None:
        """主力模型在一周内换人——新主力与调用次数必须逐字出现。"""
        for language, path in companion_paths("almanac"):
            source, _ = load(path)
            body = section_body(source, "shift", language)
            self.assertIn(ALMANAC_TABLE["claude_top_model"], body, language)
            self.assertIn(ALMANAC_TABLE["claude_top_model_calls"], body, language)
            self.assertIn(ALMANAC_TABLE["pi_new_model"], body, language)
            self.assertIn(ALMANAC_TABLE["pi_new_model_calls"], body, language)

    def test_almanac_layers_benchmarks(self) -> None:
        """独立测评与厂商口径必须分层，不得混排。"""
        for language, path in companion_paths("almanac"):
            source, _ = load(path)
            body = section_body(source, "benchmarks", language)
            for phrase in BENCHMARK_LAYERS[language]:
                self.assertIn(phrase, body, f"{language}: {phrase}")

    def test_almanac_names_the_routing_labels(self) -> None:
        for language, path in companion_paths("almanac"):
            source, _ = load(path)
            body = section_body(source, "routing", language)
            for label in ROUTING_LABELS:
                self.assertIn(label, body, f"{language}: {label}")

    # ---------------------------------------------------------- 分册 C 专有
    def test_playbook_does_not_duplicate_mechanism(self) -> None:
        """R9：机制归 engineering.html，分册 C 只装案例私有内容。"""
        for language, path in companion_paths("playbook"):
            source, _ = load(path)
            for phrase in R9_BANNED:
                self.assertNotIn(phrase, source, f"{language}: R9 — {phrase}")
            self.assertIn("/engineering.html", source, language)

    def test_playbook_incidents_trace_to_the_case(self) -> None:
        """每条事故必须带可复现痕迹，不得是空泛建议。"""
        for language, path in companion_paths("playbook"):
            source, _ = load(path)
            body = section_body(source, "incidents", language)
            for token in INCIDENT_ANCHORS:
                self.assertIn(token, body, f"{language}: {token}")


if __name__ == "__main__":
    unittest.main()
