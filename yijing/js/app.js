/* global TRIGRAMS, HEXAGRAMS, castLine, huBits, trigramName, findHexagram, duanCi, yaoFacts, cuoBits, zongBits, meihuaByTime, meihuaByNumbers, najia, meridianOf */

const HISTORY_KEY = "yijing-history";
const HISTORY_MAX = 50;
const TOSS_MS = 900;

const LINE_NAMES = { 6: "老阴（动）", 7: "少阳", 8: "少阴", 9: "老阳（动）" };
const YAO_MARK = { 6: "×", 9: "○" };

const state = { question: "", category: "综合", lines: [], chat: [], lastReading: "", lastLlmId: null, owner: "" };

function ownerKey() {
  if (state.owner) return state.owner;
  try { state.owner = localStorage.getItem("yijing-owner") || ""; } catch (e) { state.owner = ""; }
  return state.owner;
}

function verifyOwner() {
  const key = $("deep-key").value.trim();
  if (!key) return;
  fetch("/yijing/api/verify", {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ key }),
  })
    .then((rp) => rp.json())
    .then((d) => {
      if (d && d.ok) {
        state.owner = key;
        try { localStorage.setItem("yijing-owner", key); } catch (e) { /* 忽略 */ }
        $("btn-deep").textContent = "深度模式（自用）：已解锁——健康类可辨证荐方";
        $("deep-row").classList.add("hidden");
      } else {
        $("btn-deep").textContent = "深度模式：密钥不对";
      }
    })
    .catch(() => { $("btn-deep").textContent = "深度模式：校验失败"; });
}

function $(id) { return document.getElementById(id); }

function showScreen(name) {
  for (const s of ["ask", "cast", "result"]) {
    $("screen-" + s).classList.toggle("hidden", s !== name);
  }
}

function currentMethod() {
  const m = document.querySelector('input[name="method"]:checked');
  return m ? m.value : "tongqian";
}

function startCast() {
  state.question = $("question").value.trim();
  const checked = document.querySelector('input[name="category"]:checked');
  state.category = checked ? checked.value : "综合";
  state.method = currentMethod();
  state.meihua = null;
  state.lines = [];
  if (state.method === "meihua-time") { renderMeihuaResult(meihuaByTime(new Date())); return; }
  if (state.method === "meihua-num") {
    const n1 = parseInt($("num1").value, 10);
    const n2 = parseInt($("num2").value, 10);
    if (!n1 || !n2 || n1 < 1 || n2 < 1) return;
    renderMeihuaResult(meihuaByNumbers(n1, n2));
    return;
  }
  if (state.method === "random") {
    state.lines = castGua(Math.random);
    renderResult();
    return;
  }
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
    playCoin();
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


  const nj = r.ben ? najia(r.bits, r.ben.fullName, new Date()) : null;
  if (nj) {
    const naj = document.createElement("div");
    naj.className = "duan-entry";
    const rows = nj.yaos.map((y, i) =>
      `${["初","二","三","四","五","上"][i]}爻 ${y.liushou} ${y.ganZhi}（${y.wuxing}）${y.liuqin}${y.shi ? " ·世" : ""}${y.ying ? " ·应" : ""}`)
      .join("　");
    naj.innerHTML = `<div class="source">纳甲装卦（${nj.gong}宫·${nj.gongWuxing}）世${nj.shi}爻 应${nj.ying}爻</div>` +
      `<p class="ci" style="font-size:0.95rem">${rows}</p>` +
      `<p class="ref">用神：${nj.yongshen[state.category] || nj.yongshen["综合"]}；子午流注：当前${meridianOf(new Date()).shi}时当令${meridianOf(new Date()).jing}</p>`;
    duan.insertBefore(naj, duan.firstChild);
  }

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

const TRACK_DAYS = { "7": 7, "30": 30 };

function saveRecord(r) {
  try {
    const list = loadHistory();
    const period = $("track-period") ? $("track-period").value : "0";
    const days = TRACK_DAYS[period];
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
      llmId: state.lastLlmId || null,
      reading: String(state.lastReading || "").slice(0, 300),
      trackUntil: days ? Date.now() + days * 86400000 : null,
      outcome: null,
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
    const outcomeText = rec.outcome == null
      ? (rec.trackUntil ? " · 待回访" : "")
      : ` · 已回填：${["不准", "部分准", "非常准"][rec.outcome + 1] || rec.outcome}`;
    li.innerHTML = `<div>${escapeHtml(rec.benName || "?")}${rec.zhiName ? " 之 " + escapeHtml(rec.zhiName) : ""} · ${movingText}</div>` +
      `<div class="meta">${t.toLocaleString("zh-CN")} · ${escapeHtml(rec.category)} · ${escapeHtml(rec.question || "心中默念")}${outcomeText}</div>`;
    ul.appendChild(li);
  }
}

// —— 应验跟踪：到期回访弹窗 + outcome 回传（与原始卦象/AI 回复绑定落盘）——
let pendingOutcomeIdx = -1;

function findPendingOutcome() {
  const list = loadHistory();
  const now = Date.now();
  for (let i = 0; i < list.length; i++) {
    const rec = list[i];
    if (rec && rec.trackUntil && rec.outcome == null && rec.trackUntil <= now) return i;
  }
  return -1;
}

function checkOutcomeOnLoad() {
  pendingOutcomeIdx = findPendingOutcome();
  if (pendingOutcomeIdx < 0) return;
  const rec = loadHistory()[pendingOutcomeIdx];
  $("outcome-question").textContent =
    `您之前问的关于【${rec.question || "心中默念"}】（${rec.category}·${rec.benName || "?"}）有结果了吗？`;
  $("outcome-modal").classList.remove("hidden");
}

function submitOutcome(rating) {
  if (pendingOutcomeIdx < 0) return;
  const list = loadHistory();
  const rec = list[pendingOutcomeIdx];
  if (!rec) { pendingOutcomeIdx = -1; return; }
  const outcomeText = $("outcome-text").value.trim();
  rec.outcome = rating;
  rec.outcomeAt = new Date().toISOString();
  list[pendingOutcomeIdx] = rec;
  try { localStorage.setItem(HISTORY_KEY, JSON.stringify(list.slice(0, HISTORY_MAX))); } catch (e) { /* 忽略 */ }
  fetch("/yijing/api/feedback", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      kind: "outcome",
      id: rec.llmId || null,
      rating,
      outcome: outcomeText,
      question: rec.question,
      category: rec.category,
      record: {
        time: rec.time, lines: rec.lines, benId: rec.benId, benName: rec.benName,
        zhiId: rec.zhiId, zhiName: rec.zhiName, moving: rec.moving, reading: rec.reading,
      },
    }),
  }).catch(() => {}).finally(() => {
    pendingOutcomeIdx = -1;
    $("outcome-modal").classList.add("hidden");
    $("outcome-text").value = "";
  });
}

function clearHistory() {
  try { localStorage.removeItem(HISTORY_KEY); } catch (e) { /* 忽略 */ }
  renderHistory();
}

// —— AI 进一步解读：经 nginx → 本机代理 → LLM，浏览器不持密钥 ——
// —— 长期记忆：本机占例档案摘要（不上传原始记录之外的内容，不跨设备）——
function buildMemory() {
  const list = loadHistory();
  if (!list.length) return null;
  const stats = {};
  for (const rec of list) {
    if (rec.outcome == null) continue;
    const k = rec.category || "综合";
    stats[k] = stats[k] || { 1: 0, 0: 0, "-1": 0 };
    stats[k][rec.outcome] = (stats[k][rec.outcome] || 0) + 1;
  }
  const lines = [];
  const recent = list.slice(0, 5);
  for (const rec of recent) {
    const d = new Date(rec.time);
    const outcome = rec.outcome == null ? "待回访" : ["不准", "部分准", "非常准"][rec.outcome + 1];
    lines.push(`${d.toLocaleDateString("zh-CN")} 问「${rec.question || "心中默念"}」(${rec.category}) 得 ${rec.benName || "?"}` +
      (rec.zhiName ? `之${rec.zhiName}` : "") + `，回访：${outcome}`);
  }
  const statLines = Object.keys(stats).map((k) => `${k}类回访 ${stats[k][1] || 0} 准 / ${stats[k][0] || 0} 部分 / ${stats[k]["-1"] || 0} 不准`);
  return {
    count: list.length,
    recent: lines,
    stats: statLines,
  };
}

function llmPayload(r) {
  if (state.meihua) {
    const m = state.meihua;
    return {
      method: "meihua",
      question: state.question,
      category: state.category,
      memory: buildMemory(),
      owner: ownerKey() || undefined,
      gua: { upper: m.upper, lower: m.lower, movingIdx: [m.moving] },
      meihua: {
        methodNote: m.methodNote, ben: m.benName, zhi: m.zhiName, hu: m.huName,
        ti: `${m.ti}（${m.tiWuxing}）`, yong: `${m.yong}（${m.yongWuxing}）`,
        relation: m.relation, relationNote: m.relationNote,
        movingWei: ["初", "二", "三", "四", "五", "上"][m.moving] + (m.bits[m.moving] === 1 ? "九" : "六"),
      },
      ben: r ? { fullName: m.benName, tuan: (findHexagram(m.bits, HEXAGRAMS) || {}).tuan, xiang: (findHexagram(m.bits, HEXAGRAMS) || {}).xiang } : null,
      duanci: (r ? r.entries : []).map((e) => ({ source: e.source, ci: e.ci, baihua: e.baihua })),
    };
  }
  const hu = huBits(r.bits);
  const huHex = findHexagram(hu.lower.concat(hu.upper), HEXAGRAMS);
  const cuoHex = findHexagram(cuoBits(r.bits), HEXAGRAMS);
  const zongHex = findHexagram(zongBits(r.bits), HEXAGRAMS);
  return {
    question: state.question,
    category: state.category,
    memory: buildMemory(),
    owner: ownerKey() || undefined,
    gua: { upper: r.ben.upper, lower: r.ben.lower, movingIdx: r.moving },
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

function readingResult() {
  if (state.lastResult) return state.lastResult;
  if (state.meihua) {
    const m = state.meihua;
    const ben = findHexagram(m.bits, HEXAGRAMS);
    const zhi = findHexagram(m.zbits, HEXAGRAMS);
    return {
      ben, zhi, moving: [m.moving], bits: m.bits, zbits: m.zbits,
      rule: `梅花易数：${m.relation}（${m.relationNote}）`,
      entries: ben ? [{ kind: "guaci", source: `本卦${ben.fullName}·卦辞`, ci: ben.guaci, tuan: ben.tuan, xiang: ben.xiang, baihua: ben.guaciBaihua, primary: true }] : [],
    };
  }
  return null;
}

function requestInterpret() {
  const r = readingResult();
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
  const isHealth = state.category === "健康";
  $("chat-hint").textContent = isHealth
    ? "健康追问将结合《黄帝内经》养生理法持续对话；具体病情以医嘱为准。"
    : "AI 会记住本卦上下文，可接着问。";
  $("chat-text").placeholder = isHealth ? "如：近来失眠多梦，起居该如何调？" : "基于此卦继续问……";
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



// —— 梅花易数结果：体用生克为主，经传为辅 ——
function renderMeihuaResult(m) {
  state.meihua = m;
  state.lastResult = null;
  state.chat = [];
  state.lastReading = "";
  $("llm-panel").classList.add("hidden");
  $("llm-panel").innerHTML = "";
  $("chat-box").classList.add("hidden");
  $("chat-log").innerHTML = "";
  $("btn-llm").disabled = false;

  const ben = findHexagram(m.bits, HEXAGRAMS);
  const zhi = findHexagram(m.zbits, HEXAGRAMS);
  const hu = findHexagram([m.bits[1], m.bits[2], m.bits[3], m.bits[2], m.bits[3], m.bits[4]], HEXAGRAMS);
  const weiName = ["初", "二", "三", "四", "五", "上"][m.moving];

  $("result-summary").innerHTML =
    `<p>所问：${escapeHtml(state.question || "心中默念")}（${state.category}）· ${escapeHtml(m.methodNote)}</p>` +
    `<p>得 <strong>${m.benName || "?"}</strong> 之 <strong>${m.zhiName || "?"}</strong>，动爻：${weiName}${m.bits[m.moving] === 1 ? "九" : "六"}</p>` +
    `<p class="facts">体卦 ${m.ti}（${m.tiWuxing}） · 用卦 ${m.yong}（${m.yongWuxing}） · <strong class="rule">${m.relation}</strong>：${m.relationNote}</p>` +
    `<p class="facts">互卦 ${m.huName || "?"}</p>`;

  const guas = $("result-guas");
  guas.innerHTML = "";
  guas.appendChild(guaCard("本卦", ben, [m.moving]));
  guas.appendChild(guaCard("变卦", zhi, []));
  guas.appendChild(guaCard("互卦", hu, []));

  const duan = $("result-duan");
  duan.innerHTML = "";
  const head = document.createElement("div");
  head.className = "duan-entry";
  head.innerHTML = `<div class="source">梅花断：体用生克</div>` +
    `<p class="ci">${escapeHtml(m.relation)}——${escapeHtml(m.relationNote)}。体卦为我、用卦为事，生克定吉凶大势。</p>`;
  duan.appendChild(head);
  for (const h of [ben, zhi]) {
    if (!h) continue;
    duan.appendChild(entryBlock({
      source: `${h === ben ? "本卦" : "变卦"}${h.fullName}·卦辞`,
      ci: h.guaci, tuan: h.tuan, xiang: h.xiang, baihua: h.guaciBaihua, primary: h === ben,
    }));
  }
  const advice = document.createElement("div");
  advice.className = "advice";
  const tip = ben && ben.advice ? ben.advice[state.category] : "经文数据缺失";
  advice.innerHTML = `<h3>问「${state.category}」要点</h3><p>${escapeHtml(tip || "经文数据缺失")}</p>`;
  duan.appendChild(advice);

  saveMeihuaRecord(m, ben, zhi);
  showScreen("result");
}

function saveMeihuaRecord(m, ben, zhi) {
  try {
    const list = loadHistory();
    const period = $("track-period") ? $("track-period").value : "0";
    const days = TRACK_DAYS[period];
    list.unshift({
      time: new Date().toISOString(),
      question: state.question,
      category: state.category,
      method: "meihua",
      lines: m.bits,
      benId: ben ? ben.id : null,
      benName: m.benName,
      zhiId: zhi ? zhi.id : null,
      zhiName: m.zhiName,
      moving: [m.moving],
      meihua: { ti: m.ti, yong: m.yong, relation: m.relation },
      llmId: state.lastLlmId || null,
      reading: String(state.lastReading || "").slice(0, 300),
      trackUntil: days ? Date.now() + days * 86400000 : null,
      outcome: null,
    });
    localStorage.setItem(HISTORY_KEY, JSON.stringify(list.slice(0, HISTORY_MAX)));
  } catch (e) { /* 隐私模式等场景静默跳过 */ }
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
    memory: buildMemory(),
    gua: r.ben ? { upper: r.ben.upper, lower: r.ben.lower, movingIdx: r.moving } : null,
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
  const r = readingResult();
  if (!text) return;
  if (!r) {
    chatBubble("assistant", "当前没有可追问的卦象，请先起卦并完成解读。");
    return;
  }
  input.value = "";
  state.chat.push({ role: "user", content: text });
  chatBubble("user", text);
  const pending = chatBubble("assistant", "……");
  $("chat-send").disabled = true;
  fetch("/yijing/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ category: state.category, owner: ownerKey() || undefined, context: chatContext(r), messages: state.chat }),
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


// —— 音效：WebAudio 合成铜钱清脆声，无音频资源 ——
let audioCtx = null;
function soundOn() {
  try { return localStorage.getItem("yijing-sound") !== "off"; } catch (e) { return true; }
}
function playCoin() {
  if (!soundOn()) return;
  try {
    audioCtx = audioCtx || new (window.AudioContext || window.webkitAudioContext)();
    if (audioCtx.state === "suspended") audioCtx.resume();
    const t = audioCtx.currentTime;
    const o = audioCtx.createOscillator();
    const g = audioCtx.createGain();
    o.type = "triangle";
    o.frequency.setValueAtTime(2400, t);
    o.frequency.exponentialRampToValueAtTime(900, t + 0.07);
    g.gain.setValueAtTime(0.18, t);
    g.gain.exponentialRampToValueAtTime(0.001, t + 0.09);
    o.connect(g); g.connect(audioCtx.destination);
    o.start(t); o.stop(t + 0.1);
  } catch (e) { /* 无音频环境静默 */ }
}
function refreshSoundBtn() {
  $("btn-sound").textContent = soundOn() ? "音效：开" : "音效：关";
}
function toggleSound() {
  try { localStorage.setItem("yijing-sound", soundOn() ? "off" : "on"); } catch (e) { /* 忽略 */ }
  refreshSoundBtn();
}

// —— 摇一摇起卦（DeviceMotion，iOS 需授权）——
let shakeOn = false, lastShakeAt = 0, lastMag = null;
function motionHandler(e) {
  const a = e.accelerationIncludingGravity;
  if (!a) return;
  const mag = Math.abs(a.x || 0) + Math.abs(a.y || 0) + Math.abs(a.z || 0);
  if (lastMag !== null && Math.abs(mag - lastMag) > 22) {
    const now = Date.now();
    if (now - lastShakeAt > 1200 && !$("screen-ask").classList.contains("hidden")) {
      lastShakeAt = now;
      startCast();
    }
  }
  lastMag = mag;
}
function toggleShake() {
  const enable = !shakeOn;
  const apply = (ok) => {
    shakeOn = ok;
    if (ok) window.addEventListener("devicemotion", motionHandler);
    else window.removeEventListener("devicemotion", motionHandler);
    $("btn-shake").textContent = ok ? "摇一摇：开（摇动手机起卦）" : "开启摇一摇起卦";
  };
  if (enable && typeof DeviceMotionEvent !== "undefined" && DeviceMotionEvent.requestPermission) {
    DeviceMotionEvent.requestPermission().then((r) => apply(r === "granted")).catch(() => apply(false));
  } else {
    apply(enable && typeof DeviceMotionEvent !== "undefined");
  }
}

// —— 卦象海报：原生 Canvas，无第三方库 ——
function wrapCJK(ctx, text, x, y, maxW, lh, maxLines) {
  let line = "", lines = 0;
  for (const ch of String(text)) {
    if (ctx.measureText(line + ch).width > maxW) {
      ctx.fillText(line, x, y); y += lh; line = ch;
      if (++lines >= maxLines) { ctx.fillText(line + "…", x, y); return y + lh; }
    } else line += ch;
  }
  if (line) { ctx.fillText(line, x, y); y += lh; }
  return y;
}

function drawYaoColumn(ctx, bits, moving, x, yTop) {
  const W = 300, H = 34, GAP = 26;
  for (let i = 5; i >= 0; i--) {
    const y = yTop + (5 - i) * (H + GAP);
    ctx.fillStyle = "#2b2622";
    if (bits[i] === 1) ctx.fillRect(x, y, W, H);
    else { ctx.fillRect(x, y, W / 2 - 22, H); ctx.fillRect(x + W / 2 + 22, y, W / 2 - 22, H); }
    if (moving.includes(i)) {
      ctx.fillStyle = "#9e2b25";
      ctx.font = "40px 'Songti SC','SimSun',serif";
      ctx.fillText(bits[i] === 1 ? "○" : "×", x + W + 16, y + H - 2);
    }
  }
}

function drawPoster(r) {
  const cv = document.createElement("canvas");
  cv.width = 1080; cv.height = 1920;
  const ctx = cv.getContext("2d");
  ctx.fillStyle = "#f5f0e6"; ctx.fillRect(0, 0, 1080, 1920);
  let seed = 7;
  const rnd = () => (seed = (seed * 1103515245 + 12345) % 2147483648) / 2147483648;
  ctx.fillStyle = "rgba(43,38,34,0.05)";
  for (let i = 0; i < 900; i++) ctx.fillRect(rnd() * 1080, rnd() * 1920, 2, 2);
  ctx.strokeStyle = "rgba(43,38,34,0.12)";
  ctx.beginPath(); ctx.moveTo(0, 1500);
  ctx.bezierCurveTo(260, 1330, 420, 1470, 640, 1360);
  ctx.bezierCurveTo(820, 1280, 960, 1420, 1080, 1340);
  ctx.lineTo(1080, 1920); ctx.lineTo(0, 1920); ctx.closePath();
  ctx.fillStyle = "rgba(43,38,34,0.06)"; ctx.fill(); ctx.stroke();
  ctx.strokeStyle = "#2b2622"; ctx.lineWidth = 3; ctx.strokeRect(46, 46, 988, 1828);

  ctx.fillStyle = "#9e2b25"; ctx.fillRect(860, 90, 130, 130);
  ctx.fillStyle = "#fff"; ctx.font = "64px 'Songti SC','SimSun',serif";
  ctx.fillText("易", 884, 152); ctx.fillText("占", 884, 212);

  ctx.fillStyle = "#2b2622"; ctx.textAlign = "center";
  ctx.font = "108px 'Songti SC','SimSun',serif";
  ctx.fillText(r.ben ? r.ben.fullName : "？", 540, 330);
  ctx.font = "46px 'Songti SC','SimSun',serif"; ctx.fillStyle = "#8a8175";
  ctx.fillText(r.zhi ? `之 ${r.zhi.fullName}` : "六爻安静", 540, 402);
  ctx.fillText(`${state.category} · ${state.question || "心中默念"}`.slice(0, 22), 540, 468);
  ctx.textAlign = "left";

  ctx.fillStyle = "#8a8175"; ctx.font = "42px 'Songti SC','SimSun',serif";
  ctx.fillText("本卦", 180, 560); ctx.fillText("之卦", 620, 560);
  drawYaoColumn(ctx, r.bits, r.moving, 180, 600);
  drawYaoColumn(ctx, r.zbits, [], 620, 600);

  const primary = r.entries[0];
  ctx.fillStyle = "#9e2b25"; ctx.font = "44px 'Songti SC','SimSun',serif";
  ctx.fillText(primary ? primary.source : "", 120, 1120);
  ctx.fillStyle = "#2b2622"; ctx.font = "56px 'Songti SC','SimSun',serif";
  let y = wrapCJK(ctx, primary ? primary.ci : "", 120, 1200, 840, 82, 3);

  const tip = state.lastReading
    ? String(state.lastReading).split(/[。！？]/)[0] + "。"
    : (r.ben && r.ben.advice ? r.ben.advice[state.category] : "");
  ctx.fillStyle = "#8a8175"; ctx.font = "40px 'Songti SC','SimSun',serif";
  ctx.fillText("寄语", 120, y + 40);
  ctx.fillStyle = "#2b2622"; ctx.font = "46px 'Songti SC','SimSun',serif";
  y = wrapCJK(ctx, tip, 120, y + 110, 840, 70, 4);

  ctx.fillStyle = "#8a8175"; ctx.font = "36px 'Songti SC','SimSun',serif";
  ctx.textAlign = "center";
  ctx.fillText("占断仅供参考，事在人为", 540, 1760);
  ctx.textAlign = "left";
  ctx.fillText("www.vlsc.net/yijing/", 120, 1820);
  ctx.textAlign = "right";
  ctx.fillText(new Date().toLocaleDateString("zh-CN"), 960, 1820);
  ctx.textAlign = "left";
  return cv.toDataURL("image/png");
}

function showPoster() {
  const r = state.lastResult;
  if (!r) return;
  const url = drawPoster(r);
  $("poster-img").src = url;
  $("poster-download").href = url;
  $("poster-modal").classList.remove("hidden");
}

document.addEventListener("DOMContentLoaded", () => {
  $("btn-start").addEventListener("click", startCast);
  $("btn-again").addEventListener("click", startCast);
  $("btn-back").addEventListener("click", () => showScreen("ask"));
  $("btn-llm").addEventListener("click", requestInterpret);
  $("chat-send").addEventListener("click", sendChat);
  $("btn-poster").addEventListener("click", showPoster);
  $("btn-poster-close").addEventListener("click", () => $("poster-modal").classList.add("hidden"));
  for (const radio of document.querySelectorAll('input[name="method"]')) {
    radio.addEventListener("change", () => {
      $("num-row").classList.toggle("hidden", currentMethod() !== "meihua-num");
    });
  }
  $("btn-deep").addEventListener("click", () => $("deep-row").classList.toggle("hidden"));
  $("btn-deep-ok").addEventListener("click", verifyOwner);
  if (ownerKey()) $("btn-deep").textContent = "深度模式（自用）：已解锁——健康类可辨证荐方";
  $("btn-sound").addEventListener("click", toggleSound);
  $("btn-shake").addEventListener("click", toggleShake);
  $("outcome-yes").addEventListener("click", () => submitOutcome(1));
  $("outcome-part").addEventListener("click", () => submitOutcome(0));
  $("outcome-no").addEventListener("click", () => submitOutcome(-1));
  $("outcome-later").addEventListener("click", () => {
    pendingOutcomeIdx = -1;
    $("outcome-modal").classList.add("hidden");
  });
  refreshSoundBtn();
  checkOutcomeOnLoad();
  $("chat-text").addEventListener("keydown", (e) => { if (e.key === "Enter") sendChat(); });
  $("btn-history").addEventListener("click", () => { renderHistory(); $("history-panel").classList.remove("hidden"); });
  $("btn-close-history").addEventListener("click", () => $("history-panel").classList.add("hidden"));
  $("btn-clear-history").addEventListener("click", clearHistory);
});
