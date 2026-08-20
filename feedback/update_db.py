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
