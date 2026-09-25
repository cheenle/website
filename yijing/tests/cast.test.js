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
