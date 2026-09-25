import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
import llm_proxy  # noqa: E402

SAMPLE = {
    "question": "秋季换工作是否合适",
    "category": "事业",
    "ben": {"fullName": "水火既济",
            "tuan": "彖曰：既济，亨，小者亨也。",
            "xiang": "象曰：水在火上，既济；君子以思患而豫防之。"},
    "zhi": {"fullName": "山风蛊"},
    "hu": "火水未济", "cuo": "火水未济", "zong": "火水未济",
    "moving": [
        {"title": "初九", "facts": "初位阳爻，当位，与四爻有应", "xiang": "象曰：曳其轮，义无咎也。"},
        {"title": "六二", "facts": "二位阴爻，当位，居中，与五爻有应，阴乘阳（逆），阴承阳（顺）",
         "xiang": "象曰：七日得，以中道也。"},
    ],
    "rule": "四爻动，以之卦两静爻辞断，以下爻为主",
    "duanci": [
        {"source": "之卦山风蛊·九三（主）", "ci": "干父之蛊，小有悔，无大咎。",
         "baihua": "以刚治父辈遗留之积弊，虽因操之过急而小有悔恨，终不至于有大咎害。"}
    ],
}


class BuildPayloadTest(unittest.TestCase):
    def test_facts_and_structure_reach_the_model(self):
        os.environ["LLM_MODEL"] = "qwen3.8-max-0902"
        p = llm_proxy.build_payload(SAMPLE)
        content = p["messages"][0]["content"]
        self.assertEqual(p["model"], "qwen3.8-max-0902")
        self.assertEqual(p["thinking"], {"type": "enabled", "budget_tokens": 1024})
        for frag in ["水火既济", "山风蛊", "互卦：火水未济", "动爻爻位事实：",
                     "阴乘阳（逆）", "彖曰：既济", "干父之蛊", "事业", "四爻动"]:
            self.assertIn(frag, content)

    def test_quiet_gua_and_empty_question(self):
        req = {"category": "综合", "ben": {"fullName": "乾为天"}, "zhi": None,
               "hu": "乾为天", "cuo": "坤为地", "zong": "乾为天",
               "moving": [], "rule": "六爻安静，以本卦卦辞断", "duanci": []}
        content = llm_proxy.build_payload(req)["messages"][0]["content"]
        self.assertIn("无（六爻安静）", content)
        self.assertIn("心中默念", content)
        self.assertIn("动爻：无", content)


class PromptContractTest(unittest.TestCase):
    """红线守护：结构、免责与引文纪律写进提示词，改提示词时不得丢失。"""

    def test_structure_and_disclaimer(self):
        for frag in ["【卦象大势】", "【爻位细析】", "【事理推断】", "【行动建议】",
                     "忌：", "占断仅供参考，事在人为", "不得编造", "首句须点明本卦全称", "五百字"]:
            self.assertIn(frag, llm_proxy.SYSTEM_PROMPT)

    def test_version_format(self):
        self.assertRegex(llm_proxy.PROMPT_VERSION, r"^\d{4}-\d{2}-\d{2}\.v\d+$")


class ExtractTextTest(unittest.TestCase):
    def test_joins_text_and_skips_thinking(self):
        resp = {"content": [
            {"type": "thinking", "thinking": "…"},
            {"type": "text", "text": "【卦象大势】…"},
            {"type": "text", "text": "【行动建议】…"},
        ]}
        self.assertEqual(llm_proxy.extract_text(resp), "【卦象大势】…\n【行动建议】…")

    def test_empty(self):
        self.assertEqual(llm_proxy.extract_text({"content": []}), "")


if __name__ == "__main__":
    unittest.main()


class CategoryPromptTest(unittest.TestCase):
    def test_reading_prompt_carries_category_focus(self):
        s = llm_proxy.system_prompt("健康", "reading")
        self.assertIn("【卦象大势】", s)
        self.assertIn("以医嘱为准", s)

    def test_chat_prompt_rules_and_focus(self):
        s = llm_proxy.system_prompt("财运", "chat")
        self.assertIn("一百八十字", s)
        self.assertIn("盈亏风险自担", s)
        self.assertIn("正财与投机", s)
        self.assertNotIn("【卦象大势】", s)

    def test_unknown_category_falls_back(self):
        self.assertIn("主视角", llm_proxy.system_prompt("???"))


class ChatPayloadTest(unittest.TestCase):
    def test_context_first_then_capped_history(self):
        hist = [{"role": "user", "content": "q%d" % i} for i in range(12)]
        hist.append({"role": "assistant", "content": "last"})
        hist.append({"role": "system", "content": "should be dropped"})
        p = llm_proxy.build_chat_payload({
            "category": "感情",
            "context": {"ben": "水火既济", "zhi": "山风蛊", "hu": "火水未济",
                        "moving": ["初九：初位阳爻，当位"], "rule": "四爻动…", "reading": "【卦象大势】…"},
            "messages": hist,
        })
        msgs = p["messages"]
        self.assertIn("水火既济", msgs[0]["content"])
        self.assertIn("此前 AI 解读", msgs[0]["content"])
        self.assertEqual(msgs[1]["content"], "q4")   # 只保留最近 10 条（再过滤非法 role）
        self.assertEqual(msgs[-1]["content"], "last")
        self.assertNotIn("system", [m["role"] for m in msgs])
        self.assertIn("沟通、界限与等待", p["system"])

    def test_empty_messages_still_valid(self):
        p = llm_proxy.build_chat_payload({"context": {"ben": "乾为天"}, "messages": []})
        self.assertEqual(len(p["messages"]), 1)


class ValidateFeedbackTest(unittest.TestCase):
    def test_rating_kind(self):
        self.assertEqual(llm_proxy.validate_feedback({"rating": 1}), "rating")
        self.assertEqual(llm_proxy.validate_feedback({"rating": -1, "id": "x"}), "rating")
        self.assertIsNone(llm_proxy.validate_feedback({"rating": 0}))

    def test_outcome_kind(self):
        ok = {"kind": "outcome", "rating": 0, "record": {"lines": [7, 7, 7, 7, 7, 7]}, "outcome": "成了"}
        self.assertEqual(llm_proxy.validate_feedback(ok), "outcome")
        bad = dict(ok, rating=2)
        self.assertIsNone(llm_proxy.validate_feedback(bad))
        self.assertIsNone(llm_proxy.validate_feedback({"kind": "outcome", "rating": 1}))
        self.assertIsNone(llm_proxy.validate_feedback({"kind": "nope", "rating": 1}))


class MeihuaPromptTest(unittest.TestCase):
    def test_meihua_system_and_payload(self):
        req = {
            "method": "meihua", "category": "财运", "question": "合伙开店",
            "meihua": {"methodNote": "数字起卦：5、3", "ben": "火风鼎", "zhi": "火水未济", "hu": "泽天夬",
                       "ti": "巽（木）", "yong": "离（火）", "relation": "体生用", "relationNote": "耗费泄气之象",
                       "movingWei": "九二"},
            "ben": {"fullName": "火风鼎", "tuan": "彖曰：鼎，象也。", "xiang": "象曰：木上有火，鼎。"},
            "duanci": [{"source": "本卦火风鼎·卦辞", "ci": "鼎：元吉，亨。", "baihua": "大吉而亨。"}],
        }
        p = llm_proxy.build_payload(req)
        self.assertIn("梅花易数", p["system"])
        self.assertIn("【体用大势】", p["system"])
        content = p["messages"][0]["content"]
        for frag in ["体生用", "耗费泄气之象", "火风鼎", "数字起卦：5、3", "鼎：元吉，亨。"]:
            self.assertIn(frag, content)

    def test_reading_mode_unchanged(self):
        p = llm_proxy.build_payload(SAMPLE)
        self.assertIn("【卦象大势】", p["system"])
        self.assertNotIn("梅花", p["system"])


class MemoryInjectionTest(unittest.TestCase):
    def test_memory_lines_and_discipline(self):
        req = dict(SAMPLE)
        req["memory"] = {"count": 3,
                         "recent": ["2026/9/1 问「换工作」(事业) 得 水火既济之山风蛊，回访：非常准"],
                         "stats": ["事业类回访 1 准 / 0 部分 / 0 不准"]}
        p = llm_proxy.build_payload(req)
        content = p["messages"][0]["content"]
        self.assertIn("用户长期记忆（本机占例档案，共 3 条）", content)
        self.assertIn("回访：非常准", content)
        self.assertIn("回访统计：事业类回访 1 准", content)
        self.assertIn("长期记忆纪律", p["system"])

    def test_no_memory_no_section(self):
        p = llm_proxy.build_payload(SAMPLE)
        self.assertNotIn("用户长期记忆", p["messages"][0]["content"])
        self.assertIn("长期记忆纪律", p["system"])

    def test_chat_memory_from_context(self):
        p = llm_proxy.build_chat_payload({
            "category": "综合",
            "context": {"ben": "乾为天", "memory": {"count": 1, "recent": ["x"], "stats": []}},
            "messages": [],
        })
        self.assertIn("用户长期记忆", p["messages"][0]["content"])


class HealthNeijingTest(unittest.TestCase):
    def test_health_reading_and_chat_carry_neijing_pool(self):
        for mode in ("reading", "chat"):
            s = llm_proxy.system_prompt("健康", mode)
            self.assertIn("素问·四气调神大论", s)
            self.assertIn("春夏养阳，秋冬养阴", s)
            self.assertIn("以医嘱为准", s)
            self.assertIn("不得改字", s)

    def test_other_category_has_no_neijing(self):
        self.assertNotIn("黄帝内经", llm_proxy.system_prompt("事业", "chat"))

    def test_pool_integrity(self):
        self.assertEqual(len(llm_proxy.NEIJING_PASSAGES), 13)
        for src, txt in llm_proxy.NEIJING_PASSAGES:
            self.assertTrue(src.startswith(("素问", "灵枢")))
            self.assertTrue(txt.strip())


class HealthCrossRefTest(unittest.TestCase):
    REQ = {"category": "健康",
           "gua": {"upper": "离", "lower": "坤", "movingIdx": [1, 4]}}

    def test_context_lines_cover_gua_yao_season(self):
        import datetime
        lines = "\n".join(llm_proxy.health_context_lines(self.REQ, now=datetime.datetime(2026, 9, 26)))
        self.assertIn("秋", lines)
        self.assertIn("肺（大肠）", lines)
        self.assertIn("《说卦传》配目", lines)      # 离为目
        self.assertIn("《说卦传》配腹", lines)      # 坤为腹
        self.assertIn("腓（小腿）", lines)          # 二爻
        self.assertIn("喉面", lines)                # 五爻
        self.assertIn("生克推演", lines)            # 离火克秋金

    def test_winter_season(self):
        import datetime
        lines = "\n".join(llm_proxy.health_context_lines(self.REQ, now=datetime.datetime(2026, 12, 5)))
        self.assertIn("冬", lines)
        self.assertIn("肾（膀胱）", lines)

    def test_health_system_has_five_sections(self):
        s = llm_proxy.system_prompt("健康", "chat")
        for frag in ["【卦象定脏】", "【内经印证】", "【病机推演】", "【调养建议】", "【医嘱】",
                     "说卦传", "金匮真言论"]:
            self.assertIn(frag, s)

    def test_payload_carries_crossref(self):
        req = dict(SAMPLE)
        req["category"] = "健康"
        req["gua"] = {"upper": "坎", "lower": "离", "movingIdx": [0]}
        content = llm_proxy.build_payload(req)["messages"][0]["content"]
        self.assertIn("易卦×内经互证事实", content)
        self.assertIn("《说卦传》配耳", content)
