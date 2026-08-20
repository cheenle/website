# VLSC 全站用户反馈系统 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 为 VLSC 全部站点页面添加用户反馈系统：访客用经 Club Log（RumLogNG 同源）呼号库严格验证的 HAM 呼号发帖/互回，站长邮件通知 + basic-auth 后台管理。

**架构：** Python 标准库 HTTP 服务（127.0.0.1:8021，systemd 管理）+ SQLite（评论 + 呼号库）+ nginx 反代 `/feedback/*`。前端由 global-nav.js 自动注入集中托管的 feedback.css/js。呼号库每日从 clublog.org 刷新（与 RumLogNG 同 URL）。

**技术栈：** Python 3（stdlib only）、SQLite、nginx、systemd、纯前端 JS/CSS（无框架）。

**规格：** `docs/superpowers/specs/2026-08-20-feedback-system-design.md`

---

## 文件结构

```
feedback/                            # 新建：系统源码（镜像服务器布局）
├── callsign.py                      # 呼号归一化/格式正则/基准提取（纯函数）
├── db.py                            # SQLite schema、呼号库导入/查询、评论 CRUD、评论树
├── service.py                       # HTTP API + 管理后台 + 邮件通知
├── config.json                      # 配置（owner_email=cheenle@qq.com 等）
├── update_db.py                     # 呼号库刷新（clublog 下载 / 本地种子导入）
├── static/feedback.css              # Widget 样式（octen.css 变量自适应）
├── static/feedback.js               # Widget 逻辑（渲染/提交/i18n）
├── deploy.sh                        # 部署脚本（scp + systemd + nginx）
├── vlsc-feedback.service            # systemd unit
├── vlsc-feedback-db.service         # systemd oneshot（更新任务）
├── vlsc-feedback-db.timer           # systemd timer（每日 03:00）
├── msmtp.conf.example               # SMTP 配置模板
├── README.md                        # 运维说明（SMTP/.htpasswd/首次部署）
└── tests/__init__.py                # 空
    test_feedback.py                 # unittest 全量测试

修改：
- nginx/vlsc.net.conf                # 新增 /feedback/ 三个 location
- portal/js/global-nav.js            # +bootstrap（副本 1）
- efhw/js/global-nav.js              # +bootstrap（副本 2）
- mrrc/js/global-nav.js              # +bootstrap（副本 3，经 symlink）
- 全部站点 HTML：global-nav.js?v=N → ?v=5（sed 批量，~80 文件含 symlink 目标）
- mrrc_ft710/website/build_sdd.py、ft8/website/build_sdd.py、
  sunmrrc/website/build_sdd.py       # 内嵌版本号 v2→v5（防止再生成回退）

新建（仓库根）：
- .gitignore                        # 忽略运行时产物
- docs/superpowers/plans/2026-08-20-feedback-system.md（本文件）
```

---

### 任务 1：git 初始化 + 呼号验证模块 `callsign.py`

**文件：**
- 创建：`feedback/callsign.py`
- 测试：`feedback/tests/__init__.py`、`feedback/tests/test_feedback.py`（第一部分）

- [ ] **步骤 1：git init + .gitignore**

```bash
cd /Users/cheenle/HAM/website
git init -b main
cat > .gitignore <<'EOF'
feedback/feedback.db
feedback/feedback.db.bak
feedback/feedback.db-wal
feedback/feedback.db-shm
feedback/clublog_users.json
feedback/clublog_users.json.tmp
feedback/clublog-users.zip
feedback/.tmp-clublog.zip
feedback/logs/
feedback/msmtp.conf
feedback/.htpasswd
.DS_Store
EOF
```

- [ ] **步骤 2：编写失败的测试（callsign 部分）**

创建 `feedback/tests/__init__.py`（空文件）。创建 `feedback/tests/test_feedback.py`：

```python
"""VLSC 反馈系统单元测试。运行：cd feedback && python3 -m unittest discover -s tests -v"""
import json
import os
import shutil
import tempfile
import unittest

import callsign
import db


class TestCallsignNormalize(unittest.TestCase):
    def test_trim_and_upper(self):
        self.assertEqual(callsign.normalize('  bg1sb '), 'BG1SB')
        self.assertEqual(callsign.normalize('bg1 sb'), 'BG1SB')
        self.assertEqual(callsign.normalize('dl2rum'), 'DL2RUM')

    def test_reject_separators(self):
        for bad in ('BG1SB/P', 'BG1SB_14', 'BG1SB-1', '4X/BG1SB', 'bg1.sb'):
            self.assertEqual(callsign.normalize(bad), '', bad)

    def test_reject_non_string(self):
        self.assertEqual(callsign.normalize(None), '')
        self.assertEqual(callsign.normalize(123), '')


class TestCallsignFormat(unittest.TestCase):
    def test_valid(self):
        for c in ('BG1SB', 'W1AW', 'DL2RUM', 'JA1ABC', '9M2CQ', 'VE3XYZ', 'K1A', '1A0C', '4X6HP'):
            self.assertTrue(callsign.is_valid_format(c), c)

    def test_invalid(self):
        for c in ('12345', 'A1', 'A', '1234567', 'BG1SBPQ', 'FOO@BAR', 'BG1SB/P', 'BG1SB_14'):
            self.assertFalse(callsign.is_valid_format(c), c)


class TestBaseCallsign(unittest.TestCase):
    def test_variants(self):
        cases = {
            '4X/BG1SB': 'BG1SB',
            '1B/HA8PX': 'HA8PX',
            'BG1SB/P': 'BG1SB',
            '1A0C_14': '1A0C',
            'BG1SB': 'BG1SB',
            '1A0C': '1A0C',
            'SOS': '',
        }
        for key, want in cases.items():
            self.assertEqual(callsign.base_callsign(key), want, key)

- [ ] **步骤 3：运行测试验证失败**

运行：`cd feedback && python3 -m unittest discover -s tests -v`
预期：FAIL，`ModuleNotFoundError: No module named 'callsign'`

- [ ] **步骤 4：实现 `feedback/callsign.py`**

```python
"""呼号验证 — 归一化、格式正则、Club Log 基准呼号提取。纯函数，无 I/O。"""
import re

# 基准呼号：可选 1 位数字前缀（9M2/4X 等）+ 1-2 字母 + 1 位数字 + 1-3 字母
CALLSIGN_RE = re.compile(r'^[0-9]?[A-Z]{1,2}[0-9][A-Z]{1,3}$')

# 便携/特殊分隔符（反馈身份仅接受基准呼号）
SEPARATORS = '/_.-'


def normalize(raw):
    """去空白并转大写；含分隔符返回 ''（拒绝）。"""
    if not isinstance(raw, str):
        return ''
    s = raw.strip().upper().replace(' ', '')
    if not s or any(c in s for c in SEPARATORS):
        return ''
    return s


def is_valid_format(call):
    """基准呼号格式校验（输入须已 normalize）。"""
    return bool(CALLSIGN_RE.match(call))


def base_callsign(key):
    """从 Club Log 原始键提取基准呼号：
    '4X/BG1SB' -> 'BG1SB'（取 / 右侧合法段）
    'BG1SB/P'  -> 'BG1SB'（P 不合法则取左侧）
    '1A0C_14'  -> '1A0C'（去掉 _ 后缀）
    'BG1SB'    -> 'BG1SB'；'SOS' -> ''（提取失败）
    """
    if not isinstance(key, str):
        return ''
    k = key.strip().upper()
    if not k:
        return ''
    if '/' in k:
        for part in reversed([p for p in k.split('/') if p]):
            if is_valid_format(part):
                return part
        return ''
    if '_' in k:
        k = k.split('_', 1)[0]
    return k if is_valid_format(k) else ''
```

- [ ] **步骤 5：运行测试验证通过**

运行：`cd feedback && python3 -m unittest discover -s tests -v`
预期：PASS，3 个 TestCase 全绿

- [ ] **步骤 6：Commit**

```bash
cd /Users/cheenle/HAM/website
git add .gitignore feedback/callsign.py feedback/tests/
git commit -m "feat(feedback): callsign validation module (normalize/format/base extraction)"
```

---

### 任务 2：SQLite 层 `db.py`

**文件：**
- 创建：`feedback/db.py`
- 测试：`feedback/tests/test_feedback.py`（追加）

- [ ] **步骤 1：追加失败测试**

追加到 `feedback/tests/test_feedback.py` 末尾：

```python
class TestDbImport(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.db = os.path.join(self.tmp, 't.db')
        self.conn = db.connect(self.db)
        db.init_db(self.conn)
        self.json_path = os.path.join(self.tmp, 'clublog.json')
        with open(self.json_path, 'w', encoding='utf-8') as f:
            json.dump({
                'BG1SB': {'firstqso': '2020-01-01'},
                '4X/BG1SB': {},
                '1A0C_14': {},
                'JA1ABC': {},
                'SOS': {},
            }, f)

    def tearDown(self):
        self.conn.close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_import_and_lookup(self):
        count = db.import_callsigns(self.conn, self.json_path, meta_date='2026-08-20')
        self.assertEqual(count, 4)  # BG1SB/JA1ABC/1A0C 去重（4X/BG1SB 贡献 BG1SB）
        self.assertTrue(db.callsign_exists(self.conn, 'BG1SB'))
        self.assertTrue(db.callsign_exists(self.conn, 'JA1ABC'))
        self.assertTrue(db.callsign_exists(self.conn, '1A0C'))
        self.assertFalse(db.callsign_exists(self.conn, 'W1AW'))

    def test_meta(self):
        db.import_callsigns(self.conn, self.json_path, meta_date='2026-08-20')
        meta = dict(db.get_meta(self.conn))
        self.assertEqual(meta.get('db_updated_at'), '2026-08-20')
        self.assertEqual(meta.get('db_count'), '4')


class TestDbComments(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.conn = db.connect(os.path.join(self.tmp, 't.db'))
        db.init_db(self.conn)
        db.import_callsigns(self.conn, self.json_path_unused())
        self.p = '/mrrc_ft710'

    def json_path_unused(self):
        p = os.path.join(self.tmp, 'x.json')
        with open(p, 'w', encoding='utf-8') as f:
            json.dump({'BG1SB': {}}, f)
        return p

    def tearDown(self):
        self.conn.close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_thread_and_reply(self):
        c1 = db.add_comment(self.conn, self.p, 'BG1SB', '第一个问题', '1.2.3.4')
        c2 = db.add_comment(self.conn, self.p, 'JA1ABC', '回复你', '1.2.3.5', parent_id=c1)
        db.add_comment(self.conn, self.p, 'DL2RUM', '官方回复', '1.2.3.6', parent_id=c1, is_admin=1)
        db.add_comment(self.conn, '/other', 'VE3XYZ', '别的页面', '1.2.3.7')
        tree = db.get_comments(self.conn, self.p)
        self.assertEqual(len(tree), 1)
        top = tree[0]
        self.assertEqual(top['id'], c1)
        # 官方回复置顶
        self.assertEqual(top['children'][0]['callsign'], 'DL2RUM')
        self.assertTrue(top['children'][0]['is_admin'])
        self.assertEqual(len(top['children']), 2)

    def test_hide_hides_subtree(self):
        c1 = db.add_comment(self.conn, self.p, 'BG1SB', '顶部', '1.2.3.4')
        c2 = db.add_comment(self.conn, self.p, 'JA1ABC', '子', '1.2.3.5', parent_id=c1)
        db.set_status(self.conn, c1, 'hidden')
        tree = db.get_comments(self.conn, self.p)
        self.assertEqual(tree, [])
        # 后台 include_hidden 可见
        all_ = db.get_comments(self.conn, self.p, include_hidden=True)
        self.assertEqual(len(all_), 2)
        # 后台平铺列表
        rows = db.list_all(self.conn, page_filter='', callsign_filter='', status_filter='')
        self.assertEqual(len(rows), 2)

    def test_depth_and_delete(self):
        c1 = db.add_comment(self.conn, self.p, 'BG1SB', '一', '1.2.3.4')
        c2 = db.add_comment(self.conn, self.p, 'JA1ABC', '二', '1.2.3.5', parent_id=c1)
        self.assertEqual(db.comment_depth(self.conn, c1), 1)
        self.assertEqual(db.comment_depth(self.conn, c2), 2)
        db.delete_comment(self.conn, c1)
        self.assertEqual(db.get_comments(self.conn, self.p), [])
        self.assertEqual(db.get_comment(self.conn, c1), None)
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd feedback && python3 -m unittest discover -s tests -v`
预期：FAIL，`ModuleNotFoundError: No module named 'db'`

- [ ] **步骤 3：实现 `feedback/db.py`**

```python
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
```

- [ ] **步骤 4：运行测试验证通过**

运行：`cd feedback && python3 -m unittest discover -s tests -v`
预期：PASS，全部 TestCase 绿（含新增 4 个）

- [ ] **步骤 5：Commit**

```bash
cd /Users/cheenle/HAM/website
git add feedback/db.py feedback/tests/
git commit -m "feat(feedback): sqlite layer — schema, callsign import, comment tree"
```

---

### 任务 3：配置 + HTTP 服务 `service.py`

**文件：**
- 创建：`feedback/config.json`
- 创建：`feedback/service.py`
- 测试：`feedback/tests/test_feedback.py`（追加）

- [ ] **步骤 1：创建 `feedback/config.json`**

```json
{
  "owner_email": "cheenle@qq.com",
  "mail_from": "cheenle@qq.com",
  "owner_callsign": "BG1SB",
  "rate_ip_per_hour": 5,
  "rate_call_per_day": 3,
  "max_message_len": 2000,
  "listen_host": "127.0.0.1",
  "listen_port": 8021
}
```

- [ ] **步骤 2：追加失败测试**

追加到 `feedback/tests/test_feedback.py` 末尾：

```python
import service
import update_db


class FeedbackServiceBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        service.DB_PATH = os.path.join(self.tmp, 'fb.db')
        conn = service.get_conn()
        db.init_db(conn)
        db.import_callsigns(conn, self._seed())
        conn.close()
        service._ip_hits.clear()
        service._call_hits.clear()
        service._notify_owner = lambda *a, **k: None   # 测试不发真实邮件
        self.p = '/mrrc_ft710'

    def _seed(self):
        p = os.path.join(self.tmp, 'seed.json')
        with open(p, 'w', encoding='utf-8') as f:
            json.dump({'BG1SB': {}, 'JA1ABC': {}, 'DL2RUM': {}, 'W1AW': {}}, f)
        return p

    def post(self, body, ip='1.2.3.4'):
        return service.handle_request('POST', '/feedback/api/comment', {}, body, ip)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


class TestApiSubmit(FeedbackServiceBase):
    def test_valid_comment(self):
        status, ctype, body = self.post({'page': self.p, 'callsign': 'bg1sb', 'message': '你好，问题'})
        self.assertEqual(status, 200)
        self.assertTrue(body['ok'])
        conn = service.get_conn()
        tree = db.get_comments(conn, self.p)
        conn.close()
        self.assertEqual(len(tree), 1)
        self.assertEqual(tree[0]['callsign'], 'BG1SB')

    def test_format_rejected(self):
        status, _, body = self.post({'page': self.p, 'callsign': 'FOO@BAR', 'message': 'hi'})
        self.assertEqual(status, 400)
        self.assertEqual(body['error'], 'format')

    def test_not_in_db_rejected(self):
        status, _, body = self.post({'page': self.p, 'callsign': 'W2XYZ', 'message': 'hi'})
        self.assertEqual(status, 400)
        self.assertEqual(body['error'], 'not_in_db')

    def test_invalid_page(self):
        status, _, body = self.post({'page': 'evil<script>', 'callsign': 'BG1SB', 'message': 'hi'})
        self.assertEqual(status, 400)
        self.assertEqual(body['error'], 'invalid_page')

    def test_message_length(self):
        status, _, body = self.post({'page': self.p, 'callsign': 'BG1SB', 'message': 'x'})
        self.assertEqual(status, 400)
        self.assertEqual(body['error'], 'message_length')

    def test_honeypot_dropped(self):
        status, _, body = self.post({'page': self.p, 'callsign': 'BG1SB', 'message': 'hi', 'website': 'spam'})
        self.assertEqual(status, 200)
        self.assertEqual(body['id'], 0)
        conn = service.get_conn()
        self.assertEqual(db.count_all(conn), 0)
        conn.close()

    def test_rate_limit_per_ip(self):
        for i in range(5):
            status, _, _ = self.post({'page': self.p, 'callsign': 'BG1SB', 'message': 'm%d' % i})
            self.assertEqual(status, 200)
        status, _, body = self.post({'page': self.p, 'callsign': 'BG1SB', 'message': 'm5'})
        self.assertEqual(status, 429)
        self.assertEqual(body['error'], 'rate_limit')

    def test_rate_limit_per_callsign(self):
        for i in range(3):
            status, _, _ = self.post({'page': self.p, 'callsign': 'BG1SB', 'message': 'm%d' % i}, ip='9.9.9.%d' % i)
            self.assertEqual(status, 200)
        status, _, body = self.post({'page': self.p, 'callsign': 'BG1SB', 'message': 'm3'}, ip='9.9.9.9')
        self.assertEqual(status, 429)


class TestApiReply(FeedbackServiceBase):
    def test_reply_flow_and_depth(self):
        self.post({'page': self.p, 'callsign': 'BG1SB', 'message': 'q1'})
        conn = service.get_conn()
        top = db.get_comments(conn, self.p)[0]
        conn.close()
        # 回复（同 IP 换呼号避开限流）
        self.post({'page': self.p, 'callsign': 'JA1ABC', 'message': 'r1', 'reply_to': top['id']}, ip='2.2.2.2')
        status, _, body = self.post({'page': self.p, 'callsign': 'DL2RUM', 'message': 'r2', 'reply_to': 99999}, ip='2.2.2.3')
        self.assertEqual(status, 400)
        self.assertEqual(body['error'], 'invalid_reply')
        # 无效父 id 类型
        status, _, body = self.post({'page': self.p, 'callsign': 'DL2RUM', 'message': 'r3', 'reply_to': 'abc'}, ip='2.2.2.4')
        self.assertEqual(status, 400)


class TestApiAdmin(FeedbackServiceBase):
    def test_admin_reply_hide_delete(self):
        self.post({'page': self.p, 'callsign': 'BG1SB', 'message': 'q1'})
        conn = service.get_conn()
        cid = db.get_comments(conn, self.p)[0]['id']
        conn.close()
        # 官方回复
        status, _, body = service.handle_request('POST', '/feedback/admin/action', {},
                                                 {'action': 'reply', 'id': cid, 'message': '站长答复'}, '1.2.3.4')
        self.assertEqual(status, 200)
        conn = service.get_conn()
        tree = db.get_comments(conn, self.p)
        self.assertTrue(tree[0]['children'][0]['is_admin'])
        self.assertEqual(tree[0]['children'][0]['callsign'], 'BG1SB')
        conn.close()
        # 隐藏
        status, _, _ = service.handle_request('POST', '/feedback/admin/action', {},
                                              {'action': 'hide', 'id': cid}, '1.2.3.4')
        self.assertEqual(status, 200)
        conn = service.get_conn()
        self.assertEqual(db.get_comments(conn, self.p), [])
        conn.close()
        # 删除
        status, _, _ = service.handle_request('POST', '/feedback/admin/action', {},
                                              {'action': 'delete', 'id': cid}, '1.2.3.4')
        self.assertEqual(status, 200)
        conn = service.get_conn()
        self.assertEqual(db.count_all(conn), 0)
        conn.close()

    def test_origin_forbidden(self):
        status, _, body = service.handle_request('POST', '/feedback/admin/action', {},
                                                 {'action': 'delete', 'id': 1}, '1.2.3.4',
                                                 origin='https://evil.example')
        self.assertEqual(status, 403)

    def test_admin_page_renders(self):
        self.post({'page': self.p, 'callsign': 'BG1SB', 'message': 'q1'})
        status, ctype, body = service.handle_request('GET', '/feedback/admin/', {}, None, '1.2.3.4')
        self.assertEqual(status, 200)
        self.assertIn('text/html', ctype)
        self.assertIn('BG1SB', body.decode('utf-8'))
        self.assertIn('q1', body.decode('utf-8'))


class TestApiCommentsGet(FeedbackServiceBase):
    def test_get_and_zh_sharing(self):
        self.post({'page': self.p, 'callsign': 'BG1SB', 'message': 'q1'})
        # EN/CN 共享线程：/zh/ 前缀归一化到同一 page key
        status, _, body = service.handle_request('GET', '/feedback/api/comments',
                                                 {'page': '/zh/mrrc_ft710'}, None, '1.2.3.4')
        self.assertEqual(status, 200)
        self.assertEqual(len(body['comments']), 1)

    def test_get_invalid_page(self):
        status, _, body = service.handle_request('GET', '/feedback/api/comments',
                                                 {'page': '<b>'}, None, '1.2.3.4')
        self.assertEqual(status, 400)


class TestUpdateDbLocal(unittest.TestCase):
    def test_import_from_file(self):
        tmp = tempfile.mkdtemp()
        seed = os.path.join(tmp, 'clublog.json')
        with open(seed, 'w', encoding='utf-8') as f:
            json.dump({'BG1SB': {}, '1B/HA8PX': {}}, f)
        update_db.DB = os.path.join(tmp, 'fb.db')
        update_db.RAW = os.path.join(tmp, 'raw.json')
        update_db.LOG_DIR = os.path.join(tmp, 'logs')
        os.makedirs(update_db.LOG_DIR, exist_ok=True)
        count, meta_date = update_db.run(file_path=seed)
        self.assertEqual(count, 2)
        self.assertTrue(os.path.exists(update_db.DB))
        conn = db.connect(update_db.DB)
        self.assertTrue(db.callsign_exists(conn, 'BG1SB'))
        self.assertTrue(db.callsign_exists(conn, 'HA8PX'))
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)
```

- [ ] **步骤 3：运行测试验证失败**

运行：`cd feedback && python3 -m unittest discover -s tests -v`
预期：FAIL，`ModuleNotFoundError: No module named 'service'` / `'update_db'`

- [ ] **步骤 4：实现 `feedback/service.py`**

```python
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
        st = 'hidden' if r['status'] == 'hidden' else ''
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
.f-reply textarea{width:100%;min-height:70px;box-sizing:border-box;margin:6px 0;display:block}
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
```

- [ ] **步骤 5：运行测试验证通过**

运行：`cd feedback && python3 -m unittest discover -s tests -v`
预期：PASS，全部绿（含 API/后台/update_db 测试）

- [ ] **步骤 6：Commit**

```bash
cd /Users/cheenle/HAM/website
git add feedback/config.json feedback/service.py feedback/tests/
git commit -m "feat(feedback): HTTP service — submit/threads/admin API, rate limits, email"
```

---

### 任务 4：呼号库刷新 `update_db.py`

**文件：**
- 创建：`feedback/update_db.py`

- [ ] **步骤 1：实现 `feedback/update_db.py`**

（`TestUpdateDbLocal` 已在任务 3 覆盖 `run(file_path=...)` 路径）

```python
#!/usr/bin/env python3
"""呼号库刷新 — 每日从 clublog.org 下载（与 RumLogNG 同源）或本地种子导入。

用法：
  python3 update_db.py                 # 下载 clublog-users.json.zip → 解压 → 导入
  python3 update_db.py --file x.json   # 首次种子导入（本地 JSON）
"""
import argparse
import json
import logging
import os
import shutil
import sqlite3
import subprocess
import sys
import time
import urllib.request
import zipfile

import db

URL = 'https://clublog.org/clublog-users.json.zip'
BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, 'feedback.db')
RAW = os.path.join(BASE, 'clublog_users.json')
LOG_DIR = os.path.join(BASE, 'logs')


def _download(url, dest):
    try:
        subprocess.run(['curl', '-fL', '--retry', '3', '--connect-timeout', '30',
                        '--max-time', '900', '-o', dest, url],
                       check=True, capture_output=True)
    except FileNotFoundError:
        urllib.request.urlretrieve(url, dest)
    except subprocess.CalledProcessError as e:
        raise RuntimeError('download failed: %s' % (e.stderr or e))


def _extract_json(zip_path):
    with zipfile.ZipFile(zip_path) as z:
        names = [n for n in z.namelist() if n.endswith('.json')]
        if not names:
            raise RuntimeError('no .json in zip')
        data = z.read(names[0]).decode('utf-8')
    json.loads(data)                      # 完整性校验
    return data


def run(file_path=None):
    """执行导入。file_path 为 None 时从 clublog.org 下载。返回 (count, meta_date)。"""
    if file_path:
        with open(file_path, encoding='utf-8') as f:
            data = f.read()
        json.loads(data)
        meta_date = time.strftime('%Y-%m-%d')
    else:
        tmp_zip = os.path.join(BASE, '.tmp-clublog.zip')
        _download(URL, tmp_zip)
        data = _extract_json(tmp_zip)
        os.replace(tmp_zip, os.path.join(BASE, 'clublog-users.zip'))
        meta_date = time.strftime('%Y-%m-%dT%H:%M:%SZ')
    raw_tmp = RAW + '.tmp'
    with open(raw_tmp, 'w', encoding='utf-8') as f:
        f.write(data)
    os.replace(raw_tmp, RAW)              # 校验通过后才替换
    if os.path.exists(DB):
        shutil.copy2(DB, DB + '.bak')     # 旧库备份
    conn = sqlite3.connect(DB)
    try:
        db.init_db(conn)
        count = db.import_callsigns(conn, RAW, meta_date=meta_date)
    finally:
        conn.close()
    return count, meta_date


def main():
    ap = argparse.ArgumentParser(description='VLSC 反馈呼号库刷新')
    ap.add_argument('--file', help='本地 clublog_users.json（首次种子导入用）')
    args = ap.parse_args()
    os.makedirs(LOG_DIR, exist_ok=True)
    logging.basicConfig(filename=os.path.join(LOG_DIR, 'update.log'),
                        level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    try:
        count, meta_date = run(args.file)
        logging.info('imported %d callsigns (%s)', count, meta_date)
        print('OK: %d callsigns imported (%s)' % (count, meta_date))
    except Exception as e:
        logging.error('update failed: %s', e)
        print('ERROR: %s' % e, file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
```

- [ ] **步骤 2：运行全部测试**

运行：`cd feedback && python3 -m unittest discover -s tests -v`
预期：PASS（update_db 本地导入路径已验证）

- [ ] **步骤 3：Commit**

```bash
cd /Users/cheenle/HAM/website
git add feedback/update_db.py
git commit -m "feat(feedback): callsign db refresh — clublog download or local seed import"
```

---

### 任务 5：Widget 样式 `static/feedback.css`

**文件：**
- 创建：`feedback/static/feedback.css`

- [ ] **步骤 1：实现 `feedback/static/feedback.css`**

```css
/* VLSC 反馈 Widget — 复用 octen.css 设计变量，缺省时用兜底 */
.vlsc-feedback{
  --fb-accent:#22d3ee; --fb-bg:#05070c; --fb-card:#111827; --fb-border:#1f2937;
  --fb-text:#e5e7eb; --fb-muted:#9ca3af; --fb-gold:#fbbf24;
  --fb-ok:#34d399; --fb-err:#f87171;
  background:var(--bg-primary,var(--fb-bg));
  border-top:1px solid var(--border-color,var(--fb-border));
  color:var(--text-primary,var(--fb-text));
  padding:3.5rem 1.25rem 5rem;
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Inter,sans-serif;
}
.vlsc-fb-container{max-width:1200px;margin:0 auto}
.vlsc-fb-head h2{margin:0 0 .25rem;font-size:1.5rem;font-weight:700;
  color:var(--text-primary,var(--fb-text))}
.vlsc-fb-head p{margin:0 0 1.5rem;font-size:.9rem;color:var(--text-secondary,var(--fb-muted))}
.vlsc-fb-list{margin-bottom:2rem}
.vlsc-fb-muted{color:var(--text-secondary,var(--fb-muted));font-size:.9rem}
.vlsc-fb-thread{list-style:none;margin:0;padding:0}
.vlsc-fb-thread.vlsc-fb-child{margin-left:1.25rem;padding-left:1rem;
  border-left:2px solid var(--border-color,var(--fb-border))}
.vlsc-fb-item{background:var(--bg-secondary,var(--fb-card));
  border:1px solid var(--border-color,var(--fb-border));border-radius:10px;
  padding:.9rem 1rem;margin-bottom:.75rem}
.vlsc-fb-item.vlsc-fb-admin{border-color:var(--fb-gold)}
.vlsc-fb-meta{display:flex;gap:.6rem;align-items:center;flex-wrap:wrap;
  font-size:.8rem;color:var(--text-secondary,var(--fb-muted))}
.vlsc-fb-call{font-family:"JetBrains Mono",ui-monospace,monospace;font-weight:700;
  color:var(--accent,var(--fb-accent));letter-spacing:.02em}
.vlsc-fb-badge{background:var(--fb-gold);color:#1f2937;font-size:.68rem;font-weight:700;
  padding:.12rem .45rem;border-radius:999px}
.vlsc-fb-time{font-size:.75rem}
.vlsc-fb-body{margin:.45rem 0 .5rem;line-height:1.6;font-size:.92rem;
  color:var(--text-primary,var(--fb-text));white-space:pre-wrap;word-break:break-word}
.vlsc-fb-reply{background:none;border:none;color:var(--accent,var(--fb-accent));
  cursor:pointer;font-size:.78rem;padding:0}
.vlsc-fb-reply:hover{text-decoration:underline}
.vlsc-fb-reply-form{margin:.6rem 0 0}
.vlsc-fb-reply-form textarea,.vlsc-fb-form textarea,.vlsc-fb-form input{
  width:100%;box-sizing:border-box;background:var(--bg-primary,var(--fb-bg));
  border:1px solid var(--border-color,var(--fb-border));border-radius:8px;
  color:var(--text-primary,var(--fb-text));padding:.6rem .75rem;font-size:.9rem;
  font-family:inherit}
.vlsc-fb-reply-form textarea{min-height:60px;margin-bottom:.5rem}
.vlsc-fb-form{background:var(--bg-secondary,var(--fb-card));
  border:1px solid var(--border-color,var(--fb-border));border-radius:10px;padding:1.1rem}
.vlsc-fb-row{display:flex;gap:.75rem;align-items:center;margin-bottom:.75rem;flex-wrap:wrap}
.vlsc-fb-row label{font-size:.85rem;color:var(--text-secondary,var(--fb-muted));white-space:nowrap}
.vlsc-fb-row input{width:auto;flex:0 0 13rem;text-transform:uppercase}
.vlsc-fb-form textarea{margin-bottom:.75rem;min-height:90px}
.vlsc-fb-hp{position:absolute!important;left:-9999px!important;width:1px!important;
  height:1px!important;opacity:0!important;pointer-events:none!important}
.vlsc-fb-actions{display:flex;gap:.75rem;align-items:center}
.vlsc-fb-btn{background:var(--accent,var(--fb-accent));color:#052e16;font-weight:700;
  border:none;border-radius:8px;padding:.6rem 1.4rem;cursor:pointer;font-size:.9rem;
  transition:opacity .2s}
.vlsc-fb-btn:disabled{opacity:.6;cursor:default}
.vlsc-fb-status{font-size:.85rem}
.vlsc-fb-status.vlsc-fb-ok{color:var(--fb-ok)}
.vlsc-fb-status.vlsc-fb-err{color:var(--fb-err)}
.vlsc-fb-replying{font-size:.8rem;color:var(--text-secondary,var(--fb-muted));
  background:var(--bg-primary,var(--fb-bg));border:1px dashed var(--border-color,var(--fb-border));
  border-radius:6px;padding:.4rem .6rem;margin-bottom:.6rem;display:flex;justify-content:space-between}
@media(max-width:640px){
  .vlsc-fb-thread.vlsc-fb-child{margin-left:.4rem;padding-left:.6rem}
  .vlsc-fb-row input{flex:1 1 100%}
}
```

- [ ] **步骤 2：语法自检**

运行：`python3 - <<'EOF'\nfrom pathlib import Path; import tinycss2  # 若不可用则跳过\nEOF`（可选）；无工具时目检花括号配对。

- [ ] **步骤 3：Commit**

```bash
cd /Users/cheenle/HAM/website
git add feedback/static/feedback.css
git commit -m "feat(feedback): widget styles — octen.css adaptive, admin badge, mobile"
```

---

### 任务 6：Widget 逻辑 `static/feedback.js`

**文件：**
- 创建：`feedback/static/feedback.js`

- [ ] **步骤 1：实现 `feedback/static/feedback.js`**

```js
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
    replyingTo: '正在回复 #%d', now: '刚刚'
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
    replyingTo: 'Replying to #%d', now: 'just now'
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

  var replyTo = null;
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
      submitComment(form, replyTo || null);
    });
    load();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
```

- [ ] **步骤 2：语法自检**

运行：`node --check feedback/static/feedback.js`（若无 node，用 `python3 -m py_compile` 之外的简单目检）。

- [ ] **步骤 3：Commit**

```bash
cd /Users/cheenle/HAM/website
git add feedback/static/feedback.js
git commit -m "feat(feedback): widget logic — thread rendering, callsign validation flow, i18n"
```

---

### 任务 7：global-nav.js bootstrap 注入 + 全站版本号升版

**文件：**
- 修改：`portal/js/global-nav.js`（副本 1，尾部 AdSense 块后追加，注释编号 9）
- 修改：`efhw/js/global-nav.js`（副本 2，同上）
- 修改：`mrrc/js/global-nav.js`（副本 3，AdSense 已是 9，注释编号 10）
- 修改：全站所有引用 `global-nav.js` 的 HTML：`?v=N` → `?v=5`
- 修改：`/Users/cheenle/HAM/mrrc_ft710/website/build_sdd.py`、`/Users/cheenle/HAM/ft8/website/build_sdd.py`、`/Users/cheenle/HAM/sunsdr/sunmrrc/website/build_sdd.py` 内嵌版本号 → `?v=5`

- [ ] **步骤 1：在全部 7 个站点的 global-nav.js 末尾 AdSense 块之后追加 bootstrap**

7 个文件（3 种内容、7 个位置；mrrc 副本的 AdSense 段注释是 9，反馈段用 10，其余用 9）：

```
portal/js/global-nav.js                                   （md5-1，与 mrrc_ft8 同源）
/Users/cheenle/HAM/ft8/website/js/global-nav.js           （md5-1）
efhw/js/global-nav.js                                     （md5-2）
/Users/cheenle/HAM/mrrc_ft710/website/js/global-nav.js    （md5-2）
/Users/cheenle/HAM/sunsdr/sunmrrc/website/js/global-nav.js（md5-2）
/Users/cheenle/HAM/sunsdr/SunsdrMobile/website/js/global-nav.js（md5-2）
mrrc/js/global-nav.js                                     （md5-3，唯一）
```

每个文件的 `})();` 之前（AdSense 块之后）插入：

```js
  // ── 9. 反馈系统 bootstrap（全站自动注入；admin/api 页面除外）──
  if (location.hostname === 'www.vlsc.net'
      && !/\/feedback\/(admin|api)/.test(location.pathname)) {
    var fbCss = document.createElement('link');
    fbCss.rel = 'stylesheet';
    fbCss.href = '/feedback/static/feedback.css?v=1';
    (document.head || document.documentElement).appendChild(fbCss);
    var fbJs = document.createElement('script');
    fbJs.src = '/feedback/static/feedback.js?v=1';
    document.body.appendChild(fbJs);
  }
```

注意：mrrc 副本将注释改为 `── 10.`。三个副本各自编辑后 `node --check`。

- [ ] **步骤 2：全站 HTML 版本号统一升到 v=5**

对 portal/efhw（仓库内）与各 symlink 目标站点（mrrc、mrrc_ft710、mrrc_ft8、sunmrrc、SunsdrMobile）执行：

```bash
cd /Users/cheenle/HAM/website
grep -rl "global-nav.js?v=" --include="*.html" . \
  /Users/cheenle/UHRR/MRRC/website /Users/cheenle/HAM/mrrc_ft710/website \
  /Users/cheenle/HAM/ft8/website /Users/cheenle/HAM/sunsdr/sunmrrc/website \
  /Users/cheenle/HAM/sunsdr/SunsdrMobile/website 2>/dev/null \
| xargs sed -i '' 's/global-nav\.js?v=[0-9]*/global-nav.js?v=5/g'
```

预期：`grep -rc "global-nav.js?v=5" ...` 计数 = 原各版本之和（约 80 文件）。`grep -r "global-nav.js?v=[0-9]" ` 无残留。

- [ ] **步骤 3：更新 3 个 build_sdd.py 内嵌版本号**

每个脚本中形如 `global-nav.js?v=2` 的行改为 `global-nav.js?v=5`：

```bash
sed -i '' 's/global-nav\.js?v=[0-9]*/global-nav.js?v=5/g' \
  /Users/cheenle/HAM/mrrc_ft710/website/build_sdd.py \
  /Users/cheenle/HAM/ft8/website/build_sdd.py \
  /Users/cheenle/HAM/sunsdr/sunmrrc/website/build_sdd.py
```

（不重新运行 pandoc；SDD HTML 已由步骤 2 的 sed 覆盖。将来再生成时保持 v=5。）

- [ ] **步骤 4：验证**

```bash
cd /Users/cheenle/HAM/website
node --check portal/js/global-nav.js && node --check efhw/js/global-nav.js && node --check mrrc/js/global-nav.js
grep -rn "global-nav.js?v=" --include="*.html" . | grep -v "v=5" | head  # 应为空
```

- [ ] **步骤 5：Commit**

```bash
cd /Users/cheenle/HAM/website
git add portal/js/global-nav.js efhw/js/global-nav.js .gitignore
git -c core.fileMode=false add mrrc/js/global-nav.js
git commit -m "feat(feedback): auto-inject widget via global-nav.js bootstrap; bump cache versions"
git add -A
git commit -m "chore(feedback): bump global-nav cache version to v5 across all sites"
```

---

### 任务 8：nginx 配置

**文件：**
- 修改：`nginx/vlsc.net.conf`

- [ ] **步骤 1：在 "Deny hidden files" 段之前插入 3 个 location**

在 `# ── Deny hidden files ──` 前插入：

```nginx
    # ── Feedback system (Python service @ 127.0.0.1:8021) ──
    location /feedback/static/ {
        alias /home/cheenle/feedback/static/;
        expires 1h;
        add_header Cache-Control "public, max-age=3600";
    }
    location /feedback/api/ {
        proxy_pass http://127.0.0.1:8021;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    location /feedback/admin/ {
        proxy_pass http://127.0.0.1:8021;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        auth_basic "Feedback Admin";
        auth_basic_user_file /home/cheenle/feedback/.htpasswd;
    }
```

- [ ] **步骤 2：本地语法检查**

运行：`nginx -t -c $(pwd)/nginx/vlsc.net.conf 2>&1 || echo "本机无 nginx，跳过（服务器上 nginx -t 验证）"`

- [ ] **步骤 3：Commit**

```bash
cd /Users/cheenle/HAM/website
git add nginx/vlsc.net.conf
git commit -m "feat(feedback): nginx locations — static alias, api proxy, basic-auth admin"
```

---

### 任务 9：部署脚本 + systemd + 运维文档

**文件：**
- 创建：`feedback/deploy.sh`
- 创建：`feedback/vlsc-feedback.service`
- 创建：`feedback/vlsc-feedback-db.service`
- 创建：`feedback/vlsc-feedback-db.timer`
- 创建：`feedback/msmtp.conf.example`
- 创建：`feedback/README.md`

- [ ] **步骤 1：创建 systemd units 与 msmtp 模板**

`feedback/vlsc-feedback.service`：

```ini
[Unit]
Description=VLSC Feedback API service
After=network.target

[Service]
User=cheenle
WorkingDirectory=/home/cheenle/feedback
ExecStart=/usr/bin/python3 service.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

`feedback/vlsc-feedback-db.service`：

```ini
[Unit]
Description=VLSC feedback callsign DB refresh

[Service]
Type=oneshot
User=cheenle
WorkingDirectory=/home/cheenle/feedback
ExecStart=/usr/bin/python3 update_db.py
```

`feedback/vlsc-feedback-db.timer`：

```ini
[Unit]
Description=Daily callsign DB refresh (Club Log, same source as RumLogNG)

[Timer]
OnCalendar=*-*-* 03:00:00
Persistent=true
OnBootSec=10min

[Install]
WantedBy=timers.target
```

`feedback/msmtp.conf.example`：

```
# 复制为 msmtp.conf（chmod 600），填入真实凭据
defaults
auth on
tls on
tls_trust_file /etc/ssl/certs/ca-certificates.crt

account default
host smtp.qq.com
port 465
from cheenle@qq.com
user cheenle@qq.com
password 你的QQ邮箱授权码
```

- [ ] **步骤 2：创建 `feedback/deploy.sh`**

```bash
#!/bin/bash
# VLSC 反馈系统部署脚本
# 用法: ./deploy.sh                # 同步代码 + 安装 systemd + 部署 nginx
#       ./deploy.sh --files-only   # 只同步代码
set -euo pipefail

REMOTE_HOST="www.vlsc.net"
REMOTE_USER="cheenle"
REMOTE_DIR="/home/cheenle/feedback"
LOCAL_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "═══ VLSC 反馈系统部署 → $REMOTE_HOST ═══"

# ── 1. 本地校验 ──
for f in service.py callsign.py db.py update_db.py config.json \
         static/feedback.js static/feedback.css; do
  [ -f "$LOCAL_DIR/$f" ] || { echo "缺少文件: $f"; exit 1; }
done
python3 -m py_compile "$LOCAL_DIR"/service.py "$LOCAL_DIR"/callsign.py \
  "$LOCAL_DIR"/db.py "$LOCAL_DIR"/update_db.py
echo "✔ 本地校验通过"

# ── 2. 远端目录 ──
ssh "$REMOTE_USER@$REMOTE_HOST" "mkdir -p $REMOTE_DIR/static $REMOTE_DIR/logs"

# ── 3. 同步代码 ──
for f in service.py callsign.py db.py update_db.py config.json; do
  scp -q "$LOCAL_DIR/$f" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/"
done
scp -q "$LOCAL_DIR/static/feedback.js" "$LOCAL_DIR/static/feedback.css" \
  "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/static/"

# ── 4. systemd + nginx ──
if [[ "${1:-}" == "--files-only" ]]; then
  echo "（--files-only）跳过 systemd/nginx"
  exit 0
fi
read -r -p "安装/重启 systemd 并部署 nginx 配置？[y/N] " ans
if [[ "$ans" =~ ^[Yy]$ ]]; then
  scp -q "$LOCAL_DIR/vlsc-feedback.service" "$LOCAL_DIR/vlsc-feedback-db.service" \
      "$LOCAL_DIR/vlsc-feedback-db.timer" "$REMOTE_USER@$REMOTE_HOST:/tmp/"
  ssh "$REMOTE_USER@$REMOTE_HOST" "sudo install -m 644 /tmp/vlsc-feedback.service /etc/systemd/system/ && \
    sudo install -m 644 /tmp/vlsc-feedback-db.service /etc/systemd/system/ && \
    sudo install -m 644 /tmp/vlsc-feedback-db.timer /etc/systemd/system/ && \
    sudo systemctl daemon-reload && \
    sudo systemctl enable --now vlsc-feedback vlsc-feedback-db.timer && \
    sudo systemctl restart vlsc-feedback && \
    sleep 1 && sudo systemctl is-active vlsc-feedback"
  scp -q "$LOCAL_DIR/../nginx/vlsc.net.conf" "$REMOTE_USER@$REMOTE_HOST:/tmp/vlsc.net.conf"
  ssh "$REMOTE_USER@$REMOTE_HOST" "sudo cp /tmp/vlsc.net.conf /etc/nginx/sites-available/vlsc.net && \
    sudo nginx -t && sudo systemctl reload nginx && echo 'nginx OK'"
else
  echo "跳过 systemd/nginx（代码已同步）"
fi

echo
echo "✔ 部署完成。首次安装还需（详见 README.md）："
echo "  1) sudo apt install msmtp msmtp-mta"
echo "  2) 配置 $REMOTE_DIR/msmtp.conf（SMTP 凭据，chmod 600）"
echo "  3) 生成 $REMOTE_DIR/.htpasswd（后台密码）"
echo "  4) 导入呼号库: scp clublog_users.json $REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/ && \\"
echo "     ssh $REMOTE_USER@$REMOTE_HOST 'python3 $REMOTE_DIR/update_db.py --file $REMOTE_DIR/clublog_users.json'"
```

- [ ] **步骤 3：创建 `feedback/README.md`**

```markdown
# VLSC 反馈系统

全站用户反馈：访客用 HAM 呼号（Club Log 库严格验证，与 RumLogNG 同源）发帖/互回；
站长邮件通知 + 后台管理。

## 架构
- `service.py` — Python 标准库 HTTP 服务（127.0.0.1:8021，systemd 管理）
- `feedback.db` — SQLite：评论 + callsigns 呼号库 + meta
- `update_db.py` — 每日 03:00（systemd timer）从 clublog.org 刷新呼号库
- nginx：`/feedback/api/`（反代）、`/feedback/static/`（widget 静态）、
  `/feedback/admin/`（basic-auth 后台）
- 前端：global-nav.js 全站自动注入，widget 文件集中托管于 /feedback/static/

## 首次部署（服务器 www.vlsc.net）
1. `sudo apt install msmtp msmtp-mta`
2. 编辑 `/home/cheenle/feedback/msmtp.conf`（从 msmtp.conf.example 复制），
   填入 SMTP 凭据（QQ 邮箱授权码等），`chmod 600`
3. 生成后台密码：`htpasswd -c /home/cheenle/feedback/.htpasswd cheenle`
4. 导入呼号库（种子）：
   `scp clublog_users.json cheenle@www.vlsc.net:/home/cheenle/feedback/`
   `ssh cheenle@www.vlsc.net 'python3 /home/cheenle/feedback/update_db.py --file /home/cheenle/feedback/clublog_users.json'`
5. 验证：`curl -s https://www.vlsc.net/feedback/api/comments?page=/` → `{"ok":true,"comments":[]}`
   任一站点页面底部出现"反馈与问题"区块

## 日常运维
- 后台：https://www.vlsc.net/feedback/admin/（basic-auth）
- 呼号库日志：`/home/cheenle/feedback/logs/update.log`
- 服务日志：`journalctl -u vlsc-feedback -f`
- 重新部署：`cd feedback && ./deploy.sh`
- 手动刷新呼号库：`ssh cheenle@www.vlsc.net 'python3 /home/cheenle/feedback/update_db.py'`

## 呼号验证规则
- 格式正则 `^[0-9]?[A-Z]{1,2}[0-9][A-Z]{1,3}$`；拒绝便携/特殊形式（含 / _ -）
- 必须存在于 callsigns 表（从 clublog_users.json 提取基准呼号）
- 未收录的合法呼号无法留言（已知局限，产品决策 A）

## 配置（config.json）
owner_email / mail_from / owner_callsign / rate_ip_per_hour / rate_call_per_day /
max_message_len / listen_host / listen_port
```

- [ ] **步骤 4：校验 + Commit**

运行：`bash -n feedback/deploy.sh && chmod +x feedback/deploy.sh`
预期：无语法错误。

```bash
cd /Users/cheenle/HAM/website
git add feedback/deploy.sh feedback/vlsc-feedback.service feedback/vlsc-feedback-db.service \
  feedback/vlsc-feedback-db.timer feedback/msmtp.conf.example feedback/README.md
git commit -m "feat(feedback): deploy script, systemd units, ops docs"
```

---

### 任务 10：本地端到端验证

- [ ] **步骤 1：全量单测**

运行：`cd feedback && python3 -m unittest discover -s tests -v`
预期：全部 PASS。

- [ ] **步骤 2：本地起服务 + 冒烟**

```bash
cd feedback
python3 service.py &            # 127.0.0.1:8021
sleep 1
python3 - <<'EOF'
import json, urllib.request
def post(path, body):
    req = urllib.request.Request('http://127.0.0.1:8021' + path,
        data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
    return json.load(urllib.request.urlopen(req))
print(post('/feedback/api/comment', {'page': '/', 'callsign': 'BG1SB', 'message': '本地冒烟测试'}))
EOF
curl -s 'http://127.0.0.1:8021/feedback/api/comments?page=/'
curl -s 'http://127.0.0.1:8021/feedback/admin/' | head -5   # 应返回 HTML
kill %1
```

预期：提交返回 `{"ok": true, "id": 1}`；comments 返回含该条；admin 返回 HTML。
注意：本地 feedback.db 是种子导入的小库（BG1SB/JA1ABC/DL2RUM/W1AW），测试后删除 `feedback/feedback.db*` 并 `git clean` 或恢复。

- [ ] **步骤 3：Commit**

```bash
cd /Users/cheenle/HAM/website
rm -f feedback/feedback.db feedback/feedback.db-wal feedback/feedback.db-shm feedback/feedback.db.bak
git add -A
git commit -m "test(feedback): local end-to-end smoke (service + API + admin)"
```

---

### 任务 11：服务器部署 + 冒烟测试（需用户参与）

前置：本机 `feedback/` 与 `nginx/vlsc.net.conf` 已按任务 1-9 完成并 commit。

- [ ] **步骤 1：同步站点 HTML/JS 改动（版本号 v5 需随各站点部署）**

各站点（portal/efhw/mrrc/mrrc_ft710/mrrc_ft8/sunmrrc/SunsdrMobile）HTML 与 global-nav.js 改动
通过各自既有 deploy.sh 部署（`cd <site> && ./deploy.sh`），或用户确认后统一执行。

- [ ] **步骤 2：部署反馈服务**

```bash
cd /Users/cheenle/HAM/website/feedback
./deploy.sh        # 按提示选 y
```

预期：服务 is-active；nginx -t 通过并 reload。

- [ ] **步骤 3：服务器准备（需用户提供/确认）**

```bash
ssh cheenle@www.vlsc.net
sudo apt install -y msmtp msmtp-mta          # 邮件
# 编辑 msmtp.conf（SMTP 凭据），chmod 600
htpasswd -c /home/cheenle/feedback/.htpasswd cheenle   # 后台密码
```

- [ ] **步骤 4：种子导入呼号库**

```bash
scp ~/Library/Containers/de.dl2rum.RUMlogNG/Data/Library/"Application Support"/de.dl2rum.RUMlogNG/clublog_users.json \
    cheenle@www.vlsc.net:/home/cheenle/feedback/clublog_users.json
ssh cheenle@www.vlsc.net 'python3 /home/cheenle/feedback/update_db.py --file /home/cheenle/feedback/clublog_users.json'
```

预期：输出 `OK: N callsigns imported (...)`，N ≈ 60 万级。

- [ ] **步骤 5：线上冒烟测试**

```bash
curl -s https://www.vlsc.net/feedback/api/comments?page=/          # {"ok":true,"comments":[]}
curl -s -X POST https://www.vlsc.net/feedback/api/comment \
  -H 'Content-Type: application/json' \
  -d '{"page":"/","callsign":"BG1SB","message":"冒烟测试"}'          # {"ok":true,"id":1}
curl -s https://www.vlsc.net/feedback/api/comments?page=/          # 含该条
curl -s https://www.vlsc.net/feedback/admin/ -u cheenle:密码         # HTML
curl -s https://www.vlsc.net/feedback/api/comment \
  -H 'Content-Type: application/json' \
  -d '{"page":"/","callsign":"W2XYZ","message":"测试"}'             # {"ok":false,"error":"not_in_db"}
# 浏览器打开 https://www.vlsc.net/ 页面底部确认 widget 出现
# 测试数据删除：后台删除或 sqlite3 清理
```

- [ ] **步骤 6：清理测试数据 + Commit 部署记录**

```bash
ssh cheenle@www.vlsc.net 'sqlite3 /home/cheenle/feedback/feedback.db "DELETE FROM comments;"'
cd /Users/cheenle/HAM/website
git add -A && git commit -m "deploy(feedback): live deployment verified"
```
