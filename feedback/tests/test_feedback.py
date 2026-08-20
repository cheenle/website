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
