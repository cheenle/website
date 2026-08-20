"""呼号验证 — 归一化、格式正则、Club Log 基准呼号提取。纯函数，无 I/O。"""
import re

# 基准呼号：可选 1 位数字前缀（9M2/4X 等）+ 1-2 字母 + 1 位数字 + 1-3 字母
CALLSIGN_RE = re.compile(r'^[0-9]?[A-Z]{1,2}[0-9][A-Z]{1,3}$')

# 便携/特殊分隔符（反馈身份仅接受基准呼号）
SEPARATORS = '/_.-'


def normalize(raw):
    """去空白并转大写；含分隔符返回 ''（拒绝）。"""
    if not isinstance(raw, str):
        return ''
    s = raw.strip().upper().replace(' ', '')
    if not s or any(c in s for c in SEPARATORS):
        return ''
    return s


def is_valid_format(call):
    """基准呼号格式校验（输入须已 normalize）。"""
    return bool(CALLSIGN_RE.match(call))


def base_callsign(key):
    """从 Club Log 原始键提取基准呼号：
    '4X/BG1SB' -> 'BG1SB'（取 / 右侧合法段）
    'BG1SB/P'  -> 'BG1SB'（P 不合法则取左侧）
    '1A0C_14'  -> '1A0C'（去掉 _ 后缀）
    'BG1SB'    -> 'BG1SB'；'SOS' -> ''（提取失败）
    """
    if not isinstance(key, str):
        return ''
    k = key.strip().upper()
    if not k:
        return ''
    if '/' in k:
        for part in reversed([p for p in k.split('/') if p]):
            if is_valid_format(part):
                return part
        return ''
    if '_' in k:
        k = k.split('_', 1)[0]
    return k if is_valid_format(k) else ''
