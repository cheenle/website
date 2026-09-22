from __future__ import annotations

import html
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

PORTAL = Path(__file__).resolve().parents[1]
BLOG = PORTAL / "blog"

TIER_ESSAY, TIER_FIELD, TIER_THESIS, TIER_ARCHIVE, TIER_STUB = (
    "essay", "field", "thesis", "archive", "stub")

ARTICLES: dict[str, tuple[str, tuple[str, ...]]] = {
    "coda": (TIER_ESSAY, ("en", "zh")),
    "faculties": (TIER_ESSAY, ("en", "zh")),
    "ming-li-dao-tian": (TIER_ESSAY, ("en", "zh")),
    "only-imagination": (TIER_ESSAY, ("en", "zh")),
    "connections-recursive-intelligence": (TIER_ESSAY, ("en", "zh")),
    "solo-loop": (TIER_FIELD, ("en", "zh")),
    "support-loop": (TIER_FIELD, ("en", "zh")),
    "three-axes": (TIER_FIELD, ("en", "zh")),
    "seven-billion-tokens": (TIER_FIELD, ("en", "zh")),
    "seven-billion-tokens/almanac": (TIER_FIELD, ("en", "zh")),
    "seven-billion-tokens/ledger": (TIER_FIELD, ("en", "zh")),
    "seven-billion-tokens/playbook": (TIER_FIELD, ("en", "zh")),
    "ft710-usb-remote-control": (TIER_FIELD, ("en", "zh")),
    "efhw-esp32s3-auto-tuner": (TIER_FIELD, ("en", "zh")),
    "opus-vs-pcm-remote-audio": (TIER_FIELD, ("en", "zh")),
    "psk-reporter-dxcc-hunting": (TIER_FIELD, ("en", "zh")),
    "juekun": (TIER_ARCHIVE, ("root",)),
    "from-intent-to-delivery": (TIER_STUB, ("en", "zh")),
}

TLDR_MIN = {TIER_ESSAY: 4, TIER_FIELD: 3}
TLDR_EXEMPT = {"seven-billion-tokens/almanac", "seven-billion-tokens/ledger", "seven-billion-tokens/playbook"}
CLASSIC_MIN = {TIER_ESSAY: 3, TIER_FIELD: 0}
MAX_AVG_SENTENCE = {TIER_ESSAY: 40, TIER_FIELD: 55}
MAX_DASH_PERMILLE = 6.0
CLAIM_TYPES = {"fact", "inference", "thesis", "analogy"}

# 语体阈值挂起项（今天是 5 篇破折号超标）
PENDING_DASH: dict[str, str] = {
}

# 结构/镜像/引文/标点/元数据挂起项（按文章 × 语言）
PENDING_ARTICLES: dict[tuple[str, str], str] = {
    ("efhw-esp32s3-auto-tuner", "en"): "batch4", ("efhw-esp32s3-auto-tuner", "zh"): "batch4",
    ("opus-vs-pcm-remote-audio", "en"): "batch4", ("opus-vs-pcm-remote-audio", "zh"): "batch4",
    ("psk-reporter-dxcc-hunting", "en"): "batch4", ("psk-reporter-dxcc-hunting", "zh"): "batch4",
    ("juekun", "root"): "batch9",
}

BANNED_PHRASES = ("代理式工程", "三款产品", "由 Agent 写成", "written by AI", "被用来",
                  "值得注意的是", "在当今时代", "深入探讨", "综上所述")


def page_path(slug: str, lang: str) -> Path:
    if lang == "root":
        return BLOG / slug / "index.html"
    return BLOG / slug / ("index.html" if lang == "en" else f"{lang}/index.html")


def canonical(slug: str, lang: str) -> str:
    if lang == "root":
        return f"https://www.vlsc.net/blog/{slug}/"
    return f"https://www.vlsc.net/blog/{slug}/" + ("" if lang == "en" else "zh/")


class ArticleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.section_ids: list[str] = []
        self.ids: set[str] = set()
        self.anchor_targets: list[str] = []
        self.tldr_types: list[str] = []
        self.quotes: list[dict[str, str]] = []
        self.quote_children: dict[str, set[str]] = {}
        self.classes: set[str] = set()
        self._current_quote: str | None = None

    def handle_starttag(self, tag, attrs):
        a = {k: (v or "") for k, v in attrs}
        cls = a.get("class", "")
        self.classes.update(cls.split())
        if a.get("id"):
            self.ids.add(a["id"])
            if tag == "section":
                self.section_ids.append(a["id"])
        if tag == "a" and a.get("href", "").startswith("#"):
            self.anchor_targets.append(a["href"][1:])
        if "ba-tldr-tag" in cls.split():
            self.tldr_types.append(a.get("data-claim-type", ""))
        if "ba-quote" in cls.split():
            self.quotes.append({"id": a.get("data-quote-id", ""),
                                "kind": a.get("data-quote-kind", ""),
                                "cite": a.get("data-quote-cite", "")})
            self._current_quote = a.get("data-quote-id", "")
            self.quote_children.setdefault(self._current_quote, set())
        if self._current_quote and cls:
            self.quote_children[self._current_quote].update(cls.split())

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag == "blockquote":
            self._current_quote = None

    @property
    def quote_ids(self) -> list[str]:
        return [q["id"] for q in self.quotes]


def load(path: Path):
    source = path.read_text(encoding="utf-8")
    parser = ArticleParser()
    parser.feed(source)
    return source, parser


def body_text(source: str) -> str:
    """规范 §3.2：<main class="ba-main"> 可见文本，标签替换为空格后再 unescape。

    不能用 HTMLParser 拼接 handle_data —— 那样会把相邻表格单元格
    (<td>…—</td><td>—…</td>) 里的两个「—」误拼成「——」。
    """
    stripped = re.sub(r"<script.*?</script>", "", source, flags=re.S)
    stripped = re.sub(r"<style.*?</style>", "", stripped, flags=re.S)
    body = re.search(r'<main class="ba-main">.*?</main>', stripped, re.S)
    if body is None:
        return ""
    return html.unescape(re.sub(r"<[^>]+>", " ", body.group(0)))


def metrics(source: str) -> dict[str, float]:
    text = body_text(source)
    han = len(re.findall(r"[\u4e00-\u9fff]", text))
    sentences = len(re.findall(r"[。！？]", text))
    dashes = text.count("——")
    return {"han": han, "sentences": sentences,
            "avg_sentence": han / max(sentences, 1),
            "dash_permille": dashes / max(han, 1) * 1000}


class LanguageSystemTests(unittest.TestCase):
    maxDiff = None

    def test_pending_entries_are_gone(self) -> None:
        self.assertEqual({}, PENDING_DASH, "仍有破折号超标挂起项")
        self.assertEqual({}, PENDING_ARTICLES, "仍有文章级挂起项，未达到验收状态")

    def test_articles_exist_and_parse(self) -> None:
        for slug, (tier, langs) in ARTICLES.items():
            for lang in langs:
                self.assertTrue(
                    (slug, lang) in PENDING_ARTICLES or page_path(slug, lang).exists(),
                    f"{slug}/{lang} 缺失",
                )

    def test_structure_and_bilingual_mirror(self) -> None:
        for slug, (tier, langs) in ARTICLES.items():
            if tier == TIER_STUB:
                continue
            parsed = {}
            for lang in langs:
                p = page_path(slug, lang)
                if p.exists():
                    parsed[lang] = load(p)[1]
            for lang, parser in parsed.items():
                if (slug, lang) in PENDING_ARTICLES:
                    continue
                where = f"{slug}/{lang}"
                self.assertIn("ba-article", parser.classes, where)
                self.assertTrue(parser.section_ids, f"{where}: 无 section")
                for target in parser.anchor_targets:
                    self.assertIn(target, parser.ids, f"{where}: 死锚 #{target}")
            if len(parsed) == 2 and not any(
                (slug, lang) in PENDING_ARTICLES for lang in ("en", "zh")
            ):
                en, zh = parsed["en"], parsed["zh"]
                self.assertEqual(set(en.section_ids), set(zh.section_ids), f"{slug}: section 不对等")
                self.assertEqual(len(en.tldr_types), len(zh.tldr_types), f"{slug}: TL;DR 不对等")
                self.assertEqual(sorted(en.quote_ids), sorted(zh.quote_ids), f"{slug}: 引文不对等")

    def test_tldr_requirements(self) -> None:
        for slug, (tier, langs) in ARTICLES.items():
            if tier in (TIER_STUB, TIER_ARCHIVE) or slug in TLDR_EXEMPT:
                continue
            for lang in langs:
                p = page_path(slug, lang)
                if not p.exists():
                    continue
                if (slug, lang) in PENDING_ARTICLES:
                    continue
                parser = load(p)[1]
                self.assertGreaterEqual(len(parser.tldr_types), TLDR_MIN[tier], f"{slug}/{lang}: TL;DR 不足")
                self.assertTrue(set(parser.tldr_types) <= CLAIM_TYPES,
                                f"{slug}/{lang}: 非法 claim {set(parser.tldr_types) - CLAIM_TYPES}")

    def test_quote_blocks_are_well_formed(self) -> None:
        for slug, (tier, langs) in ARTICLES.items():
            for lang in langs:
                p = page_path(slug, lang)
                if not p.exists():
                    continue
                if (slug, lang) in PENDING_ARTICLES:
                    continue
                parser = load(p)[1]
                ids = [q["id"] for q in parser.quotes]
                self.assertEqual(len(ids), len(set(ids)), f"{slug}/{lang}: id 重复")
                for q in parser.quotes:
                    where = f"{slug}/{lang}/{q['id']}"
                    self.assertTrue(q["id"], f"{where}: 缺 id")
                    self.assertIn(q["kind"], {"classic", "engineering", "project"}, where)
                    self.assertTrue(q["cite"], f"{where}: 缺 cite")
                    children = parser.quote_children[q["id"]]
                    self.assertIn("ba-quote-orig", children, f"{where}: 缺原文")
                    self.assertIn("ba-quote-trans", children, f"{where}: 缺译本")
                    self.assertIn("ba-quote-cite", children, f"{where}: 出处未渲染")

    def test_tier_citation_rules(self) -> None:
        for slug, (tier, langs) in ARTICLES.items():
            if tier not in (TIER_ESSAY, TIER_FIELD):
                continue
            for lang in langs:
                p = page_path(slug, lang)
                if not p.exists() or (slug, lang) in PENDING_ARTICLES:
                    continue
                parser = load(p)[1]
                classics = [q for q in parser.quotes if q["kind"] == "classic"]
                self.assertGreaterEqual(len(classics), CLASSIC_MIN[tier], f"{slug}/{lang}: 经典不足")
                if tier == TIER_FIELD:
                    self.assertEqual([], classics, f"{slug}/{lang}: 实操文不得引经典")

    def test_zh_style_thresholds(self) -> None:
        for slug, (tier, langs) in ARTICLES.items():
            if tier not in (TIER_ESSAY, TIER_FIELD) or "zh" not in langs:
                continue
            p = page_path(slug, "zh")
            if not p.exists():
                continue
            m = metrics(p.read_text(encoding="utf-8"))
            if slug not in PENDING_DASH:
                self.assertLessEqual(m["dash_permille"], MAX_DASH_PERMILLE,
                                     f"{slug}/zh: {m['dash_permille']:.1f}‰")
            self.assertLessEqual(m["avg_sentence"], MAX_AVG_SENTENCE[tier],
                                 f"{slug}/zh: 均句长 {m['avg_sentence']:.1f}")

    def test_quote_marks_are_unified_in_zh(self) -> None:
        for slug, (tier, langs) in ARTICLES.items():
            if "zh" not in langs or tier == TIER_STUB:
                continue
            p = page_path(slug, "zh")
            if not p.exists():
                continue
            if (slug, "zh") in PENDING_ARTICLES:
                continue
            source = p.read_text(encoding="utf-8")
            body = re.search(r'<main class="ba-main">.*?</main>', source, re.S)
            if body is None:
                continue
            text = re.sub(r"<code>.*?</code>", "", body.group(0), flags=re.S)
            text = re.sub(r"<pre>.*?</pre>", "", text, flags=re.S)
            text = re.sub(r'<section id="references".*?</section>', "", text, flags=re.S)
            stripped = re.sub(r"<[^>]+>", "", text)
            self.assertNotIn('"', stripped, f"{slug}/zh: 半角直引号")
            self.assertNotIn("\u201c", stripped, f"{slug}/zh: 弯引号")
            self.assertNotIn("\u201d", stripped, f"{slug}/zh: 弯引号")

    def test_banned_phrases_and_terminology(self) -> None:
        for slug, (tier, langs) in ARTICLES.items():
            for lang in langs:
                p = page_path(slug, lang)
                if not p.exists():
                    continue
                source = p.read_text(encoding="utf-8")
                for phrase in BANNED_PHRASES:
                    self.assertNotIn(phrase, source, f"{slug}/{lang}: 禁用词「{phrase}」")
                if lang in ("zh", "root") and "agentic engineering" in source.lower():
                    self.assertIn("智能体工程", source, f"{slug}/{lang}: 术语方向")
                if lang == "en" and "智能体工程" in source:
                    self.assertIn("agentic engineering", source.lower(), f"{slug}/en: 术语方向")

    def test_legacy_layout_is_gone(self) -> None:
        for slug, (tier, langs) in ARTICLES.items():
            for lang in langs:
                p = page_path(slug, lang)
                if not p.exists() or (slug, lang) in PENDING_ARTICLES:
                    continue
                parser = load(p)[1]
                for legacy in ("ba-prose", "ba-tags"):
                    self.assertNotIn(legacy, parser.classes, f"{slug}/{lang}: 旧版式 {legacy}")

    def test_blog_indexes_mirror_each_other(self) -> None:
        en = (BLOG / "index.html").read_text(encoding="utf-8")
        zh = (BLOG / "zh/index.html").read_text(encoding="utf-8")
        archive = {s for s, (t, _) in ARTICLES.items() if t == TIER_ARCHIVE}
        no_zh_yet = {
            slug
            for slug, (_, langs) in ARTICLES.items()
            if "zh" in langs and not page_path(slug, "zh").exists()
        }
        en_slugs = (set(re.findall(r'href="/blog/([a-z0-9-]+)/"', en)) - archive - no_zh_yet) - {"zh"}
        zh_slugs = set(re.findall(r'/blog/([a-z0-9-]+)/zh/"', zh))
        self.assertEqual(en_slugs, zh_slugs, "中英索引卡片集合不一致")
        for slug in archive:
            self.assertIn(f'href="/blog/{slug}/"', en, f"英文索引缺 {slug}")
            self.assertIn(f'href="/blog/{slug}/"', zh, f"中文索引缺 {slug}")

    def test_hreflang_and_sitemap(self) -> None:
        sitemap = (PORTAL / "sitemap.xml").read_text(encoding="utf-8")
        for slug, (tier, langs) in ARTICLES.items():
            if tier == TIER_STUB:
                continue
            for lang in langs:
                p = page_path(slug, lang)
                if not p.exists() or (slug, lang) in PENDING_ARTICLES:
                    continue
                source = p.read_text(encoding="utf-8")
                self.assertIn('hreflang="zh-CN"', source, f"{slug}/{lang}: 缺 zh-CN")
                self.assertIn('hreflang="en"', source, f"{slug}/{lang}: 缺 en")
                self.assertIn("x-default", source, f"{slug}/{lang}: 缺 x-default")
                self.assertIn(canonical(slug, lang), sitemap, f"sitemap 缺 {canonical(slug, lang)}")


if __name__ == "__main__":
    unittest.main()
