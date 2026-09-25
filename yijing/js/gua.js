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
