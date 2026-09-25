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
