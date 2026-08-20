"""SQLite 访问 — schema、呼号库导入/查询、评论 CRUD 与评论树组装。"""
import json
import sqlite3

from callsign import base_callsign

SCHEMA = """
CREATE TABLE IF NOT EXISTS comments(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  page TEXT NOT NULL,
  parent_id INTEGER,
  callsign TEXT NOT NULL,
  message TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'published',
  is_admin INTEGER NOT NULL DEFAULT 0,
  ip TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY(parent_id) REFERENCES comments(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_comments_page ON comments(page, created_at);
CREATE INDEX IF NOT EXISTS idx_comments_parent ON comments(parent_id);
CREATE TABLE IF NOT EXISTS callsigns(callsign TEXT PRIMARY KEY);
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT);
"""


def connect(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA foreign_keys=ON')
    return conn


def init_db(conn):
    conn.executescript(SCHEMA)
    conn.commit()


def import_callsigns(conn, json_path, meta_date=None):
    """从 clublog_users.json 重建 callsigns 表。返回去重后的基准呼号条数。"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    seen = set()
    for key in data.keys():
        base = base_callsign(key)
        if base:
            seen.add(base)
    conn.execute('DELETE FROM callsigns')
    conn.executemany('INSERT OR IGNORE INTO callsigns(callsign) VALUES (?)',
                     [(c,) for c in seen])
    if meta_date:
        conn.execute('INSERT OR REPLACE INTO meta(key,value) VALUES (?,?)',
                     ('db_updated_at', meta_date))
        conn.execute('INSERT OR REPLACE INTO meta(key,value) VALUES (?,?)',
                     ('db_count', str(len(seen))))
    conn.commit()
    return len(seen)


def callsign_exists(conn, call):
    return conn.execute('SELECT 1 FROM callsigns WHERE callsign=?', (call,)).fetchone() is not None


def get_meta(conn):
    return conn.execute('SELECT key, value FROM meta').fetchall()


def add_comment(conn, page, callsign_, message, ip, parent_id=None, is_admin=0, status='published'):
    cur = conn.execute(
        'INSERT INTO comments(page,parent_id,callsign,message,status,is_admin,ip) VALUES (?,?,?,?,?,?,?)',
        (page, parent_id, callsign_, message, status, is_admin, ip))
    conn.commit()
    return cur.lastrowid


def get_comment(conn, cid):
    return conn.execute('SELECT * FROM comments WHERE id=?', (cid,)).fetchone()


def set_status(conn, cid, status):
    conn.execute('UPDATE comments SET status=? WHERE id=?', (status, cid))
    conn.commit()


def delete_comment(conn, cid):
    conn.execute('DELETE FROM comments WHERE id=?', (cid,))
    conn.commit()


def comment_depth(conn, cid, max_depth=10):
    depth = 0
    while cid is not None and depth < max_depth:
        depth += 1
        row = conn.execute('SELECT parent_id FROM comments WHERE id=?', (cid,)).fetchone()
        cid = row['parent_id'] if row else None
    return depth


def get_comments(conn, page, include_hidden=False, limit=100):
    """返回该页评论树（顶层限 limit 条）。官方回复每层置顶；hidden 隐藏整个子树。"""
    rows = conn.execute('SELECT * FROM comments WHERE page=? ORDER BY created_at, id',
                        (page,)).fetchall()
    if not rows:
        return []
    nodes = {}
    for r in rows:
        nodes[r['id']] = {
            'id': r['id'], 'parent_id': r['parent_id'], 'callsign': r['callsign'],
            'message': r['message'], 'status': r['status'], 'is_admin': bool(r['is_admin']),
            'created_at': r['created_at'], 'children': [],
        }
    for r in rows:
        n = nodes[r['id']]
        if r['parent_id'] is not None and r['parent_id'] in nodes:
            nodes[r['parent_id']]['children'].append(n)

    if not include_hidden:
        hidden = set()

        def mark(nid):
            if nid in hidden:
                return
            hidden.add(nid)
            for c in nodes[nid]['children']:
                mark(c['id'])

        for r in rows:
            if r['status'] == 'hidden':
                mark(r['id'])

        def prune(ns):
            out = [n for n in ns if n['id'] not in hidden]
            for n in out:
                n['children'] = prune(n['children'])
            return out
    else:
        def prune(ns):
            return list(ns)

    def sort_level(ns):
        ns.sort(key=lambda n: (0 if n['is_admin'] else 1, n['created_at'], n['id']))
        for n in ns:
            sort_level(n['children'])

    roots = prune([nodes[r['id']] for r in rows if r['parent_id'] is None])
    sort_level(roots)
    return roots[:limit]


def list_all(conn, page_filter='', callsign_filter='', status_filter='', limit=500):
    """后台平铺列表，按时间倒序。"""
    q = 'SELECT * FROM comments WHERE 1=1'
    params = []
    if page_filter:
        q += ' AND page LIKE ?'
        params.append('%' + page_filter + '%')
    if callsign_filter:
        q += ' AND callsign LIKE ?'
        params.append('%' + callsign_filter + '%')
    if status_filter in ('published', 'hidden'):
        q += ' AND status=?'
        params.append(status_filter)
    q += ' ORDER BY created_at DESC, id DESC LIMIT ?'
    params.append(limit)
    return conn.execute(q, params).fetchall()


def count_all(conn, status=None):
    if status:
        return conn.execute('SELECT COUNT(*) FROM comments WHERE status=?', (status,)).fetchone()[0]
    return conn.execute('SELECT COUNT(*) FROM comments').fetchone()[0]
