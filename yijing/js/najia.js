// 纳甲筮法装卦：八宫世应、爻纳干支、六亲、六兽、用神（纯函数，不碰 DOM）。
// 八宫卦序：本卦、一世、二世、三世、四世、五世、游魂、归魂；世位 6,1,2,3,4,5,4,3。
const BAGONG = {
  乾: ["乾为天", "天风姤", "天山遁", "天地否", "风地观", "山地剥", "火地晋", "火天大有"],
  坎: ["坎为水", "水泽节", "水雷屯", "水火既济", "泽火革", "雷火丰", "地火明夷", "地水师"],
  艮: ["艮为山", "山火贲", "山天大畜", "山泽损", "火泽睽", "天泽履", "风泽中孚", "风山渐"],
  震: ["震为雷", "雷地豫", "雷水解", "雷风恒", "地风升", "水风井", "泽风大过", "泽雷随"],
  巽: ["巽为风", "风天小畜", "风火家人", "风雷益", "天雷无妄", "火雷噬嗑", "山雷颐", "山风蛊"],
  离: ["离为火", "火山旅", "火风鼎", "火水未济", "山水蒙", "风水涣", "天水讼", "天火同人"],
  坤: ["坤为地", "地雷复", "地泽临", "地天泰", "雷天大壮", "泽天夬", "水天需", "水地比"],
  兑: ["兑为泽", "泽水困", "泽地萃", "泽山咸", "水山蹇", "地山谦", "雷山小过", "雷泽归妹"],
};
const SHI_WEI = [6, 1, 2, 3, 4, 5, 4, 3]; // 世爻（1-based，上爻=6）
// 纳甲：内卦三支、外卦三支 + 天干（内/外）
const NAJIA = {
  乾: { gan: ["甲", "壬"], nei: ["子", "寅", "辰"], wai: ["午", "申", "戌"] },
  坤: { gan: ["乙", "癸"], nei: ["未", "巳", "卯"], wai: ["丑", "亥", "酉"] },
  震: { gan: ["庚", "庚"], nei: ["子", "寅", "辰"], wai: ["午", "申", "戌"] },
  巽: { gan: ["辛", "辛"], nei: ["丑", "亥", "酉"], wai: ["未", "巳", "卯"] },
  坎: { gan: ["戊", "戊"], nei: ["寅", "辰", "午"], wai: ["申", "戌", "子"] },
  离: { gan: ["己", "己"], nei: ["卯", "丑", "亥"], wai: ["酉", "未", "巳"] },
  艮: { gan: ["丙", "丙"], nei: ["辰", "午", "申"], wai: ["戌", "子", "寅"] },
  兑: { gan: ["丁", "丁"], nei: ["巳", "卯", "丑"], wai: ["亥", "酉", "未"] },
};
const ZHI_WUXING = { 子: "水", 丑: "土", 寅: "木", 卯: "木", 辰: "土", 巳: "火",
  午: "火", 未: "土", 申: "金", 酉: "金", 戌: "土", 亥: "水" };
const LIUSHOU = ["青龙", "朱雀", "勾陈", "腾蛇", "白虎", "玄武"];
const RIGAN_START = { 甲: 0, 乙: 0, 丙: 1, 丁: 1, 戊: 2, 己: 3, 庚: 4, 辛: 4, 壬: 5, 癸: 5 };
const GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"];
const YONGSHEN = {
  事业: "官鬼", 财运: "妻财", 感情: "妻财/官鬼", 健康: "官鬼为病、子孙为医药", 出行: "世爻与官鬼", 综合: "世爻",
};

function gongOf(fullName) {
  for (const g of Object.keys(BAGONG)) {
    const i = BAGONG[g].indexOf(fullName);
    if (i >= 0) return { gong: g, wei: i, shi: SHI_WEI[i] };
  }
  return null;
}

function liuqin(gongWx, zhiWx) {
  const SHENG = { 木: "火", 火: "土", 土: "金", 金: "水", 水: "木" };
  const KE = { 木: "土", 土: "水", 水: "火", 火: "金", 金: "木" };
  if (gongWx === zhiWx) return "兄弟";
  if (SHENG[zhiWx] === gongWx) return "父母";   // 爻生宫 = 生我
  if (SHENG[gongWx] === zhiWx) return "子孙";   // 宫生爻 = 我生
  if (KE[zhiWx] === gongWx) return "官鬼";      // 爻克宫 = 克我
  if (KE[gongWx] === zhiWx) return "妻财";      // 宫克爻 = 我克
  return "兄弟";
}

// 日柱干支：锚 2000-01-01 = 戊午（六十甲子序 54）
function dayGanzhi(date) {
  const anchor = Date.UTC(2000, 0, 1);
  const day = Math.round((Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()) - anchor) / 86400000);
  const idx = ((54 + day) % 60 + 60) % 60;
  return { gan: GAN[idx % 10], idx };
}

// bits: 初爻在前 0/1；返回每爻 {ganZhi, wuxing, liuqin, liushou, shi, ying}
function najia(bits, fullName, date) {
  const g = gongOf(fullName);
  if (!g) return null;
  const T = (typeof module !== "undefined" && module.exports) ? require("./data/trigrams.js") : TRIGRAMS;
  const lowerName = trigramNameLocal(bits.slice(0, 3), T);
  const upperName = trigramNameLocal(bits.slice(3), T);
  const lower = NAJIA[lowerName];
  const upper = NAJIA[upperName];
  const gongWx = T[g.gong].wuxing;
  const start = RIGAN_START[dayGanzhi(date).gan];
  const ying = g.shi <= 3 ? g.shi + 3 : g.shi - 3;
  const yaos = [];
  for (let i = 0; i < 6; i++) {
    const outer = i >= 3;
    const zhi = (outer ? upper.wai : lower.nei)[i % 3];
    const gan = outer ? upper.gan[1] : lower.gan[0];
    const wx = ZHI_WUXING[zhi];
    yaos.push({
      wei: i + 1,
      ganZhi: gan + zhi,
      wuxing: wx,
      liuqin: liuqin(gongWx, wx),
      liushou: LIUSHOU[(start + i) % 6],
      shi: g.shi === i + 1,
      ying: ying === i + 1,
    });
  }
  return { gong: g.gong, gongWuxing: gongWx, shi: g.shi, ying, yaos, yongshen: YONGSHEN };
}

function trigramNameLocal(bits3, T) {
  const s = bits3.join("");
  for (const n of Object.keys(T)) if (T[n].symbol === s) return n;
  return null;
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { BAGONG, SHI_WEI, NAJIA, ZHI_WUXING, LIUSHOU, RIGAN_START, YONGSHEN,
    gongOf, liuqin, dayGanzhi, najia };
}
