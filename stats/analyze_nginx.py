#!/usr/bin/env python3
"""VLSC Website Statistics Analyzer — parse nginx logs, store in SQLite, generate HTML dashboard.

Replaces the old Apache-specific analyze.py. Handles nginx combined log format
with optional vhost filtering via a custom log_format.

Dimensions: per-domain (vhost) and per sub-site (first path segment) breakdowns
with long-term daily summaries, bandwidth, engagement (returning visitors, visit
span, pages/visitor), 7x24h activity heatmap, traffic sources, devices, status
codes, top 404s and most active visitors.

Usage:
    python3 analyze_nginx.py          # incremental parse + render dashboard
    python3 analyze_nginx.py --full   # full re-parse of all available logs

Deploy to server and run via cron every 30 min:
    */30 * * * * cd /home/cheenle/stats && python3 analyze_nginx.py
"""

import sqlite3
import os
import re
import json
import gzip
import subprocess
import hashlib
import time
import argparse
from datetime import datetime, timedelta, timezone
from collections import Counter, defaultdict
from urllib.parse import urlparse

# --- Constants ---
STATS_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(STATS_DIR, "stats_nginx.db")
# Dashboard output — override via env so the SQLite DB (visitor IPs) can live
# outside the web-served directory: STATS_HTML_PATH=/home/cheenle/stats/index.html
HTML_PATH = os.environ.get("STATS_HTML_PATH", os.path.join(STATS_DIR, "index.html"))
MMDB_PATH = os.path.join(STATS_DIR, "GeoLite2-Country.mmdb")
CST = timezone(timedelta(hours=8))
HITS_RETENTION_DAYS = 30

# Nginx access log paths
NGINX_LOG = "/var/log/nginx/access.log"
NGINX_LOG_GLOB = "/var/log/nginx/access.log*"

# --- Nginx combined log format regex ---
# Format: $remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent"
# Example: 10.0.0.1 - - [12/Jul/2026:12:00:00 +0800] "GET /mrrc/ HTTP/2.0" 200 1234 "https://..." "Mozilla/..."
# Also handles optional $host prefix if configured: host:port remote_addr - ...
# and optional $request_time at end

LOG_RE = re.compile(
    r'^(?:(\S+)\s+)?'                      # optional vhost:port prefix
    r'(\S+)\s+'                              # remote_addr
    r'(\S+)\s+'                              # remote_user (usually -)
    r'(\S+)\s+'                              # auth (usually -)
    r'\[([^\]]+)\]\s+'                       # [time_local]
    r'"(\S+)\s+(\S+)\s+(\S+)"\s+'           # "METHOD /path PROTO"
    r'(\d{3})\s+'                            # status
    r'(\S+)\s+'                              # body_bytes_sent (- or number)
    r'"([^"]*)"\s+'                          # "http_referer"
    r'"([^"]*)"'                             # "http_user_agent"
    r'(?:\s+(\S+))?'                         # optional: request_time
)

# UA parsing — bot tokens (lowercase)
BOT_TOKENS = [
    "googlebot", "bingbot", "baiduspider", "yandexbot", "slurp", "duckduckbot",
    "ahrefsbot", "semrushbot", "petalbot", "bytespider", "facebookexternalhit",
    "twitterbot", "libredtail-http", "nuclei", "nikto", "nmap", "zgrab", "masscan",
    "go-http-client", "python-requests", "curl", "wget", "censys", "shodan",
    "netcraft", "gobuster", "dirbuster", "nessus", "burp", "sqlmap",
]

# Scanner paths (heuristic — flag regardless of UA)
SCANNER_PATH_TOKENS = [
    "cgi-bin", ".env", "wp-admin", "admin.php", "config.php", ".git/",
    "phpmyadmin", "wp-login", "xmlrpc", ".asp", "phpunit", "actuator",
    "geoserver", "web/config", "sdk/weblanguage", "hello.world",
]

# Search engines — referer hosts containing the key roll up to the label
SEARCH_ENGINES = {
    "google.": "Google", "bing.com": "Bing", "baidu.com": "Baidu",
    "duckduckgo.com": "DuckDuckGo", "sogou.com": "Sogou", "so.com": "360 Search",
    "yandex.": "Yandex", "search.yahoo": "Yahoo",
}

# Known sub-sites (first path segment) — everything else rolls up to "portal"
KNOWN_SITES = {
    "mrrc", "mrrc_modern", "mrrc_ft8", "mrrc_ft710", "sunmrrc", "sunsdrmobile",
    "efhw", "yijing", "blog", "rig", "stats", "feedback", "mrrc_hub",
    "mrrc_portal", "ft8",
}


def site_from_path(path):
    """Map a request path to its sub-site (first segment) or 'portal'."""
    if not path:
        return "portal"
    seg = path.lstrip("/").split("/", 1)[0].split("?", 1)[0].lower()
    return seg if seg in KNOWN_SITES else "portal"


def fmt_bytes(n):
    """Human-readable byte count."""
    n = float(n or 0)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{int(n)} B" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024

_MONTH_MAP = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}


def parse_timestamp(ts_str):
    """Parse nginx [DD/Mon/YYYY:HH:MM:SS +TZ] to ISO 8601 in CST."""
    date_part, time_part = ts_str.split(":", 1)
    day, mon, year = date_part.split("/")
    month = _MONTH_MAP[mon]
    time_rest = time_part.rsplit(" ", 1)
    h, m, s = time_rest[0].split(":")
    tz_str = time_rest[1]

    tz_sign = 1 if tz_str[0] == "+" else -1
    tz_h = int(tz_str[1:3])
    tz_m = int(tz_str[3:5])
    tz_offset = timezone(timedelta(hours=tz_sign * tz_h, minutes=tz_sign * tz_m))

    t = datetime(int(year), month, int(day), int(h), int(m), int(s), tzinfo=tz_offset)
    local = t.astimezone(CST)
    return local.strftime("%Y-%m-%dT%H:%M:%S"), local.strftime("%Y-%m-%d")


def read_log_lines(filepath):
    """Read all lines from a log file (plain text or gzip). Uses sudo for access."""
    try:
        result = subprocess.run(
            ["sudo", "cat", filepath],
            capture_output=True, timeout=30
        )
        if result.returncode != 0:
            print(f"  WARNING: sudo cat {filepath} failed: {result.stderr.decode().strip()}")
            return []
        raw = result.stdout
    except Exception as e:
        print(f"  ERROR reading {filepath}: {e}")
        return []

    if raw[:2] == b"\x1f\x8b":
        import io
        return gzip.open(io.BytesIO(raw), "rt", errors="replace").readlines()

    return raw.decode("utf-8", errors="replace").splitlines()


def parse_log_line(line):
    """Parse one nginx combined log line. Returns dict or None if no match."""
    m = LOG_RE.match(line)
    if not m:
        return None

    vhost = m.group(1)  # may be None
    ip = m.group(2)
    ident, auth = m.group(3), m.group(4)
    ts_raw = m.group(5)
    method, path, proto = m.group(6), m.group(7), m.group(8)
    status = m.group(9)
    bytes_str = m.group(10)
    referer = m.group(11)
    ua = m.group(12)

    ts_iso, ts_date = parse_timestamp(ts_raw)
    try:
        status = int(status)
    except ValueError:
        status = 0
    try:
        b = int(bytes_str)
    except ValueError:
        b = 0

    return {
        "ts": ts_iso,
        "date": ts_date,
        "vhost": vhost or "www.vlsc.net",
        "ip": ip,
        "method": method,
        "path": path,
        "status": status,
        "bytes": b,
        "referer": referer,
        "ua": ua,
    }


def parse_ua(ua_str):
    """Extract browser and OS from UA string. Returns (browser, os_name, is_bot)."""
    ua_lower = ua_str.lower() if ua_str else ""

    is_bot = 0
    for token in BOT_TOKENS:
        if token in ua_lower:
            is_bot = 1
            break

    browser = "Other"
    if "edg/" in ua_lower:
        browser = "Edge"
    elif "chrome/" in ua_lower and "samsungbrowser" not in ua_lower:
        browser = "Chrome"
    elif "safari/" in ua_lower and "chrome/" not in ua_lower:
        browser = "Safari"
    elif "firefox/" in ua_lower:
        browser = "Firefox"
    elif "opera" in ua_lower or "opr/" in ua_lower:
        browser = "Opera"
    elif "samsungbrowser" in ua_lower:
        browser = "Samsung Internet"
    elif "qqbrowser" in ua_lower:
        browser = "QQ Browser"
    elif is_bot:
        browser = "Bot"

    os_name = "Other"
    if "windows nt" in ua_lower:
        os_name = "Windows"
    elif "mac os x" in ua_lower:
        os_name = "macOS"
    elif "android" in ua_lower:
        os_name = "Android"
    elif "iphone" in ua_lower or "ipad" in ua_lower:
        os_name = "iOS"
    elif "linux" in ua_lower and "android" not in ua_lower:
        os_name = "Linux"
    elif "cros" in ua_lower:
        os_name = "ChromeOS"

    return browser, os_name, is_bot


def is_scanner_path(path):
    """Check if path matches known scanner/exploit patterns."""
    path_lower = path.lower() if path else ""
    for token in SCANNER_PATH_TOKENS:
        if token in path_lower:
            return True
    if "%2e%2e" in path_lower or "%%32%%65" in path_lower or "%ADd+" in path_lower:
        return True
    return False


# --- GeoIP ---
_geoip_reader = None


def init_geoip():
    global _geoip_reader
    if _geoip_reader is not None:
        return _geoip_reader if _geoip_reader is not False else None
    if not os.path.exists(MMDB_PATH):
        print("  WARNING: GeoIP database not found at", MMDB_PATH)
        _geoip_reader = False
        return None
    try:
        import maxminddb
        _geoip_reader = maxminddb.open_database(MMDB_PATH)
        return _geoip_reader
    except ImportError:
        print("  WARNING: maxminddb not installed. Run: pip3 install maxminddb")
        _geoip_reader = False
        return None
    except Exception as e:
        print(f"  WARNING: Failed to open GeoIP database: {e}")
        _geoip_reader = False
        return None


def lookup_country(ip):
    reader = init_geoip()
    if reader is None:
        return "Unknown"
    try:
        result = reader.get(ip)
        if result and "country" in result:
            return result["country"]["names"].get("en", "Unknown")
    except Exception:
        pass
    return "Unknown"


def country_flag(country_name):
    country_to_code = {
        "United States": "\U0001f1fa\U0001f1f8", "China": "\U0001f1e8\U0001f1f3",
        "Japan": "\U0001f1ef\U0001f1f5", "Germany": "\U0001f1e9\U0001f1ea",
        "United Kingdom": "\U0001f1ec\U0001f1e7", "France": "\U0001f1eb\U0001f1f7",
        "Canada": "\U0001f1e8\U0001f1e6", "Australia": "\U0001f1e6\U0001f1fa",
        "South Korea": "\U0001f1f0\U0001f1f7", "Russia": "\U0001f1f7\U0001f1fa",
        "Brazil": "\U0001f1e7\U0001f1f7", "India": "\U0001f1ee\U0001f1f3",
        "Singapore": "\U0001f1f8\U0001f1ec", "Netherlands": "\U0001f1f3\U0001f1f1",
        "Sweden": "\U0001f1f8\U0001f1ea", "Switzerland": "\U0001f1e8\U0001f1ed",
        "Taiwan": "\U0001f1f9\U0001f1fc", "Hong Kong": "\U0001f1ed\U0001f1f0",
        "Italy": "\U0001f1ee\U0001f1f9", "Spain": "\U0001f1ea\U0001f1f8",
        "Poland": "\U0001f1f5\U0001f1f1", "Ukraine": "\U0001f1fa\U0001f1e6",
        "Thailand": "\U0001f1f9\U0001f1ed", "Vietnam": "\U0001f1fb\U0001f1f3",
        "Indonesia": "\U0001f1ee\U0001f1e9", "Malaysia": "\U0001f1f2\U0001f1fe",
        "Philippines": "\U0001f1f5\U0001f1ed", "Finland": "\U0001f1eb\U0001f1ee",
        "Norway": "\U0001f1f3\U0001f1f4", "Denmark": "\U0001f1e9\U0001f1f0",
        "Belgium": "\U0001f1e7\U0001f1ea", "Austria": "\U0001f1e6\U0001f1f9",
        "Czechia": "\U0001f1e8\U0001f1ff", "Ireland": "\U0001f1ee\U0001f1ea",
        "New Zealand": "\U0001f1f3\U0001f1ff", "Mexico": "\U0001f1f2\U0001f1fd",
        "Argentina": "\U0001f1e6\U0001f1f7", "Turkey": "\U0001f1f9\U0001f1f7",
        "Israel": "\U0001f1ee\U0001f1f1", "United Arab Emirates": "\U0001f1e6\U0001f1ea",
    }
    code = country_to_code.get(country_name, "\U0001f310")
    return f"{code} {country_name}"


# --- Database ---

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS meta (
            key   TEXT PRIMARY KEY,
            value TEXT
        );
        CREATE TABLE IF NOT EXISTS hits (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            ts         TEXT NOT NULL,
            vhost      TEXT,
            ip         TEXT,
            method     TEXT,
            path       TEXT,
            status     INTEGER,
            bytes      INTEGER,
            referer    TEXT,
            ua         TEXT,
            ua_browser TEXT,
            ua_os      TEXT,
            is_bot     INTEGER DEFAULT 0,
            is_404     INTEGER DEFAULT 0,
            country    TEXT,
            site       TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_hits_ts ON hits(ts);
        CREATE INDEX IF NOT EXISTS idx_hits_path ON hits(path);
        CREATE TABLE IF NOT EXISTS daily_summary (
            date          TEXT PRIMARY KEY,
            pv            INTEGER DEFAULT 0,
            uv            INTEGER DEFAULT 0,
            bytes_total   INTEGER DEFAULT 0,
            status_2xx    INTEGER DEFAULT 0,
            status_3xx    INTEGER DEFAULT 0,
            status_4xx    INTEGER DEFAULT 0,
            status_5xx    INTEGER DEFAULT 0,
            top_pages     TEXT,
            top_refs      TEXT,
            top_countries TEXT,
            bots_pct      REAL
        );
        CREATE TABLE IF NOT EXISTS daily_domain_summary (
            date        TEXT NOT NULL,
            vhost       TEXT NOT NULL,
            pv          INTEGER DEFAULT 0,
            uv          INTEGER DEFAULT 0,
            bytes_total INTEGER DEFAULT 0,
            bots        INTEGER DEFAULT 0,
            PRIMARY KEY (date, vhost)
        );
        CREATE TABLE IF NOT EXISTS daily_site_summary (
            date        TEXT NOT NULL,
            site        TEXT NOT NULL,
            pv          INTEGER DEFAULT 0,
            uv          INTEGER DEFAULT 0,
            bytes_total INTEGER DEFAULT 0,
            PRIMARY KEY (date, site)
        );
    """)
    conn.commit()
    return conn


def migrate_db(conn):
    """Add hits.site to pre-existing databases and backfill it from path."""
    cols = [r[1] for r in conn.execute("PRAGMA table_info(hits)")]
    if "site" not in cols:
        conn.execute("ALTER TABLE hits ADD COLUMN site TEXT")
        conn.commit()
    if conn.execute("SELECT 1 FROM hits WHERE site IS NULL LIMIT 1").fetchone():
        for site in sorted(KNOWN_SITES):
            conn.execute(
                "UPDATE hits SET site=? WHERE site IS NULL AND (path LIKE ? OR path=?)",
                (site, f"/{site}/%", f"/{site}")
            )
        conn.execute("UPDATE hits SET site='portal' WHERE site IS NULL")
        conn.commit()
        print("  Backfilled hits.site for existing rows")


def get_parse_state(conn):
    cur = conn.execute("SELECT key, value FROM meta WHERE key IN ('log_file', 'position', 'inode')")
    state = dict(cur.fetchall())
    return {
        "log_file": state.get("log_file", NGINX_LOG),
        "position": int(state.get("position", 0)),
        "inode": int(state.get("inode", 0)),
    }


def save_parse_state(conn, log_file, position, inode):
    conn.execute("INSERT OR REPLACE INTO meta VALUES ('log_file', ?)", (log_file,))
    conn.execute("INSERT OR REPLACE INTO meta VALUES ('position', ?)", (str(position),))
    conn.execute("INSERT OR REPLACE INTO meta VALUES ('inode', ?)", (str(inode),))
    conn.commit()


def _insert_from_lines(conn, lines):
    count = 0
    cur = conn.cursor()
    for line in lines:
        parsed = parse_log_line(line.strip())
        if parsed is None:
            continue
        browser, os_name, is_bot = parse_ua(parsed["ua"])
        if not is_bot and is_scanner_path(parsed["path"]):
            is_bot = 1
        country = lookup_country(parsed["ip"])
        is_404 = 1 if parsed["status"] == 404 else 0
        site = site_from_path(parsed["path"])
        cur.execute(
            """INSERT INTO hits (ts, vhost, ip, method, path, status, bytes, referer, ua,
               ua_browser, ua_os, is_bot, is_404, country, site)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (parsed["ts"], parsed["vhost"], parsed["ip"], parsed["method"],
             parsed["path"], parsed["status"], parsed["bytes"], parsed["referer"],
             parsed["ua"], browser, os_name, is_bot, is_404, country, site)
        )
        count += 1
    conn.commit()
    return count


def ingest_logs(conn, full=False):
    try:
        result = subprocess.run(
            ["sudo", "stat", "-c", "%i %s", NGINX_LOG],
            capture_output=True, text=True, timeout=5
        )
        current_inode, current_size = map(int, result.stdout.strip().split())
    except Exception as e:
        print(f"  ERROR: Cannot stat log file: {e}")
        return 0

    state = get_parse_state(conn)
    prev_inode = state["inode"]
    prev_position = state["position"]

    if full:
        prev_position = 0
        conn.execute("DELETE FROM hits")
        conn.execute("DELETE FROM daily_summary")
        conn.execute("DELETE FROM daily_domain_summary")
        conn.execute("DELETE FROM daily_site_summary")
        conn.execute("DELETE FROM meta WHERE key LIKE 'historical%'")
        conn.commit()
        print("  Full re-parse requested — cleared existing data")

    # Log rotation detected
    if prev_inode != 0 and prev_inode != current_inode and not full:
        print(f"  Log rotated. Processing remaining data from old log")
        old_lines = read_log_lines(state["log_file"])
        new_from_old = _insert_from_lines(conn, old_lines[prev_position:])
        print(f"  Got {new_from_old} hits from rotated log tail")
        _ingest_historical_logs(conn)
        prev_position = 0

    lines = read_log_lines(NGINX_LOG)
    if prev_position >= len(lines) and prev_inode == current_inode and not full:
        print(f"  No new data (position={prev_position}, lines={len(lines)})")
        return 0

    new_lines = lines[prev_position:] if prev_position < len(lines) else []
    new_count = _insert_from_lines(conn, new_lines)

    if full:
        _ingest_historical_logs(conn)

    save_parse_state(conn, NGINX_LOG, len(lines), current_inode)
    print(f"  Inserted {new_count} new hits (position now {len(lines)})")
    return new_count


def _ingest_historical_logs(conn):
    import glob
    seen_key = "historical_processed"
    cur = conn.execute("SELECT value FROM meta WHERE key=?", (seen_key,))
    row = cur.fetchone()
    processed = set(row[0].split(",")) if row else set()

    for fpath in sorted(glob.glob(NGINX_LOG_GLOB)):
        if fpath == NGINX_LOG:
            continue
        if fpath in processed:
            continue
        print(f"  Processing historical log: {fpath}")
        lines = read_log_lines(fpath)
        n = _insert_from_lines(conn, lines)
        print(f"    Inserted {n} hits from {fpath}")
        processed.add(fpath)

    conn.execute("INSERT OR REPLACE INTO meta VALUES (?, ?)", (seen_key, ",".join(processed)))
    conn.commit()


def cleanup_old_hits(conn):
    cutoff = datetime.now(CST) - timedelta(days=HITS_RETENTION_DAYS)
    cutoff_str = cutoff.strftime("%Y-%m-%dT00:00:00")
    cur = conn.execute("DELETE FROM hits WHERE ts < ?", (cutoff_str,))
    deleted = cur.rowcount
    if deleted:
        print(f"  Cleaned up {deleted} old hits (before {cutoff_str})")
    conn.commit()


def summarize_date(conn, date):
    """(Re)build daily_summary + per-domain + per-site summaries for one date (CST)."""
    day_start, day_end = date + "T00:00:00", date + "T23:59:59"

    cur = conn.execute("""
        SELECT
            COUNT(*) AS pv,
            COUNT(DISTINCT ip || '|' || ua) AS uv,
            SUM(bytes) AS bytes_total,
            SUM(CASE WHEN status BETWEEN 200 AND 299 THEN 1 ELSE 0 END) AS s2xx,
            SUM(CASE WHEN status BETWEEN 300 AND 399 THEN 1 ELSE 0 END) AS s3xx,
            SUM(CASE WHEN status BETWEEN 400 AND 499 THEN 1 ELSE 0 END) AS s4xx,
            SUM(CASE WHEN status BETWEEN 500 AND 599 THEN 1 ELSE 0 END) AS s5xx,
            ROUND(100.0 * SUM(is_bot) / MAX(COUNT(*), 1), 1) AS bots_pct
        FROM hits WHERE ts >= ? AND ts < ?
    """, (day_start, day_end))
    row = cur.fetchone()

    cur = conn.execute("""
        SELECT path, COUNT(*) AS c FROM hits
        WHERE ts >= ? AND ts < ? AND is_bot = 0 AND status < 400
        GROUP BY path ORDER BY c DESC LIMIT 10
    """, (day_start, day_end))
    top_pages = json.dumps([{"path": r[0], "count": r[1]} for r in cur.fetchall()])

    cur = conn.execute("""
        SELECT referer, COUNT(*) AS c FROM hits
        WHERE ts >= ? AND ts < ? AND is_bot = 0 AND referer != '' AND referer != '-'
        GROUP BY referer ORDER BY c DESC LIMIT 10
    """, (day_start, day_end))
    top_refs = json.dumps([{"ref": r[0], "count": r[1]} for r in cur.fetchall()])

    cur = conn.execute("""
        SELECT country, COUNT(*) AS c FROM hits
        WHERE ts >= ? AND ts < ? AND is_bot = 0
        GROUP BY country ORDER BY c DESC LIMIT 10
    """, (day_start, day_end))
    top_countries = json.dumps([{"country": r[0], "count": r[1]} for r in cur.fetchall()])

    conn.execute("""
        INSERT OR REPLACE INTO daily_summary
        (date, pv, uv, bytes_total, status_2xx, status_3xx, status_4xx, status_5xx,
         top_pages, top_refs, top_countries, bots_pct)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, (date, row[0], row[1], row[2] or 0, row[3], row[4], row[5], row[6],
          top_pages, top_refs, top_countries, row[7] or 0.0))

    conn.execute("DELETE FROM daily_domain_summary WHERE date=?", (date,))
    for vhost, pv, uv, b, bots in conn.execute("""
        SELECT vhost, COUNT(*), COUNT(DISTINCT ip||'|'||ua),
               COALESCE(SUM(bytes),0), COALESCE(SUM(is_bot),0)
        FROM hits WHERE ts >= ? AND ts < ? GROUP BY vhost
    """, (day_start, day_end)):
        conn.execute(
            "INSERT INTO daily_domain_summary VALUES (?,?,?,?,?,?)",
            (date, vhost or "-", pv, uv, b, bots)
        )

    conn.execute("DELETE FROM daily_site_summary WHERE date=?", (date,))
    for site, pv, uv, b in conn.execute("""
        SELECT COALESCE(site, 'portal'), COUNT(*), COUNT(DISTINCT ip||'|'||ua),
               COALESCE(SUM(bytes),0)
        FROM hits WHERE ts >= ? AND ts < ? AND is_bot = 0
        GROUP BY COALESCE(site, 'portal')
    """, (day_start, day_end)):
        conn.execute(
            "INSERT INTO daily_site_summary VALUES (?,?,?,?,?)",
            (date, site, pv, uv, b)
        )

    conn.commit()


def update_daily_summary(conn, full=False):
    today = datetime.now(CST).strftime("%Y-%m-%d")
    if full:
        dates = [r[0] for r in conn.execute(
            "SELECT DISTINCT SUBSTR(ts, 1, 10) FROM hits ORDER BY 1")]
        for d in dates:
            summarize_date(conn, d)
        print(f"  Rebuilt summaries for {len(dates)} day(s)")
        return
    summarize_date(conn, today)
    row = conn.execute("SELECT pv, uv FROM daily_summary WHERE date=?", (today,)).fetchone()
    if row:
        print(f"  Updated daily_summary for {today}: PV={row[0]}, UV={row[1]}")


def query_stats(conn):
    now = datetime.now(CST)
    today = now.strftime("%Y-%m-%d")
    month_start = now.strftime("%Y-%m-01")
    day_start, day_end = today + "T00:00:00", today + "T23:59:59"
    d30_start = (now - timedelta(days=29)).strftime("%Y-%m-%d")

    def q(sql, params=()):
        row = conn.execute(sql, params).fetchone()
        if row is None:
            return None
        return row[0]

    def qall(sql, params=()):
        return conn.execute(sql, params).fetchall()

    stats = {}

    stats["today_pv"] = q("SELECT COALESCE(SUM(pv),0) FROM daily_summary WHERE date=?", (today,))
    stats["today_uv"] = q(
        "SELECT COUNT(DISTINCT ip||'|'||ua) FROM hits WHERE ts>=? AND ts<?",
        (day_start, day_end)
    )
    stats["month_pv"] = q("SELECT COALESCE(SUM(pv),0) FROM daily_summary WHERE date>=?", (month_start,))
    stats["total_pv"] = q("SELECT COALESCE(SUM(pv),0) FROM daily_summary")
    stats["today_bytes"] = q(
        "SELECT COALESCE(SUM(bytes),0) FROM hits WHERE ts>=? AND ts<?", (day_start, day_end))
    stats["month_bytes"] = q(
        "SELECT COALESCE(SUM(bytes_total),0) FROM daily_summary WHERE date>=?", (month_start,))

    human_pv = q(
        "SELECT COUNT(*) FROM hits WHERE ts>=? AND ts<? AND is_bot=0", (day_start, day_end)) or 0
    human_uv = q(
        "SELECT COUNT(DISTINCT ip||'|'||ua) FROM hits WHERE ts>=? AND ts<? AND is_bot=0",
        (day_start, day_end)) or 0
    stats["human_pv"] = human_pv
    stats["human_uv"] = human_uv
    stats["pages_per_uv"] = round(human_pv / human_uv, 1) if human_uv else 0.0

    hourly = qall("""
        SELECT SUBSTR(ts,12,2) AS h, COUNT(*) FROM hits
        WHERE ts>=? AND ts<? AND is_bot=0
        GROUP BY h ORDER BY h
    """, (day_start, day_end))
    stats["hourly"] = [(int(h), c) for h, c in hourly]
    stats["hourly_max"] = max([c for _, c in hourly]) if hourly else 0
    stats["peak_hour"] = max(stats["hourly"], key=lambda x: x[1])[0] if hourly else None

    daily = qall("""
        SELECT date, pv, uv FROM daily_summary
        WHERE date >= ? ORDER BY date
    """, (d30_start,))
    stats["daily"] = [(d, pv, uv) for d, pv, uv in daily]
    stats["daily_max"] = max([pv for _, pv, _ in daily]) if daily else 1

    # --- Per-domain (vhost) breakdown ---
    vhost_30d = dict(qall(
        "SELECT vhost, SUM(pv) FROM daily_domain_summary WHERE date>=? GROUP BY vhost",
        (d30_start,)))
    vhost_rows = qall("""
        SELECT vhost, COUNT(*), COUNT(DISTINCT ip||'|'||ua), COALESCE(SUM(bytes),0)
        FROM hits WHERE ts>=? AND ts<? GROUP BY vhost ORDER BY 2 DESC
    """, (day_start, day_end))
    total_vhost_pv = sum(r[1] for r in vhost_rows) or 1
    stats["vhosts"] = [
        {"vhost": v or "-", "pv": pv, "uv": uv, "bytes": b,
         "pv30": int(vhost_30d.get(v or "-", 0)),
         "share": round(100 * pv / total_vhost_pv, 1)}
        for v, pv, uv, b in vhost_rows
    ]

    # --- Per sub-site breakdown (first path segment) ---
    site_30d = dict(qall(
        "SELECT site, SUM(pv) FROM daily_site_summary WHERE date>=? GROUP BY site",
        (d30_start,)))
    site_rows = qall("""
        SELECT COALESCE(site,'portal'), COUNT(*), COUNT(DISTINCT ip||'|'||ua),
               COALESCE(SUM(bytes),0)
        FROM hits WHERE ts>=? AND ts<? AND is_bot=0
        GROUP BY COALESCE(site,'portal') ORDER BY 2 DESC
    """, (day_start, day_end))
    total_site_pv = sum(r[1] for r in site_rows) or 1
    stats["sites"] = [
        {"site": s, "pv": pv, "uv": uv, "bytes": b,
         "pv30": int(site_30d.get(s, 0)),
         "share": round(100 * pv / total_site_pv, 1)}
        for s, pv, uv, b in site_rows
    ]

    # Top pages per top site (for tabbed view)
    site_pages = {}
    for entry in stats["sites"][:8]:
        rows = qall("""
            SELECT path, COUNT(*) AS c FROM hits
            WHERE ts>=? AND ts<? AND is_bot=0 AND status<400 AND COALESCE(site,'portal')=?
            GROUP BY path ORDER BY c DESC LIMIT 8
        """, (day_start, day_end, entry["site"]))
        site_pages[entry["site"]] = [{"path": r[0], "count": r[1]} for r in rows]
    stats["site_pages"] = site_pages

    stats["top_pages"] = json.loads(q(
        "SELECT top_pages FROM daily_summary WHERE date=?", (today,)
    ) or "[]")

    stats["top_refs"] = json.loads(q(
        "SELECT top_refs FROM daily_summary WHERE date=?", (today,)
    ) or "[]")

    # Referer sources grouped by domain (search engines rolled up, internal excluded)
    ref_rows = qall("""
        SELECT referer, COUNT(*) AS c FROM hits
        WHERE ts>=? AND ts<? AND is_bot=0 AND referer != '' AND referer != '-'
        GROUP BY referer
    """, (day_start, day_end))
    sources = Counter()
    for ref, c in ref_rows:
        host = (urlparse(ref).netloc or ref).lower()
        if not host or host.endswith("vlsc.net"):
            continue
        label = host
        for key, name in SEARCH_ENGINES.items():
            if key in host:
                label = name
                break
        sources[label] += c
    stats["ref_sources"] = sources.most_common(12)

    stats["top_countries"] = json.loads(q(
        "SELECT top_countries FROM daily_summary WHERE date=?", (today,)
    ) or "[]")

    browser_rows = qall("""
        SELECT ua_browser, COUNT(*) AS c FROM hits
        WHERE ts>=? AND ts<? AND is_bot=0
        GROUP BY ua_browser ORDER BY c DESC
    """, (day_start, day_end))
    total_browser = sum(c for _, c in browser_rows) or 1
    stats["browsers"] = [(b, c, round(100 * c / total_browser, 1)) for b, c in browser_rows]

    os_rows = qall("""
        SELECT ua_os, COUNT(*) AS c FROM hits
        WHERE ts>=? AND ts<? AND is_bot=0
        GROUP BY ua_os ORDER BY c DESC
    """, (day_start, day_end))
    total_os = sum(c for _, c in os_rows) or 1
    stats["os_list"] = [(o, c, round(100 * c / total_os, 1)) for o, c in os_rows]

    # Device type split
    dev_rows = qall("""
        SELECT CASE
            WHEN LOWER(ua) LIKE '%ipad%' OR LOWER(ua) LIKE '%tablet%' THEN 'Tablet'
            WHEN LOWER(ua) LIKE '%mobile%' OR LOWER(ua) LIKE '%iphone%'
                 OR LOWER(ua) LIKE '%android%' THEN 'Mobile'
            ELSE 'Desktop' END AS dev, COUNT(*) AS c
        FROM hits WHERE ts>=? AND ts<? AND is_bot=0 GROUP BY dev ORDER BY c DESC
    """, (day_start, day_end))
    total_dev = sum(c for _, c in dev_rows) or 1
    stats["devices"] = [(d, c, round(100 * c / total_dev, 1)) for d, c in dev_rows]

    # Status code distribution
    srow = conn.execute("""
        SELECT SUM(CASE WHEN status BETWEEN 200 AND 299 THEN 1 ELSE 0 END),
               SUM(CASE WHEN status BETWEEN 300 AND 399 THEN 1 ELSE 0 END),
               SUM(CASE WHEN status BETWEEN 400 AND 499 THEN 1 ELSE 0 END),
               SUM(CASE WHEN status BETWEEN 500 AND 599 THEN 1 ELSE 0 END)
        FROM hits WHERE ts>=? AND ts<?
    """, (day_start, day_end)).fetchone()
    stats["status_dist"] = [(srow[i] or 0) for i in range(4)]

    stats["top_404"] = qall("""
        SELECT path, COUNT(*) AS c FROM hits
        WHERE ts>=? AND ts<? AND status=404
        GROUP BY path ORDER BY c DESC LIMIT 10
    """, (day_start, day_end))

    # 7-day x 24-hour activity heatmap (human traffic)
    d7_start = (now - timedelta(days=6)).strftime("%Y-%m-%d")
    heat_rows = qall("""
        SELECT SUBSTR(ts,1,10) AS d, CAST(SUBSTR(ts,12,2) AS INTEGER) AS h, COUNT(*) AS c
        FROM hits WHERE ts>=? AND is_bot=0 GROUP BY d, h
    """, (d7_start + "T00:00:00",))
    stats["heatmap"] = {(d, h): c for d, h, c in heat_rows}
    stats["heatmap_days"] = [
        (now - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
    stats["heatmap_max"] = max(stats["heatmap"].values()) if stats["heatmap"] else 0

    # --- Engagement / activity ---
    unique_ips = q(
        "SELECT COUNT(DISTINCT ip) FROM hits WHERE ts>=? AND ts<? AND is_bot=0",
        (day_start, day_end)) or 0
    returning = q("""
        SELECT COUNT(DISTINCT ip) FROM hits
        WHERE ts>=? AND ts<? AND is_bot=0
          AND ip IN (SELECT DISTINCT ip FROM hits WHERE ts<? AND is_bot=0)
    """, (day_start, day_end, day_start)) or 0
    stats["unique_ips"] = unique_ips
    stats["returning_ips"] = returning
    stats["returning_pct"] = round(100 * returning / unique_ips, 1) if unique_ips else 0.0

    spans = qall("""
        SELECT MIN(ts), MAX(ts) FROM hits
        WHERE ts>=? AND ts<? AND is_bot=0
        GROUP BY ip||'|'||ua HAVING COUNT(*) > 1
    """, (day_start, day_end))
    durations = []
    for t0, t1 in spans:
        try:
            delta = (datetime.fromisoformat(t1) - datetime.fromisoformat(t0)).total_seconds()
            if 0 < delta <= 12 * 3600:
                durations.append(delta)
        except (ValueError, TypeError):
            pass
    stats["avg_duration_min"] = round(sum(durations) / len(durations) / 60, 1) if durations else 0.0

    # Most active visitors today
    av_rows = qall("""
        SELECT ip, COUNT(*) AS reqs, COUNT(DISTINCT path) AS pages,
               MAX(country), MIN(ts), MAX(ts), MAX(ua_browser), MAX(ua_os)
        FROM hits WHERE ts>=? AND ts<? AND is_bot=0
        GROUP BY ip ORDER BY reqs DESC LIMIT 15
    """, (day_start, day_end))
    active = []
    for ip, reqs, pages, country, t0, t1, browser, osname in av_rows:
        try:
            dur = (datetime.fromisoformat(t1) - datetime.fromisoformat(t0)).total_seconds()
        except (ValueError, TypeError):
            dur = 0
        active.append({
            "ip": ip, "reqs": reqs, "pages": pages,
            "country": country or "Unknown",
            "first": (t0 or "")[11:19], "last": (t1 or "")[11:19],
            "duration_min": round(dur / 60, 1),
            "browser": browser or "?", "os": osname or "?",
        })
    stats["active_visitors"] = active

    stats["today_404"] = q(
        "SELECT COUNT(*) FROM hits WHERE ts>=? AND ts<? AND status=404",
        (day_start, day_end)
    )
    stats["bots_pct"] = q(
        "SELECT COALESCE(bots_pct,0) FROM daily_summary WHERE date=?", (today,)
    ) or 0.0
    stats["total_hits_today"] = q(
        "SELECT COUNT(*) FROM hits WHERE ts>=? AND ts<?",
        (day_start, day_end)
    )

    suspicious = qall("""
        SELECT ip, COUNT(*) AS c, GROUP_CONCAT(DISTINCT SUBSTR(path,1,80)) AS paths FROM hits
        WHERE ts>=? AND ts<? AND is_bot=1
        GROUP BY ip HAVING c >= 3 ORDER BY c DESC LIMIT 5
    """, (day_start, day_end))
    stats["suspicious"] = [(ip, c, paths) for ip, c, paths in suspicious]

    stats["last_update"] = now.strftime("%Y-%m-%d %H:%M:%S CST")

    return stats


def _pct_bar(pct, color="#00d4ff"):
    return f'<div class="pct-bar-bg"><div class="pct-bar-fill" style="width:{pct}%;background:{color}"></div></div>'


def render_html(stats):
    # 24h hourly bars
    hour_bars = ""
    for h in range(24):
        height_pct = 0
        count = 0
        for hh, c in stats["hourly"]:
            if hh == h:
                count = c
                height_pct = int(c / max(stats["hourly_max"], 1) * 100)
                break
        peak_class = 'peak' if count == stats["hourly_max"] and count > 0 else ''
        hour_bars += f'<div class="hour-col"><div class="hour-bar {peak_class}" style="height:{height_pct}%"></div><span class="hour-label">{h:02d}</span></div>'

    # 30-day SVG
    svg_points_pv = ""
    svg_points_uv = ""
    if stats["daily"]:
        max_val = stats["daily_max"]
        w_step = 780.0 / max(len(stats["daily"]) - 1, 1)
        for i, (d, pv, uv) in enumerate(stats["daily"]):
            x = i * w_step + 40
            y_pv = 200 - (pv / max_val * 180) if max_val > 0 else 200
            y_uv = 200 - (uv / max_val * 180) if max_val > 0 else 200
            svg_points_pv += f"{x:.1f},{y_pv:.1f} "
            svg_points_uv += f"{x:.1f},{y_uv:.1f} "

    # Domains (vhosts)
    vhost_html = ""
    for v in stats["vhosts"]:
        vhost_html += (
            f'<tr><td class="mono">{v["vhost"]}</td><td>{v["pv"]:,}</td>'
            f'<td>{v["uv"]:,}</td><td>{fmt_bytes(v["bytes"])}</td><td>{v["pv30"]:,}</td>'
            f'<td class="share-cell">{_pct_bar(v["share"])}'
            f'<span class="share-pct">{v["share"]}%</span></td></tr>'
        )
    if not vhost_html:
        vhost_html = '<tr><td colspan="6" class="empty">No data yet</td></tr>'

    # Sub-sites (human traffic)
    sites_html = ""
    for s in stats["sites"]:
        sites_html += (
            f'<tr><td class="mono">/{s["site"]}/</td><td>{s["pv"]:,}</td>'
            f'<td>{s["uv"]:,}</td><td>{fmt_bytes(s["bytes"])}</td><td>{s["pv30"]:,}</td>'
            f'<td class="share-cell">{_pct_bar(s["share"], "#7c3aed")}'
            f'<span class="share-pct">{s["share"]}%</span></td></tr>'
        )
    if not sites_html:
        sites_html = '<tr><td colspan="6" class="empty">No data yet</td></tr>'

    # 7-day x 24-hour heatmap
    heat_html = ""
    hmax = max(stats["heatmap_max"], 1)
    for d in stats["heatmap_days"]:
        cells = ""
        for h in range(24):
            c = stats["heatmap"].get((d, h), 0)
            alpha = (0.12 + 0.88 * c / hmax) if c else 0.04
            cells += (
                f'<div class="heat-cell" style="background:rgba(0,212,255,{alpha:.2f})" '
                f'title="{d} {h:02d}:00 — {c} hits"></div>'
            )
        heat_html += f'<div class="heat-row"><span class="heat-day">{d[5:]}</span>{cells}</div>'
    heat_hours = "".join(f'<span>{h}</span>' for h in range(24))

    # Top pages per site (tabbed)
    tab_buttons = ""
    for i, entry in enumerate(stats["sites"][:8]):
        active = " active" if i == 0 else ""
        tab_buttons += (
            f"<button class=\"tab-btn{active}\" "
            f"onclick=\"showSite('{entry['site']}',this)\">{entry['site']}</button>"
        )
    default_rows = stats["site_pages"].get(stats["sites"][0]["site"], []) if stats["sites"] else []
    site_pages_rows = ""
    for item in default_rows:
        site_pages_rows += f'<tr><td class="mono">{item["path"][:70]}</td><td>{item["count"]}</td></tr>'
    if not site_pages_rows:
        site_pages_rows = '<tr><td colspan="2" class="empty">No data yet</td></tr>'
    site_pages_json = json.dumps(stats["site_pages"], ensure_ascii=False).replace("</", "<\\/")

    # Referer sources (grouped by domain)
    ref_src_html = ""
    for name, c in stats["ref_sources"]:
        ref_src_html += f'<tr><td>{name}</td><td>{c}</td></tr>'
    if not ref_src_html:
        ref_src_html = '<tr><td colspan="2" class="empty">No external referrers yet</td></tr>'

    # Countries
    countries_html = ""
    for item in stats["top_countries"]:
        name = country_flag(item["country"])
        countries_html += f'<tr><td>{name}</td><td>{item["count"]}</td></tr>'
    if not countries_html:
        countries_html = '<tr><td colspan="2" class="empty">No GeoIP data</td></tr>'

    # Browsers
    browser_html = ""
    for name, count, pct in stats["browsers"][:8]:
        browser_html += f'<div class="dist-row"><span class="dist-label">{name}</span><span class="dist-value">{pct}%</span>{_pct_bar(pct)}</div>'
    if not browser_html:
        browser_html = '<div class="empty">No data</div>'

    # OS
    os_html = ""
    for name, count, pct in stats["os_list"][:8]:
        os_html += f'<div class="dist-row"><span class="dist-label">{name}</span><span class="dist-value">{pct}%</span>{_pct_bar(pct, "#7c3aed")}</div>'
    if not os_html:
        os_html = '<div class="empty">No data</div>'

    # Devices
    device_html = ""
    for name, count, pct in stats["devices"]:
        device_html += f'<div class="dist-row"><span class="dist-label">{name}</span><span class="dist-value">{pct}%</span>{_pct_bar(pct, "#10b981")}</div>'
    if not device_html:
        device_html = '<div class="empty">No data</div>'

    # Status codes
    total_req = sum(stats["status_dist"]) or 1
    status_html = ""
    status_meta = [
        ("2xx Success", "#10b981"), ("3xx Redirect", "#00d4ff"),
        ("4xx Client Error", "#f59e0b"), ("5xx Server Error", "#ef4444"),
    ]
    for (label, color), c in zip(status_meta, stats["status_dist"]):
        pct = round(100 * c / total_req, 1)
        status_html += (
            f'<div class="dist-row"><span class="dist-label wide">{label} ({c:,})</span>'
            f'<span class="dist-value">{pct}%</span>{_pct_bar(pct, color)}</div>'
        )

    # Top 404 paths
    p404_html = ""
    for path, c in stats["top_404"]:
        p404_html += f'<tr><td class="mono">{path[:70]}</td><td>{c}</td></tr>'
    if not p404_html:
        p404_html = '<tr><td colspan="2" class="empty">No 404s today</td></tr>'

    # Most active visitors
    av_html = ""
    for v in stats["active_visitors"]:
        av_html += (
            f'<tr><td class="mono">{v["ip"]}</td><td>{v["reqs"]}</td><td>{v["pages"]}</td>'
            f'<td>{country_flag(v["country"])}</td>'
            f'<td class="mono small">{v["first"]}–{v["last"]}</td>'
            f'<td>{v["duration_min"]} min</td><td>{v["browser"]} / {v["os"]}</td></tr>'
        )
    if not av_html:
        av_html = '<tr><td colspan="7" class="empty">No visitors yet</td></tr>'

    peak_hour_txt = f'{stats["peak_hour"]:02d}:00' if stats["peak_hour"] is not None else "—"

    # Suspicious
    suspicious_html = ""
    for ip, count, paths in stats["suspicious"]:
        suspicious_html += f'<tr><td class="mono">{ip}</td><td>{count}</td><td class="mono small">{paths[:80]}</td></tr>'
    if not suspicious_html:
        suspicious_html = '<tr><td colspan="3" class="empty">No suspicious activity detected</td></tr>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex">
<title>VLSC Website Statistics (Nginx)</title>
<style>
:root {{
    --primary: #00d4ff;
    --primary-dark: #0099cc;
    --purple: #7c3aed;
    --bg-dark: #0a0a0f;
    --bg-card: #13131f;
    --bg-light: #1e1e2e;
    --text: #ffffff;
    --text-secondary: #a0a0b0;
    --text-muted: #6b7280;
    --border: #2d2d3d;
    --success: #10b981;
    --warning: #f59e0b;
    --error: #ef4444;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--bg-dark); color: var(--text);
    line-height: 1.6; min-height: 100vh;
}}
.mono {{ font-family: 'JetBrains Mono', 'Courier New', monospace; font-size: 0.85rem; }}
.container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}

.header {{
    display: flex; justify-content: space-between; align-items: center;
    padding: 24px 0; border-bottom: 1px solid var(--border); margin-bottom: 32px;
    flex-wrap: wrap; gap: 12px;
}}
.header h1 {{ font-size: 1.5rem; color: var(--primary); }}
.header-meta {{ color: var(--text-muted); font-size: 0.85rem; text-align: right; }}
.header-meta span {{ display: block; }}

.cards {{ display: grid; grid-template-columns: repeat(6,1fr); gap: 16px; margin-bottom: 32px; }}
.card {{
    background: var(--bg-card); border: 1px solid var(--border);
    border-radius: 12px; padding: 24px; text-align: center;
}}
.card-number {{ font-size: 2rem; font-weight: 700; color: var(--primary);
    font-family: 'JetBrains Mono', monospace; }}
.card-label {{ font-size: 0.85rem; color: var(--text-secondary); margin-top: 4px; }}

.section {{ margin-bottom: 32px; }}
.section-title {{ font-size: 1.1rem; font-weight: 600; margin-bottom: 16px; color: var(--text); }}

.hour-chart {{
    background: var(--bg-card); border: 1px solid var(--border);
    border-radius: 12px; padding: 24px;
    display: flex; align-items: flex-end; gap: 4px; height: 180px;
}}
.hour-col {{ flex:1; display:flex; flex-direction:column; align-items:center; height:100%; justify-content:flex-end; }}
.hour-bar {{
    width: 100%; max-width: 32px; background: var(--bg-light);
    border-radius: 4px 4px 0 0; min-height: 2px; transition: height 0.3s;
}}
.hour-bar.peak {{ background: var(--primary); box-shadow: 0 0 12px rgba(0,212,255,0.5); }}
.hour-label {{ font-size: 0.65rem; color: var(--text-muted); margin-top: 6px; }}

.trend-box {{
    background: var(--bg-card); border: 1px solid var(--border);
    border-radius: 12px; padding: 24px; overflow-x: auto;
}}
.legend {{ display: flex; gap: 24px; margin-bottom: 8px; font-size: 0.85rem; }}
.legend-pv {{ color: var(--primary); }}
.legend-uv {{ color: var(--purple); }}

.grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 32px; }}

.table-box {{
    background: var(--bg-card); border: 1px solid var(--border);
    border-radius: 12px; padding: 20px; overflow-x: auto;
}}
table {{ width: 100%; border-collapse: collapse; }}
th {{ text-align: left; padding: 8px 12px; border-bottom: 1px solid var(--border);
    color: var(--text-muted); font-size: 0.8rem; text-transform: uppercase; }}
td {{ padding: 8px 12px; border-bottom: 1px solid rgba(45,45,61,0.5); font-size: 0.9rem; }}
.empty {{ color: var(--text-muted); font-style: italic; padding: 16px; text-align: center; }}
.small {{ font-size: 0.75rem; }}

.dist-row {{ display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }}
.dist-label {{ width: 100px; font-size: 0.85rem; flex-shrink: 0; }}
.dist-value {{ width: 45px; font-size: 0.85rem; color: var(--text-secondary); text-align: right; }}
.pct-bar-bg {{ flex:1; height: 8px; background: var(--bg-light); border-radius: 4px; overflow: hidden; }}
.pct-bar-fill {{ height: 100%; border-radius: 4px; transition: width 0.3s; }}

.anomaly {{
    background: var(--bg-card); border: 1px solid var(--border);
    border-radius: 12px; padding: 24px; margin-bottom: 32px;
}}
.anomaly-title {{ color: var(--warning); font-weight: 600; margin-bottom: 12px; }}
.anomaly-stats {{ display: flex; gap: 32px; flex-wrap: wrap; margin-bottom: 16px; }}
.anomaly-stat {{ font-size: 0.9rem; }}
.anomaly-stat strong {{ color: var(--warning); }}

.share-cell {{ display: flex; align-items: center; gap: 8px; min-width: 150px; }}
.share-pct {{ font-size: 0.8rem; color: var(--text-secondary); width: 44px; flex-shrink: 0; }}

.heat-row {{ display: flex; align-items: center; gap: 2px; margin-bottom: 2px; }}
.heat-day {{ width: 46px; font-size: 0.7rem; color: var(--text-muted); flex-shrink: 0; }}
.heat-cell {{ flex: 1; height: 16px; border-radius: 2px; min-width: 8px; }}
.heat-hours {{ display: flex; gap: 2px; margin: 6px 0 0 48px; }}
.heat-hours span {{ flex: 1; text-align: center; font-size: 0.6rem; color: var(--text-muted); min-width: 8px; }}

.tab-btn {{
    background: var(--bg-light); color: var(--text-secondary);
    border: 1px solid var(--border); border-radius: 6px;
    padding: 4px 12px; font-size: 0.8rem; cursor: pointer; margin: 0 4px 8px 0;
}}
.tab-btn.active {{ background: var(--primary); color: #000; border-color: var(--primary); font-weight: 600; }}

.dist-label.wide {{ width: 170px; }}

.engage {{ display: grid; grid-template-columns: repeat(4,1fr); gap: 16px; margin-bottom: 32px; }}
.engage-item {{
    background: var(--bg-card); border: 1px solid var(--border);
    border-radius: 12px; padding: 16px 20px;
}}
.engage-num {{ font-size: 1.4rem; font-weight: 700; color: var(--purple);
    font-family: 'JetBrains Mono', monospace; }}
.engage-label {{ font-size: 0.8rem; color: var(--text-secondary); margin-top: 2px; }}

@media (max-width: 1024px) {{
    .cards {{ grid-template-columns: repeat(3,1fr); }}
    .engage {{ grid-template-columns: repeat(2,1fr); }}
}}
@media (max-width: 768px) {{
    .cards {{ grid-template-columns: repeat(2,1fr); }}
    .grid-2 {{ grid-template-columns: 1fr; }}
    .hour-chart {{ height: 120px; }}
    .anomaly-stats {{ flex-direction: column; gap: 8px; }}
}}
@media (max-width: 480px) {{
    .cards {{ grid-template-columns: 1fr; }}
    .engage {{ grid-template-columns: 1fr; }}
    .header {{ flex-direction: column; text-align: center; }}
    .header-meta {{ text-align: center; }}
}}
</style>
</head>
<body>
<div class="container">

<div class="header">
    <div><h1>\U0001f4ca VLSC Website Statistics (Nginx)</h1></div>
    <div class="header-meta">
        <span>Last update: {stats["last_update"]}</span>
        <span>Source: nginx access.log</span>
    </div>
</div>

<div class="cards">
    <div class="card"><div class="card-number">{stats["today_pv"]:,}</div><div class="card-label">Today PV</div></div>
    <div class="card"><div class="card-number">{stats["today_uv"]:,}</div><div class="card-label">Today UV</div></div>
    <div class="card"><div class="card-number">{stats["pages_per_uv"]}</div><div class="card-label">Pages / Visitor (human)</div></div>
    <div class="card"><div class="card-number">{fmt_bytes(stats["today_bytes"])}</div><div class="card-label">Bandwidth Today</div></div>
    <div class="card"><div class="card-number">{stats["month_pv"]:,}</div><div class="card-label">Month PV</div></div>
    <div class="card"><div class="card-number">{stats["total_pv"]:,}</div><div class="card-label">Total PV (All-time)</div></div>
</div>

<div class="section">
    <div class="section-title">\U0001f4c8 24-Hour Traffic (Today, CST)</div>
    <div class="hour-chart">{hour_bars}</div>
</div>

<div class="section">
    <div class="section-title">\U0001f4c9 30-Day Trend</div>
    <div class="trend-box">
        <div class="legend"><span class="legend-pv">━ PV</span><span class="legend-uv">┅ UV</span></div>
        <svg viewBox="0 0 860 240" width="100%" height="240">
            <line x1="40" y1="20" x2="820" y2="20" stroke="#2d2d3d" stroke-dasharray="4,4"/>
            <line x1="40" y1="200" x2="820" y2="200" stroke="#2d2d3d"/>
            <line x1="40" y1="20" x2="40" y2="210" stroke="#2d2d3d"/>
            <line x1="35" y1="200" x2="820" y2="200" stroke="#2d2d3d"/>
            <polyline fill="none" stroke="#00d4ff" stroke-width="2" points="{svg_points_pv.strip()}"/>
            <polyline fill="none" stroke="#7c3aed" stroke-width="1.5" stroke-dasharray="6,4" points="{svg_points_uv.strip()}"/>
        </svg>
    </div>
</div>

<div class="section">
    <div class="section-title">\U0001f310 Domains (vhosts, today vs 30-day)</div>
    <div class="table-box">
        <table><thead><tr><th>Domain</th><th>PV today</th><th>UV today</th><th>Bandwidth</th><th>PV 30d</th><th>Share</th></tr></thead><tbody>{vhost_html}</tbody></table>
    </div>
</div>

<div class="section">
    <div class="section-title">\U0001f9e9 Sub-sites (human traffic, today vs 30-day)</div>
    <div class="table-box">
        <table><thead><tr><th>Site</th><th>PV today</th><th>UV today</th><th>Bandwidth</th><th>PV 30d</th><th>Share</th></tr></thead><tbody>{sites_html}</tbody></table>
    </div>
</div>

<div class="section">
    <div class="section-title">\U0001f525 Activity Heatmap (last 7 days × 24h, human traffic)</div>
    <div class="trend-box">
        {heat_html}
        <div class="heat-hours">{heat_hours}</div>
    </div>
</div>

<div class="section">
    <div class="section-title">\U0001f4aa Engagement (today, human visitors)</div>
    <div class="engage">
        <div class="engage-item"><div class="engage-num">{stats["unique_ips"]:,}</div><div class="engage-label">Unique IPs</div></div>
        <div class="engage-item"><div class="engage-num">{stats["returning_pct"]}%</div><div class="engage-label">Returning Visitors ({stats["returning_ips"]:,} IPs)</div></div>
        <div class="engage-item"><div class="engage-num">{stats["avg_duration_min"]} min</div><div class="engage-label">Avg Visit Span</div></div>
        <div class="engage-item"><div class="engage-num">{peak_hour_txt}</div><div class="engage-label">Peak Hour (CST)</div></div>
    </div>
</div>

<div class="grid-2">
    <div class="table-box">
        <div class="section-title">\U0001f4c4 Top Pages by Site (today)</div>
        <div>{tab_buttons}</div>
        <table><thead><tr><th>Path</th><th>Hits</th></tr></thead><tbody id="site-pages-body">{site_pages_rows}</tbody></table>
    </div>
    <div class="table-box">
        <div class="section-title">\U0001f517 Traffic Sources (today)</div>
        <table><thead><tr><th>Source</th><th>Visits</th></tr></thead><tbody>{ref_src_html}</tbody></table>
    </div>
</div>

<div class="grid-2">
    <div class="table-box">
        <div class="section-title">\U0001f30d Countries / Regions</div>
        <table><thead><tr><th>Country</th><th>Visitors</th></tr></thead><tbody>{countries_html}</tbody></table>
    </div>
    <div class="table-box">
        <div class="section-title">\U0001f5a5 Browsers</div>
        {browser_html}
        <div class="section-title" style="margin-top:16px;">\U0001f4f1 Operating Systems</div>
        {os_html}
        <div class="section-title" style="margin-top:16px;">\U0001f4f2 Device Types</div>
        {device_html}
    </div>
</div>

<div class="grid-2">
    <div class="table-box">
        <div class="section-title">\U0001f4e1 Status Codes (today)</div>
        {status_html}
    </div>
    <div class="table-box">
        <div class="section-title">\U0001f6ab Top 404 Paths (today)</div>
        <table><thead><tr><th>Path</th><th>Count</th></tr></thead><tbody>{p404_html}</tbody></table>
    </div>
</div>

<div class="section">
    <div class="section-title">\U0001f464 Most Active Visitors (today, human)</div>
    <div class="table-box">
        <table><thead><tr><th>IP</th><th>Requests</th><th>Pages</th><th>Country</th><th>Active Window</th><th>Span</th><th>Browser / OS</th></tr></thead><tbody>{av_html}</tbody></table>
    </div>
</div>

<div class="anomaly">
    <div class="anomaly-title">⚠️ Anomaly Monitoring (Today)</div>
    <div class="anomaly-stats">
        <div class="anomaly-stat">404 Errors: <strong>{stats["today_404"]}</strong></div>
        <div class="anomaly-stat">Bot Traffic: <strong>{stats["bots_pct"]}%</strong></div>
        <div class="anomaly-stat">Total Requests: <strong>{stats["total_hits_today"]:,}</strong></div>
    </div>
    <table style="margin-top:12px;"><thead><tr><th>Suspicious IP</th><th>Requests</th><th>Paths Attempted</th></tr></thead><tbody>{suspicious_html}</tbody></table>
</div>

</div>

<script>
const SITE_PAGES = {site_pages_json};
function showSite(site, btn) {{
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const rows = SITE_PAGES[site] || [];
    const esc = s => {{ const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }};
    document.getElementById('site-pages-body').innerHTML = rows.length
        ? rows.map(r => `<tr><td class="mono">${{esc(r.path)}}</td><td>${{r.count}}</td></tr>`).join('')
        : '<tr><td colspan="2" class="empty">No data</td></tr>';
}}
</script>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description="Nginx log analyzer for VLSC websites")
    parser.add_argument("--full", action="store_true", help="Full re-parse of all logs")
    args = parser.parse_args()

    start_time = time.time()
    print(f"[{datetime.now(CST).strftime('%Y-%m-%d %H:%M:%S')}] Starting nginx stats analysis...")

    conn = init_db()
    migrate_db(conn)

    print("1. Ingesting logs...")
    new_count = ingest_logs(conn, full=args.full)
    print(f"   {new_count} new hits ingested")

    print("2. Cleaning up old hits...")
    cleanup_old_hits(conn)

    print("3. Updating daily summary...")
    update_daily_summary(conn, full=args.full)

    print("4. Rendering dashboard...")
    stats = query_stats(conn)
    html = render_html(stats)

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    conn.close()

    elapsed = time.time() - start_time
    print(f"Done in {elapsed:.1f}s. Dashboard written to {HTML_PATH}")


if __name__ == "__main__":
    main()
