#!/usr/bin/env python3
"""Mirror http://www.seidensha-ltd.co.jp/~seiden/rekishi.html and every
linked device page into RIG/, converting CP932 -> UTF-8 and fetching images."""
import os, re, sys, time, urllib.request, urllib.parse

BASE = "http://www.seidensha-ltd.co.jp/~seiden/"
OUT = "RIG"
os.makedirs(os.path.join(OUT, "gif"), exist_ok=True)

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (archive)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()

def to_utf8(raw):
    for enc in ("cp932", "shift_jis", "utf-8"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("cp932", errors="replace")

# 1. main page already downloaded; re-read raw copy
raw_main = open(os.path.join(OUT, "_rekishi_raw.html"), "rb").read()
main = to_utf8(raw_main)

# 2. collect local html links from main page
links = re.findall(r'href="([^"#]+?\.html)"', main, flags=re.I)
pages = []
for l in links:
    if ":" in l:            # absolute external
        continue
    name = urllib.parse.unquote(l)
    if name.lower() in ("index.html",):
        continue
    if name not in pages:
        pages.append(name)

print(f"{len(pages)} device/related pages to fetch")

ok, fail = [], []
for i, p in enumerate(pages, 1):
    url = urllib.parse.urljoin(BASE, urllib.parse.quote(p))
    dst = os.path.join(OUT, p)
    try:
        if not os.path.exists(dst):
            raw = fetch(url)
            with open(dst, "w", encoding="utf-8") as f:
                f.write(to_utf8(raw))
            time.sleep(0.3)
        ok.append(p)
    except Exception as e:
        print(f"FAIL {p}: {e}")
        fail.append(p)
    if i % 25 == 0:
        print(f"  {i}/{len(pages)}")

# 3. save main page as rekishi.html
with open(os.path.join(OUT, "rekishi.html"), "w", encoding="utf-8") as f:
    f.write(main)

# 4. collect images (src / background) from all pages incl. main
imgs = set()
for p in ["rekishi.html"] + ok:
    try:
        txt = open(os.path.join(OUT, p), encoding="utf-8").read()
    except Exception:
        continue
    for m in re.findall(r'(?:src|background)="([^"]+?)"', txt, flags=re.I):
        if ":" in m:
            continue
        imgs.add(urllib.parse.unquote(m))

print(f"{len(imgs)} images to fetch")
img_fail = []
for i, im in enumerate(sorted(imgs), 1):
    url = urllib.parse.urljoin(BASE, urllib.parse.quote(im))
    dst = os.path.join(OUT, im)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    try:
        if not os.path.exists(dst):
            with open(dst, "wb") as f:
                f.write(fetch(url))
            time.sleep(0.2)
    except Exception as e:
        print(f"FAIL img {im}: {e}")
        img_fail.append(im)
    if i % 50 == 0:
        print(f"  {i}/{len(imgs)}")

print(f"DONE pages ok={len(ok)} fail={len(fail)} imgs fail={len(img_fail)}")
if fail: print("failed pages:", fail)
if img_fail: print("failed imgs:", img_fail[:20])
