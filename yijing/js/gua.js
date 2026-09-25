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

if (typeof module !== "undefined" && module.exports) {
  module.exports = { toBits, movingLines, zhiBits, huBits, trigramName, findHexagram, duanCi };
}
