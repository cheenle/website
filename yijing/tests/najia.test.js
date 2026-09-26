const test = require("node:test");
const assert = require("node:assert/strict");
const nj = require("../js/najia.js");
const lz = require("../js/liuzhu.js");

const JIAZI_DAY = new Date(2000, 0, 7); // 甲子日

test("八宫世应：乾为天世上爻应三；天风姤一世世初爻应四爻", () => {
  const q = nj.gongOf("乾为天");
  assert.equal(q.gong, "乾"); assert.equal(q.shi, 6);
  const g = nj.gongOf("天风姤");
  assert.equal(g.gong, "乾"); assert.equal(g.shi, 1);
  const n = nj.najia([1,1,1,1,1,1], "乾为天", JIAZI_DAY);
  assert.equal(n.ying, 3);
});

test("纳甲干支：乾内甲子寅辰、外壬午申戌", () => {
  const n = nj.najia([1,1,1,1,1,1], "乾为天", JIAZI_DAY);
  assert.deepEqual(n.yaos.map((y) => y.ganZhi), ["甲子","甲寅","甲辰","壬午","壬申","壬戌"]);
});

test("六亲：乾宫金，子水为子孙、辰土为父母", () => {
  const n = nj.najia([1,1,1,1,1,1], "乾为天", JIAZI_DAY);
  assert.equal(n.yaos[0].liuqin, "子孙"); // 甲子水，金生水
  assert.equal(n.yaos[2].liuqin, "父母"); // 甲辰土，土生金
  assert.equal(n.gongWuxing, "金");
});

test("六兽：甲子日初爻起青龙，顺行六兽", () => {
  const n = nj.najia([1,1,1,1,1,1], "乾为天", JIAZI_DAY);
  assert.deepEqual(n.yaos.map((y) => y.liushou), ["青龙","朱雀","勾陈","腾蛇","白虎","玄武"]);
});

test("日柱锚点：2000-01-01 戊午", () => {
  assert.equal(nj.dayGanzhi(new Date(2000, 0, 1)).gan, "戊");
  assert.equal(nj.dayGanzhi(JIAZI_DAY).gan, "甲");
});

test("子午流注：巳时脾经、子时胆经、酉时肾经", () => {
  assert.equal(lz.meridianOf(new Date(2026, 8, 26, 10, 0)).jing, "脾经");
  assert.equal(lz.meridianOf(new Date(2026, 8, 26, 0, 30)).jing, "胆经");
  assert.equal(lz.meridianOf(new Date(2026, 8, 26, 18, 0)).jing, "肾经");
});
