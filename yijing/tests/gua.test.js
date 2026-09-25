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
