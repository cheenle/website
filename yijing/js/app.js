/* global TRIGRAMS, HEXAGRAMS, castLine, huBits, trigramName, findHexagram, duanCi */

const HISTORY_KEY = "yijing-history";
const HISTORY_MAX = 50;
const TOSS_MS = 900;

const LINE_NAMES = { 6: "老阴（动）", 7: "少阳", 8: "少阴", 9: "老阳（动）" };
const YAO_MARK = { 6: "×", 9: "○" };

const state = { question: "", category: "综合", lines: [] };

function $(id) { return document.getElementById(id); }

function showScreen(name) {
  for (const s of ["ask", "cast", "result"]) {
    $("screen-" + s).classList.toggle("hidden", s !== name);
  }
}

function startCast() {
  state.question = $("question").value.trim();
  const checked = document.querySelector('input[name="category"]:checked');
  state.category = checked ? checked.value : "综合";
  state.lines = [];
  showScreen("cast");
  $("cast-lines").innerHTML = "";
  tossStep(0);
}

// 三枚铜钱的正反面：阳面（值 3）/阴面（值 2），和 = 6 + 阳面数。
// 按爻值反推阳面枚数并洗牌供展示；传统以无字之背为阳、有字之面为阴。
function coinFaces(value) {
  const heads = value - 6;
  const faces = [];
  for (let i = 0; i < 3; i++) faces.push(i < heads);
  for (let i = faces.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    const t = faces[i]; faces[i] = faces[j]; faces[j] = t;
  }
  return faces;
}

function tossStep(i) {
  if (i >= 6) { renderResult(); return; }
  $("cast-progress").textContent = `第 ${i + 1} 爻（自下而上，共六爻）`;
  const coins = $("coins");
  coins.classList.add("tossing");
  setTimeout(() => {
    coins.classList.remove("tossing");
    void coins.offsetWidth; // 强制重排，令下一爻的翻转动画能重新播放
    const value = castLine(Math.random);
    state.lines.push(value);
    const faces = coinFaces(value);
    for (let c = 0; c < 3; c++) {
      coins.children[c].classList.toggle("head", faces[c]); // head = 阳面（背）
    }
    appendCastRow(i, value, faces);
    tossStep(i + 1);
  }, TOSS_MS);
}

function appendCastRow(i, value, faces) {
  const row = document.createElement("div");
  row.className = "cast-row";
  const face = document.createElement("span");
  face.className = "face";
  face.textContent = faces.map((f) => (f ? "背" : "字")).join("");
  const yao = document.createElement("div");
  yao.appendChild(buildYao(value === 7 || value === 9 ? 1 : 0, value === 6 || value === 9));
  const name = document.createElement("span");
  name.className = "face name";
  name.textContent = LINE_NAMES[value];
  row.append(face, yao, name);
  $("cast-lines").appendChild(row); // column-reverse：后追加的显示在上方
}

function buildYao(bit, moving) {
  const yao = document.createElement("div");
  yao.className = "yao " + (bit ? "yang" : "yin");
  yao.append(document.createElement("span"), document.createElement("span"), document.createElement("span"));
  if (moving) {
    const mark = document.createElement("span");
    mark.className = "mark";
    mark.textContent = YAO_MARK[bit ? 9 : 6];
    yao.appendChild(mark);
  }
  return yao;
}

function renderResult() {
  const r = duanCi(state.lines, HEXAGRAMS);
  const hu = huBits(r.bits);
  const huHex = findHexagram(hu.lower.concat(hu.upper), HEXAGRAMS);

  // 摘要
  const movingNames = r.moving.map((i) => r.ben.yaos[i] ? r.ben.yaos[i].title : `第${i + 1}爻`).join("、") || "无";
  $("result-summary").innerHTML =
    `<p>所问：${escapeHtml(state.question || "心中默念")}（${state.category}）</p>` +
    `<p>得 <strong>${r.ben ? r.ben.fullName : "未知卦"}</strong>` +
    (r.zhi ? ` 之 <strong>${r.zhi.fullName}</strong>` : "") +
    `，动爻：${movingNames}</p>` +
    `<p class="rule">断法：${r.rule}</p>`;

  // 三卦排盘
  const guas = $("result-guas");
  guas.innerHTML = "";
  guas.appendChild(guaCard("本卦", r.ben, r.moving));
  guas.appendChild(guaCard("之卦", r.zhi, []));
  guas.appendChild(guaCard("互卦", huHex, []));

  // 断辞
  const duan = $("result-duan");
  duan.innerHTML = "";
  for (const e of r.entries) duan.appendChild(entryBlock(e));

  const advice = document.createElement("div");
  advice.className = "advice";
  const tip = r.ben && r.ben.advice ? r.ben.advice[state.category] : "经文数据缺失";
  advice.innerHTML = `<h3>问「${state.category}」要点</h3><p>${escapeHtml(tip || "经文数据缺失")}</p>` +
    `<h3>综合断语</h3><p>${escapeHtml(buildSummary(r))}</p>`;
  duan.appendChild(advice);

  saveRecord(r);
  showScreen("result");
}

function buildSummary(r) {
  const q = state.question || "所问之事";
  const ben = r.ben ? r.ben.name : "?";
  const zhi = r.zhi ? `，变而为${r.zhi.name}` : "";
  const primary = r.entries[0];
  return `${q}，得${ben}卦${zhi}。${r.rule}。${primary ? primary.baihua : "经文数据缺失。"}`;
}

function guaCard(role, hex, moving) {
  const card = document.createElement("div");
  card.className = "gua-card";
  const roleEl = document.createElement("div");
  roleEl.className = "role";
  roleEl.textContent = role;
  card.appendChild(roleEl);
  if (!hex) {
    const none = document.createElement("h3");
    none.textContent = "—";
    card.appendChild(none);
    return card;
  }
  const name = document.createElement("h3");
  name.textContent = hex.fullName;
  card.appendChild(name);
  const lines = document.createElement("div");
  lines.className = "gua-lines";
  const bits = hex.lines.split("").map(Number);
  for (let i = 0; i < 6; i++) lines.appendChild(buildYao(bits[i], moving.includes(i)));
  card.appendChild(lines);
  const tri = document.createElement("div");
  tri.className = "trigrams";
  const lowerName = hex.lines.slice(0, 3).split("").map(Number);
  const upperName = hex.lines.slice(3).split("").map(Number);
  const lowerT = trigramName(lowerName);
  const upperT = trigramName(upperName);
  const lowerInfo = TRIGRAMS[lowerT];
  const upperInfo = TRIGRAMS[upperT];
  tri.textContent = `${lowerT}${lowerInfo.nature}（${lowerInfo.wuxing}·${lowerInfo.fangwei}）下 · ` +
    `${upperT}${upperInfo.nature}（${upperInfo.wuxing}·${upperInfo.fangwei}）上`;
  card.appendChild(tri);
  return card;
}

function entryBlock(e) {
  const div = document.createElement("div");
  div.className = "duan-entry" + (e.primary ? "" : " secondary");
  const source = document.createElement("div");
  source.className = "source";
  source.textContent = e.source + (e.primary ? "（主）" : "（参）");
  div.appendChild(source);
  const ci = document.createElement("p");
  ci.className = "ci";
  ci.textContent = e.ci || "经文数据缺失";
  div.appendChild(ci);
  for (const k of ["tuan", "xiang"]) {
    if (e[k]) {
      const ref = document.createElement("p");
      ref.className = "ref";
      ref.textContent = e[k];
      div.appendChild(ref);
    }
  }
  const bh = document.createElement("p");
  bh.className = "baihua";
  bh.textContent = e.baihua || "经文数据缺失";
  div.appendChild(bh);
  return div;
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
// —— 占例记录（localStorage，静默降级）——
function loadHistory() {
  try {
    const list = JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
    if (!Array.isArray(list)) return [];
    return list.filter((r) => r && typeof r === "object" && Array.isArray(r.moving));
  } catch (e) { return []; }
}

function saveRecord(r) {
  try {
    const list = loadHistory();
    list.unshift({
      time: new Date().toISOString(),
      question: state.question,
      category: state.category,
      lines: state.lines,
      benId: r.ben ? r.ben.id : null,
      benName: r.ben ? r.ben.fullName : null,
      zhiId: r.zhi ? r.zhi.id : null,
      zhiName: r.zhi ? r.zhi.fullName : null,
      moving: r.moving,
    });
    localStorage.setItem(HISTORY_KEY, JSON.stringify(list.slice(0, HISTORY_MAX)));
  } catch (e) { /* 隐私模式等场景静默跳过 */ }
}

function renderHistory() {
  const ul = $("history-list");
  ul.innerHTML = "";
  const list = loadHistory();
  if (!list.length) {
    const li = document.createElement("li");
    li.textContent = "暂无占例。";
    ul.appendChild(li);
    return;
  }
  for (const rec of list) {
    const li = document.createElement("li");
    const t = new Date(rec.time);
    const movingText = rec.moving.length
      ? rec.moving.map((i) => ["初","二","三","四","五","上"][i]).join("、") + "爻动"
      : "六爻安静";
    li.innerHTML = `<div>${escapeHtml(rec.benName || "?")}${rec.zhiName ? " 之 " + escapeHtml(rec.zhiName) : ""} · ${movingText}</div>` +
      `<div class="meta">${t.toLocaleString("zh-CN")} · ${escapeHtml(rec.category)} · ${escapeHtml(rec.question || "心中默念")}</div>`;
    ul.appendChild(li);
  }
}

function clearHistory() {
  try { localStorage.removeItem(HISTORY_KEY); } catch (e) { /* 忽略 */ }
  renderHistory();
}

document.addEventListener("DOMContentLoaded", () => {
  $("btn-start").addEventListener("click", startCast);
  $("btn-again").addEventListener("click", startCast);
  $("btn-back").addEventListener("click", () => showScreen("ask"));
  $("btn-history").addEventListener("click", () => { renderHistory(); $("history-panel").classList.remove("hidden"); });
  $("btn-close-history").addEventListener("click", () => $("history-panel").classList.add("hidden"));
  $("btn-clear-history").addEventListener("click", clearHistory);
});
