#!/usr/bin/env python3
"""Find and re-check Goodreads review excerpts for the reviews slider.

    python3 tools/pull-reviews.py --check              # are all saved excerpts still word-for-word on Goodreads?
    python3 tools/pull-reviews.py --candidates hustle  # list strong positive lines from that book's reviews

Reads each book's public Goodreads page the way a visitor would (one request per book).
Excerpts live in content/reviews.json; add a new one by copying a line from --candidates
exactly, with the reviewer's display name. Keep excerpts short and attributed, and remove
any a reviewer asks to have taken down. Then run: python3 build.py
"""
import argparse
import html
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
      "Accept-Language": "en-US,en;q=0.9"}
PRAISE = re.compile(r"\b(love[ds]?|amazing|addict\w*|couldn.t (put|stop)|can.t (put|stop)|obsess\w*|hooked|favorite|recommend\w*|great|fantastic|awesome|swoon\w*|perfect\w*|brilliant|compelling|gripping|intense|devoured|binge)\b", re.I)


def clean(t):
    t = re.sub(r"<br\s*/?>", " ", t or "")
    t = re.sub(r"<[^>]+>", "", t)
    return re.sub(r"\s+", " ", html.unescape(t)).strip()


def reviews_for(url):
    req = urllib.request.Request(url, headers=UA)
    page = urllib.request.urlopen(req, timeout=40).read().decode("utf-8", "ignore")
    data = json.loads(re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', page, re.S).group(1))
    state = data["props"]["pageProps"]["apolloState"]
    out = []
    for key, r in state.items():
        if key.startswith("Review:"):
            user = state.get(r["creator"]["__ref"], {})
            out.append({"name": (user.get("name") or "").strip(), "rating": r.get("rating") or 0, "likes": r.get("likeCount") or 0,
                        "spoiler": bool(r.get("spoilerStatus")), "text": clean(r.get("text"))})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--candidates", metavar="BOOK")
    a = ap.parse_args()
    books = {b["slug"]: b for b in json.loads((ROOT / "content/books.json").read_text())["books"]}
    if a.check:
        saved = json.loads((ROOT / "content/reviews.json").read_text())["reviews"]
        cache, missing = {}, 0
        for r in saved:
            if r["book"] not in cache:
                cache[r["book"]] = reviews_for(books[r["book"]]["goodreads"])
            ok = any(x["name"] == r["name"] and r["text"] in x["text"] for x in cache[r["book"]])
            print(("ok       " if ok else "MISSING  ") + f'{r["book"]}: {r["name"]}: {r["text"][:60]}')
            missing += 0 if ok else 1
        sys.exit(1 if missing else 0)
    if a.candidates:
        rows = [r for r in reviews_for(books[a.candidates]["goodreads"]) if r["rating"] >= 4 and not r["spoiler"]]
        rows.sort(key=lambda r: -r["likes"])
        for r in rows:
            lines = [s for s in re.split(r"(?<=[.!?])\s+", r["text"]) if 30 <= len(s) <= 230 and PRAISE.search(s)]
            if lines:
                print(f'- {r["name"]} | {r["rating"]} stars | {r["likes"]} likes')
                for s in lines[:3]:
                    print("    >", s)
        return
    ap.print_help()


if __name__ == "__main__":
    main()
