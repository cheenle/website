// 三枚铜钱起卦。random: () => [0,1) 的随机数，注入以便测试。
function castLine(random) {
  let total = 0;
  for (let i = 0; i < 3; i++) total += random() < 0.5 ? 3 : 2;
  return total; // 6 老阴 / 7 少阳 / 8 少阴 / 9 老阳
}

function castGua(random) {
  const lines = [];
  for (let i = 0; i < 6; i++) lines.push(castLine(random));
  return lines;
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { castLine, castGua };
}
