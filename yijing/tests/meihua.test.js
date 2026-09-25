const test = require("node:test");
const assert = require("node:assert/strict");
const mh = require("../js/meihua.js");

test("先天数取卦：除 8 余 0 作 8（坤），余数映射正确", () => {
  assert.equal(mh.numToTrigram(1), "乾");
  assert.equal(mh.numToTrigram(8), "坤");
  assert.equal(mh.numToTrigram(16), "坤");
  assert.equal(mh.numToTrigram(9), "乾");
  assert.equal(mh.numToTrigram(34), "兑"); // 34%8=2
});

test("动爻取数：除 6 余 0 作 6（上爻，下标 5）", () => {
  assert.equal(mh.numToMoving(6), 5);
  assert.equal(mh.numToMoving(12), 5);
  assert.equal(mh.numToMoving(7), 0);
  assert.equal(mh.numToMoving(43), 0); // 43%6=1 → 初爻
});

test("历法换算：年支/节气月/时支", () => {
  assert.equal(mh.yearBranchNum(2026), 7);   // 丙午年，午=7
  assert.equal(mh.yearBranchNum(2020), 1); // 庚子年，子=1
  assert.equal(mh.jieqiMonthNum(2), 1);     // 二月≈寅月
  assert.equal(mh.jieqiMonthNum(1), 12);    // 一月≈丑月
  assert.equal(mh.hourBranchNum(23), 1);    // 子时
  assert.equal(mh.hourBranchNum(15), 9);    // 申时
});

test("体用生克关系表", () => {
  assert.equal(mh.wuxingRelation("金", "火"), "用克体");
  assert.equal(mh.wuxingRelation("火", "金"), "体克用");
  assert.equal(mh.wuxingRelation("土", "金"), "体生用");
  assert.equal(mh.wuxingRelation("金", "土"), "用生体");
  assert.equal(mh.wuxingRelation("水", "水"), "比和");
});

test("体用归属：动爻在下卦则下卦为用", () => {
  const m = mh.buildMeihua("乾", "坤", 1, "t"); // 动爻下标1 在下卦 → 用=坤 体=乾
  assert.equal(m.yong, "坤");
  assert.equal(m.ti, "乾");
  assert.equal(m.relation, "用生体"); // 体乾金、用坤土：土生金
  const m2 = mh.buildMeihua("乾", "坤", 4, "t"); // 动爻在上卦 → 用=乾 体=坤
  assert.equal(m2.ti, "坤");
  assert.equal(m2.yong, "乾");
});

test("数字起卦确定性 + 卦画与经卦一致 + 变卦只翻动爻", () => {
  const m = mh.meihuaByNumbers(5, 3);
  assert.equal(m.upper, "巽");   // n1=5 → 巽为上卦
  assert.equal(m.lower, "离");   // n2=3 → 离为下卦
  const m2 = mh.meihuaByNumbers(5, 3);
  assert.deepEqual(m, m2);
  assert.equal(m.bits.length, 6);
  for (let i = 0; i < 6; i++) if (i !== m.moving) assert.equal(m.zbits[i], m.bits[i]);
  assert.notEqual(m.zbits[m.moving], m.bits[m.moving]);
  assert.ok(m.benName && m.zhiName && m.huName);
});

test("时间起卦字段齐备", () => {
  const m = mh.meihuaByTime(new Date(2026, 8, 26, 10, 0));
  for (const k of ["bits", "moving", "ti", "yong", "relation", "relationNote", "benName"]) {
    assert.ok(m[k] !== undefined, k);
  }
  assert.match(m.methodNote, /时间起卦/);
});
