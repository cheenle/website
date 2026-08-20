/* VLSC 反馈 Widget — 自动注入（由 global-nav.js bootstrap 触发）。
   渲染评论树、呼号验证提交流程、EN/CN i18n。无依赖。 */
(function () {
  'use strict';

  if (location.hostname !== 'www.vlsc.net') return;          // 仅线上域名
  if (/\/feedback\/(admin|api)/.test(location.pathname)) return;

  var API = '/feedback/api';
  var MAX_DEPTH = 3;
  var isCN = (document.documentElement.getAttribute('lang') || '').indexOf('zh') === 0
    || /\/zh\//.test(location.pathname);

  var L = isCN ? {
    title: '反馈与问题', subtitle: '提问、建议或报告问题。发布前需通过呼号验证（Club Log 数据库，与 RumLogNG 同源）。',
    callLabel: 'HAM 呼号', callPh: '如 BG1SB', placeholder: '写下你的问题或反馈…',
    submit: '发布', submitting: '正在验证呼号…', reply: '回复', replyPh: '回复内容…',
    replyBtn: '回复', cancel: '取消', adminBadge: '官方回复',
    empty: '还没有反馈，来抢沙发？',
    err_format: '呼号格式不正确（示例：BG1SB）',
    err_not_in_db: '呼号未在 Club Log 数据库中找到（RumLogNG 同源数据），请检查拼写。',
    err_rate_limit: '提交过于频繁，请稍后再试。',
    err_generic: '提交失败，请稍后再试。',
    ok: '发布成功！', loading: '加载评论…', loadFailed: '评论加载失败',
    now: '刚刚'
  } : {
    title: 'Feedback & Questions', subtitle: 'Ask questions, suggest, or report issues. A valid callsign (Club Log database, same source as RumLogNG) is required.',
    callLabel: 'HAM Callsign', callPh: 'e.g. BG1SB', placeholder: 'Write your question or feedback…',
    submit: 'Post', submitting: 'Validating callsign…', reply: 'Reply', replyPh: 'Reply…',
    replyBtn: 'Reply', cancel: 'Cancel', adminBadge: 'Official',
    empty: 'No feedback yet — be the first!',
    err_format: 'Invalid callsign format (e.g. BG1SB)',
    err_not_in_db: 'Callsign not found in the Club Log database (RumLogNG data source). Check spelling.',
    err_rate_limit: 'Too many submissions. Please try again later.',
    err_generic: 'Submission failed. Please try again.',
    ok: 'Posted!', loading: 'Loading…', loadFailed: 'Failed to load comments',
    now: 'just now'
  };

  function esc(s) { return String(s).replace(/[&<>"']/g, function (c) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }

  function pageKey() {
    var p = location.pathname.replace(/\/+$/, '');
    p = p.replace(/^\/zh(?=\/|$)/, '');          // EN/CN 共享线程
    p = p.replace(/\/index\.html$/, '');
    return p || '/';
  }

  function fmtTime(utc) {
    if (!utc) return '';
    var d = new Date(utc.replace(' ', 'T') + 'Z');
    if (isNaN(d)) return utc;
    var now = Date.now();
    if (now - d.getTime() < 60000) return L.now;
    try { return d.toLocaleString(); } catch (e) { return utc; }
  }

  function rememberCall(c) { try { localStorage.setItem('vlsc-fb-call', c); } catch (e) {} }
  function recallCall() { try { return localStorage.getItem('vlsc-fb-call') || ''; } catch (e) { return ''; } }

  var CALL_RE = /^[0-9]?[A-Z]{1,2}[0-9][A-Z]{1,3}$/;

  function buildSection() {
    var sec = document.createElement('section');
    sec.id = 'vlsc-feedback';
    sec.className = 'vlsc-feedback';
    sec.innerHTML =
      '<div class="vlsc-fb-container">' +
        '<div class="vlsc-fb-head"><h2>' + esc(L.title) + '</h2><p>' + esc(L.subtitle) + '</p></div>' +
        '<div id="vlsc-fb-list" class="vlsc-fb-list"><p class="vlsc-fb-muted">' + esc(L.loading) + '</p></div>' +
        '<form id="vlsc-fb-form" class="vlsc-fb-form" autocomplete="off">' +
          '<div class="vlsc-fb-row">' +
            '<label for="vlsc-fb-call">' + esc(L.callLabel) + '</label>' +
            '<input id="vlsc-fb-call" name="callsign" required maxlength="12" placeholder="' + esc(L.callPh) + '" value="' + esc(recallCall()) + '">' +
          '</div>' +
          '<textarea id="vlsc-fb-msg" name="message" required maxlength="2000" rows="4" placeholder="' + esc(L.placeholder) + '"></textarea>' +
          '<input type="text" name="website" class="vlsc-fb-hp" tabindex="-1" autocomplete="off">' +
          '<div id="vlsc-fb-replying" class="vlsc-fb-replying" hidden></div>' +
          '<div class="vlsc-fb-actions">' +
            '<button type="submit" class="vlsc-fb-btn">' + esc(L.submit) + '</button>' +
            '<span id="vlsc-fb-status" class="vlsc-fb-status"></span>' +
          '</div>' +
        '</form>' +
      '</div>';
    document.body.appendChild(sec);
  }

  var $ = function (id) { return document.getElementById(id); };

  function showStatus(el, msg, cls) {
    el.textContent = msg;
    el.className = 'vlsc-fb-status' + (cls ? ' ' + cls : '');
  }

  function render(comments) {
    var box = $('vlsc-fb-list');
    if (!comments || !comments.length) {
      box.innerHTML = '<p class="vlsc-fb-muted">' + esc(L.empty) + '</p>';
      return;
    }
    box.innerHTML = '';
    var ul = document.createElement('ul');
    ul.className = 'vlsc-fb-thread';
    comments.forEach(function (c) { ul.appendChild(node(c, 0)); });
    box.appendChild(ul);
  }

  function node(c, depth) {
    var li = document.createElement('li');
    li.className = 'vlsc-fb-item' + (c.is_admin ? ' vlsc-fb-admin' : '');
    var meta = '<span class="vlsc-fb-call">' + esc(c.callsign) + '</span>' +
      (c.is_admin ? '<span class="vlsc-fb-badge">' + esc(L.adminBadge) + '</span>' : '') +
      '<span class="vlsc-fb-time">' + esc(fmtTime(c.created_at)) + '</span>';
    li.innerHTML =
      '<div class="vlsc-fb-meta">' + meta + '</div>' +
      '<div class="vlsc-fb-body">' + esc(c.message).replace(/\n/g, '<br>') + '</div>' +
      '<div class="vlsc-fb-actions2"></div>';
    if (depth < MAX_DEPTH) {
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'vlsc-fb-reply';
      btn.textContent = L.reply;
      btn.addEventListener('click', function () { toggleReplyForm(li, c.id); });
      li.querySelector('.vlsc-fb-actions2').appendChild(btn);
    }
    if (c.children && c.children.length) {
      var childUl = document.createElement('ul');
      childUl.className = 'vlsc-fb-thread vlsc-fb-child';
      c.children.forEach(function (ch) { childUl.appendChild(node(ch, depth + 1)); });
      li.appendChild(childUl);
    }
    return li;
  }

  function toggleReplyForm(li, cid) {
    var existing = li.querySelector('.vlsc-fb-reply-form');
    if (existing) { existing.remove(); return; }
    var form = document.createElement('form');
    form.className = 'vlsc-fb-reply-form';
    form.innerHTML =
      '<textarea required maxlength="2000" placeholder="' + esc(L.replyPh) + '"></textarea>' +
      '<div class="vlsc-fb-row">' +
        '<label>' + esc(L.callLabel) + '</label>' +
        '<input name="callsign" required maxlength="12" value="' + esc(recallCall()) + '">' +
      '</div>' +
      '<div class="vlsc-fb-actions">' +
        '<button type="submit" class="vlsc-fb-btn">' + esc(L.replyBtn) + '</button>' +
        '<button type="button" class="vlsc-fb-reply">' + esc(L.cancel) + '</button>' +
        '<span class="vlsc-fb-status"></span>' +
      '</div>';
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      submitComment(form, cid);
    });
    form.querySelector('button[type="button"]').addEventListener('click', function () { form.remove(); });
    li.querySelector('.vlsc-fb-actions2').appendChild(form);
  }

  function submitComment(form, replyId) {
    var call = (form.querySelector('input[name="callsign"]').value || '').toUpperCase().replace(/\s+/g, '');
    var msg = form.querySelector('textarea').value.trim();
    var statusEl = form.querySelector('.vlsc-fb-status');
    var btn = form.querySelector('button[type="submit"]');
    if (!CALL_RE.test(call)) { showStatus(statusEl, L.err_format, 'vlsc-fb-err'); return; }
    if (msg.length < 2) { showStatus(statusEl, L.err_generic, 'vlsc-fb-err'); return; }
    btn.disabled = true;
    btn.textContent = L.submitting;
    fetch(API + '/comment', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ page: pageKey(), callsign: call, message: msg, reply_to: replyId, website: '' })
    }).then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
      .then(function (res) {
        if (res.ok && res.j && res.j.ok) {
          rememberCall(call);
          if (form.id === 'vlsc-fb-form') { $('vlsc-fb-msg').value = ''; }
          showStatus(statusEl, L.ok, 'vlsc-fb-ok');
          load();
          if (replyId) { var f = form; setTimeout(function () { f.remove(); }, 1200); }
        } else {
          var code = res.j && res.j.error;
          showStatus(statusEl, { format: L.err_format, not_in_db: L.err_not_in_db,
            rate_limit: L.err_rate_limit }[code] || L.err_generic, 'vlsc-fb-err');
        }
      })
      .catch(function () { showStatus(statusEl, L.err_generic, 'vlsc-fb-err'); })
      .then(function () {
        btn.disabled = false;
        btn.textContent = (form.id === 'vlsc-fb-form') ? L.submit : L.replyBtn;
      });
  }

  function load() {
    var box = $('vlsc-fb-list');
    if (box) box.innerHTML = '<p class="vlsc-fb-muted">' + esc(L.loading) + '</p>';
    fetch(API + '/comments?page=' + encodeURIComponent(pageKey()))
      .then(function (r) { return r.json(); })
      .then(function (j) {
        if (j && j.ok) render(j.comments || []);
        else if (box) box.innerHTML = '<p class="vlsc-fb-muted">' + esc(L.loadFailed) + '</p>';
      })
      .catch(function () {
        if (box) box.innerHTML = '<p class="vlsc-fb-muted">' + esc(L.loadFailed) + '</p>';
      });
  }

  function init() {
    if (!document.body) { document.addEventListener('DOMContentLoaded', init); return; }
    buildSection();
    var form = $('vlsc-fb-form');
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      submitComment(form, null);
    });
    load();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
