"""VLSC 反馈服务 — HTTP API + 管理后台（Python 标准库）。
运行：python3 service.py   （cwd = /home/cheenle/feedback）
"""
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import callsign
import db

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, 'feedback.db')


def load_config():
    with open(os.path.join(BASE, 'config.json'), encoding='utf-8') as f:
        return json.load(f)


CONFIG = load_config()

PAGE_RE = re.compile(r'[a-z0-9/_\-]{1,200}')


def normalize_page(raw):
    if not isinstance(raw, str):
        return ''
    p = raw.strip()
    p = re.sub(r'^/zh(?=/|$)', '', p)          # EN/CN 共享同一线程
    p = p.rstrip('/')
    p = re.sub(r'/index\.html$', '', p)
    return p or '/'


def valid_page(raw):
    return bool(PAGE_RE.fullmatch(normalize_page(raw)))


def get_conn():
    return db.connect(DB_PATH)


# ── 限流（进程内存）──
_lock = threading.Lock()
_ip_hits = {}
_call_hits = {}


def _rate_limited(key, max_count, window_seconds, store):
    now = time.time()
    with _lock:
        ts = [t for t in store.get(key, []) if t > now - window_seconds]
        if len(ts) >= max_count:
            store[key] = ts
            return True
        ts.append(now)
        store[key] = ts
        return False


# ── 邮件通知（异步，msmtp；失败仅记日志）──
def _notify_owner(page, call, msg, cid):
    def run():
        subject = '[VLSC Feedback] %s (%s)' % (call, page)
        body = ('新反馈 #%d\n页面：%s\n呼号：%s\n时间：%s\n\n%s\n\n'
                '后台管理：https://www.vlsc.net/feedback/admin/\n'
                % (cid, page, call, time.strftime('%Y-%m-%d %H:%M:%S'), msg))
        mail = ('From: %s\nTo: %s\nSubject: %s\nMIME-Version: 1.0\n'
                'Content-Type: text/plain; charset=UTF-8\n'
                'Content-Transfer-Encoding: 8bit\n\n%s\n'
                % (CONFIG['mail_from'], CONFIG['owner_email'], subject, body))
        try:
            subprocess.run(['msmtp', '-t'], input=mail.encode('utf-8'),
                           capture_output=True, timeout=30)
        except Exception as e:  # 不阻塞发布
            sys.stderr.write('mail notify failed: %s\n' % e)
    threading.Thread(target=run, daemon=True).start()


# ── 业务路由 ──
def handle_request(method, path, query, body, ip, origin=None):
    """返回 (http_status, content_type, bytes)。"""
    if path == '/feedback/admin/' and method == 'GET':
        return 200, 'text/html; charset=utf-8', _admin_page(query).encode('utf-8')
    if path == '/feedback/admin/action' and method == 'POST':
        if origin and origin not in ('https://www.vlsc.net', 'http://www.vlsc.net'):
            return 403, 'application/json; charset=utf-8', b'{"ok":false,"error":"forbidden"}'
        status, payload = _admin_action(body or {})
        return status, 'application/json; charset=utf-8', \
            json.dumps(payload, ensure_ascii=False).encode('utf-8')
    if path == '/feedback/api/comments' and method == 'GET':
        page = query.get('page', '')
        if not valid_page(page):
            return 400, 'application/json; charset=utf-8', b'{"ok":false,"error":"invalid_page"}'
        with get_conn() as conn:
            tree = db.get_comments(conn, normalize_page(page))
        return 200, 'application/json; charset=utf-8', \
            json.dumps({'ok': True, 'comments': tree}, ensure_ascii=False).encode('utf-8')
    if path == '/feedback/api/comment' and method == 'POST':
        status, payload = _submit_comment(body or {}, ip)
        return status, 'application/json; charset=utf-8', \
            json.dumps(payload, ensure_ascii=False).encode('utf-8')
    return 404, 'application/json; charset=utf-8', b'{"ok":false,"error":"not_found"}'


def _submit_comment(body, ip):
    if body.get('website'):                       # 蜜罐：假装成功但丢弃
        return 200, {'ok': True, 'id': 0}
    page = body.get('page', '')
    if not valid_page(page):
        return 400, {'ok': False, 'error': 'invalid_page'}
    page = normalize_page(page)
    call = callsign.normalize(body.get('callsign', ''))
    if not call or not callsign.is_valid_format(call):
        return 400, {'ok': False, 'error': 'format'}
    msg = (body.get('message') or '').strip()
    if not (2 <= len(msg) <= CONFIG['max_message_len']):
        return 400, {'ok': False, 'error': 'message_length'}
    reply_to = body.get('reply_to')
    if reply_to not in (None, ''):
        try:
            reply_to = int(reply_to)
        except (TypeError, ValueError):
            return 400, {'ok': False, 'error': 'invalid_reply'}
    else:
        reply_to = None
    if _rate_limited(ip or '?', CONFIG['rate_ip_per_hour'], 3600, _ip_hits):
        return 429, {'ok': False, 'error': 'rate_limit'}
    if _rate_limited(call, CONFIG['rate_call_per_day'], 86400, _call_hits):
        return 429, {'ok': False, 'error': 'rate_limit'}
    with get_conn() as conn:
        if not db.callsign_exists(conn, call):
            return 400, {'ok': False, 'error': 'not_in_db'}
        if reply_to is not None:
            parent = db.get_comment(conn, reply_to)
            if not parent or parent['page'] != page or parent['status'] != 'published':
                return 400, {'ok': False, 'error': 'invalid_reply'}
            if db.comment_depth(conn, reply_to) >= 3:
                return 400, {'ok': False, 'error': 'depth_limit'}
        cid = db.add_comment(conn, page, call, msg, ip, parent_id=reply_to)
    _notify_owner(page, call, msg, cid)
    return 200, {'ok': True, 'id': cid}


def _admin_action(body):
    action = body.get('action')
    try:
        cid = int(body.get('id'))
    except (TypeError, ValueError):
        return 400, {'ok': False, 'error': 'bad_id'}
    with get_conn() as conn:
        if action == 'delete':
            db.delete_comment(conn, cid)
        elif action == 'hide':
            db.set_status(conn, cid, 'hidden')
        elif action == 'unhide':
            db.set_status(conn, cid, 'published')
        elif action == 'reply':
            msg = (body.get('message') or '').strip()
            if not (1 <= len(msg) <= CONFIG['max_message_len']):
                return 400, {'ok': False, 'error': 'message_length'}
            parent = db.get_comment(conn, cid)
            if not parent:
                return 400, {'ok': False, 'error': 'bad_id'}
            if db.comment_depth(conn, cid) >= 3:
                return 400, {'ok': False, 'error': 'depth_limit'}
            db.add_comment(conn, parent['page'], CONFIG['owner_callsign'], msg,
                           ip=None, parent_id=cid, is_admin=1)
        else:
            return 400, {'ok': False, 'error': 'bad_action'}
    return 200, {'ok': True}


def _admin_page(query):
    from html import escape as esc
    page_filter = (query.get('page') or '').strip()
    call_filter = (query.get('callsign') or '').strip().upper()
    status_filter = query.get('status') or ''
    with get_conn() as conn:
        rows = db.list_all(conn, page_filter, call_filter, status_filter)
        meta = dict(db.get_meta(conn))
        total = db.count_all(conn)
        hidden = db.count_all(conn, 'hidden')
    status_opts = ''
    for s, label in (('', '全部状态'), ('published', '已发布'), ('hidden', '已隐藏')):
        sel = ' selected' if status_filter == s else ''
        status_opts += '<option value="%s"%s>%s</option>' % (s, sel, label)
    items = []
    for r in rows:
        badge = '官方回复' if r['is_admin'] else r['callsign']
        reply_form = (
            '<details><summary>回复</summary>'
            '<form method="post" action="/feedback/admin/action" class="f-reply">'
            '<input type="hidden" name="action" value="reply">'
            '<input type="hidden" name="id" value="%d">'
            '<textarea name="message" required maxlength="2000"></textarea>'
            '<button type="submit">发布官方回复</button></form></details>'
            % r['id'])
        hide_btn = ('<form method="post" action="/feedback/admin/action" class="f-btn">'
                    '<input type="hidden" name="action" value="%s">'
                    '<input type="hidden" name="id" value="%d">'
                    '<button type="submit">%s</button></form>'
                    % ('unhide' if r['status'] == 'hidden' else 'hide',
                       r['id'], '取消隐藏' if r['status'] == 'hidden' else '隐藏'))
        del_btn = ('<form method="post" action="/feedback/admin/action" class="f-btn" '
                   'onsubmit="return confirm(\'确认删除该条及其所有回复？\')">'
                   '<input type="hidden" name="action" value="delete">'
                   '<input type="hidden" name="id" value="%d">'
                   '<button type="submit" class="danger">删除</button></form>' % r['id'])
        items.append(
            '<div class="f-item %s"><div class="f-meta">'
            '<span class="f-id">#%d</span><span class="f-call">%s</span>'
            '<span class="f-page">%s</span><span>%s</span><span>%s</span></div>'
            '<div class="f-msg">%s</div>'
            '<div class="f-actions">%s%s%s</div></div>'
            % (('f-admin' if r['is_admin'] else '') + (' f-status-hidden' if r['status'] == 'hidden' else ''),
               r['id'], esc(badge), esc(r['page']), esc(r['created_at']), esc(r['ip'] or ''),
               esc(r['message']).replace('\n', '<br>'), reply_form, hide_btn, del_btn))
    rows_html = '\n'.join(items) if items else '<p class="none">暂无反馈</p>'
    db_line = '呼号库更新：%s（%s 条）' % (meta.get('db_updated_at', '未导入'), meta.get('db_count', '0'))
    html = """<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<title>VLSC 反馈管理</title>
<style>
body{font-family:system-ui,-apple-system,sans-serif;background:#0a0e14;color:#e5e7eb;margin:0;padding:24px}
h1{font-size:20px;margin:0 0 12px}.wrap{max-width:960px;margin:0 auto}
.filters form{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:12px 0}
input,select,button{background:#111827;color:#e5e7eb;border:1px solid #1f2937;border-radius:6px;padding:6px 10px;font-size:14px}
button{cursor:pointer}.f-item{background:#111827;border:1px solid #1f2937;border-radius:8px;padding:12px;margin:10px 0}
.f-admin{outline:1px solid #b45309}.f-status-hidden{opacity:.55}.f-status-hidden .f-msg::after{content:' [已隐藏]';color:#f87171}
.f-meta{font-size:12px;color:#9ca3af;display:flex;gap:12px;flex-wrap:wrap;align-items:center}
.f-call{color:#22d3ee;font-family:ui-monospace,monospace;font-weight:700}.f-id{color:#6b7280}
.f-page{color:#a78bfa;font-family:ui-monospace,monospace}.f-msg{margin:8px 0;white-space:pre-wrap;line-height:1.5}
.f-actions{display:flex;gap:8px;margin-top:8px;flex-wrap:wrap;align-items:flex-start}
.f-actions form{display:inline}.f-btn button{padding:4px 10px;font-size:12px}
.f-btn .danger{border-color:#7f1d1d;color:#f87171}
details summary{cursor:pointer;color:#22d3ee;font-size:13px;padding:2px 0}
.f-reply textarea{width:100%%;min-height:70px;box-sizing:border-box;margin:6px 0;display:block}
.foot{margin-top:24px;font-size:12px;color:#9ca3af;display:flex;gap:16px;flex-wrap:wrap}
.none{color:#9ca3af}
</style></head><body><div class="wrap">
<h1>VLSC 反馈管理</h1>
<div class="filters"><form method="get" action="/feedback/admin/">
<input name="page" placeholder="页面包含…" value="%s">
<input name="callsign" placeholder="呼号包含…" value="%s">
<select name="status">%s</select>
<button type="submit">筛选</button>
<a href="/feedback/admin/" style="color:#22d3ee;font-size:13px">重置</a>
</form></div>
<div class="foot"><span>%s</span><span>评论总数：%d（隐藏 %d）</span><span>共显示 %d 条</span></div>
%s</div></body></html>
""" % (esc(page_filter), esc(call_filter), status_opts, db_line, total, hidden, len(rows), rows_html)
    return html


# ── HTTP 层 ──
class Handler(BaseHTTPRequestHandler):
    def _serve(self):
        parsed = urllib.parse.urlparse(self.path)
        query = {k: v[0] for k, v in urllib.parse.parse_qs(parsed.query).items()}
        body = None
        length = int(self.headers.get('Content-Length') or 0)
        if length:
            raw = self.rfile.read(length).decode('utf-8')
            if 'application/json' in self.headers.get('Content-Type', ''):
                try:
                    body = json.loads(raw)
                except Exception:
                    body = None
            else:  # 后台 HTML 表单（application/x-www-form-urlencoded）
                body = {k: v[0] for k, v in urllib.parse.parse_qs(raw).items()}
        ip = self.headers.get('X-Real-IP') or self.client_address[0]
        origin = self.headers.get('Origin')
        status, ctype, data = handle_request(self.command, parsed.path, query, body, ip, origin)
        self.send_response(status)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self._serve()

    def do_POST(self):
        self._serve()

    def log_message(self, fmt, *args):
        sys.stderr.write('%s - %s\n' % (self.address_string(), fmt % args))


def main():
    conn = get_conn()
    db.init_db(conn)
    conn.close()
    srv = ThreadingHTTPServer((CONFIG['listen_host'], CONFIG['listen_port']), Handler)
    sys.stderr.write('feedback service: http://%s:%d\n'
                     % (CONFIG['listen_host'], CONFIG['listen_port']))
    srv.serve_forever()


if __name__ == '__main__':
    main()
