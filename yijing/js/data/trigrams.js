// 八卦基础数据。symbol: 三位字符串，自下而上（初爻在前），1 阳 0 阴。
const TRIGRAMS = {
  "乾": { "symbol": "111", "wuxing": "金", "fangwei": "西北", "nature": "天", "family": "父" },
  "兑": { "symbol": "110", "wuxing": "金", "fangwei": "西",  "nature": "泽", "family": "少女" },
  "离": { "symbol": "101", "wuxing": "火", "fangwei": "南",  "nature": "火", "family": "中女" },
  "震": { "symbol": "100", "wuxing": "木", "fangwei": "东",  "nature": "雷", "family": "长男" },
  "巽": { "symbol": "011", "wuxing": "木", "fangwei": "东南", "nature": "风", "family": "长女" },
  "坎": { "symbol": "010", "wuxing": "水", "fangwei": "北",  "nature": "水", "family": "中男" },
  "艮": { "symbol": "001", "wuxing": "土", "fangwei": "东北", "nature": "山", "family": "少男" },
  "坤": { "symbol": "000", "wuxing": "土", "fangwei": "西南", "nature": "地", "family": "母" }
};
if (typeof module !== "undefined" && module.exports) module.exports = TRIGRAMS;
