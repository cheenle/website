// 梅花易数起卦与体用分析（纯函数，不碰 DOM）。
// 先天卦数：乾1 兑2 离3 震4 巽5 坎6 艮7 坤8；除 8 余 0 作 8。
// 历法说明：年取干支年支数、月取节气月（立春起寅月，以公历月近似）、时取时支数，
// 为免引入历法库的通行简化，UI 已注明「近似」。
const XIANTIAN = ["乾", "兑", "离", "震", "巽", "坎", "艮", "坤"];
const WUXING_SHENG = { 木: "火", 火: "土", 土: "金", 金: "水", 水: "木" };
const WUXING_KE = { 木: "土", 土: "水", 水: "火", 火: "金", 金: "木" };
const RELATION_NOTE = {
  用生体: "有外助进益之象，事多顺成",
  体生用: "耗费泄气之象，宜节制投入",
  体克用: "可得而费力，须主动争取",
  用克体: "受制于外，不利妄动",
  比和: "体用同气，平稳顺遂",
};

function numToTrigram(n) {
  let m = Math.abs(Math.trunc(n)) % 8;
  if (m === 0) m = 8;
  return XIANTIAN[m - 1];
}

function numToMoving(n) {
  let m = Math.abs(Math.trunc(n)) % 6;
  if (m === 0) m = 6;
  return m - 1; // 0-based，初爻为 0
}

function yearBranchNum(year) { return ((year - 4) % 12 + 12) % 12 + 1; }   // 子=1 … 亥=12（2020 庚子=1）
function jieqiMonthNum(month1to12) { return ((month1to12 - 2 + 12) % 12) + 1; } // 寅月=1
function hourBranchNum(hour0to23) { return Math.floor(((hour0to23 + 1) % 24) / 2) + 1; }

function wuxingRelation(tiWx, yongWx) {
  if (tiWx === yongWx) return "比和";
  if (WUXING_SHENG[yongWx] === tiWx) return "用生体";
  if (WUXING_SHENG[tiWx] === yongWx) return "体生用";
  if (WUXING_KE[tiWx] === yongWx) return "体克用";
  if (WUXING_KE[yongWx] === tiWx) return "用克体";
  return "比和";
}

// 浏览器经 script 标签获得全局 TRIGRAMS/HEXAGRAMS；Node 测试经 require 获得。
const MT = (typeof module !== "undefined" && module.exports) ? require("./data/trigrams.js") : TRIGRAMS;
const MH = (typeof module !== "undefined" && module.exports) ? require("./data/hexagrams.js") : HEXAGRAMS;

function hexNameByBits(bits6) {
  const s = bits6.join("");
  const h = MH.find((x) => x.lines === s);
  return h ? h.fullName : null;
}

function buildMeihua(upperName, lowerName, moving, methodNote) {
  const bits = MT[lowerName].symbol.split("").map(Number).concat(MT[upperName].symbol.split("").map(Number));
  const yongIsLower = moving <= 2; // 动爻在下卦则下卦为用
  const ti = yongIsLower ? upperName : lowerName;
  const yong = yongIsLower ? lowerName : upperName;
  const relation = wuxingRelation(MT[ti].wuxing, MT[yong].wuxing);
  const zbits = bits.slice();
  zbits[moving] = 1 - zbits[moving];
  const hu = { lower: [bits[1], bits[2], bits[3]], upper: [bits[2], bits[3], bits[4]] };
  return {
    method: "meihua",
    methodNote,
    upper: upperName,
    lower: lowerName,
    bits,
    zbits,
    moving,
    ti, yong,
    tiWuxing: MT[ti].wuxing,
    yongWuxing: MT[yong].wuxing,
    relation,
    relationNote: RELATION_NOTE[relation],
    benName: hexNameByBits(bits),
    zhiName: hexNameByBits(zbits),
    huName: hexNameByBits(hu.lower.concat(hu.upper)),
  };
}

function meihuaByTime(d) {
  const y = yearBranchNum(d.getFullYear());
  const m = jieqiMonthNum(d.getMonth() + 1);
  const day = d.getDate();
  const h = hourBranchNum(d.getHours());
  return buildMeihua(
    numToTrigram(y + m + day),
    numToTrigram(y + m + day + h),
    numToMoving(y + m + day + h),
    `时间起卦：年支${y} 节气月${m} 日${day} 时支${h}（历法近似）`
  );
}

function meihuaByNumbers(n1, n2) {
  return buildMeihua(numToTrigram(n1), numToTrigram(n2), numToMoving(n1 + n2), `数字起卦：${n1}、${n2}`);
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { numToTrigram, numToMoving, yearBranchNum, jieqiMonthNum, hourBranchNum,
    wuxingRelation, buildMeihua, meihuaByTime, meihuaByNumbers, XIANTIAN };
}
