# 易占（yijing/）易经占卜应用实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 vlsc.net 仓库新增纯静态子站 `yijing/`：铜钱摇卦起卦，排本卦/之卦/互卦，按朱熹《易学启蒙》断法取断辞，引《周易》经传原文配白话今译。

**Architecture:** 单页四屏（问卦→摇卦→排卦断卦→存档），无框架无构建。数据层 `js/data/*.js` 为 JSON 严格字面量（键带引号、无尾逗号、无注释），浏览器经 script 标签全局共享，Node 经 `require` 复用；逻辑层 `cast.js`（起卦）、`gua.js`（排卦与断法，纯函数）不碰 DOM；`app.js` 是唯一 DOM/状态层。Python 校验脚本 `check_hexagrams.py` 作部署前验证门。

**Tech Stack:** 纯 HTML/CSS/JS；Node v22 内置 `node --test`（`yijing/tests/`，不打入部署包）；Python 3 标准库校验脚本。

**Spec:** `docs/superpowers/specs/2026-09-24-yijing-divination-design.md`

**全局约定（每个任务都必须遵守）：**

- `yijing/js/data/*.js` 必须是 **JSON 严格字面量**：所有键带双引号、无注释、无尾逗号，文件结尾附 CommonJS 导出守卫：
  ```js
  if (typeof module !== "undefined" && module.exports) module.exports = XXX;
  ```
  这是 `check_hexagrams.py` 能用 Python `json.loads` 解析的前提。
- 卦画编码 `lines`：六位字符串，**初爻在前**（自下而上），`1` 阳 `0` 阴。下经卦 = 前三位，上经卦 = 后三位。
- 八卦卦符 `symbol`：三位字符串，自下而上。乾111 兑110 离101 震100 巽011 坎010 艮001 坤000。
- 经文原文用通行本《周易》（公版）；白话今译与 `advice` 为新撰，语体仿任务 5 中乾、坤两卦示例。
- 每完成一个任务即 commit（commit message 用中文，格式 `feat(yijing): …` / `test(yijing): …`）。
- 运行 Node 测试的命令统一为：`cd yijing && node --test`

---

## Task 1: 项目骨架与 deploy.sh

**Files:**
- Create: `yijing/deploy.sh`

- [ ] **Step 1: 创建目录与 deploy.sh**

```bash
mkdir -p yijing/css yijing/js/data yijing/tests
```

`yijing/deploy.sh`（仿 `efhw/deploy.sh`，前置数据校验门，排除工具脚本与测试）：

```bash
#!/bin/bash
#
# deploy.sh — Deploy 易占 to www.vlsc.net/yijing/
# Usage: ./deploy.sh [--force]
#
set -e

LOCAL_WEBSITE_DIR="/Users/cheenle/HAM/website/yijing"
REMOTE_HOST="www.vlsc.net"
REMOTE_USER="cheenle"
REMOTE_WEBROOT="/var/www/vlsc.net/yijing"
BACKUP_DIR="/tmp/yijing_backup_$(date +%Y%m%d_%H%M%S)"
TARBALL="/tmp/yijing_site_$(date +%Y%m%d_%H%M%S).tar.gz"

echo "=========================================="
echo "  易占 Deployment"
echo "  Target: ${REMOTE_HOST}:${REMOTE_WEBROOT}"
echo "=========================================="
echo ""

# Data validation gate — 64 卦数据不全不准上线
echo "[..] Running check_hexagrams.py (strict)..."
/usr/bin/python3 "${LOCAL_WEBSITE_DIR}/check_hexagrams.py"

# Check required files
for f in "index.html" "css/yijing.css" "js/app.js" "js/cast.js" "js/gua.js" "js/data/trigrams.js" "js/data/hexagrams.js"; do
    if [ ! -f "${LOCAL_WEBSITE_DIR}/${f}" ]; then
        echo "ERROR: Required file not found: ${LOCAL_WEBSITE_DIR}/${f}"
        exit 1
    fi
done
echo "[OK] Required files present."

# Create tarball（工具脚本与测试不进 webroot）
echo "[..] Creating tarball..."
cd "$(dirname "${LOCAL_WEBSITE_DIR}")"
tar czf "${TARBALL}" \
    --exclude='yijing/check_hexagrams.py' \
    --exclude='yijing/deploy.sh' \
    --exclude='yijing/tests' \
    --exclude='yijing/.DS_Store' \
    yijing/
echo "[OK] Tarball created: ${TARBALL}"

# Confirm
if [ "$1" != "--force" ]; then
    echo ""
    echo "This will deploy to https://www.vlsc.net/yijing/"
    read -p "Proceed? (y/N) " -r CONFIRM
    if [[ ! "${CONFIRM}" =~ ^[Yy]$ ]]; then
        echo "Aborted."
        rm -f "${TARBALL}"
        exit 0
    fi
fi

# Backup current site
echo "[..] Backing up current site..."
ssh "${REMOTE_USER}@${REMOTE_HOST}" "
    if [ -d ${REMOTE_WEBROOT} ]; then
        sudo mkdir -p ${BACKUP_DIR} && sudo cp -a ${REMOTE_WEBROOT}/* ${BACKUP_DIR}/ 2>/dev/null || true
        echo 'Backup: ${BACKUP_DIR}'
    else
        echo 'No existing site to back up.'
    fi
"

# Upload
echo "[..] Uploading..."
scp "${TARBALL}" "${REMOTE_USER}@${REMOTE_HOST}:/tmp/"

# Extract and set permissions
echo "[..] Extracting and setting permissions..."
ssh "${REMOTE_USER}@${REMOTE_HOST}" "
    sudo rm -rf ${REMOTE_WEBROOT}/* 2>/dev/null || true
    sudo mkdir -p ${REMOTE_WEBROOT}
    sudo tar xzf /tmp/yijing_site_*.tar.gz -C /var/www/vlsc.net/
    sudo chown -R www-data:www-data ${REMOTE_WEBROOT}
    sudo find ${REMOTE_WEBROOT} -type d -exec chmod 755 {} \;
    sudo find ${REMOTE_WEBROOT} -type f -exec chmod 644 {} \;
    rm -f /tmp/yijing_site_*.tar.gz
    echo '[OK] Files extracted to ${REMOTE_WEBROOT}'
"

# Reload nginx
echo "[..] Reloading nginx..."
ssh "${REMOTE_USER}@${REMOTE_HOST}" "sudo nginx -t && sudo systemctl reload nginx"
echo "[OK] nginx reloaded."

# Cleanup
rm -f "${TARBALL}"

echo ""
echo "=========================================="
echo "  Deployment Complete!"
echo "  URL: https://www.vlsc.net/yijing/"
echo "=========================================="
```

- [ ] **Step 2: 赋予执行权限并提交**

```bash
chmod +x yijing/deploy.sh
git add yijing/deploy.sh
git commit -m "feat(yijing): 项目骨架与部署脚本"
```

---

## Task 2: 八卦数据 trigrams.js

**Files:**
- Create: `yijing/js/data/trigrams.js`
- Test: `yijing/tests/trigrams.test.js`

- [ ] **Step 1: 写失败测试**

`yijing/tests/trigrams.test.js`：

```js
const test = require("node:test");
const assert = require("node:assert/strict");
const TRIGRAMS = require("../js/data/trigrams.js");

test("八卦齐备，卦符唯一且合法", () => {
  const names = Object.keys(TRIGRAMS);
  assert.deepEqual([...names].sort(), ["乾","兑","离","震","巽","坎","艮","坤"].sort());
  const symbols = names.map((n) => TRIGRAMS[n].symbol);
  assert.equal(new Set(symbols).size, 8);
  for (const s of symbols) assert.match(s, /^[01]{3}$/);
});

test("卦符编码自下而上：乾111 坤000 坎010 离101 震100 艮001 兑110 巽011", () => {
  assert.equal(TRIGRAMS["乾"].symbol, "111");
  assert.equal(TRIGRAMS["坤"].symbol, "000");
  assert.equal(TRIGRAMS["坎"].symbol, "010");
  assert.equal(TRIGRAMS["离"].symbol, "101");
  assert.equal(TRIGRAMS["震"].symbol, "100");
  assert.equal(TRIGRAMS["艮"].symbol, "001");
  assert.equal(TRIGRAMS["兑"].symbol, "110");
  assert.equal(TRIGRAMS["巽"].symbol, "011");
});

test("每卦有五行、方位、自然取象、家庭取象", () => {
  for (const name of Object.keys(TRIGRAMS)) {
    for (const f of ["wuxing", "fangwei", "nature", "family"]) {
      assert.ok(TRIGRAMS[name][f], `${name} 缺 ${f}`);
    }
  }
});
```

- [ ] **Step 2: 运行确认失败**

Run: `cd yijing && node --test`
Expected: FAIL — `Cannot find module '../js/data/trigrams.js'`

- [ ] **Step 3: 实现 trigrams.js**

`yijing/js/data/trigrams.js`（JSON 严格格式）：

```js
// 八卦基础数据。symbol: 三位字符串，自下而上（初爻在前），1 阳 0 阴。
const TRIGRAMS = {
  "乾": { "symbol": "111", "wuxing": "金", "fangwei": "西北", "nature": "天", "family": "父" },
  "兑": { "symbol": "110", "wuxing": "金", "fangwei": "西",  "nature": "泽", "family": "少女" },
  "离": { "symbol": "101", "wuxing": "火", "fangwei": "南",  "nature": "火", "family": "中女" },
  "震": { "symbol": "100", "wuxing": "木", "fangwei": "东",  "nature": "雷", "family": "长男" },
  "巽": { "symbol": "011", "wuxing": "木", "fangwei": "东南", "nature": "风", "family": "长女" },
  "坎": { "symbol": "010", "wuxing": "水", "fangwei": "北",  "nature": "水", "family": "中男" },
  "艮": { "symbol": "001", "wuxing": "土", "fangwei": "东北", "nature": "山", "family": "少男" },
  "坤": { "symbol": "000", "wuxing": "土", "fangwei": "西南", "nature": "地", "family": "母" }
};
if (typeof module !== "undefined" && module.exports) module.exports = TRIGRAMS;
```

- [ ] **Step 4: 运行确认通过**

Run: `cd yijing && node --test`
Expected: PASS（3 个测试全绿）

- [ ] **Step 5: Commit**

```bash
git add yijing/js/data/trigrams.js yijing/tests/trigrams.test.js
git commit -m "feat(yijing): 八卦基础数据"
```

---

## Task 3: 起卦算法 cast.js

**Files:**
- Create: `yijing/js/cast.js`
- Test: `yijing/tests/cast.test.js`

规则：每爻掷三枚铜钱，正面 3 反面 2，合计 6=老阴（动）、7=少阳、8=少阴、9=老阳（动）；概率 1/8、3/8、3/8、1/8。

- [ ] **Step 1: 写失败测试**

`yijing/tests/cast.test.js`：

```js
const test = require("node:test");
const assert = require("node:assert/strict");
const { castLine, castGua } = require("../js/cast.js");

test("三正面得老阳 9，三反面得老阴 6", () => {
  assert.equal(castLine(() => 0.1), 9);
  assert.equal(castLine(() => 0.9), 6);
});

test("一阳面二阴面得少阳 7，二阳面一阴面得少阴 8", () => {
  // random() < 0.5 记阳面（值 3），否则阴面（值 2）；和 = 6 + 阳面数
  const a = [0.1, 0.9, 0.9]; let i = 0;
  assert.equal(castLine(() => a[i++]), 7);
  const b = [0.1, 0.1, 0.9]; let j = 0;
  assert.equal(castLine(() => b[j++]), 8);
});

test("castGua 返回六爻，值域 6-9", () => {
  const g = castGua(Math.random);
  assert.equal(g.length, 6);
  for (const v of g) assert.ok([6, 7, 8, 9].includes(v));
});

test("概率分布合古法：老阴老阳各约 1/8，少阴少阳各约 3/8", () => {
  const counts = { 6: 0, 7: 0, 8: 0, 9: 0 };
  const N = 80000;
  for (let i = 0; i < N; i++) counts[castLine(Math.random)]++;
  assert.ok(Math.abs(counts[6] / N - 0.125) < 0.01, `老阴 ${counts[6] / N}`);
  assert.ok(Math.abs(counts[9] / N - 0.125) < 0.01, `老阳 ${counts[9] / N}`);
  assert.ok(Math.abs(counts[7] / N - 0.375) < 0.01, `少阳 ${counts[7] / N}`);
  assert.ok(Math.abs(counts[8] / N - 0.375) < 0.01, `少阴 ${counts[8] / N}`);
});
```

- [ ] **Step 2: 运行确认失败**

Run: `cd yijing && node --test`
Expected: FAIL — `Cannot find module '../js/cast.js'`

- [ ] **Step 3: 实现 cast.js**

`yijing/js/cast.js`：

```js
// 三枚铜钱起卦。random: () => [0,1) 的随机数，注入以便测试。
function castLine(random) {
  let total = 0;
  for (let i = 0; i < 3; i++) total += random() < 0.5 ? 3 : 2;
  return total; // 6 老阴 / 7 少阳 / 8 少阴 / 9 老阳
}

function castGua(random) {
  const lines = [];
  for (let i = 0; i < 6; i++) lines.push(castLine(random));
  return lines;
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { castLine, castGua };
}
```

- [ ] **Step 4: 运行确认通过**

Run: `cd yijing && node --test`
Expected: PASS（含任务 2 的测试共 7 个全绿）

- [ ] **Step 5: Commit**

```bash
git add yijing/js/cast.js yijing/tests/cast.test.js
git commit -m "feat(yijing): 铜钱起卦算法"
```

---

## Task 4: 排卦几何 gua.js（上）

**Files:**
- Create: `yijing/js/gua.js`
- Test: `yijing/tests/gua.test.js`

本任务只做不依赖 64 卦数据的纯几何函数；`findHexagram`/`duanCi` 在任务 10（数据齐备后）追加到同一文件。

- [ ] **Step 1: 写失败测试**

`yijing/tests/gua.test.js`：

```js
const test = require("node:test");
const assert = require("node:assert/strict");
const gua = require("../js/gua.js");

test("toBits: 7/9 为阳，6/8 为阴", () => {
  assert.deepEqual(gua.toBits([7, 8, 9, 6, 7, 8]), [1, 0, 1, 0, 1, 0]);
});

test("movingLines: 6/9 为动爻，返回下标（初爻为 0）", () => {
  assert.deepEqual(gua.movingLines([9, 7, 8, 6, 7, 9]), [0, 3, 5]);
  assert.deepEqual(gua.movingLines([7, 7, 7, 7, 7, 7]), []);
});

test("zhiBits: 动爻阴阳互变得之卦", () => {
  assert.deepEqual(gua.zhiBits([9, 7, 8, 6, 7, 9]), [0, 1, 0, 1, 1, 0]);
  assert.deepEqual(gua.zhiBits([7, 7, 7, 7, 7, 7]), [1, 1, 1, 1, 1, 1]);
});

test("huBits: 二三四爻为互卦下卦，三四五爻为互卦上卦", () => {
  const hu = gua.huBits([1, 0, 1, 0, 1, 1]);
  assert.deepEqual(hu.lower, [0, 1, 0]);
  assert.deepEqual(hu.upper, [1, 0, 1]);
});

test("trigramName: 三爻卦符查经卦名", () => {
  assert.equal(gua.trigramName([1, 1, 1]), "乾");
  assert.equal(gua.trigramName([0, 0, 0]), "坤");
  assert.equal(gua.trigramName([0, 1, 0]), "坎");
  assert.equal(gua.trigramName([1, 0, 0]), "震");
});
```

- [ ] **Step 2: 运行确认失败**

Run: `cd yijing && node --test`
Expected: FAIL — `Cannot find module '../js/gua.js'`

- [ ] **Step 3: 实现 gua.js 几何部分**

`yijing/js/gua.js`：

```js
// 排卦与断法（纯函数，不碰 DOM）。
// 浏览器中经 script 标签获得全局 TRIGRAMS；Node 测试中经 require 获得。
const T = (typeof module !== "undefined" && module.exports)
  ? require("./data/trigrams.js")
  : TRIGRAMS;

// 6/7/8/9 → 0/1（阴/阳）
function toBits(lines) {
  return lines.map((v) => (v === 7 || v === 9 ? 1 : 0));
}

// 动爻下标数组（初爻为 0）
function movingLines(lines) {
  const out = [];
  lines.forEach((v, i) => { if (v === 6 || v === 9) out.push(i); });
  return out;
}

// 之卦卦画：动爻阴阳互变
function zhiBits(lines) {
  return toBits(lines).map((b, i) => (lines[i] === 6 || lines[i] === 9 ? 1 - b : b));
}

// 互卦：二三四爻为下卦，三四五爻为上卦
function huBits(bits) {
  return { lower: [bits[1], bits[2], bits[3]], upper: [bits[2], bits[3], bits[4]] };
}

// 三爻卦符 → 经卦名
function trigramName(bits3) {
  const s = bits3.join("");
  for (const name of Object.keys(T)) {
    if (T[name].symbol === s) return name;
  }
  return null;
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { toBits, movingLines, zhiBits, huBits, trigramName };
}
```

- [ ] **Step 4: 运行确认通过**

Run: `cd yijing && node --test`
Expected: PASS（累计 12 个测试全绿）

- [ ] **Step 5: Commit**

```bash
git add yijing/js/gua.js yijing/tests/gua.test.js
git commit -m "feat(yijing): 排卦几何（本卦/之卦/互卦/动爻）"
```

---

## Task 5: check_hexagrams.py + hexagrams.js 骨架（乾、坤两卦）

**Files:**
- Create: `yijing/check_hexagrams.py`
- Create: `yijing/js/data/hexagrams.js`（先含乾、坤两卦，作为全部批次的格式锚点）

- [ ] **Step 1: 写校验脚本 check_hexagrams.py**

`yijing/check_hexagrams.py`（Python 3 标准库；默认严格要求 64 卦齐备，撰写批次期间可用 `ALLOW_PARTIAL=1` 只校验已有卦）：

```python
#!/usr/bin/env python3
"""check_hexagrams.py — yijing/ 数据完整性验证门。

校验八卦与 64 卦数据：卦数、卦画编码、上下经卦一致性、爻题、用九用六、
白话与问事要点字段齐备。默认严格模式要求 64 卦齐备；
批次撰写期间设 ALLOW_PARTIAL=1 时只校验已有卦的字段结构。
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CATEGORIES = ["综合", "事业", "财运", "感情", "健康", "出行"]


def extract_const(path, name):
    """从 JS 文件中提取 JSON 严格字面量常量（配对括号扫描，跳过字符串）。"""
    text = path.read_text(encoding="utf-8")
    m = re.search(re.escape(name) + r"\s*=\s*", text)
    if not m:
        raise SystemExit(f"FAIL: {path} 中找不到常量 {name}")
    start = m.end()
    opener = text[start]
    closer = "]" if opener == "[" else "}"
    depth = 0
    in_str = False
    esc = False
    i = start
    while i < len(text):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == opener:
                depth += 1
            elif ch == closer:
                depth -= 1
                if depth == 0:
                    return json.loads(text[start:i + 1])
        i += 1
    raise SystemExit(f"FAIL: {path} 中 {name} 字面量未闭合")


def yao_title(i, yang):
    pos = ["初", "二", "三", "四", "五", "上"][i]
    num = "九" if yang else "六"
    return pos + num if i in (0, 5) else num + pos


def main():
    strict = os.environ.get("ALLOW_PARTIAL") != "1"
    trigrams = extract_const(ROOT / "js/data/trigrams.js", "TRIGRAMS")
    hexes = extract_const(ROOT / "js/data/hexagrams.js", "HEXAGRAMS")
    errors = []

    if len(trigrams) != 8:
        errors.append(f"八卦数量 {len(trigrams)} != 8")
    symbols = [t["symbol"] for t in trigrams.values()]
    if len(set(symbols)) != 8 or any(not re.fullmatch(r"[01]{3}", s) for s in symbols):
        errors.append("八卦卦符不唯一或不合法")

    if strict and len(hexes) != 64:
        errors.append(f"卦数 {len(hexes)} != 64")
    if strict and sorted(h["id"] for h in hexes) != list(range(1, 65)):
        errors.append("卦序 id 不是 1..64")

    seen_lines = set()
    for h in hexes:
        hid = h.get("id", "?")
        hname = h.get("name", "?")
        lines = h["lines"]
        if not re.fullmatch(r"[01]{6}", lines):
            errors.append(f"#{hid} {hname}: lines 非法 {lines!r}")
        if lines in seen_lines:
            errors.append(f"#{hid} {hname}: lines 重复 {lines}")
        seen_lines.add(lines)
        if h["lower"] not in trigrams or h["upper"] not in trigrams:
            errors.append(f"#{hid} {hname}: 上下卦名非法")
        else:
            expect = trigrams[h["lower"]]["symbol"] + trigrams[h["upper"]]["symbol"]
            if lines != expect:
                errors.append(f"#{hid} {hname}: lines={lines} 与 {h['lower']}下{h['upper']}上={expect} 不符")
        yaos = h["yaos"]
        if len(yaos) != 6:
            errors.append(f"#{hid} {hname}: 爻数 {len(yaos)} != 6")
        for i, y in enumerate(yaos):
            want = yao_title(i, lines[i] == "1")
            if y["title"] != want:
                errors.append(f"#{hid} {hname}: 第{i+1}爻题 {y['title']} 应为 {want}")
            for f in ("ci", "xiang", "baihua"):
                if not str(y.get(f, "")).strip():
                    errors.append(f"#{hid} {hname} {y.get('title')}: {f} 为空")
        if h["id"] in (1, 2):
            yong = h.get("yong")
            if not yong or not all(str(yong.get(f, "")).strip() for f in ("ci", "xiang", "baihua")):
                errors.append(f"#{hid}: 乾坤须有完整用九/用六")
        elif h.get("yong") is not None:
            errors.append(f"#{hid} {hname}: 非乾坤不得有 yong 字段")
        for f in ("guaci", "tuan", "xiang", "guaciBaihua"):
            if not str(h.get(f, "")).strip():
                errors.append(f"#{hid} {hname}: {f} 为空")
        advice = h.get("advice") or {}
        for c in CATEGORIES:
            if not str(advice.get(c, "")).strip():
                errors.append(f"#{hid} {hname}: advice[{c}] 为空")

    if errors:
        for e in errors:
            print("FAIL:", e)
        print(f"\n共 {len(errors)} 处问题")
        sys.exit(1)
    mode = "strict" if strict else f"partial（{len(hexes)} 卦）"
    print(f"OK: 数据校验通过（{mode}）")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 创建 hexagrams.js 骨架（乾、坤两卦作为格式锚点）**

`yijing/js/data/hexagrams.js`（JSON 严格字面量；后续批次在数组内按 id 升序追加，右括号 `];` 永远是文件数据部分的结尾）：

```js
// 64 卦数据。lines: 六位字符串，初爻在前（自下而上），1 阳 0 阴。
const HEXAGRAMS = [
  {
    "id": 1,
    "name": "乾",
    "fullName": "乾为天",
    "upper": "乾",
    "lower": "乾",
    "lines": "111111",
    "guaci": "乾：元，亨，利，贞。",
    "tuan": "彖曰：大哉乾元，万物资始，乃统天。云行雨施，品物流形。大明终始，六位时成，时乘六龙以御天。乾道变化，各正性命，保合大和，乃利贞。首出庶物，万国咸宁。",
    "xiang": "象曰：天行健，君子以自强不息。",
    "yaos": [
      { "title": "初九", "ci": "潜龙勿用。", "xiang": "象曰：潜龙勿用，阳在下也。", "baihua": "龙潜伏于水下，暂时不宜有所动作。阳气初生而居最下之位，宜韬光养晦、积蓄力量，待时而动。" },
      { "title": "九二", "ci": "见龙在田，利见大人。", "xiang": "象曰：见龙在田，德施普也。", "baihua": "龙出现在田野之上，利于谒见有德有位的大人。才华初显于世，宜寻求贵人赏识与提携。" },
      { "title": "九三", "ci": "君子终日乾乾，夕惕若厉，无咎。", "xiang": "象曰：终日乾乾，反复道也。", "baihua": "君子整日奋发不懈，入夜仍警惕自省如临危境，如此可免咎害。处上下之交、进退之地，戒慎恐惧则无灾。" },
      { "title": "九四", "ci": "或跃在渊，无咎。", "xiang": "象曰：或跃在渊，进无咎也。", "baihua": "龙或腾跃而起、或退处深渊，审度时势而后动，没有咎害。逼近尊位而进退未决，贵在相机而行。" },
      { "title": "九五", "ci": "飞龙在天，利见大人。", "xiang": "象曰：飞龙在天，大人造也。", "baihua": "龙飞腾于九天之上，正是大展宏图之时，利于见大人、成大事。德与位俱隆，为全卦最盛之爻。" },
      { "title": "上九", "ci": "亢龙有悔。", "xiang": "象曰：亢龙有悔，盈不可久也。", "baihua": "龙飞得过高，必将有悔。盛极则衰、盈不可久，知进而不知退者，当以此为戒。" }
    ],
    "yong": { "ci": "用九：见群龙无首，吉。", "xiang": "象曰：用九，天德不可为首也。", "baihua": "六爻皆老阳而动：群龙并现而不以首领自居，吉祥。刚健至极而不居首、不争先，方合天德。" },
    "guaciBaihua": "乾卦象征天，具元始、亨通、利物、贞正四德。天道刚健，运行不息，守正者大为亨通。",
    "advice": {
      "综合": "阳刚正盛，宜奋发进取、乘时而为；然须戒骄戒亢，知进退存亡，方保长久。",
      "事业": "大有为之卦，宜主动担当、积极开创；居上位者须戒独断专行，盛时思衰。",
      "财运": "财路通畅，可积极经营开拓；切忌贪满求盈，盈不可久，见好即收为上。",
      "感情": "阳刚之气过盛，宜以柔相济；主动有余而体贴不足时，当自省收敛。",
      "健康": "阳气充旺，总体健朗；防过劳、防上火，亢则生悔，宜知休养。",
      "出行": "利出行，宜往高远之处；行事宜正大光明，不取巧径。"
    }
  },
  {
    "id": 2,
    "name": "坤",
    "fullName": "坤为地",
    "upper": "坤",
    "lower": "坤",
    "lines": "000000",
    "guaci": "坤：元亨，利牝马之贞。君子有攸往，先迷后得主，利。西南得朋，东北丧朋。安贞吉。",
    "tuan": "彖曰：至哉坤元，万物资生，乃顺承天。坤厚载物，德合无疆。含弘光大，品物咸亨。牝马地类，行地无疆，柔顺利贞。君子攸行，先迷失道，后顺得常。西南得朋，乃与类行；东北丧朋，乃终有庆。安贞之吉，应地无疆。",
    "xiang": "象曰：地势坤，君子以厚德载物。",
    "yaos": [
      { "title": "初六", "ci": "履霜，坚冰至。", "xiang": "象曰：履霜坚冰，阴始凝也。驯致其道，至坚冰也。", "baihua": "脚下踩到霜，便知坚冰将至。阴气开始凝聚，见微而知著，凡事宜早作防备。" },
      { "title": "六二", "ci": "直方大，不习无不利。", "xiang": "象曰：六二之动，直以方也。不习无不利，地道光也。", "baihua": "正直、端方、宏大，纵使不加修习也无所不利。得地道之正，顺其自然则亨通光明。" },
      { "title": "六三", "ci": "含章可贞，或从王事，无成有终。", "xiang": "象曰：含章可贞，以时发也。或从王事，知光大也。", "baihua": "内藏文采而可守正；若随从君王做事，不居其成而得有善终。才华宜含蓄待时，功成而不自居。" },
      { "title": "六四", "ci": "括囊，无咎无誉。", "xiang": "象曰：括囊无咎，慎不害也。", "baihua": "扎紧囊口，谨慎缄默，虽无荣誉亦无咎害。处危疑之地，收敛自守方免其害。" },
      { "title": "六五", "ci": "黄裳，元吉。", "xiang": "象曰：黄裳元吉，文在中也。", "baihua": "黄色的下裳，大为吉祥。居尊位而守谦柔，美德蕴于其中，吉莫大焉。" },
      { "title": "上六", "ci": "龙战于野，其血玄黄。", "xiang": "象曰：龙战于野，其道穷也。", "baihua": "龙在郊野争斗，血色玄黄。阴气盛极而与阳争，其道已穷，两败俱伤，宜早知止。" }
    ],
    "yong": { "ci": "用六：利永贞。", "xiang": "象曰：用六永贞，以大终也。", "baihua": "六爻皆老阴而动：利于永远守持正固。柔顺而不失其正，方能以大德善终。" },
    "guaciBaihua": "坤卦象征地，柔顺厚德，含容万物。宜守正持柔，先迷后得，安于正道则吉。",
    "advice": {
      "综合": "宜柔顺守正、厚德载物；先人后己反致迷，随顺天时方得主。静而能容，吉。",
      "事业": "利辅佐与协作，不宜争先出头；踏实积累、含章待时，终有善成。",
      "财运": "宜稳健守成，不宜投机进取；厚积薄发，利西南（同类）而忌东北（异类）。",
      "感情": "以柔相济、包容为上；先主动恐迷，随顺而行则得主而吉。",
      "健康": "脾胃、腹部当留意；柔顺调养、安贞静养为宜，忌躁动妄为。",
      "出行": "利西南方向；宜结伴随行不宜独行争先，安贞守正则吉。"
    }
  }
];
if (typeof module !== "undefined" && module.exports) module.exports = HEXAGRAMS;
```

- [ ] **Step 3: 运行校验（partial 模式）**

Run: `ALLOW_PARTIAL=1 python3 yijing/check_hexagrams.py`
Expected: `OK: 数据校验通过（partial（2 卦））`

- [ ] **Step 4: Commit**

```bash
git add yijing/check_hexagrams.py yijing/js/data/hexagrams.js
git commit -m "feat(yijing): 数据校验门 + 乾坤两卦格式锚点"
```

---

## Task 6: 数据批次一 —— id 3–16（14 卦）

**Files:**
- Modify: `yijing/js/data/hexagrams.js`

- [ ] **Step 1: 追加 14 卦完整条目**

在 HEXAGRAMS 数组中按 id 升序追加：3 屯（水雷屯 "100010"）、4 蒙（山水蒙 "010001"）、5 需（水天需 "111010"）、6 讼（天水讼 "010111"）、7 师（地水师 "010000"）、8 比（水地比 "000010"）、9 小畜（风天小畜 "111011"）、10 履（天泽履 "110111"）、11 泰（地天泰 "111000"）、12 否（天地否 "000111"）、13 同人（天火同人 "101111"）、14 大有（火天大有 "111101"）、15 谦（地山谦 "001000"）、16 豫（雷地豫 "000100"）。

每卦完整字段：id/name/fullName/upper/lower/lines/guaci/tuan/xiang/yaos（6 爻，通行本爻辞+小象+自撰白话）/yong:null/guaciBaihua/advice 六类。经文用通行本《周易》原文；`yong` 一律为 `null`。格式仿乾、坤锚点条目（JSON 严格：键带引号、无注释、无尾逗号）。`lines` 必须与（下经卦 symbol + 上经卦 symbol）一致，否则校验门会报错。

- [ ] **Step 2: 运行校验**

Run: `ALLOW_PARTIAL=1 python3 yijing/check_hexagrams.py`
Expected: `OK: 数据校验通过（partial（16 卦））`

- [ ] **Step 3: Commit**

```bash
git add yijing/js/data/hexagrams.js
git commit -m "feat(yijing): 数据批次一——id 3–16（14 卦）"
```

---

## Task 7: 数据批次二 —— id 17–32（16 卦）

**Files:**
- Modify: `yijing/js/data/hexagrams.js`

- [ ] **Step 1: 追加 16 卦完整条目**

17 随（泽雷随 "100110"）、18 蛊（山风蛊 "011001"）、19 临（地泽临 "110000"）、20 观（风地观 "000011"）、21 噬嗑（火雷噬嗑 "100101"）、22 贲（山火贲 "101001"）、23 剥（山地剥 "000001"）、24 复（地雷复 "100000"）、25 无妄（天雷无妄 "100111"）、26 大畜（山天大畜 "111001"）、27 颐（山雷颐 "100001"）、28 大过（泽风大过 "011110"）、29 坎（坎为水 "010010"，卦辞含"习坎"）、30 离（离为火 "101101"）、31 咸（泽山咸 "001110"）、32 恒（雷风恒 "011100"）。

字段要求同 Task 6。`yong` 一律 `null`。

- [ ] **Step 2: 运行校验**

Run: `ALLOW_PARTIAL=1 python3 yijing/check_hexagrams.py`
Expected: `OK: 数据校验通过（partial（32 卦））`

- [ ] **Step 3: Commit**

```bash
git add yijing/js/data/hexagrams.js
git commit -m "feat(yijing): 数据批次二——id 17–32（16 卦）"
```

---

## Task 8: 数据批次三 —— id 33–48（16 卦）

**Files:**
- Modify: `yijing/js/data/hexagrams.js`

- [ ] **Step 1: 追加 16 卦完整条目**

33 遁（天山遁 "001111"）、34 大壮（雷天大壮 "111100"）、35 晋（火地晋 "000101"）、36 明夷（地火明夷 "101000"）、37 家人（风火家人 "101011"）、38 睽（火泽睽 "110101"）、39 蹇（水山蹇 "001010"）、40 解（雷水解 "010100"）、41 损（山泽损 "110001"）、42 益（风雷益 "100011"）、43 夬（泽天夬 "111110"）、44 姤（天风姤 "011111"）、45 萃（泽地萃 "000110"）、46 升（地风升 "011000"）、47 困（泽水困 "010110"）、48 井（水风井 "011010"）。

字段要求同 Task 6。`yong` 一律 `null`。

- [ ] **Step 2: 运行校验**

Run: `ALLOW_PARTIAL=1 python3 yijing/check_hexagrams.py`
Expected: `OK: 数据校验通过（partial（48 卦））`

- [ ] **Step 3: Commit**

```bash
git add yijing/js/data/hexagrams.js
git commit -m "feat(yijing): 数据批次三——id 33–48（16 卦）"
```

---

## Task 9: 数据批次四 —— id 49–64（16 卦）+ 严格校验全绿

**Files:**
- Modify: `yijing/js/data/hexagrams.js`

- [ ] **Step 1: 追加 16 卦完整条目**

49 革（泽火革 "101110"）、50 鼎（火风鼎 "011101"）、51 震（震为雷 "100100"）、52 艮（艮为山 "001001"）、53 渐（风山渐 "001011"）、54 归妹（雷泽归妹 "110100"）、55 丰（雷火丰 "101100"）、56 旅（火山旅 "001101"）、57 巽（巽为风 "011011"）、58 兑（兑为泽 "110110"）、59 涣（风水涣 "010011"）、60 节（水泽节 "110010"）、61 中孚（风泽中孚 "110011"）、62 小过（雷山小过 "001100"）、63 既济（水火既济 "101010"）、64 未济（火水未济 "010101"）。

字段要求同 Task 6。`yong` 一律 `null`。

- [ ] **Step 2: 严格模式校验 64 卦全绿**

Run: `python3 yijing/check_hexagrams.py`
Expected: `OK: 数据校验通过（strict）`

- [ ] **Step 3: Commit**

```bash
git add yijing/js/data/hexagrams.js
git commit -m "feat(yijing): 数据批次四——id 49–64，64 卦齐备校验全绿"
```

---

## Task 10: 断法 gua.js（下）—— findHexagram 与 duanCi（朱熹断法）

**Files:**
- Modify: `yijing/js/gua.js`（追加两函数并更新导出）
- Test: `yijing/tests/gua-duan.test.js`

- [ ] **Step 1: 写失败测试**

`yijing/tests/gua-duan.test.js`：

```js
const test = require("node:test");
const assert = require("node:assert/strict");
const HEXAGRAMS = require("../js/data/hexagrams.js");
const gua = require("../js/gua.js");

test("findHexagram: 111111 乾、000000 坤、100010 屯", () => {
  assert.equal(gua.findHexagram([1,1,1,1,1,1], HEXAGRAMS).id, 1);
  assert.equal(gua.findHexagram([0,0,0,0,0,0], HEXAGRAMS).id, 2);
  assert.equal(gua.findHexagram([1,0,0,0,1,0], HEXAGRAMS).name, "屯");
});

test("断法：六爻安静取本卦卦辞，无之卦", () => {
  const r = gua.duanCi([7,7,7,7,7,7], HEXAGRAMS);
  assert.deepEqual(r.moving, []);
  assert.equal(r.zhi, null);
  assert.equal(r.ben.name, "乾");
  assert.equal(r.entries.length, 1);
  assert.equal(r.entries[0].kind, "guaci");
  assert.equal(r.entries[0].primary, true);
  assert.equal(r.entries[0].source, "本卦乾为天·卦辞");
  assert.ok(r.entries[0].tuan.includes("大哉乾元"));
  assert.ok(r.entries[0].xiang.includes("天行健"));
});

test("断法：一爻动取本卦动爻辞", () => {
  const r = gua.duanCi([9,7,7,7,7,7], HEXAGRAMS);
  assert.equal(r.entries[0].kind, "yao");
  assert.equal(r.entries[0].source, "本卦乾为天·初九");
  assert.match(r.entries[0].ci, /潜龙勿用/);
  assert.ok(r.entries[0].baihua);
});

test("断法：两爻动以上爻为主", () => {
  const r = gua.duanCi([9,7,7,9,7,7], HEXAGRAMS);
  assert.equal(r.entries[0].source, "本卦乾为天·九四");
  assert.equal(r.entries[0].primary, true);
  assert.equal(r.entries[1].source, "本卦乾为天·初九");
  assert.equal(r.entries[1].primary, false);
});

test("断法：三爻动参本变卦辞，本卦为主", () => {
  const r = gua.duanCi([9,9,9,7,7,7], HEXAGRAMS);
  assert.equal(r.zhi.lines, "000111"); // 天地否
  assert.equal(r.entries[0].kind, "guaci");
  assert.equal(r.entries[0].source, "本卦乾为天·卦辞");
  assert.equal(r.entries[0].primary, true);
  assert.equal(r.entries[1].source, "之卦天地否·卦辞");
  assert.equal(r.entries[1].primary, false);
});

test("断法：四爻动取之卦两静爻，以下爻为主", () => {
  const r = gua.duanCi([9,9,7,9,9,7], HEXAGRAMS);
  assert.equal(r.zhi.lines, "001001"); // 艮为山
  assert.deepEqual(r.entries.map((e) => e.primary), [true, false]);
  assert.equal(r.entries[0].source, `之卦${r.zhi.fullName}·${r.zhi.yaos[2].title}`);
  assert.equal(r.entries[1].source, `之卦${r.zhi.fullName}·${r.zhi.yaos[5].title}`);
});

test("断法：五爻动取之卦静爻", () => {
  const r = gua.duanCi([9,9,9,9,9,7], HEXAGRAMS);
  assert.equal(r.zhi.lines, "000001"); // 山地剥
  assert.equal(r.entries.length, 1);
  assert.equal(r.entries[0].source, `之卦${r.zhi.fullName}·${r.zhi.yaos[5].title}`);
});

test("断法：乾六爻皆动取用九", () => {
  const r = gua.duanCi([9,9,9,9,9,9], HEXAGRAMS);
  assert.equal(r.zhi.name, "坤");
  assert.equal(r.entries[0].kind, "yong");
  assert.equal(r.entries[0].source, "乾为天·用九");
  assert.match(r.entries[0].ci, /群龙无首/);
});

test("断法：坤六爻皆动取用六", () => {
  const r = gua.duanCi([6,6,6,6,6,6], HEXAGRAMS);
  assert.equal(r.zhi.name, "乾");
  assert.equal(r.entries[0].kind, "yong");
  assert.equal(r.entries[0].source, "坤为地·用六");
  assert.match(r.entries[0].ci, /利永贞/);
});

test("断法：他卦六爻皆动取之卦卦辞", () => {
  const r = gua.duanCi([9,6,6,6,9,6], HEXAGRAMS); // 屯全动
  assert.equal(r.zhi.name, "鼎");
  assert.equal(r.entries[0].kind, "guaci");
  assert.equal(r.entries[0].primary, true);
  assert.match(r.rule, /以之卦卦辞断/);
});
```

- [ ] **Step 2: 运行确认失败**

Run: `cd yijing && node --test`
Expected: FAIL — `gua.findHexagram is not a function`

- [ ] **Step 3: 实现（在 gua.js 的 `trigramName` 之后、导出之前插入）**

```js
// 六位卦画 → 卦对象
function findHexagram(bits6, hexagrams) {
  const s = bits6.join("");
  return hexagrams.find((h) => h.lines === s) || null;
}

// 朱熹《易学启蒙》断法：依动爻数取断辞。
function duanCi(lines, hexagrams) {
  const bits = toBits(lines);
  const moving = movingLines(lines);
  const ben = findHexagram(bits, hexagrams);
  const zbits = zhiBits(lines);
  const zhi = moving.length ? findHexagram(zbits, hexagrams) : null;

  const guaciEntry = (h, primary, tag) => ({
    kind: "guaci",
    source: `${tag}${h.fullName}·卦辞`,
    ci: h.guaci,
    tuan: h.tuan,
    xiang: h.xiang,
    baihua: h.guaciBaihua,
    primary,
  });
  const yaoEntry = (h, i, primary, tag) => ({
    kind: "yao",
    source: `${tag}${h.fullName}·${h.yaos[i].title}`,
    ci: h.yaos[i].ci,
    xiang: h.yaos[i].xiang,
    baihua: h.yaos[i].baihua,
    primary,
  });

  let rule, entries;
  const still = [0, 1, 2, 3, 4, 5].filter((i) => !moving.includes(i));
  switch (moving.length) {
    case 0:
      rule = "六爻安静，以本卦卦辞断";
      entries = [guaciEntry(ben, true, "本卦")];
      break;
    case 1:
      rule = "一爻动，以本卦动爻辞断";
      entries = [yaoEntry(ben, moving[0], true, "本卦")];
      break;
    case 2:
      rule = "两爻动，取两动爻辞，以上爻为主";
      entries = [
        yaoEntry(ben, moving[1], true, "本卦"),
        yaoEntry(ben, moving[0], false, "本卦"),
      ];
      break;
    case 3:
      rule = "三爻动，参本卦与之卦卦辞，以本卦为主";
      entries = [guaciEntry(ben, true, "本卦"), guaciEntry(zhi, false, "之卦")];
      break;
    case 4:
      rule = "四爻动，以之卦两静爻辞断，以下爻为主";
      entries = [
        yaoEntry(zhi, still[0], true, "之卦"),
        yaoEntry(zhi, still[1], false, "之卦"),
      ];
      break;
    case 5:
      rule = "五爻动，以之卦静爻辞断";
      entries = [yaoEntry(zhi, still[0], true, "之卦")];
      break;
    default:
      if (ben.id === 1 || ben.id === 2) {
        rule = ben.id === 1 ? "乾六爻皆动，取用九" : "坤六爻皆动，取用六";
        entries = [{
          kind: "yong",
          source: `${ben.fullName}·用${ben.id === 1 ? "九" : "六"}`,
          ci: ben.yong.ci,
          xiang: ben.yong.xiang,
          baihua: ben.yong.baihua,
          primary: true,
        }];
      } else {
        rule = "六爻皆动，以之卦卦辞断";
        entries = [guaciEntry(zhi, true, "之卦")];
      }
  }
  return { rule, ben, zhi, moving, bits, zbits, entries };
}
```

导出行更新为：

```js
if (typeof module !== "undefined" && module.exports) {
  module.exports = { toBits, movingLines, zhiBits, huBits, trigramName, findHexagram, duanCi };
}
```

- [ ] **Step 4: 运行确认通过**

Run: `cd yijing && node --test`
Expected: PASS（累计 22 个测试全绿）

- [ ] **Step 5: Commit**

```bash
git add yijing/js/gua.js yijing/tests/gua-duan.test.js
git commit -m "feat(yijing): 朱熹断法——findHexagram 与 duanCi"
```

---

## Task 11: 页面骨架 index.html 与样式 css/yijing.css

**Files:**
- Create: `yijing/index.html`
- Create: `yijing/css/yijing.css`

- [ ] **Step 1: index.html 完整代码**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>易占 · 易经占卜</title>
<meta name="description" content="据《周易》古法起卦断卦：铜钱摇卦，排本卦之卦互卦，卦辞爻辞彖象原文与白话今译。">
<link rel="stylesheet" href="css/yijing.css">
</head>
<body>
<header class="site-header">
  <h1 class="seal">易占</h1>
  <p class="subtitle">究天人之际，通古今之变 —— 据《周易》经传而断</p>
</header>

<main>
  <section id="screen-ask" class="screen">
    <h2>问卦</h2>
    <p class="hint">心有所疑，默想所问之事，然后摇卦。诚则灵，渎则不告。</p>
    <textarea id="question" rows="3" maxlength="100" placeholder="所问何事？（可不填，心中默念即可）"></textarea>
    <fieldset class="categories">
      <legend>问事类别</legend>
      <label><input type="radio" name="category" value="综合" checked>综合</label>
      <label><input type="radio" name="category" value="事业">事业</label>
      <label><input type="radio" name="category" value="财运">财运</label>
      <label><input type="radio" name="category" value="感情">感情</label>
      <label><input type="radio" name="category" value="健康">健康</label>
      <label><input type="radio" name="category" value="出行">出行</label>
    </fieldset>
    <button id="btn-start" class="primary">净手摇卦</button>
    <button id="btn-history" class="link">查看占例记录</button>
  </section>

  <section id="screen-cast" class="screen hidden">
    <h2>摇卦</h2>
    <p id="cast-progress" class="hint"></p>
    <div id="coins" class="coins">
      <div class="coin"></div>
      <div class="coin"></div>
      <div class="coin"></div>
    </div>
    <div id="cast-lines" class="cast-lines"></div>
  </section>

  <section id="screen-result" class="screen hidden">
    <h2>卦成</h2>
    <div id="result-summary"></div>
    <div id="result-guas" class="guas"></div>
    <div id="result-duan"></div>
    <div class="actions">
      <button id="btn-again" class="primary">再占一卦</button>
      <button id="btn-back" class="link">返回问卦</button>
    </div>
  </section>

  <aside id="history-panel" class="hidden">
    <div class="panel-head">
      <h2>占例记录</h2>
      <button id="btn-clear-history" class="link">清空</button>
      <button id="btn-close-history" class="link">关闭</button>
    </div>
    <ul id="history-list"></ul>
  </aside>
</main>

<footer class="site-footer">
  <p>经文据通行本《周易》；断法依朱熹《易学启蒙》。占断仅供参考，事在人为。</p>
  <p><a href="/">返回 vlsc.net 首页</a></p>
</footer>

<script src="js/data/trigrams.js"></script>
<script src="js/data/hexagrams.js"></script>
<script src="js/cast.js"></script>
<script src="js/gua.js"></script>
<script src="js/app.js"></script>
</body>
</html>
```

- [ ] **Step 2: css/yijing.css 完整代码**

```css
:root {
  --paper: #f5f0e6;
  --ink: #2b2622;
  --cinnabar: #9e2b25;
  --faint: #8a8175;
  --rule: #d8d0c0;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  min-height: 100vh;
  background: var(--paper);
  color: var(--ink);
  font-family: "Songti SC", "STSong", "SimSun", serif;
  line-height: 1.8;
}

.hidden { display: none; }

.site-header {
  text-align: center;
  padding: 2.5rem 1rem 1rem;
  border-bottom: 1px solid var(--rule);
}

.seal {
  display: inline-block;
  margin: 0;
  padding: 0.35rem 0.9rem;
  font-size: 2.2rem;
  letter-spacing: 0.35em;
  color: #fff;
  background: var(--cinnabar);
  border-radius: 4px;
  box-shadow: 2px 2px 0 rgba(0, 0, 0, 0.15);
}

.subtitle { margin: 0.6rem 0 0; color: var(--faint); font-size: 0.95rem; letter-spacing: 0.1em; }

main { max-width: 720px; margin: 0 auto; padding: 1.5rem 1rem 3rem; }

.screen h2 {
  font-size: 1.4rem;
  letter-spacing: 0.2em;
  border-left: 4px solid var(--cinnabar);
  padding-left: 0.6rem;
  margin: 1.5rem 0 0.8rem;
}

.hint { color: var(--faint); font-size: 0.9rem; }

textarea {
  width: 100%;
  padding: 0.7rem;
  font: inherit;
  color: var(--ink);
  background: #fffdf8;
  border: 1px solid var(--rule);
  border-radius: 4px;
  resize: vertical;
}

.categories { border: 1px solid var(--rule); border-radius: 4px; margin: 1rem 0; padding: 0.6rem 1rem; }
.categories legend { color: var(--faint); font-size: 0.85rem; padding: 0 0.4rem; }
.categories label { margin-right: 1.1rem; white-space: nowrap; }

button { font: inherit; cursor: pointer; }

.primary {
  display: block;
  width: 100%;
  padding: 0.8rem;
  font-size: 1.1rem;
  letter-spacing: 0.3em;
  color: #fff;
  background: var(--cinnabar);
  border: none;
  border-radius: 4px;
}
.primary:hover { filter: brightness(1.1); }

.link {
  background: none;
  border: none;
  color: var(--cinnabar);
  text-decoration: underline;
  padding: 0.4rem;
}

.actions { display: flex; gap: 1rem; align-items: center; margin-top: 1.5rem; }
.actions .primary { flex: 1; }

/* 摇卦：铜钱 */
.coins { display: flex; justify-content: center; gap: 1rem; margin: 1.2rem 0; perspective: 600px; }

.coin {
  position: relative;
  width: 64px; height: 64px;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 30%, #d9b45c, #a87f2a);
  border: 2px solid #7c5c1c;
}
.coin::after {
  content: "";
  position: absolute; top: 50%; left: 50%;
  width: 18px; height: 18px;
  transform: translate(-50%, -50%);
  background: var(--paper);
  border: 1px solid #7c5c1c;
}
.coin.head::before {
  content: "背";  /* head = 阳面（无字之背） */
  position: absolute; top: 50%; left: 50%;
  transform: translate(-50%, -50%) translateY(-22px);
  font-size: 0.8rem; color: #5c430f;
}
.coins.tossing .coin { animation: toss 0.9s ease-in-out; }
@keyframes toss {
  0% { transform: rotateX(0deg) translateY(0); }
  50% { transform: rotateX(540deg) translateY(-40px); }
  100% { transform: rotateX(1080deg) translateY(0); }
}

/* 摇卦逐爻与卦画 */
.cast-lines, .gua-lines { display: flex; flex-direction: column-reverse; align-items: center; gap: 0.45rem; margin: 1rem 0; }
.cast-lines .cast-row { display: flex; align-items: center; gap: 0.8rem; }
.cast-row .face { width: 3rem; color: var(--faint); font-size: 0.85rem; text-align: right; }

.yao { position: relative; display: flex; gap: 1.6rem; width: 150px; height: 13px; }
.yao span { flex: 1; }
.yao.yang span { background: var(--ink); }
.yao.yin span:first-child, .yao.yin span:last-child { background: var(--ink); }
.yao.yin span:nth-child(2) { flex: 0 0 1.6rem; background: transparent; }
.yao .mark {
  position: absolute; right: -1.6rem; top: -0.25rem;
  color: var(--cinnabar); font-size: 0.95rem;
}

/* 结果区 */
#result-summary { background: #fffdf8; border: 1px solid var(--rule); border-radius: 4px; padding: 0.8rem 1rem; }
#result-summary .rule { color: var(--cinnabar); }

.guas { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin: 1.2rem 0; }
.gua-card { text-align: center; border: 1px solid var(--rule); border-radius: 4px; padding: 0.8rem 0.4rem; background: #fffdf8; }
.gua-card h3 { margin: 0.2rem 0; font-size: 1.05rem; }
.gua-card .role { color: var(--faint); font-size: 0.8rem; letter-spacing: 0.2em; }
.gua-card .trigrams { color: var(--faint); font-size: 0.8rem; }

.duan-entry { border-bottom: 1px dashed var(--rule); padding: 0.9rem 0; }
.duan-entry .source { font-weight: bold; color: var(--cinnabar); }
.duan-entry .ci { font-size: 1.1rem; margin: 0.3rem 0; }
.duan-entry .ref { color: var(--faint); font-size: 0.9rem; border-left: 3px solid var(--rule); padding-left: 0.6rem; margin: 0.3rem 0; }
.duan-entry .baihua { margin: 0.3rem 0; }
.duan-entry.secondary { opacity: 0.75; }

.advice { background: #fffdf8; border: 1px solid var(--rule); border-radius: 4px; padding: 0.8rem 1rem; margin-top: 1rem; }
.advice h3 { margin: 0 0 0.4rem; font-size: 1rem; color: var(--cinnabar); }

/* 历史面板 */
#history-panel { position: fixed; inset: 0; z-index: 10; background: rgba(43, 38, 34, 0.45); padding: 2rem 1rem; overflow-y: auto; }
.panel-head { display: flex; align-items: center; gap: 0.8rem; max-width: 640px; margin: 0 auto 0.8rem; }
.panel-head h2 { flex: 1; margin: 0; color: var(--paper); }
#history-list { max-width: 640px; margin: 0 auto; padding: 0; list-style: none; }
#history-list li { background: var(--paper); border-radius: 4px; padding: 0.7rem 1rem; margin-bottom: 0.6rem; font-size: 0.9rem; }
#history-list .meta { color: var(--faint); font-size: 0.8rem; }

.site-footer { text-align: center; color: var(--faint); font-size: 0.85rem; padding: 1.5rem 1rem 2.5rem; border-top: 1px solid var(--rule); }
.site-footer a { color: var(--cinnabar); }

@media (max-width: 600px) {
  .guas { grid-template-columns: 1fr; }
  .coin { width: 52px; height: 52px; }
}
```

- [ ] **Step 3: Commit**

```bash
git add yijing/index.html yijing/css/yijing.css
git commit -m "feat(yijing): 页面骨架与水墨宣纸样式"
```

---

## Task 12: 应用逻辑 js/app.js

**Files:**
- Create: `yijing/js/app.js`

- [ ] **Step 1: app.js 完整代码**

```js
/* global TRIGRAMS, HEXAGRAMS, castLine, castGua, toBits, movingLines, zhiBits, huBits, trigramName, findHexagram, duanCi */

const HISTORY_KEY = "yijing-history";
const HISTORY_MAX = 50;
const TOSS_MS = 900;

const LINE_NAMES = { 6: "老阴（动）", 7: "少阳", 8: "少阴", 9: "老阳（动）" };
const YAO_MARK = { 6: "×", 9: "○" };

const state = { question: "", category: "综合", lines: [] };

function $(id) { return document.getElementById(id); }

function showScreen(name) {
  for (const s of ["ask", "cast", "result"]) {
    $("screen-" + s).classList.toggle("hidden", s !== name);
  }
}

function startCast() {
  state.question = $("question").value.trim();
  const checked = document.querySelector('input[name="category"]:checked');
  state.category = checked ? checked.value : "综合";
  state.lines = [];
  showScreen("cast");
  $("cast-lines").innerHTML = "";
  tossStep(0);
}

// 三枚铜钱的正反面：阳面（值 3）/阴面（值 2），和 = 6 + 阳面数。
// 按爻值反推阳面枚数并洗牌供展示；传统以无字之背为阳、有字之面为阴。
function coinFaces(value) {
  const heads = value - 6;
  const faces = [];
  for (let i = 0; i < 3; i++) faces.push(i < heads);
  for (let i = faces.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    const t = faces[i]; faces[i] = faces[j]; faces[j] = t;
  }
  return faces;
}

function tossStep(i) {
  if (i >= 6) { renderResult(); return; }
  $("cast-progress").textContent = `第 ${i + 1} 爻（自下而上，共六爻）`;
  const coins = $("coins");
  coins.classList.add("tossing");
  setTimeout(() => {
    coins.classList.remove("tossing");
    const value = castLine(Math.random);
    state.lines.push(value);
    const faces = coinFaces(value);
    for (let c = 0; c < 3; c++) {
      coins.children[c].classList.toggle("head", faces[c]); // head = 阳面（背）
    }
    appendCastRow(i, value, faces);
    tossStep(i + 1);
  }, TOSS_MS);
}

function appendCastRow(i, value, faces) {
  const row = document.createElement("div");
  row.className = "cast-row";
  const face = document.createElement("span");
  face.className = "face";
  face.textContent = faces.map((f) => (f ? "字" : "背")).join("");
  const yao = document.createElement("div");
  yao.appendChild(buildYao(value === 7 || value === 9 ? 1 : 0, value === 6 || value === 9));
  const name = document.createElement("span");
  name.className = "face";
  name.style.textAlign = "left";
  name.textContent = LINE_NAMES[value];
  row.append(face, yao, name);
  $("cast-lines").appendChild(row); // column-reverse：后追加的显示在上方
}

function buildYao(bit, moving) {
  const yao = document.createElement("div");
  yao.className = "yao " + (bit ? "yang" : "yin");
  yao.append(document.createElement("span"), document.createElement("span"), document.createElement("span"));
  if (moving) {
    const mark = document.createElement("span");
    mark.className = "mark";
    mark.textContent = YAO_MARK[bit ? 9 : 6];
    yao.appendChild(mark);
  }
  return yao;
}

function renderResult() {
  const r = duanCi(state.lines, HEXAGRAMS);
  const hu = huBits(r.bits);
  const huHex = findHexagram(hu.lower.concat(hu.upper), HEXAGRAMS);

  // 摘要
  const movingNames = r.moving.map((i) => r.ben.yaos[i] ? r.ben.yaos[i].title : `第${i + 1}爻`).join("、") || "无";
  $("result-summary").innerHTML =
    `<p>所问：${escapeHtml(state.question || "心中默念")}（${state.category}）</p>` +
    `<p>得 <strong>${r.ben ? r.ben.fullName : "未知卦"}</strong>` +
    (r.zhi ? ` 之 <strong>${r.zhi.fullName}</strong>` : "") +
    `，动爻：${movingNames}</p>` +
    `<p class="rule">断法：${r.rule}</p>`;

  // 三卦排盘
  const guas = $("result-guas");
  guas.innerHTML = "";
  guas.appendChild(guaCard("本卦", r.ben, r.moving));
  guas.appendChild(guaCard("之卦", r.zhi, []));
  guas.appendChild(guaCard("互卦", huHex, []));

  // 断辞
  const duan = $("result-duan");
  duan.innerHTML = "";
  for (const e of r.entries) duan.appendChild(entryBlock(e));

  const advice = document.createElement("div");
  advice.className = "advice";
  const tip = r.ben && r.ben.advice ? r.ben.advice[state.category] : "经文数据缺失";
  advice.innerHTML = `<h3>问「${state.category}」要点</h3><p>${escapeHtml(tip || "经文数据缺失")}</p>` +
    `<h3>综合断语</h3><p>${escapeHtml(buildSummary(r))}</p>`;
  duan.appendChild(advice);

  saveRecord(r);
  showScreen("result");
}

function buildSummary(r) {
  const q = state.question || "所问之事";
  const ben = r.ben ? r.ben.name : "?";
  const zhi = r.zhi ? `，变而为${r.zhi.name}` : "";
  const primary = r.entries[0];
  return `${q}，得${ben}卦${zhi}。${r.rule}。${primary ? primary.baihua : "经文数据缺失。"}`;
}

function guaCard(role, hex, moving) {
  const card = document.createElement("div");
  card.className = "gua-card";
  const roleEl = document.createElement("div");
  roleEl.className = "role";
  roleEl.textContent = role;
  card.appendChild(roleEl);
  if (!hex) {
    const none = document.createElement("h3");
    none.textContent = "—";
    card.appendChild(none);
    return card;
  }
  const name = document.createElement("h3");
  name.textContent = hex.fullName;
  card.appendChild(name);
  const lines = document.createElement("div");
  lines.className = "gua-lines";
  const bits = hex.lines.split("").map(Number);
  for (let i = 0; i < 6; i++) lines.appendChild(buildYao(bits[i], moving.includes(i)));
  card.appendChild(lines);
  const tri = document.createElement("div");
  tri.className = "trigrams";
  const lowerName = hex.lines.slice(0, 3).split("").map(Number);
  const upperName = hex.lines.slice(3).split("").map(Number);
  const lowerT = trigramName(lowerName);
  const upperT = trigramName(upperName);
  tri.textContent = `${lowerT}${TRIGRAMS[lowerT].nature}下 · ${upperT}${TRIGRAMS[upperT].nature}上`;
  card.appendChild(tri);
  return card;
}

function entryBlock(e) {
  const div = document.createElement("div");
  div.className = "duan-entry" + (e.primary ? "" : " secondary");
  const source = document.createElement("div");
  source.className = "source";
  source.textContent = e.source + (e.primary ? "（主）" : "（参）");
  div.appendChild(source);
  const ci = document.createElement("p");
  ci.className = "ci";
  ci.textContent = e.ci || "经文数据缺失";
  div.appendChild(ci);
  for (const k of ["tuan", "xiang"]) {
    if (e[k]) {
      const ref = document.createElement("p");
      ref.className = "ref";
      ref.textContent = e[k];
      div.appendChild(ref);
    }
  }
  const bh = document.createElement("p");
  bh.className = "baihua";
  bh.textContent = e.baihua || "经文数据缺失";
  div.appendChild(bh);
  return div;
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
```

历史记录与事件绑定（接上文，同一文件末尾）：

```js
// —— 占例记录（localStorage，静默降级）——
function loadHistory() {
  try {
    return JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
  } catch (e) { return []; }
}

function saveRecord(r) {
  try {
    const list = loadHistory();
    list.unshift({
      time: new Date().toISOString(),
      question: state.question,
      category: state.category,
      lines: state.lines,
      benId: r.ben ? r.ben.id : null,
      benName: r.ben ? r.ben.fullName : null,
      zhiId: r.zhi ? r.zhi.id : null,
      zhiName: r.zhi ? r.zhi.fullName : null,
      moving: r.moving,
    });
    localStorage.setItem(HISTORY_KEY, JSON.stringify(list.slice(0, HISTORY_MAX)));
  } catch (e) { /* 隐私模式等场景静默跳过 */ }
}

function renderHistory() {
  const ul = $("history-list");
  ul.innerHTML = "";
  const list = loadHistory();
  if (!list.length) {
    const li = document.createElement("li");
    li.textContent = "暂无占例。";
    ul.appendChild(li);
    return;
  }
  for (const rec of list) {
    const li = document.createElement("li");
    const t = new Date(rec.time);
    const movingText = rec.moving.length
      ? rec.moving.map((i) => ["初","二","三","四","五","上"][i]).join("、") + "爻动"
      : "六爻安静";
    li.innerHTML = `<div>${escapeHtml(rec.benName || "?")}${rec.zhiName ? " 之 " + escapeHtml(rec.zhiName) : ""} · ${movingText}</div>` +
      `<div class="meta">${t.toLocaleString("zh-CN")} · ${escapeHtml(rec.category)} · ${escapeHtml(rec.question || "心中默念")}</div>`;
    ul.appendChild(li);
  }
}

function clearHistory() {
  try { localStorage.removeItem(HISTORY_KEY); } catch (e) { /* 忽略 */ }
  renderHistory();
}

document.addEventListener("DOMContentLoaded", () => {
  $("btn-start").addEventListener("click", startCast);
  $("btn-again").addEventListener("click", startCast);
  $("btn-back").addEventListener("click", () => showScreen("ask"));
  $("btn-history").addEventListener("click", () => { renderHistory(); $("history-panel").classList.remove("hidden"); });
  $("btn-close-history").addEventListener("click", () => $("history-panel").classList.add("hidden"));
  $("btn-clear-history").addEventListener("click", clearHistory);
});
```

- [ ] **Step 2: Commit**

```bash
git add yijing/js/app.js
git commit -m "feat(yijing): 应用逻辑——摇卦动画、排卦断卦渲染、占例存档"
```

---

## Task 13: 集成验证

**Files:** 无新文件（验证门）

- [ ] **Step 1: Node 测试全绿**

Run: `cd yijing && node --test`
Expected: 全部 PASS（trigrams 3 + cast 4 + gua 5 + gua-duan 10 = 22 个）

- [ ] **Step 2: 数据校验门严格模式通过**

Run: `python3 yijing/check_hexagrams.py`
Expected: `OK: 数据校验通过（strict）`

- [ ] **Step 3: 本地静态服务冒烟**

```bash
cd yijing && python3 -m http.server 8765 &
SERVER_PID=$!
sleep 1
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8765/            # 预期 200
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8765/css/yijing.css # 预期 200
curl -s http://localhost:8765/js/data/hexagrams.js | head -c 120            # 预期见 "const HEXAGRAMS = [" 与乾卦条目
kill $SERVER_PID
```

浏览器手动验证清单（无法自动化，人工过一遍）：打开 `http://localhost:8765/`，填问题选类别→摇卦动画六次逐爻出现→排卦三栏（本卦/之卦/互卦）卦画正确、动爻有 ○/× 标记→断卦区有断法规则、原文、彖象引用、白话、问事要点与综合断语→刷新页面后"查看占例记录"能看到刚才一卦→清空按钮生效。

- [ ] **Step 4: 确认部署排除清单**

Run: `grep -n "exclude" yijing/deploy.sh`
Expected: 排除 `check_hexagrams.py`、`deploy.sh`、`tests`、`.DS_Store` 四项。

- [ ] **Step 5: Commit（如有验证期间的修补）**

```bash
git add -A yijing
git commit -m "test(yijing): 集成验证收尾"
```

---

## 完成定义（Definition of Done）

1. `cd yijing && node --test` 22 个测试全绿；
2. `python3 yijing/check_hexagrams.py` 严格模式 OK（64 卦、386 条爻辞级断言全过）；
3. 浏览器手动清单全部通过；
4. `git log --oneline` 可见按任务的中文 commit 序列；
5. 部署本身不在本计划内执行（`yijing/deploy.sh` 由用户择机运行）。
