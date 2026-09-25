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
