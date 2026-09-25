const test = require("node:test");
const assert = require("node:assert/strict");
const HEXAGRAMS = require("../js/data/hexagrams.js");
const gua = require("../js/gua.js");
const { castGua } = require("../js/cast.js");

// 全部 4^6 = 4096 种起卦结果都必须能排出卦、取到断辞
test("穷举 4096 种起卦结果：排卦与断辞均完备", () => {
  const vals = [6, 7, 8, 9];
  let n = 0;
  for (const a of vals) for (const b of vals) for (const c of vals)
  for (const d of vals) for (const e of vals) for (const f of vals) {
    const lines = [a, b, c, d, e, f];
    const r = gua.duanCi(lines, HEXAGRAMS);
    n++;
    assert.ok(r.ben, `本卦缺失 ${lines}`);
    assert.ok(r.rule, `断法说明缺失 ${lines}`);
    assert.ok(r.entries.length >= 1, `断辞为空 ${lines}`);
    for (const en of r.entries) {
      assert.ok(en.source && en.ci && en.baihua, `断辞字段缺失 ${lines} ${JSON.stringify(en.source)}`);
    }
    if (r.moving.length) {
      assert.ok(r.zhi, `有动爻却无之卦 ${lines}`);
    } else {
      assert.equal(r.zhi, null);
    }
    const hu = gua.huBits(r.bits);
    assert.ok(gua.findHexagram(hu.lower.concat(hu.upper), HEXAGRAMS), `互卦缺失 ${lines}`);
  }
  assert.equal(n, 4096);
});

// 64 卦都能被 findHexagram 反查到（数据与卦画编码双向一致）
test("64 卦 lines 反查唯一", () => {
  for (const h of HEXAGRAMS) {
    const bits = h.lines.split("").map(Number);
    assert.equal(gua.findHexagram(bits, HEXAGRAMS).id, h.id);
  }
});

// 随机起卦 200 次，值域与结构稳定
test("随机起卦 200 次结构稳定", () => {
  for (let i = 0; i < 200; i++) {
    const lines = castGua(Math.random);
    const r = gua.duanCi(lines, HEXAGRAMS);
    assert.ok(r.ben && r.entries.length);
    assert.ok(r.ben.advice["综合"] && r.ben.advice["出行"]);
  }
});
