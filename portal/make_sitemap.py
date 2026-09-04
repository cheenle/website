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


# Sub-site second-level pages. Sub-sites are deployed as nginx aliases from
# their own repos (symlinked into the workspace), so os.walk needs
# followlinks=True to see them at all. Only depth-1 content pages plus their
# zh/ mirrors are indexed: deep doc trees (sdd/, docs/) stay out on purpose,
# matching the sitemap's existing "entry + identity pages" scope.
SITE_ROOT = os.path.dirname(ROOT)


def find_subsite_pages():
    out = []
    for site in SUBSITES:
        base = os.path.join(SITE_ROOT, site.strip('/'))
        if not os.path.isdir(base):
            continue
        for sub in ('', 'zh'):
            d = os.path.join(base, sub)
            if not os.path.isdir(d):
                continue
            for fn in sorted(os.listdir(d)):
                if not fn.endswith('.html') or fn.startswith('.') or fn == 'index.html':
                    continue
                out.append((f'{BASE}{site}{sub + "/" if sub else ""}{fn}',
                            os.path.join(d, fn)))
    return out


def lastmod(path):
    ts = os.path.getmtime(path)
    return datetime.date.fromtimestamp(ts).isoformat()


pages = find_html(ROOT)
# sub-site roots (deployed as nginx aliases under the same domain)
# mrrc_modern was missing from this list: its root and agentic.html were
# never in the sitemap even though nginx serves them.
SUBSITES = ['/mrrc/', '/mrrc_ft710/', '/mrrc_ft8/', '/mrrc_modern/',
            '/sunmrrc/', '/sunsdrmobile/', '/efhw/']

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
for url, path in sorted(find_subsite_pages()):
    urls.append(f'<url><loc>{url}</loc><lastmod>{lastmod(path)}</lastmod></url>')

sitemap = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           + '\n'.join(urls) + '\n</urlset>\n')
with open(os.path.join(ROOT, 'sitemap.xml'), 'w') as f:
    f.write(sitemap)
print(f"wrote sitemap.xml with {len(urls)} URLs")
