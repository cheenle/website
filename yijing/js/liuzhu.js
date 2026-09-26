// 子午流注：十二时辰配十二经（纯函数）。
const SHICHEN_JING = [
  { shi: "子", jing: "胆经", zangfu: "胆", hours: "23-01" },
  { shi: "丑", jing: "肝经", zangfu: "肝", hours: "01-03" },
  { shi: "寅", jing: "肺经", zangfu: "肺", hours: "03-05" },
  { shi: "卯", jing: "大肠经", zangfu: "大肠", hours: "05-07" },
  { shi: "辰", jing: "胃经", zangfu: "胃", hours: "07-09" },
  { shi: "巳", jing: "脾经", zangfu: "脾", hours: "09-11" },
  { shi: "午", jing: "心经", zangfu: "心", hours: "11-13" },
  { shi: "未", jing: "小肠经", zangfu: "小肠", hours: "13-15" },
  { shi: "申", jing: "膀胱经", zangfu: "膀胱", hours: "15-17" },
  { shi: "酉", jing: "肾经", zangfu: "肾", hours: "17-19" },
  { shi: "戌", jing: "心包经", zangfu: "心包", hours: "19-21" },
  { shi: "亥", jing: "三焦经", zangfu: "三焦", hours: "21-23" },
];
const ZHI_ORDER = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"];

function shichenOf(date) {
  const h = date.getHours();
  return ZHI_ORDER[Math.floor(((h + 1) % 24) / 2)];
}

function meridianOf(date) {
  const shi = shichenOf(date);
  const m = SHICHEN_JING.find((x) => x.shi === shi);
  return { shi, jing: m.jing, zangfu: m.zangfu, hours: m.hours };
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { SHICHEN_JING, shichenOf, meridianOf };
}
