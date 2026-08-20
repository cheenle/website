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
