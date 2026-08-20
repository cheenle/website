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
        self.assertEqual(count, 3)  # BG1SB / 1A0C / JA1ABC（4X/BG1SB 并入 BG1SB，SOS 无效）
        self.assertTrue(db.callsign_exists(self.conn, 'BG1SB'))
        self.assertTrue(db.callsign_exists(self.conn, 'JA1ABC'))
        self.assertTrue(db.callsign_exists(self.conn, '1A0C'))
        self.assertFalse(db.callsign_exists(self.conn, 'W1AW'))

    def test_meta(self):
        db.import_callsigns(self.conn, self.json_path, meta_date='2026-08-20')
        meta = dict(db.get_meta(self.conn))
        self.assertEqual(meta.get('db_updated_at'), '2026-08-20')
        self.assertEqual(meta.get('db_count'), '3')


class TestDbComments(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.conn = db.connect(os.path.join(self.tmp, 't.db'))
        db.init_db(self.conn)
        seed = os.path.join(self.tmp, 'x.json')
        with open(seed, 'w', encoding='utf-8') as f:
            json.dump({'BG1SB': {}}, f)
        db.import_callsigns(self.conn, seed)
        self.p = '/mrrc_ft710'

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
        self.assertEqual(top['children'][0]['callsign'], 'DL2RUM')
        self.assertTrue(top['children'][0]['is_admin'])
        self.assertEqual(len(top['children']), 2)

    def test_hide_hides_subtree(self):
        c1 = db.add_comment(self.conn, self.p, 'BG1SB', '顶部', '1.2.3.4')
        db.add_comment(self.conn, self.p, 'JA1ABC', '子', '1.2.3.5', parent_id=c1)
        db.set_status(self.conn, c1, 'hidden')
        self.assertEqual(db.get_comments(self.conn, self.p), [])
        all_ = db.get_comments(self.conn, self.p, include_hidden=True)
        self.assertEqual(len(all_), 1)          # 树根
        self.assertEqual(len(all_[0]['children']), 1)  # 隐藏根的回复仍在 include_hidden 视图内
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
        status, _, raw = service.handle_request('POST', '/feedback/api/comment', {}, body, ip)
        return status, json.loads(raw.decode('utf-8'))

    def jresp(self, method, path, query=None, body=None, ip='1.2.3.4', origin=None):
        status, _, raw = service.handle_request(method, path, query or {}, body, ip, origin)
        return status, json.loads(raw.decode('utf-8'))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


class TestApiSubmit(FeedbackServiceBase):
    def test_valid_comment(self):
        status, body = self.post({'page': self.p, 'callsign': 'bg1sb', 'message': '你好，问题'})
        self.assertEqual(status, 200)
        self.assertTrue(body['ok'])
        conn = service.get_conn()
        tree = db.get_comments(conn, self.p)
        conn.close()
        self.assertEqual(len(tree), 1)
        self.assertEqual(tree[0]['callsign'], 'BG1SB')

    def test_format_rejected(self):
        status, body = self.post({'page': self.p, 'callsign': 'FOO@BAR', 'message': 'hi'})
        self.assertEqual(status, 400)
        self.assertEqual(body['error'], 'format')

    def test_not_in_db_rejected(self):
        status, body = self.post({'page': self.p, 'callsign': 'W2XYZ', 'message': 'hi'})
        self.assertEqual(status, 400)
        self.assertEqual(body['error'], 'not_in_db')

    def test_invalid_page(self):
        status, body = self.post({'page': 'evil<script>', 'callsign': 'BG1SB', 'message': 'hi'})
        self.assertEqual(status, 400)
        self.assertEqual(body['error'], 'invalid_page')

    def test_message_length(self):
        status, body = self.post({'page': self.p, 'callsign': 'BG1SB', 'message': 'x'})
        self.assertEqual(status, 400)
        self.assertEqual(body['error'], 'message_length')

    def test_honeypot_dropped(self):
        status, body = self.post({'page': self.p, 'callsign': 'BG1SB', 'message': 'hi', 'website': 'spam'})
        self.assertEqual(status, 200)
        self.assertEqual(body['id'], 0)
        conn = service.get_conn()
        self.assertEqual(db.count_all(conn), 0)
        conn.close()

    def test_rate_limit_per_ip(self):
        calls = ['BG1SB', 'JA1ABC', 'DL2RUM', 'W1AW']
        for i in range(5):
            status, _ = self.post({'page': self.p, 'callsign': calls[i % 4], 'message': 'm%d' % i})
            self.assertEqual(status, 200)
        status, body = self.post({'page': self.p, 'callsign': 'BG1SB', 'message': 'm5'})
        self.assertEqual(status, 429)
        self.assertEqual(body['error'], 'rate_limit')

    def test_rate_limit_per_callsign(self):
        for i in range(3):
            status, _ = self.post({'page': self.p, 'callsign': 'BG1SB', 'message': 'm%d' % i}, ip='9.9.9.%d' % i)
            self.assertEqual(status, 200)
        status, body = self.post({'page': self.p, 'callsign': 'BG1SB', 'message': 'm3'}, ip='9.9.9.9')
        self.assertEqual(status, 429)


class TestApiReply(FeedbackServiceBase):
    def test_reply_flow_and_depth(self):
        self.post({'page': self.p, 'callsign': 'BG1SB', 'message': 'q1'})
        conn = service.get_conn()
        top = db.get_comments(conn, self.p)[0]
        conn.close()
        self.post({'page': self.p, 'callsign': 'JA1ABC', 'message': 'r1', 'reply_to': top['id']}, ip='2.2.2.2')
        status, body = self.post({'page': self.p, 'callsign': 'DL2RUM', 'message': 'r2', 'reply_to': 99999}, ip='2.2.2.3')
        self.assertEqual(status, 400)
        self.assertEqual(body['error'], 'invalid_reply')
        status, body = self.post({'page': self.p, 'callsign': 'DL2RUM', 'message': 'r3', 'reply_to': 'abc'}, ip='2.2.2.4')
        self.assertEqual(status, 400)


class TestApiAdmin(FeedbackServiceBase):
    def test_admin_reply_hide_delete(self):
        self.post({'page': self.p, 'callsign': 'BG1SB', 'message': 'q1'})
        conn = service.get_conn()
        cid = db.get_comments(conn, self.p)[0]['id']
        conn.close()
        status, body = self.jresp('POST', '/feedback/admin/action', body={'action': 'reply', 'id': cid, 'message': '站长答复'})
        self.assertEqual(status, 200)
        conn = service.get_conn()
        tree = db.get_comments(conn, self.p)
        self.assertTrue(tree[0]['children'][0]['is_admin'])
        self.assertEqual(tree[0]['children'][0]['callsign'], 'BG1SB')
        conn.close()
        status, _ = self.jresp('POST', '/feedback/admin/action', body={'action': 'hide', 'id': cid})
        self.assertEqual(status, 200)
        conn = service.get_conn()
        self.assertEqual(db.get_comments(conn, self.p), [])
        conn.close()
        status, _ = self.jresp('POST', '/feedback/admin/action', body={'action': 'delete', 'id': cid})
        self.assertEqual(status, 200)
        conn = service.get_conn()
        self.assertEqual(db.count_all(conn), 0)
        conn.close()

    def test_origin_forbidden(self):
        status, _ = self.jresp('POST', '/feedback/admin/action', body={'action': 'delete', 'id': 1},
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
        status, body = self.jresp('GET', '/feedback/api/comments', query={'page': '/zh/mrrc_ft710'})
        self.assertEqual(status, 200)
        self.assertEqual(len(body['comments']), 1)

    def test_get_invalid_page(self):
        status, body = self.jresp('GET', '/feedback/api/comments', query={'page': '<b>'})
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
