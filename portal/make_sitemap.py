#!/usr/bin/env python3
"""Generate sitemap.xml for www.vlsc.net from the portal directory tree."""
import os, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = "https://www.vlsc.net"


def find_html(base):
    pages = []
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if not d.startswith('.')]
        for fn in filenames:
            if fn.endswith('.html') and not fn.startswith('.'):
                full = os.path.join(dirpath, fn)
                if fn == 'index.html':
                    url = os.path.relpath(dirpath, base) + '/'
                else:
                    url = os.path.relpath(full, base)
                pages.append((url.replace(os.sep, '/'), full))
    return pages


def lastmod(path):
    ts = os.path.getmtime(path)
    return datetime.date.fromtimestamp(ts).isoformat()


pages = find_html(ROOT)
# sub-site roots (deployed as nginx aliases under the same domain)
SUBSITES = ['/mrrc/', '/mrrc_ft710/', '/mrrc_ft8/', '/sunmrrc/', '/sunsdrmobile/', '/efhw/']

urls = []
urls.append(f'<url><loc>{BASE}/</loc><changefreq>weekly</changefreq></url>')
for url, path in sorted(pages):
    if url.startswith('zh/'):
        loc = f'{BASE}/zh/{url[3:]}'
    else:
        loc = f'{BASE}/{url}'
    urls.append(f'<url><loc>{loc}</loc><lastmod>{lastmod(path)}</lastmod></url>')
for s in SUBSITES:
    urls.append(f'<url><loc>{BASE}{s}</loc><changefreq>weekly</changefreq></url>')

sitemap = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           + '\n'.join(urls) + '\n</urlset>\n')
with open(os.path.join(ROOT, 'sitemap.xml'), 'w') as f:
    f.write(sitemap)
print(f"wrote sitemap.xml with {len(urls)} URLs")
