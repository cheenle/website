import json
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
import llm_proxy  # noqa: E402

SAMPLE = {
    "question": "秋季换工作是否合适",
    "category": "事业",
    "ben": {"fullName": "水火既济"},
    "zhi": {"fullName": "山风蛊"},
    "movingTitles": ["初九", "六二", "九五", "上六"],
    "rule": "四爻动，以之卦两静爻辞断，以下爻为主",
    "duanci": [
        {"source": "之卦山风蛊·九三（主）", "ci": "干父之蛊，小有悔，无大咎。",
         "baihua": "以刚治父辈遗留之积弊，虽因操之过急而小有悔恨，终不至于有大咎害。"}
    ],
}


class BuildPayloadTest(unittest.TestCase):
    def test_model_from_env(self):
        os.environ["LLM_MODEL"] = "qwen3.8-max-0902"
        p = llm_proxy.build_payload(SAMPLE)
        self.assertEqual(p["model"], "qwen3.8-max-0902")
        self.assertEqual(p["messages"][0]["role"], "user")
        self.assertIn("水火既济", p["messages"][0]["content"])
        self.assertIn("干父之蛊", p["messages"][0]["content"])
        self.assertIn("事业", p["messages"][0]["content"])
        self.assertIn("三百字以内", p["system"])

    def test_no_zhi_and_no_question(self):
        req = {"category": "综合", "ben": {"fullName": "乾为天"}, "zhi": None,
               "movingTitles": [], "rule": "六爻安静，以本卦卦辞断", "duanci": []}
        content = llm_proxy.build_payload(req)["messages"][0]["content"]
        self.assertIn("无（六爻安静）", content)
        self.assertIn("心中默念", content)


class ExtractTextTest(unittest.TestCase):
    def test_joins_text_and_skips_thinking(self):
        resp = {"content": [
            {"type": "thinking", "thinking": "…"},
            {"type": "text", "text": "卦象：…"},
            {"type": "text", "text": "行动：…"},
        ]}
        self.assertEqual(llm_proxy.extract_text(resp), "卦象：…\n行动：…")

    def test_empty(self):
        self.assertEqual(llm_proxy.extract_text({"content": []}), "")


if __name__ == "__main__":
    unittest.main()
