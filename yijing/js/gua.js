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

// 数据缺失时的占位条目：让 UI 走「经文数据缺失」分支而不抛错（规范 §8）。
function missingEntry(h, label, primary) {
  return { kind: "missing", source: h ? `${h.fullName}·${label}` : label, ci: "", baihua: "", primary };
}

// 朱熹《易学启蒙》断法：依动爻数取断辞。
function duanCi(lines, hexagrams) {
  const bits = toBits(lines);
  const moving = movingLines(lines);
  const ben = findHexagram(bits, hexagrams);
  const zbits = zhiBits(lines);
  const zhi = moving.length ? findHexagram(zbits, hexagrams) : null;

  const guaciEntry = (h, primary, tag) => (h ? {
    kind: "guaci",
    source: `${tag}${h.fullName}·卦辞`,
    ci: h.guaci,
    tuan: h.tuan,
    xiang: h.xiang,
    baihua: h.guaciBaihua,
    primary,
  } : missingEntry(h, `${tag}卦辞`, primary));
  const yaoEntry = (h, i, primary, tag) => {
    const y = h && h.yaos ? h.yaos[i] : null;
    if (!y) return missingEntry(h, `${tag}第${i + 1}爻`, primary);
    return {
      kind: "yao",
      source: `${tag}${h.fullName}·${y.title}`,
      ci: y.ci,
      xiang: y.xiang,
      baihua: y.baihua,
      primary,
    };
  };

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
      if (ben && ben.yong && (ben.id === 1 || ben.id === 2)) {
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


// —— 爻位与卦变分析（象数事实层，供展示与 LLM 解读取用）——
const WEI = ["初", "二", "三", "四", "五", "上"];

// 单爻事实：当位/失正、中、应、乘承顺逆
function yaoFacts(bits, i) {
  const yang = bits[i] === 1;
  const yangPos = i === 0 || i === 2 || i === 4; // 初、三、五为阳位
  const facts = [`${WEI[i]}位${yang ? "阳" : "阴"}爻，${yang === yangPos ? "当位" : "失正"}`];
  if (i === 1 || i === 4) facts.push("居中");
  const j = i < 3 ? i + 3 : i - 3;
  facts.push(`与${WEI[j]}爻${bits[j] !== bits[i] ? "有应" : "敌应"}`);
  if (i > 0) {
    if (!yang && bits[i - 1] === 1) facts.push("阴乘阳（逆）");
    if (yang && bits[i - 1] === 0) facts.push("阳乘阴（顺）");
  }
  if (i < 5) {
    if (!yang && bits[i + 1] === 1) facts.push("阴承阳（顺）");
    if (yang && bits[i + 1] === 0) facts.push("阳承阴（逆）");
  }
  return facts.join("，");
}

// 错卦：六爻全反；综卦：上下颠倒
function cuoBits(bits) { return bits.map((b) => 1 - b); }
function zongBits(bits) { return bits.slice().reverse(); }

if (typeof module !== "undefined" && module.exports) {
  module.exports = { toBits, movingLines, zhiBits, huBits, trigramName, findHexagram, duanCi, yaoFacts, cuoBits, zongBits, WEI };
}
