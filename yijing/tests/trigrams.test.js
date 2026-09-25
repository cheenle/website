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
