/* global TRIGRAMS, HEXAGRAMS, castLine, huBits, trigramName, findHexagram, duanCi, yaoFacts, cuoBits, zongBits */

const HISTORY_KEY = "yijing-history";
const HISTORY_MAX = 50;
const TOSS_MS = 900;

const LINE_NAMES = { 6: "老阴（动）", 7: "少阳", 8: "少阴", 9: "老阳（动）" };
const YAO_MARK = { 6: "×", 9: "○" };

const state = { question: "", category: "综合", lines: [], chat: [], lastReading: "", lastLlmId: null };

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
  state.lastResult = r;
  state.chat = [];
  state.lastReading = "";
  $("llm-panel").classList.add("hidden");
  $("llm-panel").innerHTML = "";
  $("chat-box").classList.add("hidden");
  $("chat-log").innerHTML = "";
  $("btn-llm").disabled = false;
  const hu = huBits(r.bits);
  const huHex = findHexagram(hu.lower.concat(hu.upper), HEXAGRAMS);

  // 摘要
  const movingNames = r.moving.map((i) => r.ben.yaos[i] ? r.ben.yaos[i].title : `第${i + 1}爻`).join("、") || "无";
  const facts = r.moving.map((i) => `${r.ben.yaos[i] ? r.ben.yaos[i].title : `第${i + 1}爻`}：${yaoFacts(r.bits, i)}`).join("；");
  const cuoHex = findHexagram(cuoBits(r.bits), HEXAGRAMS);
  const zongHex = findHexagram(zongBits(r.bits), HEXAGRAMS);
  $("result-summary").innerHTML =
    `<p>所问：${escapeHtml(state.question || "心中默念")}（${state.category}）</p>` +
    `<p>得 <strong>${r.ben ? r.ben.fullName : "未知卦"}</strong>` +
    (r.zhi ? ` 之 <strong>${r.zhi.fullName}</strong>` : "") +
    `，动爻：${movingNames}</p>` +
    (facts ? `<p class="facts">爻位：${escapeHtml(facts)}</p>` : "") +
    `<p class="facts">互卦 ${huHex ? huHex.fullName : "?"} · 错卦 ${cuoHex ? cuoHex.fullName : "?"} · 综卦 ${zongHex ? zongHex.fullName : "?"}</p>` +
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

// —— AI 进一步解读：经 nginx → 本机代理 → LLM，浏览器不持密钥 ——
function llmPayload(r) {
  const hu = huBits(r.bits);
  const huHex = findHexagram(hu.lower.concat(hu.upper), HEXAGRAMS);
  const cuoHex = findHexagram(cuoBits(r.bits), HEXAGRAMS);
  const zongHex = findHexagram(zongBits(r.bits), HEXAGRAMS);
  return {
    question: state.question,
    category: state.category,
    ben: r.ben ? { fullName: r.ben.fullName, tuan: r.ben.tuan, xiang: r.ben.xiang } : null,
    zhi: r.zhi ? { fullName: r.zhi.fullName } : null,
    hu: huHex ? huHex.fullName : null,
    cuo: cuoHex ? cuoHex.fullName : null,
    zong: zongHex ? zongHex.fullName : null,
    moving: r.moving.map((i) => ({
      title: r.ben.yaos[i] ? r.ben.yaos[i].title : `第${i + 1}爻`,
      facts: yaoFacts(r.bits, i),
      xiang: r.ben.yaos[i] ? r.ben.yaos[i].xiang : "",
    })),
    rule: r.rule,
    duanci: r.entries.map((e) => ({ source: e.source, ci: e.ci, baihua: e.baihua })),
  };
}

function requestInterpret() {
  const r = state.lastResult;
  if (!r) return;
  const panel = $("llm-panel");
  const btn = $("btn-llm");
  btn.disabled = true;
  panel.classList.remove("hidden");
  panel.innerHTML = "<p class=\"llm-status\">正在请 AI 结合卦象与断辞进一步解读……</p>";
  fetch("/yijing/api/interpret", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(llmPayload(r)),
    signal: AbortSignal.timeout(100000),
  })
    .then((rp) => rp.json())
    .then((data) => {
      if (!data || !data.ok) {
        throw new Error(data && data.error === "content-inspection"
          ? "上游内容审查误拦，可稍后重试或换个问法"
          : (data && data.error) || "bad response");
      }
      renderLlm(data.text, data.id);
    })
    .catch((e) => {
      panel.innerHTML = `<p class="llm-error">AI 解读暂不可用（${escapeHtml(e.message)}）。古典断辞如上，仍可依经而断。</p>`;
    })
    .finally(() => { btn.disabled = false; });
}

function renderLlm(text, id) {
  state.lastReading = text;
  state.lastLlmId = id || null;
  $("chat-box").classList.remove("hidden");
  const panel = $("llm-panel");
  panel.innerHTML = "";
  const head = document.createElement("h3");
  head.textContent = "AI 进一步解读";
  panel.appendChild(head);
  for (const para of String(text).split(/\n+/)) {
    if (!para.trim()) continue;
    const p = document.createElement("p");
    p.textContent = para;
    panel.appendChild(p);
  }
  const fb = document.createElement("div");
  fb.className = "llm-feedback";
  const tip = document.createElement("span");
  tip.textContent = "此解读是否切题有用？";
  const up = document.createElement("button");
  up.className = "link";
  up.textContent = "👍 有用";
  const down = document.createElement("button");
  down.className = "link";
  down.textContent = "👎 不准";
  const send = (rating) => {
    up.disabled = down.disabled = true;
    fetch("/yijing/api/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id: id || null, rating, question: state.question, category: state.category }),
    }).catch(() => {}).finally(() => { tip.textContent = "已记录，感谢反馈。"; });
  };
  up.addEventListener("click", () => send(1));
  down.addEventListener("click", () => send(-1));
  fb.append(tip, up, down);
  panel.appendChild(fb);
  const note = document.createElement("p");
  note.className = "llm-note";
  note.textContent = "以上由大模型生成，非经文原意；占断仅供参考，事在人为。";
  panel.appendChild(note);
}


// —— 多轮追问：/yijing/api/chat，上下文 = 卦象事实 + 首轮解读 ——
function chatContext(r) {
  return {
    ben: r.ben ? r.ben.fullName : null,
    zhi: r.zhi ? r.zhi.fullName : null,
    hu: (findHexagram(huBits(r.bits).lower.concat(huBits(r.bits).upper), HEXAGRAMS) || {}).fullName || null,
    moving: r.moving.map((i) => (r.ben.yaos[i] ? r.ben.yaos[i].title : `第${i + 1}爻`)),
    rule: r.rule,
    reading: state.lastReading,
  };
}

function chatBubble(role, text) {
  const log = $("chat-log");
  const div = document.createElement("div");
  div.className = "bubble " + role;
  div.textContent = text;
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
  return div;
}

function sendChat() {
  const input = $("chat-text");
  const text = input.value.trim();
  const r = state.lastResult;
  if (!text || !r) return;
  input.value = "";
  state.chat.push({ role: "user", content: text });
  chatBubble("user", text);
  const pending = chatBubble("assistant", "……");
  $("chat-send").disabled = true;
  fetch("/yijing/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ category: state.category, context: chatContext(r), messages: state.chat }),
    signal: AbortSignal.timeout(100000),
  })
    .then((rp) => rp.json())
    .then((data) => {
      if (!data || !data.ok) throw new Error((data && data.error) || "bad response");
      pending.textContent = data.text;
      state.chat.push({ role: "assistant", content: data.text });
    })
    .catch((e) => {
      pending.textContent = "追问暂不可用（" + e.message + "）。";
      state.chat.pop(); // 失败不留下悬空的用户轮
    })
    .finally(() => {
      $("chat-send").disabled = false;
      $("chat-log").scrollTop = $("chat-log").scrollHeight;
    });
}

document.addEventListener("DOMContentLoaded", () => {
  $("btn-start").addEventListener("click", startCast);
  $("btn-again").addEventListener("click", startCast);
  $("btn-back").addEventListener("click", () => showScreen("ask"));
  $("btn-llm").addEventListener("click", requestInterpret);
  $("chat-send").addEventListener("click", sendChat);
  $("chat-text").addEventListener("keydown", (e) => { if (e.key === "Enter") sendChat(); });
  $("btn-history").addEventListener("click", () => { renderHistory(); $("history-panel").classList.remove("hidden"); });
  $("btn-close-history").addEventListener("click", () => $("history-panel").classList.add("hidden"));
  $("btn-clear-history").addEventListener("click", clearHistory);
});
