#!/usr/bin/env python3
"""llm_proxy.py — 易占的 LLM 进一步解读代理（Python 标准库，无第三方依赖）。

浏览器绝不接触密钥：前端 POST /yijing/api/interpret → nginx → 本服务（仅监听
127.0.0.1）→ Anthropic 兼容端点（DashScope）。密钥经环境变量/EnvironmentFile 注入。

持续提升闭环：
  - 每次解读写 JSONL 日志（含 PROMPT_VERSION、请求事实、回复全文、耗时）；
  - 前端 👍/ 经 POST /yijing/api/feedback 回传同目录 feedback.jsonl；
  - eval_run.py 用黄金用例 + 评审模型打分，对比各 PROMPT_VERSION 后迭代提示词。

环境变量：
  LLM_BASE_URL    默认 https://dashscope.aliyuncs.com/apps/anthropic
  LLM_AUTH_TOKEN  必填，缺失时服务拒绝启动
  LLM_MODEL       默认 qwen3.8-max-0902
  LLM_PORT        默认 8100
  LLM_LOG_DIR     默认 /home/cheenle/yijing-llm-logs
"""
import hmac
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DEFAULT_BASE = "https://dashscope.aliyuncs.com/apps/anthropic"
DEFAULT_MODEL = "qwen3.8-max-0902"
DEFAULT_LOG_DIR = "/home/cheenle/yijing-llm-logs"
MAX_BODY = 64 * 1024
UPSTREAM_TIMEOUT = 90
PROMPT_VERSION = "2026-09-26.v13"

SYSTEM_PROMPT = (
    "你是兼通象数与义理的易学解读者，熟稔《周易》经传与朱熹《易学启蒙》断法。"
    "用户给出一次铜钱起卦的完整事实：本卦与之卦、互卦/错卦/综卦、动爻及其爻位事实"
    "（当位失正、中、应、乘承顺逆）、断法所取断辞原文与白话、问事类别。\n"
    "写作要求：\n"
    "1. 结构固定为四段，段首用【卦象大势】【爻位细析】【事理推断】【行动建议】；\n"
    "2. 【卦象大势】首句须点明本卦全称（如「乾为天」「水火既济」），并结合上下经卦取象与互卦所示内情、错综所示反面与换位视角，说明局势；\n"
    "3. 【爻位细析】只析所给动爻（不逐爻泛论），须使用所给爻位事实论证（如失正而居中、有应而乘刚），并引用所给动爻"
    "爻辞或小象原句至少一处，引文必须用「」原样标出且不得省略引号、不得改写；\n"
    "4. 【事理推断】针对所问类别，把卦爻之意落到具体事理，不得空泛；每段至多三句；\n"
    "5. 【行动建议】给二至四条可执行建议，最后一条必须以「忌：」开头写忌讳，不得省略；\n"
    "6. 全文不超过五百字（含标点），宁简勿冗；只用所给经文，不得编造或引用未提供的卦爻辞；\n"
    "7. 不使用「总的来说」「综上所述」之类套话；结尾另起一行写：占断仅供参考，事在人为；\n"    "8. 回复只输出规定段落的正文本身，严禁输出思考过程、自我问答、结构说明或「我来分析」之类元语言。"
)

CATEGORY_FOCUS = {
    "事业": "事业类须落到岗位、权责、上下级与合作关系：何时进取、何时守成、如何处理遗留与交接；"
            "忌空谈格局，须给可执行的职场动作。",
    "财运": "财运类须区分正财与投机：宜守宜投、现金流与止损纪律；凡涉投资须提示风险自负，不给确定性收益承诺。",
    "感情": "感情类须落到沟通、界限与等待：谁主动、何时表态、如何修补；忌替对方断心意，只给自身可为之事。",
    "健康": "健康类只谈调养作息与就医态度，不作诊断、不荐药方；凡涉病症须提醒以医嘱为准。",
    "出行": "出行类须落到时机、方向与准备：宜早宜迟、宜伴宜独、须备何物；忌泛泛言吉凶。",
    "综合": "综合类须先厘清所问核心，再给一个主视角与两条可执行建议。",
}


MEIHUA_SYSTEM = (
    "你是精通梅花易数的解读者（邵雍《梅花易数》体用生克一路），与朱熹六爻断法不同：以体用生克定吉凶大势，"
    "以卦象取象辅证，不以爻辞为主断。用户给出梅花起卦事实：起卦方式、本卦/变卦/互卦、动爻、体卦用卦及其五行与生克关系，"
    "以及本卦变卦卦辞供辅证。\n"
    "写作要求：\n"
    "1. 结构固定四段，段首用【体用大势】【卦象辅证】【事理推断】【行动建议】；\n"
    "2. 【体用大势】首句点明本卦全称与体用生克关系（如「用克体」），并释其势；\n"
    "3. 【卦象辅证】用上下经卦取象、互卦内情与变卦走向辅证，可引所给卦辞原句（用「」标出）；\n"
    "4. 【事理推断】针对所问类别落到具体事理；【行动建议】二至四条，末条以「忌：」开头；\n"
    "5. 全文不超过五百字（含标点）；不得编造未提供的经文；结尾另起一行写：占断仅供参考，事在人为。"
)

# 《黄帝内经》公版条文池（健康类专用 grounding，防模型编造原文）
NEIJING_PASSAGES = [
    ("素问·上古天真论", "法于阴阳，和于术数，食饮有节，起居有常，不妄作劳，故能形与神俱，而尽终其天年。"),
    ("素问·上古天真论", "恬惔虚无，真气从之，精神内守，病安从来。"),
    ("素问·四气调神大论", "春夏养阳，秋冬养阴，以从其根。"),
    ("素问·四气调神大论", "圣人不治已病治未病，不治已乱治未乱。"),
    ("素问·四气调神大论", "春三月……夜卧早起，广步于庭；夏三月……夜卧早起，无厌于日；秋三月……早卧早起，与鸡俱兴；冬三月……早卧晚起，必待日光。"),
    ("素问·阴阳应象大论", "怒伤肝，喜伤心，思伤脾，忧伤肺，恐伤肾。"),
    ("素问·阴阳应象大论", "阴平阳秘，精神乃治；阴阳离决，精气乃绝。"),
    ("素问·藏气法时论", "五谷为养，五果为助，五畜为益，五菜为充，气味合而服之，以补精益气。"),
    ("素问·举痛论", "百病生于气也。怒则气上，喜则气缓，悲则气消，恐则气下，思则气结。"),
    ("素问·痹论", "饮食自倍，肠胃乃伤。"),
    ("灵枢·本神", "智者之养生也，必顺四时而适寒暑，和喜怒而安居处，节阴阳而调刚柔。"),
    ("素问·阴阳应象大论", "天有四时五行，以生长收藏，以生寒暑燥湿风；人有五脏化五气，以生喜怒悲忧恐。"),
    ("素问·金匮真言论", "东方青色，入通于肝；南方赤色，入通于心；中央黄色，入通于脾；西方白色，入通于肺；北方黑色，入通于肾。"),
]

TRIGRAM_WUXING = {"乾": "金", "兑": "金", "离": "火", "震": "木", "巽": "木", "坎": "水", "艮": "土", "坤": "土"}

# 易传/后天配属表：八卦→身体部位（《说卦传》）与五行→脏（后天配脏）
GUA_BODY = {"乾": "首", "坤": "腹", "震": "足", "巽": "股", "坎": "耳", "离": "目", "艮": "手", "兑": "口"}
WUXING_ZANG = {"木": "肝（胆）", "火": "心（小肠）", "土": "脾（胃）", "金": "肺（大肠）", "水": "肾（膀胱）"}
# 爻位配人身（依咸卦爻辞拇→腓→股→心→辅颊之序列，后世通行配属）
YAO_BODY = ["足", "腓（小腿）", "股腰", "胸心", "喉面", "首顶"]
# 公历月→四时与当令之脏（节气月近似；每季末月兼脾土）
SEASON_ZANG = {
    "春": ("肝（胆）", "夜卧早起，广步于庭，以使志生"),
    "夏": ("心（小肠）", "夜卧早起，无厌于日，使志无怒"),
    "秋": ("肺（大肠）", "早卧早起，与鸡俱兴，使志安宁"),
    "冬": ("肾（膀胱）", "早卧晚起，必待日光，使志若伏若匿"),
}
MONTH_SEASON = {2: "春", 3: "春", 4: "春", 5: "夏", 6: "夏", 7: "夏",
                8: "秋", 9: "秋", 10: "秋", 11: "冬", 12: "冬", 1: "冬"}
SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}


def season_of(month1to12, now_day=15):
    season = MONTH_SEASON[month1to12]
    tail = month1to12 in (4, 7, 10, 1)  # 每季末月，脾土当令兼主
    return season, tail


def health_context_lines(req, now=None):
    """易卦×内经互证事实层（纯函数）：卦配脏腑、爻位配身、当令季节、生克推演。"""
    import datetime
    now = now or datetime.datetime.now()
    gua = req.get("gua") or {}
    out = ["易卦×内经互证事实："]
    season, tail = season_of(now.month)
    zang, yangsheng = SEASON_ZANG[season]
    out.append("- 当前四时：%s（公历%d月，节气近似）；当令之脏：%s；四气调神要点：%s%s" % (
        season, now.month, zang, yangsheng, "；季末之月兼脾土当令，顾护中州" if tail else ""))
    wx_zang = None
    for pos, name in (("上卦", gua.get("upper")), ("下卦", gua.get("lower"))):
        if not name:
            continue
        wx = TRIGRAM_WUXING.get(name, "?")
        out.append("- %s%s：《说卦传》配%s；五行属%s，后天配脏%s" % (pos, name, GUA_BODY.get(name, "?"), wx, WUXING_ZANG.get(wx, "?")))
        if pos == "上卦":
            wx_zang = wx
    for idx in gua.get("movingIdx") or []:
        if 0 <= idx <= 5:
            out.append("- 动爻第%s爻：爻位配人身%s（依咸卦爻辞身部序列），病位可于此参看" % (
                ["初", "二", "三", "四", "五", "上"][idx], YAO_BODY[idx]))
    if wx_zang and wx_zang != "?":
        season_wx = {"春": "木", "夏": "火", "秋": "金", "冬": "水"}[season]
        if KE.get(season_wx) == wx_zang:
            out.append("- 生克推演：当令%s气克卦中%s气，当令之脏受制，宜扶该脏而泄其克者" % (season_wx, wx_zang))
        elif KE.get(wx_zang) == season_wx:
            out.append("- 生克推演：卦中%s气克当令%s气，卦势逆时，宜抑其过而顺时养脏" % (wx_zang, season_wx))
        elif SHENG.get(season_wx) == wx_zang:
            out.append("- 生克推演：当令%s气生卦中%s气，得天时之助，宜顺势调养" % (season_wx, wx_zang))
        elif SHENG.get(wx_zang) == season_wx:
            out.append("- 生克推演：卦中%s气生当令%s气，我泄于时，宜补母固本" % (wx_zang, season_wx))
        else:
            out.append("- 生克推演：卦中%s气与当令%s气比和，气机平顺，宜守常" % (wx_zang, season_wx))
    return out



def health_block():
    lines = ["可引用的《黄帝内经》条文池（仅此池内，引用须注明篇名、原文不得改字）："]
    for src, txt in NEIJING_PASSAGES:
        lines.append("- 《%s》：%s" % (src, txt))
    return "\n".join(lines)

# —— 深度模式（属主自用解锁）：可辨证、可荐方；公网默认关闭 ——
def is_owner(req):
    key = req.get("owner") or ""
    env = os.environ.get("YIJING_OWNER_KEY", "")
    return bool(key) and bool(env) and hmac.compare_digest(str(key), str(env))


# 经方/时方池（公版组成，常规参考剂量 g）：方名、出处、组成、煎服、主证
FANG_POOL = [
    ("桂枝汤", "伤寒论", "桂枝9 芍药9 炙甘草6 生姜9 大枣12枚", "水煎，服后啜热粥温覆取微汗", "营卫不和、自汗恶风"),
    ("小柴胡汤", "伤寒论", "柴胡12 黄芩9 人参6 半夏9 炙甘草6 生姜9 大枣4枚", "水煎去滓再煎温服", "少阳枢机不利、寒热往来、口苦咽干"),
    ("理中丸", "伤寒论", "人参9 干姜9 白术9 炙甘草9", "水煎温服，或作丸", "中焦虚寒、腹满吐利"),
    ("半夏泻心汤", "伤寒论", "半夏9 黄芩6 干姜6 人参6 黄连3 大枣4枚 炙甘草9", "水煎去滓再煎", "寒热错杂之痞、呕逆肠鸣"),
    ("四君子汤", "太平惠民和剂局方", "人参9 白术9 茯苓9 炙甘草6", "水煎温服", "脾胃气虚、食少便溏"),
    ("归脾汤", "济生方", "黄芪12 白术9 当归9 茯苓9 远志6 龙眼肉12 酸枣仁12 人参6 木香6 炙甘草3", "加姜枣水煎", "心脾两虚、心悸失眠、食少体倦"),
    ("酸枣仁汤", "金匮要略", "酸枣仁15 炙甘草3 知母6 茯苓6 川芎6", "水煎分温", "肝血不足、虚烦不得眠"),
    ("温胆汤", "三因极一病证方论", "半夏9 竹茹9 枳实9 陈皮9 炙甘草3 茯苓6", "加姜枣水煎", "胆郁痰扰、惊悸失眠、呕恶"),
    ("六味地黄丸", "小儿药证直诀", "熟地24 山萸肉12 干山药12 泽泻9 丹皮9 茯苓9", "蜜丸或水煎减量", "肝肾阴虚、腰膝酸软、盗汗"),
    ("逍遥散", "太平惠民和剂局方", "柴胡9 当归9 白芍9 白术9 茯苓9 炙甘草6 薄荷3 生姜3", "水煎温服", "肝郁血虚脾弱、胁胀神疲"),
    ("补中益气汤", "脾胃论", "黄芪15 人参6 白术9 炙甘草6 当归6 陈皮6 升麻3 柴胡3", "水煎空腹温服", "脾虚气陷、倦怠乏力、久泻"),
    ("血府逐瘀汤", "医林改错", "桃仁12 红花9 当归9 生地9 川芎6 赤芍6 牛膝9 桔梗5 柴胡3 枳壳6 甘草3", "水煎", "胸中血瘀、胸痛失眠、舌暗"),
]

# 子午流注：十二时辰配十二经
SHICHEN_JING_PY = ["胆", "肝", "肺", "大肠", "胃", "脾", "心", "小肠", "膀胱", "肾", "心包", "三焦"]
SHICHEN_ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]


def liuzhu_now(now=None):
    import datetime
    now = now or datetime.datetime.now()
    i = ((now.hour + 1) % 24) // 2
    return "%s时（%s）当令 %s经" % (SHICHEN_ZHI[i], "%02d:00-%02d:00" % ((i * 2 + 23) % 24, (i * 2 + 25) % 24 or 24), SHICHEN_JING_PY[i])


def deep_health_block():
    lines = ["深度模式（属主自用）：可作中医辨证与方药推荐。可用处方池（组成与常规参考剂量，g）："]
    for name, src, comp, decoct, zhu in FANG_POOL:
        lines.append("- %s（%s）：%s；煎服：%s；主证：%s" % (name, src, comp, decoct, zhu))
    return "\n".join(lines)


def system_prompt(category, mode="reading", deep=False):
    """按问事类别与模式动态组装 System Prompt。"""
    reading_structure = "1. 结构固定为四段，段首用【卦象大势】【爻位细析】【事理推断】【行动建议】；\n"
    if mode == "meihua":
        base = MEIHUA_SYSTEM
    elif mode == "chat":
        base = (
            "你是兼通易理的疏导者，正就一次已成的卦象与用户多轮对话。规则：\n"
            "1. 紧扣所给卦象事实与此前解读，不另起新卦、不脱离上下文；\n"
            "2. 每轮回复不超过一百八十字；先接住用户的情绪或问题，再给一个视角、一个具体行动或一个反思提问；\n"
            "3. 不预测确定结果；不作医疗、法律、投资的替代意见；\n"
            "4. 涉及健康须附一句「具体请以医嘱为准」，涉及钱财须附一句「盈亏风险自担」；\n"
            "5. 语气温和克制，不堆砌术语。"
        )
    else:
        base = SYSTEM_PROMPT
        if deep and category == "健康":
            # 深度模式五段与基础四段互斥，必须替换而非并存
            base = base.replace(reading_structure,
                                "1. 结构以深度模式五段为准（见类别专项要求），不使用四段结构；\n")
    out = base + "\n\n所问类别专项要求：" + CATEGORY_FOCUS.get(category, CATEGORY_FOCUS["综合"])
    if category == "健康":
        common = ("\n\n黄帝内经理法：" + health_block() +
                  "\n引用内经只可用池内条文且不得改字；须结合「易卦×内经互证」事实层"
                  "（卦配脏腑、爻位配身、当令四时、生克推演、子午流注）。")
        if deep:
            out += common + ("\n\n" + deep_health_block() +
                             "\n深度模式（属主自用）结构固定五段："
                             "【辨证】（八纲+脏腑证型，给出证型名与依据，卦象与内经互证）、"
                             "【治则】（治法八字以内）、"
                             "【方药】（只可用池内方，可合方或加减但须注明；给出组成剂量与煎服法）、"
                             "【针灸择时】（结合子午流注当令经与病位脏府，给取经取穴原则与宜忌时辰）、"
                             "【禁忌与红线】（配伍禁忌与须立即就医的情形）。"
                             "\n深度模式不作每轮医嘱套话，就医红线由【禁忌与红线】段承担；""\n深度模式字数上限放宽至九百字；回复只输出五段正文，严禁思考过程外泄。")
        else:
            out += common + ("\n健康类结构固定五段：【卦象定脏】【内经印证】【病机推演】【调养建议】【医嘱】；"
                             "本模式面向公众：不得作诊断、不荐药方，仅作调养参考，并始终提醒以医嘱为准。")
    return out + MEMORY_RULE


MEMORY_RULE = ("\n\n长期记忆纪律：若输入含「用户长期记忆」，只可引用其中明确记录的占例与回访结论，"
               "不得扩写、虚构或把它当作本次卦象的依据；本次解读仍以当前卦象与断辞为主。")


def memory_lines(req):
    mem = req.get("memory")
    if not isinstance(mem, dict):
        return []
    out = ["用户长期记忆（本机占例档案，共 %s 条）：" % mem.get("count", "?")]
    for line in mem.get("recent") or []:
        out.append("- %s" % line)
    for line in mem.get("stats") or []:
        out.append("- 回访统计：%s" % line)
    return out


def build_payload(req):
    """由前端请求体构造上游 Messages 请求（纯函数，便于测试）。"""
    if req.get("method") == "meihua":
        return _build_meihua_payload(req)
    ben = req.get("ben") or {}
    zhi = req.get("zhi")
    moving = req.get("moving") or []
    duanci = req.get("duanci") or []
    lines = ["所问之事：%s" % (req.get("question") or "心中默念"),
             "问事类别：%s" % req.get("category", "综合"),
             "本卦：%s" % ben.get("fullName", "?")]
    if ben.get("tuan"):
        lines.append("本卦彖传：%s" % ben["tuan"])
    if ben.get("xiang"):
        lines.append("本卦大象：%s" % ben["xiang"])
    lines.append("之卦：%s" % (zhi.get("fullName") if zhi else "无（六爻安静）"))
    lines.append("互卦：%s　错卦：%s　综卦：%s" % (req.get("hu") or "?", req.get("cuo") or "?", req.get("zong") or "?"))
    if moving:
        lines.append("动爻爻位事实：")
        for m in moving:
            one = "- %s：%s" % (m.get("title", "?"), m.get("facts", ""))
            if m.get("xiang"):
                one += "　小象：%s" % m["xiang"]
            lines.append(one)
    else:
        lines.append("动爻：无")
    lines.append("断法：%s" % req.get("rule", "?"))
    if req.get("category") == "健康":
        lines.extend(health_context_lines(req))
        lines.append("- 子午流注：当前%s" % liuzhu_now())
    lines.extend(memory_lines(req))
    lines.append("断辞：")
    for e in duanci:
        lines.append("- %s：%s（白话：%s）" % (e.get("source", "?"), e.get("ci", ""), e.get("baihua", "")))
    return {
        "model": os.environ.get("LLM_MODEL", DEFAULT_MODEL),
        "max_tokens": 3000 if is_owner(req) else 2048,
        # 思考型模型：给 thinking 设预算，避免思考吃满额度/超时导致正文为空；深度模式加倍
        "thinking": {"type": "enabled", "budget_tokens": 2048 if is_owner(req) else 1024},
        "system": system_prompt(req.get("category", "综合"), "reading", is_owner(req)),
        "messages": [{"role": "user", "content": "\n".join(lines)}],
    }


def build_chat_payload(req):
    """多轮追问：卦象上下文作首条 user 消息，历史 messages 截断续接（纯函数）。"""
    ctx = req.get("context") or {}
    head = ["当前卦象事实：",
            "本卦：%s　之卦：%s　互卦：%s" % (ctx.get("ben") or "?", ctx.get("zhi") or "无", ctx.get("hu") or "?")]
    if ctx.get("moving"):
        head.append("动爻：%s" % "；".join(ctx["moving"]))
    head.append("断法：%s" % (ctx.get("rule") or "?"))
    if ctx.get("reading"):
        head.append("此前 AI 解读：%s" % str(ctx["reading"])[:600])
    if req.get("category") == "健康":
        head.extend(health_context_lines(req))
        head.append("- 子午流注：当前%s" % liuzhu_now())
    head.extend(memory_lines({"memory": ctx.get("memory")}))
    msgs = [{"role": "user", "content": "\n".join(head)}]
    for m in (req.get("messages") or [])[-10:]:
        if isinstance(m, dict) and m.get("role") in ("user", "assistant") and isinstance(m.get("content"), str):
            msgs.append({"role": m["role"], "content": m["content"][:2000]})
    return {
        "model": os.environ.get("LLM_MODEL", DEFAULT_MODEL),
        "max_tokens": 1600 if is_owner(req) else 800,
        "thinking": {"type": "enabled", "budget_tokens": 1024 if is_owner(req) else 512},
        "system": system_prompt(req.get("category", "综合"), "chat", is_owner(req)),
        "messages": msgs,
    }


def _build_meihua_payload(req):
    mh = req.get("meihua") or {}
    ben = req.get("ben") or {}
    lines = ["所问之事：%s" % (req.get("question") or "心中默念"),
             "问事类别：%s" % req.get("category", "综合"),
             "起卦方式：%s" % (mh.get("methodNote") or "梅花易数"),
             "本卦：%s　变卦：%s　互卦：%s" % (mh.get("ben") or "?", mh.get("zhi") or "?", mh.get("hu") or "?"),
             "动爻：%s" % (mh.get("movingWei") or "?"),
             "体卦：%s　用卦：%s　生克关系：%s（%s）" % (
                 mh.get("ti") or "?", mh.get("yong") or "?", mh.get("relation") or "?", mh.get("relationNote") or "")]
    if ben.get("tuan"):
        lines.append("本卦彖传：%s" % ben["tuan"])
    if ben.get("xiang"):
        lines.append("本卦大象：%s" % ben["xiang"])
    if req.get("category") == "健康":
        lines.extend(health_context_lines(req))
        lines.append("- 子午流注：当前%s" % liuzhu_now())
    lines.extend(memory_lines(req))
    lines.append("辅证卦辞：")
    for e in req.get("duanci") or []:
        lines.append("- %s：%s（白话：%s）" % (e.get("source", "?"), e.get("ci", ""), e.get("baihua", "")))
    return {
        "model": os.environ.get("LLM_MODEL", DEFAULT_MODEL),
        "max_tokens": 3000 if is_owner(req) else 2048,
        "thinking": {"type": "enabled", "budget_tokens": 2048 if is_owner(req) else 1024},
        "system": system_prompt(req.get("category", "综合"), "meihua", is_owner(req)),
        "messages": [{"role": "user", "content": "\n".join(lines)}],
    }


def extract_text(resp):
    """从 Messages 响应中取出 text 块拼接（thinking 块忽略）。"""
    parts = [b.get("text", "") for b in resp.get("content", []) if b.get("type") == "text"]
    return "\n".join(p for p in parts if p).strip()


def call_upstream(payload):
    base = os.environ.get("LLM_BASE_URL", DEFAULT_BASE).rstrip("/")
    token = os.environ.get("LLM_AUTH_TOKEN", "")
    if not token:
        raise RuntimeError("LLM_AUTH_TOKEN 未配置")
    rq = urllib.request.Request(
        base + "/v1/messages",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "x-api-key": token,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(rq, timeout=UPSTREAM_TIMEOUT) as rp:
        return json.loads(rp.read().decode("utf-8"))


def validate_feedback(body):
    """反馈体校验（纯函数）：rating 点赞/点踩，或 outcome 应验回填（1/0/-1）。"""
    if not isinstance(body, dict):
        return None
    kind = body.get("kind", "rating")
    if kind == "rating":
        if body.get("rating") not in (1, -1):
            return None
    elif kind == "outcome":
        if body.get("rating") not in (1, 0, -1):
            return None
        if not isinstance(body.get("record"), dict):
            return None
    else:
        return None
    return kind


def log_event(kind, obj):
    d = os.environ.get("LLM_LOG_DIR", DEFAULT_LOG_DIR)
    try:
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "%s.jsonl" % kind), "a", encoding="utf-8") as f:
            rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "version": PROMPT_VERSION}
            rec.update(obj)
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError:
        pass  # 日志失败不阻断解读


class Handler(BaseHTTPRequestHandler):
    server_version = "YijingLLMProxy/2.0"

    def _send(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > MAX_BODY:
            return None
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return None

    def do_POST(self):
        if self.path == "/interpret":
            self._interpret()
        elif self.path == "/verify":
            self._verify()
        elif self.path == "/chat":
            self._chat()
        elif self.path == "/feedback":
            self._feedback()
        else:
            self._send(404, {"ok": False, "error": "not found"})

    def _interpret(self):
        req = self._read_json()
        if req is None:
            self._send(400, {"ok": False, "error": "bad json"})
            return
        rid = uuid.uuid4().hex[:16]
        log_event("interpret_req", {"id": rid, "deep": is_owner(req), "req": req})
        t0 = time.time()
        text = ""
        try:
            # 思考型模型偶发把额度耗在 thinking 上导致正文为空，重试一次
            for _attempt in range(2):
                resp = call_upstream(build_payload(req))
                text = extract_text(resp)
                if text:
                    break
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8", "replace")
            except Exception:
                pass
            if e.code == 400 and "DataInspection" in body:
                log_event("interpret_err", {"id": rid, "error": "content-inspection"})
                self._send(409, {"ok": False, "error": "content-inspection"})
                return
            log_event("interpret_err", {"id": rid, "error": "upstream %d" % e.code})
            self._send(502, {"ok": False, "error": "upstream %d" % e.code})
            return
        except Exception as e:
            log_event("interpret_err", {"id": rid, "error": type(e).__name__})
            self._send(502, {"ok": False, "error": "upstream error: %s" % type(e).__name__})
            return
        if not text:
            log_event("interpret_err", {"id": rid, "error": "empty completion"})
            self._send(502, {"ok": False, "error": "empty completion"})
            return
        log_event("interpret_res", {"id": rid, "ms": int((time.time() - t0) * 1000), "text": text})
        self._send(200, {"ok": True, "text": text, "id": rid, "version": PROMPT_VERSION})

    def _verify(self):
        body = self._read_json()
        if not isinstance(body, dict) or not is_owner({"owner": body.get("key")}):
            self._send(403, {"ok": False, "error": "forbidden"})
            return
        self._send(200, {"ok": True})

    def _chat(self):
        req = self._read_json()
        if req is None or not isinstance(req.get("messages"), list):
            self._send(400, {"ok": False, "error": "messages list required"})
            return
        rid = uuid.uuid4().hex[:16]
        log_event("chat_req", {"id": rid, "req": req})
        t0 = time.time()
        text = ""
        try:
            for _attempt in range(2):
                resp = call_upstream(build_chat_payload(req))
                text = extract_text(resp)
                if text:
                    break
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8", "replace")
            except Exception:
                pass
            if e.code == 400 and "DataInspection" in body:
                log_event("chat_err", {"id": rid, "error": "content-inspection"})
                self._send(409, {"ok": False, "error": "content-inspection"})
                return
            log_event("chat_err", {"id": rid, "error": "upstream %d" % e.code})
            self._send(502, {"ok": False, "error": "upstream %d" % e.code})
            return
        except Exception as e:
            log_event("chat_err", {"id": rid, "error": type(e).__name__})
            self._send(502, {"ok": False, "error": "upstream error: %s" % type(e).__name__})
            return
        if not text:
            log_event("chat_err", {"id": rid, "error": "empty completion"})
            self._send(502, {"ok": False, "error": "empty completion"})
            return
        log_event("chat_res", {"id": rid, "ms": int((time.time() - t0) * 1000), "text": text})
        self._send(200, {"ok": True, "text": text, "id": rid, "version": PROMPT_VERSION})

    def _feedback(self):
        body = self._read_json()
        kind = validate_feedback(body)
        if kind is None:
            self._send(400, {"ok": False, "error": "invalid feedback payload"})
            return
        rec = {
            "kind": kind,
            "id": body.get("id"),
            "rating": body["rating"],
            "question": body.get("question", ""),
            "category": body.get("category", ""),
        }
        if kind == "outcome":
            rec["outcome"] = str(body.get("outcome", ""))[:2000]
            rec["record"] = body["record"]
        log_event("feedback", rec)
        self._send(200, {"ok": True})

    def do_GET(self):
        self._send(405, {"ok": False, "error": "method not allowed"})

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main():
    if not os.environ.get("LLM_AUTH_TOKEN"):
        sys.exit("LLM_AUTH_TOKEN 未配置，拒绝启动")
    port = int(os.environ.get("LLM_PORT", "8100"))
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    sys.stderr.write("yijing llm proxy %s on 127.0.0.1:%d\n" % (PROMPT_VERSION, port))
    srv.serve_forever()


if __name__ == "__main__":
    main()
