#!/usr/bin/env python3
"""Add a TikTok post to the home-page feed in one command.

    python3 tools/add-post.py https://www.tiktok.com/@ashley.claudy/video/123... --likes 55K
    python3 tools/add-post.py URL --caption "My own caption" --hide
    python3 tools/add-post.py URL1 URL2 URL3          # several at once

It asks TikTok's public oEmbed service about the link (so a wrong link is caught),
saves the video's thumbnail into assets/social/, and adds or updates the entry in
content/fan.json. Then run: python3 build.py

Needs internet access and Python 3. ffmpeg is used to shrink thumbnails if installed.
Photo posts can't be looked up this way, so they are not supported yet.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FAN = ROOT / "content/fan.json"
OUT = ROOT / "assets/social"
UA = {"User-Agent": "Mozilla/5.0 (compatible; ashleyclaudy-site-tool)"}
EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿⬀-⯿️‍]+")


def clean_caption(title):
    text = re.sub(r"#\w+", "", title or "")
    text = EMOJI.sub("", text)
    return re.sub(r"\s+", " ", text).strip()


def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=timeout).read()


def add(url, likes, caption, hide):
    m = re.search(r"tiktok\.com/@([\w.]+)/video/(\d+)", url)
    if not m:
        sys.exit(f"Not a TikTok video link: {url}")
    handle, vid = m.groups()
    api = "https://www.tiktok.com/oembed?url=" + urllib.parse.quote(url, safe="")
    try:
        info = json.loads(fetch(api))
    except urllib.error.HTTPError as err:
        sys.exit(f"TikTok did not recognize {url} (HTTP {err.code}). Check the link.")
    if info.get("author_unique_id") and info["author_unique_id"].lower() != handle.lower():
        sys.exit(f"Link belongs to {info['author_unique_id']}, not {handle}.")
    OUT.mkdir(parents=True, exist_ok=True)
    thumb_rel = ""
    if info.get("thumbnail_url"):
        raw = OUT / f"{vid}.raw"
        raw.write_bytes(fetch(info["thumbnail_url"]))
        dest = OUT / f"{vid}.jpg"
        if shutil.which("ffmpeg"):
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(raw), "-vf", "scale=540:-1", "-q:v", "4", str(dest)], check=True)
            raw.unlink()
        else:
            raw.rename(dest)
        thumb_rel = f"assets/social/{vid}.jpg"
    entry = {
        "platform": "tiktok",
        "url": f"https://www.tiktok.com/@{handle}/video/{vid}",
        "caption": caption if caption is not None else clean_caption(info.get("title")),
        "thumb": thumb_rel,
        "likes": likes or "",
        "show": not hide,
    }
    data = json.loads(FAN.read_text())
    posts = data.setdefault("social_posts", [])
    for i, p in enumerate(posts):
        if str(p.get("url", "")).endswith(f"/video/{vid}"):
            posts[i] = {**p, **{k: v for k, v in entry.items() if v != "" or k in ("caption",)}}
            action = "updated"
            break
    else:
        posts.append(entry)
        action = "added"
    FAN.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    shown = "hidden" if hide else "shown"
    print(f"{action}: {vid} ({shown}) caption={entry['caption']!r} likes={likes or '-'}")


def main():
    ap = argparse.ArgumentParser(description="Add TikTok posts to the site feed.")
    ap.add_argument("urls", nargs="+")
    ap.add_argument("--likes", help='like count to show, for example "55K" (only with one link)')
    ap.add_argument("--caption", help="caption to show instead of TikTok's own text (only with one link)")
    ap.add_argument("--hide", action="store_true", help="save it but keep it off the site")
    a = ap.parse_args()
    if len(a.urls) > 1 and (a.likes or a.caption):
        sys.exit("--likes and --caption work with one link at a time.")
    for u in a.urls:
        add(u, a.likes, a.caption, a.hide)


if __name__ == "__main__":
    main()
