#!/usr/bin/env python3
"""Build ashleyclaudy.com from content/*.json into a static folder.

    python3 build.py                 # writes dist/
    python3 build.py --out somewhere/else
"""
import argparse
import html
import json
import re
import shutil
from datetime import date, datetime, timedelta, timezone
from urllib.parse import quote
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CURRENT = ' aria-current="page"'
MARKER = ".ashleyclaudy-build"

SITE = json.loads((ROOT / "content/site.json").read_text())
CATALOG = json.loads((ROOT / "content/books.json").read_text())
FAN = json.loads((ROOT / "content/fan.json").read_text())
QUIZ = json.loads((ROOT / "content/quiz.json").read_text())
GENRES = json.loads((ROOT / "content/genres.json").read_text())["pages"]
GENRE_BY_SLUG = {g["slug"]: g for g in GENRES}
AFTER = json.loads((ROOT / "content/after.json").read_text())
BOOKS = {b["slug"]: b for b in CATALOG["books"]}
SERIES = {s["id"]: s for s in CATALOG["series"]}

ARROW = ('<svg class="ico" viewBox="0 0 20 20" aria-hidden="true"><path d="M4 10h11m-4.5-5L15.5 10l-5 5" '
         'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>')
STAR = ('<svg class="ico star" viewBox="0 0 20 20" width="14" height="14" aria-hidden="true" style="width:14px;height:14px">'
        '<path d="M10 1.8l2.4 5.3 5.8.6-4.3 3.9 1.2 5.7L10 14.4l-5.1 2.9 1.2-5.7L1.8 7.7l5.8-.6z" fill="currentColor"/></svg>')
ICON_MAIL = ('<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
             'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="3"/>'
             '<path d="M4 7.5l8 6 8-6"/></svg>')
ICON_BOOKS = ('<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
              'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3.5" y="4" width="4.5" height="16" rx="1"/>'
              '<rect x="10" y="4" width="4.5" height="16" rx="1"/><path d="M16.8 5.4l4-.9 2 14.6-4 .9z" transform="translate(-2 0)"/></svg>')

# Home-page shelf: (slug, mood label). Order is the order readers should meet the books.
SHELF = [
    ("ride", "Street racing & MC"),
    ("wreck", "Crowns & Chaos #2"),
    ("hustle", "College football"),
    ("outside-the-ropes", "Boxing · Trilogy"),
    ("it-goes-on", "Secrets & money"),
]

MOODS = dict(SHELF)
PRIVACY_HREF = "@@R@@privacy.html"
AMZ_STORES = [("com", "United States"), ("co.uk", "United Kingdom"), ("ca", "Canada"), ("com.au", "Australia"), ("de", "Germany"), ("fr", "France"),
              ("es", "Spain"), ("it", "Italy"), ("nl", "Netherlands"), ("in", "India"), ("co.jp", "Japan"), ("com.mx", "Mexico"), ("com.br", "Brazil")]
BOOK_GENRE = {}
for _g in GENRES:
    if _g["slug"] != "kindle-unlimited-romance":
        for _b in _g["books"]:
            BOOK_GENRE.setdefault(_b, _g)
PLATFORMS = {"tiktok": "TikTok", "instagram": "Instagram", "facebook": "Facebook"}
PLAY = ('<svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5.5v13l11-6.5z" fill="currentColor"/></svg>')
PAUSE = ('<svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 5h4v14H7zM13 5h4v14h-4z" fill="currentColor"/></svg>')

OLD_URLS = {
    "/book/ride/": "/books/ride.html",
    "/book/hustle/": "/books/hustle.html",
    "/book/outside-the-ropes/": "/books/outside-the-ropes.html",
    "/book/inside-danger/": "/books/inside-danger.html",
    "/book/otherside-of-fear/": "/books/otherside-of-fear.html",
    "/book/it-goes-on/": "/books/it-goes-on.html",
    "/book-series/outside-the-ropes-series/": "/books.html#outside-the-ropes",
    "/book-author/ashley-claudy/": "/books.html",
    "/where-are-your-books/": "/books.html#where-to-buy",
    "/contact/": "/#about",
    "/803-2/": "/links.html",
    "/signup": "/bonus.html",
    "/signup/": "/bonus.html",
}


def e(value):
    return html.escape(str(value), quote=True)


def abs_url(path=""):
    return SITE["site_url"].rstrip("/") + "/" + path.lstrip("/")


# ---------- retailer links ----------

def amazon(asin):
    tag = SITE.get("amazon_affiliate_tag")
    return f"https://www.amazon.com/dp/{asin}" + (f"?tag={tag}" if tag else "")


def kindle_sample(asin):
    return f"https://read.amazon.com/kp/embed?asin={asin}&preview=newtab&linkCode=kpe"


def asin_attr(url):
    m = re.match(r"https://www\.amazon\.com/dp/([A-Z0-9]{10})", url)
    return f' data-asin="{m.group(1)}"' if m else ""


def out_link(url, label, store, book="", cls="link", extra=""):
    return (f'<a class="{cls}" href="{e(url)}" target="_blank" rel="noopener"{asin_attr(url)}{extra} '
            f'data-track="{e(store)}" data-book="{e(book)}">{label}</a>')


def kindle_label(book):
    if book["status"] == "preorder":
        return "Preorder on Kindle"
    return "Read free in Kindle Unlimited" if book.get("kindle_unlimited") else "Buy on Kindle"


def short_cta(book):
    if book["status"] == "preorder":
        return f"Preorder {book['title']}"
    return f"Read {book['title']} free" if book.get("kindle_unlimited") else f"Buy {book['title']}"


def series_label(book):
    if book["series"] == "standalones":
        return "Standalone"
    return f'{SERIES[book["series"]]["name"]} · Book {book["number"]}'


SHORT_SERIES = {"crowns-and-chaos": "Crowns & Chaos", "outside-the-ropes": "Trilogy"}


def short_label(book):
    if book["series"] == "standalones":
        return "Standalone"
    return f'{SHORT_SERIES.get(book["series"], SERIES[book["series"]]["name"])} #{book["number"]}'


def formats(book):
    out = ["Kindle"]
    if book.get("paperback"):
        out.append("Paperback")
    if book.get("audiobook"):
        out.append("Audiobook")
    return " · ".join(out)


def release_dt(book):
    return datetime.fromisoformat(book["release_iso"])


def release_short(book):
    dt = release_dt(book)
    return f"{dt.strftime('%b')} {dt.day}"


def days_left(book):
    dt = release_dt(book)
    return max(0, (dt - datetime.now(dt.tzinfo)).days)


def wreck():
    return BOOKS["wreck"]


def split_tagline(tagline):
    """'Some rides are worth the crash.' -> ('Some rides are', 'worth the crash.')"""
    words = tagline.split()
    if len(words) < 5:
        return "", tagline
    return " ".join(words[:-3]), " ".join(words[-3:])


# ---------- shared pieces ----------

def analytics():
    a = SITE.get("analytics", {})
    parts = []
    if a.get("plausible_domain"):
        parts.append(
            f'<script defer data-domain="{e(a["plausible_domain"])}" src="https://plausible.io/js/script.js"></script>\n'
            '<script>window.plausible=window.plausible||function(){(window.plausible.q=window.plausible.q||[]).push(arguments)}</script>'
        )
    if a.get("ga4_id"):
        gid = e(a["ga4_id"])
        parts.append(
            f'<script type="text/plain" data-consent="analytics" src="https://www.googletagmanager.com/gtag/js?id={gid}"></script>\n'
            f"<script type=\"text/plain\" data-consent=\"analytics\">window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{gid}');</script>"
        )
    if a.get("meta_pixel_id"):
        pid = e(a["meta_pixel_id"])
        parts.append(
            "<script type=\"text/plain\" data-consent=\"analytics\">!function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?"
            "n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;"
            "n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];"
            "s.parentNode.insertBefore(t,s)}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');"
            f"fbq('init','{pid}');fbq('track','PageView');</script>"
        )
    return "\n".join(parts)


def header(r, current=""):
    items = [("books.html", "Books"), ("quiz.html", "Quiz")]
    if wreck()["status"] == "preorder":
        items.append(("books/wreck.html", "Wreck"))
    items.append(("index.html#about", "About"))
    links = "".join(
        f'<a href="{r}{href}"{CURRENT if href == current else ""}>{label}</a>' for href, label in items
    )
    panel_links = "".join(
        f'<a href="{r}{href}">{label}{"<small>Preorder</small>" if label == "Wreck" else ""}</a>' for href, label in items
    )
    cta = f'<a class="btn btn-glow btn-sm" href="{r}bonus.html">Free bonus chapters</a>'
    cta_big = f'<a class="btn btn-glow btn-block" href="{r}bonus.html">Free bonus chapters {ARROW}</a>'
    return f"""<a class="skip" href="#main">Skip to content</a>
{promo_bar()}
<header class="site-head">
  <div class="wrap head-row">
    <a class="logo" href="{r}index.html" aria-label="Ashley Claudy, home">Ashley Claudy</a>
    <nav class="nav" aria-label="Main">{links}{cta}</nav>
    <details class="menu">
      <summary aria-label="Menu"><i></i><i></i></summary>
      <nav class="menu-panel" aria-label="Menu">{panel_links}{cta_big}</nav>
    </details>
  </div>
</header>"""


def fb_group():
    g = SITE.get("facebook_group") or {}
    return (g.get("url", ""), g.get("name") or "Reader group")


def socials():
    items = "".join(
        f'<li><a href="{e(s["url"])}" target="_blank" rel="noopener" data-track="social-{e(s["name"].lower())}">'
        f'{e(s["name"])} <small>{e(s["handle"])}</small></a></li>'
        for s in SITE["social"] if not s.get("hidden")
    )
    gurl, gname = fb_group()
    if gurl:
        items += (f'<li><a href="{e(gurl)}" target="_blank" rel="noopener" data-track="social-facebook-group">'
                  f'Reader group <small>{e(gname)}</small></a></li>')
    return f'<ul class="socials">{items}</ul>'


def social_url(name):
    for s in SITE["social"]:
        if s["name"].lower() == name.lower():
            return s["url"]
    return SITE["amazon_author_url"]


def footer(r):
    year = date.today().year
    return f"""<footer class="site-foot">
  <div class="wrap foot-grid">
    <nav class="foot-nav" aria-label="Footer">
      <a href="{r}books.html">Books</a>
      <a href="{r}quiz.html">Quiz</a>
      <a href="{r}bonus.html">Bonus chapters</a>
      <a href="{r}books.html#where-to-buy">Where to buy</a>
      <a href="{r}creators.html">Creators &amp; press</a>
      <a href="{r}arc.html">ARC team</a>
      <a href="{r}links.html">Links</a>
      <a href="{r}privacy.html">Privacy</a>
      <a href="{r}index.html#about">About</a>
    </nav>
    <nav class="foot-nav foot-explore" aria-label="Explore">
      {"".join(f'<a href="{r}{g["slug"]}.html">{e(g["label"])}</a>' for g in GENRES)}
    </nav>
    <div class="fine-col">
      <p class="fine">As an Amazon Associate I earn from qualifying purchases.</p>
      <p class="fine">© {year} Ashley Claudy. All rights reserved.</p>
      <p class="amz-pick fine"><label for="amz-store">Amazon store</label>
        <select id="amz-store" data-amz-select>{"".join(f'<option value="{d}">{n} (amazon.{d})</option>' for d, n in AMZ_STORES)}</select></p>
    </div>
  </div>
  <div class="big-mark" aria-hidden="true"><span>Ashley</span><span>Claudy</span></div>
</footer>"""


def crew_form(form_id, book=""):
    nl = SITE["newsletter"]
    action = nl.get("mailerlite_form_action", "")
    return f"""<div class="signup-wrap">
    <form class="signup" data-signup="{e(form_id)}" method="post" data-action="{e(action)}" data-fallback="{e(nl["fallback_url"])}" novalidate>
      <div class="signup-row">
        <label class="sr-only" for="{form_id}-email">Email address</label>
        <input class="input" id="{form_id}-email" name="fields[email]" type="email" inputmode="email" autocomplete="email" placeholder="Your email address" required>
        <button class="btn btn-glow" type="submit">Send me the chapters {ARROW}</button>
      </div>
      <input type="hidden" name="ml-submit" value="1">
      <input type="hidden" name="anticsrf" value="true">
      <input type="hidden" name="fields[signup_source]" value="{e(form_id)}">
      <input type="hidden" name="fields[book]" value="{e(book)}">
      <input type="hidden" name="fields[quiz_result]" value="">
      <input type="hidden" name="fields[utm_source]" value="">
      <input type="hidden" name="fields[utm_medium]" value="">
      <input type="hidden" name="fields[utm_campaign]" value="">
      <p class="signup-error" role="alert" hidden></p>
      <p class="signup-note">Free. Unsubscribe anytime. Your email is never shared. <a href="{PRIVACY_HREF}">Privacy</a></p>
    </form>
    <div class="signup-done" role="status" hidden>
      <p class="done-title">You're on the Crew.</p>
      <p>Your bonus chapters are on the way. If the email isn't in your inbox in a few minutes, check Promotions or Spam and move it to your main inbox so you don't miss the Wreck cover reveal.</p>
      <div class="row">
        <a class="btn btn-line btn-sm" href="{e(social_url("TikTok"))}" target="_blank" rel="noopener" data-track="social-tiktok">Follow on TikTok</a>
        <a class="btn btn-line btn-sm" href="{e(social_url("Facebook"))}" target="_blank" rel="noopener" data-track="social-facebook">Follow on Facebook</a>
        {f'<a class="btn btn-glow btn-sm" href="{e(fb_group()[0])}" target="_blank" rel="noopener" data-track="social-facebook-group">Join the reader group</a>' if fb_group()[0] else ""}
      </div>
    </div>
  </div>"""


def crew(form_id, headline=None, book=""):
    nl = SITE["newsletter"]
    perks = "".join(f"<li>{e(p)}</li>" for p in nl["perks"])
    headline = headline or 'Get the bonus chapters. <span class="serif">Free.</span>'
    return f"""<div class="crew">
  <div class="crew-copy">
    <p class="kicker">Join the Crew</p>
    <h2>{headline}</h2>
    <p class="lede">{e(nl["crew_line"])}</p>
  </div>
  {crew_form(form_id, book)}
  <ul class="perks">{perks}</ul>
</div>"""


def join_modal():
    return f"""<dialog class="modal" id="join-modal" aria-label="Get free bonus chapters">
  <button class="modal-close" type="button" data-close aria-label="Close">×</button>
  {crew("modal")}
</dialog>"""


def dock_html(dock):
    primary = out_link(dock["url"], f'{e(dock["label"])}', dock["store"], dock["book"], "btn btn-glow")
    secondary = f'<a class="btn btn-line dock-sec" href="{e(dock["sec"])}">Free chapters</a>'
    return f'<div class="dock" role="region" aria-label="Quick actions">{primary}{secondary}</div>'


def page(path, title, description, body, *, image="og/home.jpg", jsonld=None, solo=False, current="", theme="blue", dock=None, extra_js=(), noindex=False):
    r = "/" if path == "404.html" else "../" * path.count("/")
    canonical = abs_url("" if path == "index.html" else path)
    ld = "".join(
        '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False).replace("</", "<\\/") + "</script>"
        for obj in (jsonld or [])
    )
    ml_frame = ('<iframe name="ml-frame" title="Newsletter signup" hidden></iframe>'
                if SITE["newsletter"].get("mailerlite_form_action") else "")
    robots = '<meta name="robots" content="noindex">\n' if noindex else ""
    amz_json = json.dumps(amz_config(), separators=(",", ":"))
    consent_flag = "window.AC_CONSENT=true;" if needs_consent() else ""
    head = f"""<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{e(canonical)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Ashley Claudy">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{e(canonical)}">
<meta property="og:image" content="{e(abs_url("assets/" + image))}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{e(abs_url("assets/" + image))}">
<meta name="theme-color" content="#09090b">
<link rel="icon" href="{r}assets/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="{r}assets/icons/apple-touch-icon.png">
<link rel="manifest" href="{r}manifest.webmanifest">
<meta name="apple-mobile-web-app-title" content="Ashley Claudy">
<link rel="preload" href="{r}assets/fonts/bricolage-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{r}assets/fonts/inter-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{r}assets/css/site.css">
<script>document.documentElement.classList.add("js")</script>
{robots}<script>window.AC_AMZ={amz_json};{consent_flag}</script>
{analytics()}
{ld}"""
    chrome_top = "" if solo else header(r, current)
    chrome_bottom = ("" if solo else footer(r) + join_modal()) + consent_banner()
    dock_markup = dock_html(dock) if dock else ""
    extra_scripts = "\n".join(f'<script src="{r}assets/js/{name}" defer></script>' for name in extra_js)
    body_class = f"t-{theme}" + (" has-dock" if dock else "")
    content = f"""{chrome_top}
<main id="main">
{body}
</main>
{chrome_bottom}
{dock_markup}
{ml_frame}
<script src="{r}assets/js/site.js" defer></script>
{extra_scripts}"""

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
{head}
</head>
<body class="{body_class}">
{content}
</body>
</html>
""".replace("@@R@@", r)


def person_ld():
    return {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": SITE["author"],
        "url": abs_url(),
        "jobTitle": "Author",
        "description": SITE["tagline"],
        "sameAs": [s["url"] for s in SITE["social"]],
    }


# ---------- components ----------

def hero_bg(src):
    return f'<img class="hero-bg" src="{src}" alt="" aria-hidden="true" width="324" height="500">'


def trope_marquee():
    skip = {"Standalone", "Preorder", "Series finale"}
    seen, items = set(), []
    for b in CATALOG["books"]:
        for t in b["tropes"]:
            if t in skip or t.startswith("Book ") or "#" in t or t in seen:
                continue
            seen.add(t)
            items.append(t)
    group = "".join(f"<span>{e(t)}</span>" for t in items)
    return f'<div class="marquee" aria-hidden="true"><div class="marquee-track">{group}{group}</div></div>'


def shelf_card(book, r, label, line=None, badge="", delay=0):
    href = f"{r}books/{book['slug']}.html"
    cta = "Preorder" if book["status"] == "preorder" else ("Read free" if book.get("kindle_unlimited") else "View book")
    badge_html = f'<span class="badge">{e(badge)}</span>' if badge else ""
    return f"""<a class="shelf-card t-{book['accent']} reveal" style="--d:{delay}s" href="{href}">
  <span class="cover">{badge_html}<img src="{r}assets/covers/{e(book['cover'])}" alt="{e(book['title'])} by Ashley Claudy, cover" width="333" height="500" loading="lazy"></span>
  <p class="kicker">{e(label)}</p>
  <h3>{e(book['title'])}</h3>
  <p class="line">{e(line or book['hook'])}</p>
  <span class="more">{cta} {ARROW}</span>
</a>"""


def countdown(book, done_id):
    return f"""<div class="board" data-countdown="{e(book['release_iso'])}" data-countdown-done="#{done_id}" role="timer" aria-label="Time until release">
  <div class="board-cell"><span class="board-num" data-unit="d">{days_left(book)}</span><span class="board-unit">Days</span></div>
  <div class="board-cell"><span class="board-num" data-unit="h">00</span><span class="board-unit">Hours</span></div>
  <div class="board-cell"><span class="board-num" data-unit="m">00</span><span class="board-unit">Min</span></div>
  <div class="board-cell"><span class="board-num" data-unit="s">00</span><span class="board-unit">Sec</span></div>
</div>
<p class="lede" id="{done_id}" hidden>Out now on Kindle.</p>"""



# ---------- growth: regional Amazon, consent, promo, privacy, reader proof ----------

def amz_config():
    tags = {k: v for k, v in (SITE.get("amazon_tags") or {}).items() if v}
    default = SITE.get("amazon_affiliate_tag")
    if default:
        tags.setdefault("com", default)
    tracking = {k.lower(): v for k, v in (SITE.get("amazon_tracking_ids") or {}).items() if v}
    return {"tags": tags, "tracking": tracking}


def needs_consent():
    a = SITE.get("analytics", {})
    return bool(a.get("ga4_id") or a.get("meta_pixel_id"))


def consent_banner():
    if not needs_consent():
        return ""
    return f"""<div class="consent" data-consent-banner role="region" aria-label="Analytics choice" hidden>
  <p>May we use analytics cookies to see which pages help readers? Nothing is sold. <a href="{PRIVACY_HREF}">Privacy</a></p>
  <div class="consent-actions"><button class="btn btn-glow btn-sm" type="button" data-consent="yes">Accept</button><button class="btn btn-line btn-sm" type="button" data-consent="no">Decline</button></div>
</div>"""


def promo_bar():
    pr = SITE.get("promo") or {}
    if not pr.get("enabled") or not pr.get("text"):
        return ""
    ends = pr.get("ends_iso", "")
    if ends:
        try:
            end_dt = datetime.fromisoformat(ends)
            if end_dt < datetime.now(end_dt.tzinfo):
                return ""
        except ValueError:
            ends = ""
    link = (f'<a class="promo-cta" href="{e(pr["url"])}" target="_blank" rel="noopener"{asin_attr(pr["url"])} data-track="promo" data-book="">{e(pr.get("cta", "Get the deal"))}</a>' if pr.get("url") else "")
    clock = '<span class="promo-clock" data-promo-clock></span>' if ends else ""
    return (f'<div class="promo" data-promo data-ends="{e(ends)}" role="region" aria-label="Sale"><span class="promo-text">{e(pr["text"])}</span>{clock}{link}'
            f'<button class="promo-x" type="button" data-promo-close aria-label="Dismiss">×</button></div>')


def rating_of(book):
    m = re.search(r"(\d\.\d+)\s*stars", book.get("proof") or "")
    return float(m.group(1)) if m else None


def stars_html(rating):
    return f'<span class="stars" style="--r:{rating}" role="img" aria-label="{rating} out of 5 stars"></span>'


def featured_slug():
    forced = (SITE.get("featured_book") or "").strip()
    if forced in BOOKS:
        return forced
    w = wreck()
    if w["status"] == "out" and w.get("release_iso"):
        if 0 <= (datetime.now(release_dt(w).tzinfo) - release_dt(w)).days <= 45:
            return "wreck"
    return "ride"


def mailto_form(cls, subject, intro, fields_html, button, note=""):
    email = SITE.get("contact_email", "")
    return f"""<form class="{cls}" data-mailto="{e(email)}" data-subject="{e(subject)}" data-intro="{e(intro)}">
  {fields_html}
  <button class="btn btn-glow" type="submit">{button} {ARROW}</button>
  <p class="signup-note req-note" role="status" hidden>If your email app didn't open, write to <b>{e(email)}</b>.</p>
  {note}
</form>"""


def reaction_block(book=None):
    opts = "".join(f'<option value="{e(b["title"])}"{" selected" if book and b["slug"] == book["slug"] else ""}>{e(b["title"])}</option>'
                   for b in CATALOG["books"] if b["status"] == "out")
    fields = f"""<label>Your name or handle<input class="input" name="name" data-label="Name or handle" required autocomplete="name"></label>
  <label>Which book<select class="input" name="book" data-label="Book">{opts}</select></label>
  <label>Your reaction<textarea class="input" name="reaction" data-label="Reaction" rows="3" required placeholder="One line about what you loved"></textarea></label>
  <label class="check"><input type="checkbox" name="permission" data-label="OK to quote me with my name or handle on ashleyclaudy.com and Ashley's social pages" required><span>You may quote this with my name or handle on ashleyclaudy.com and Ashley's social pages.</span></label>"""
    form = mailto_form("req", "Reader reaction: {book}", "A reaction for the site:", fields, "Open my email")
    return f"""<div class="crew reveal" id="react" style="grid-template-areas:'copy' 'form'">
  <div class="crew-copy">
    <p class="kicker">Share a line</p>
    <h2>Loved it? <span class="serif">Tell us.</span></h2>
    <p class="lede">Send one line about what you loved. With your OK, it may appear on this site.</p>
  </div>
  <div class="signup-wrap">{form}</div>
</div>"""


def build_after(book):
    r = "../"
    slug = book["slug"]
    cover_src = f"{r}assets/covers/{e(book['cover'])}"
    nexts = [BOOKS[n] for n in AFTER.get(slug, []) if n in BOOKS and n != slug]
    primary = nexts[0] if nexts else None
    feature = ""
    if primary:
        tags = "".join(f"<li>{e(t)}</li>" for t in primary["tropes"][:4])
        order_note = ("Book 2 in the same series." if primary["series"] == book["series"] and book["series"] != "standalones"
                      else "A different world, same kind of trouble.")
        feature = f"""<article class="res t-{primary['accent']}"><div class="res-grid">
  <a class="res-cover reveal" href="{r}books/{primary['slug']}.html"><img class="cover-art" src="{r}assets/covers/{e(primary['cover'])}" alt="{e(primary['title'])} by Ashley Claudy, cover" width="333" height="500"></a>
  <div class="res-copy reveal">
    <p class="kicker">Read next · {e(order_note)}</p>
    <h2 class="res-title">{e(primary['title'])}</h2>
    <p class="lede">{e(primary['hook'])}</p>
    <ul class="tags">{tags}</ul>
    <div class="cta-row" data-dock-watch>{out_link(amazon(primary['kindle_asin']), f"{e(kindle_label(primary))} {ARROW}", "kindle-after", primary['slug'], "btn btn-glow")}<a class="btn btn-line" href="{r}books/{primary['slug']}.html">See the book</a></div>
  </div></div></article>"""
    more_cards = "".join(shelf_card(b, r, short_label(b), badge="Preorder" if b["status"] == "preorder" else "") for b in nexts[1:])
    review_url = f"https://www.amazon.com/review/create-review?asin={book['kindle_asin']}"
    review_btn = out_link(review_url, f"Leave a review on Amazon {ARROW}", "review-amazon", slug, "btn btn-glow", extra=' data-kind="review"')
    gr_btn = out_link(book["goodreads"], "Rate it on Goodreads", "review-goodreads", slug, "btn btn-line")
    body = f"""<section class="hero t-{book['accent']}">
  {hero_bg(cover_src)}
  <div class="wrap page-head">
    <p class="kicker">Thanks for reading</p>
    <h1>You finished <span class="serif" style="color:var(--glow)">{e(book['title'])}.</span></h1>
    <p class="lede">Thank you. If it kept you up, here is what to read next, and one small favor.</p>
  </div>
</section>
<section class="series t-{primary['accent'] if primary else book['accent']}" aria-label="Read next"><div class="wrap">{feature}
  {f'<div class="grid-books" style="margin-top:44px">{more_cards}</div>' if more_cards else ''}
</div></section>
<section class="series t-{book['accent']}" aria-labelledby="fav-title"><div class="wrap">
  <div class="series-head reveal"><p class="kicker">A small favor</p><h2 id="fav-title">Two minutes that help <span class="serif" style="color:var(--glow)">a lot.</span></h2>
    <p>Honest reviews help other readers find the book. You never have to write one, and reviews can't be traded for anything.</p></div>
  <div class="cta-row reveal" style="max-width:560px">{review_btn}{gr_btn}</div>
  <p class="reveal" style="margin-top:22px"><button class="link" type="button" data-share-link="{abs_url('books/' + slug + '.html')}" data-share-text="I just finished {e(book['title'])} by Ashley Claudy.">Tell a friend about it</button></p>
</div></section>
<section class="section" id="join" aria-label="Join the Crew" data-dock-watch style="padding-top:0"><div class="wrap reveal">{crew(f"after-{slug}", 'Never miss the <span class="serif">next one.</span>', slug)}</div></section>
<section class="section" style="padding-top:0"><div class="wrap">{reaction_block(book)}</div></section>
<section class="section" style="padding-top:0"><div class="wrap"><div class="chip-links reveal"><a class="chip-link" href="{r}quiz.html">Take the quiz</a><a class="chip-link" href="{r}books.html">All books</a>{out_link(social_url("TikTok"), "Follow on TikTok", "social-tiktok", slug, "chip-link")}</div></div></section>"""
    dock = {"label": f"Next: {primary['title']}" if primary else "Browse books", "url": amazon(primary["kindle_asin"]) if primary else "#",
            "store": "kindle-dock", "book": primary["slug"] if primary else "", "sec": "#join"} if primary else None
    return page(f"after/{slug}.html", f"Thanks for reading {book['title']} · Ashley Claudy",
                f"What to read after {book['title']} by Ashley Claudy.", body, image=f"og/{slug}.jpg", theme=book["accent"], dock=dock, noindex=True)


def arc_form():
    nl = SITE["newsletter"]
    action = nl.get("mailerlite_form_action", "")
    w = wreck()
    title = w["title"] if w["status"] == "preorder" else "the next release"
    plat = "".join(f'<label class="check"><input type="checkbox" name="platform" value="{p}" data-label="{p}"><span>{p}</span></label>'
                   for p in ["Amazon", "Goodreads", "BookBub", "TikTok", "Instagram", "A blog or podcast"])
    if action:
        return f"""<div class="signup-wrap">
  <form class="signup req" data-signup="arc" method="post" data-action="{e(action)}" data-fallback="{e(nl["fallback_url"])}" novalidate>
    <label>Your name<input class="input" name="fields[name]" required autocomplete="name"></label>
    <label>Email<input class="input" id="arc-email" name="fields[email]" type="email" required autocomplete="email"></label>
    <label>Link to your page or profile<input class="input" name="fields[review_link]" placeholder="tiktok.com/@you or goodreads.com/you"></label>
    <fieldset class="check-group"><legend>Where will you post an honest review?</legend>{plat.replace('name="platform"', 'name="fields[platforms][]"')}</fieldset>
    <input type="hidden" name="ml-submit" value="1"><input type="hidden" name="anticsrf" value="true">
    <input type="hidden" name="fields[arc]" value="yes"><input type="hidden" name="fields[signup_source]" value="arc">
    <input type="hidden" name="fields[quiz_result]" value=""><input type="hidden" name="fields[utm_source]" value="">
    <input type="hidden" name="fields[utm_medium]" value=""><input type="hidden" name="fields[utm_campaign]" value="">
    <p class="signup-error" role="alert" hidden></p>
    <button class="btn btn-glow" type="submit">Apply for the ARC team {ARROW}</button>
    <p class="signup-note">You'll also join the Crew newsletter. <a href="{PRIVACY_HREF}">Privacy</a></p>
  </form>
  <div class="signup-done" role="status" hidden><p class="done-title">Application received.</p><p>Ashley picks the team before release. Watch your inbox.</p></div>
</div>"""
    fields = f"""<label>Your name<input class="input" name="name" data-label="Name" required autocomplete="name"></label>
  <label>Link to your page or profile<input class="input" name="link" data-label="My page" required placeholder="tiktok.com/@you or goodreads.com/you"></label>
  <fieldset class="check-group"><legend>Where will you post an honest review?</legend>{plat}</fieldset>"""
    return f'<div class="signup-wrap">{mailto_form("req", f"ARC team application: {title}", f"I would like to apply for the ARC team for {title}. I will post an honest review on the platforms below.", fields, "Apply for the ARC team")}</div>'


def build_arc():
    w = wreck()
    what = "Wreck" if w["status"] == "preorder" else "Ashley's next release"
    when = f"Wreck comes out {w['released']}." if w["status"] == "preorder" else "Applications stay open for the next release."
    body = f"""<section class="hero t-ember">
  {hero_bg("assets/covers/wreck.jpg")}
  <div class="wrap page-head">
    <p class="kicker">ARC team</p>
    <h1>Read {e(what)} <span class="serif" style="color:var(--glow)">early.</span></h1>
    <p class="lede">{e(when)} Join the advance reader team, get the book before release day, and post an honest review when it goes live.</p>
  </div>
</section>
<section class="section" style="padding-top:0"><div class="wrap">
  <div class="crew reveal" style="grid-template-areas:'copy' 'form'">
    <div class="crew-copy">
      <p class="kicker">How it works</p>
      <h2>Apply in <span class="serif">a minute.</span></h2>
      <ul class="perks">
        <li>Ashley picks the team and sends the book privately before release.</li>
        <li>You post an honest review on release day. Good or critical, it is your opinion.</li>
        <li>Say in your post that you received a free copy (for example #gifted).</li>
        <li>Reviews can't be exchanged for payment or rewards, and nobody is asked for a positive one.</li>
      </ul>
    </div>
    {arc_form()}
  </div>
</div></section>"""
    return page("arc.html", "Join the ARC Team · Ashley Claudy",
                "Apply for Ashley Claudy's advance reader (ARC) team: read the next book early and post an honest review on release day.",
                body, image="og/wreck.jpg", theme="ember")


def build_privacy():
    a = SITE.get("analytics", {})
    tools = []
    if a.get("plausible_domain"):
        tools.append("Plausible Analytics, which does not use cookies and does not track you across sites")
    if a.get("ga4_id"):
        tools.append("Google Analytics, which uses cookies and loads only if you click Accept")
    if a.get("meta_pixel_id"):
        tools.append("the Meta Pixel (Facebook and Instagram), which uses cookies, measures our ads, and loads only if you click Accept")
    analytics_p = ("This site uses " + "; ".join(tools) + "." if tools else "This site does not currently use analytics tools.")
    email = SITE.get("contact_email", "")
    sections = [
        ("Who runs this site", f"This is the website of author Ashley Claudy. Questions about this policy: {e(email)}."),
        ("What you give us", "If you join the newsletter, we collect your email address. We also record which page or form you joined from, which book you were viewing, your quiz result if you took the quiz, and the campaign link that brought you here, so we can send emails you will like. If you apply for the ARC team or send a review-copy request, a reaction, or a message, it goes to us by email from your own email app; the site itself does not receive it."),
        ("Newsletter provider", "Newsletter signups are handled by MailerLite, which stores your email and sends our emails. Every email has an unsubscribe link. We do not sell or rent your email address."),
        ("Stored in your browser", "To remember your choices, the site saves small items in your browser's local storage: whether you joined the newsletter, your quiz result, your Amazon store choice, and which campaign link you arrived by. They stay on your device. You can clear them in your browser settings."),
        ("Analytics", analytics_p),
        ("Amazon links", "Many buttons link to Amazon. As an Amazon Associate, Ashley earns from qualifying purchases. Amazon sets its own cookies when you visit it. We send visitors outside the US to their own Amazon store when we can tell where they are; you can change the store at the bottom of any page."),
        ("Other companies", "TikTok, Instagram, and Spotify content loads only after you tap it, and then those companies' own policies apply. Fonts and images are hosted on this site."),
        ("Your choices", "Unsubscribe from any email, or write to us to see, correct, or delete what we hold about you. You can decline analytics cookies when asked, and clear your browser storage at any time. Depending on where you live, you may have extra rights under laws such as the GDPR or the California Consumer Privacy Act, and you can use them by writing to us."),
        ("Age", "The books are for readers 18 and older, and this site is not directed at children under 13."),
        ("Changes", f"We will update this page if how we handle information changes. Last updated: {e(SITE.get('privacy_updated', ''))}."),
    ]
    body_html = "".join(f"<h2>{t}</h2><p>{c}</p>" for t, c in sections)
    body = f"""<section class="hero t-blue">
  {hero_bg("assets/covers/ride.jpg")}
  <div class="wrap page-head"><p class="kicker">Privacy</p><h1>Privacy <span class="serif" style="color:var(--glow)">policy.</span></h1></div>
</section>
<section class="section" style="padding-top:0"><div class="wrap"><div class="prose">{body_html}</div></div></section>"""
    return page("privacy.html", "Privacy Policy · Ashley Claudy", "How Ashley Claudy's website handles your email address, analytics, and browser storage.", body)


# ---------- fan features (each one renders only when its content exists) ----------

def embed_url(post):
    url = post.get("url", "").strip()
    if post.get("platform") == "tiktok":
        m = re.search(r"/video/(\d+)", url)
        return f"https://www.tiktok.com/embed/v2/{m.group(1)}" if m else ""
    if post.get("platform") == "instagram" and url:
        return url.split("?")[0].rstrip("/") + "/embed"
    if post.get("platform") == "facebook" and "facebook.com/" in url:
        return "https://www.facebook.com/plugins/video.php?href=" + quote(url, safe="") + "&show_text=false&t=0"
    return ""


def feed_section():
    posts = [p for p in FAN.get("social_posts", []) if p.get("show", True) and p.get("platform") in PLATFORMS and embed_url(p)]
    if not posts:
        return ""
    cards = ""
    for i, p in enumerate(posts):
        label = PLATFORMS[p["platform"]]
        thumb = p.get("thumb", "")
        img = (f'<span class="post-bg" style="background-image:url({e(thumb)})"></span><img class="post-img" src="{e(thumb)}" alt="" width="270" height="480" loading="lazy">'
               if thumb else "")
        likes = f'<span class="post-likes">{e(p["likes"])} likes</span>' if p.get("likes") else ""
        cap = f'<span class="post-cap">{e(p["caption"])}</span>' if p.get("caption") else ""
        cards += f"""<article class="post reveal{" has-img" if thumb else ""}" style="--d:{round(i * 0.06, 2)}s" data-embed="{e(embed_url(p))}">
  <button class="post-play" type="button" aria-label="Play this {label} post">{img}<span class="post-top"><span class="post-badge">{label}</span>{likes}</span>{cap}<span class="post-go">{PLAY}</span></button>
  <a class="post-open" href="{e(p["url"])}" target="_blank" rel="noopener" data-track="social-{p["platform"]}">Open on {label} {ARROW}</a>
</article>"""
    follow = "".join(
        out_link(social_url(name), f"Follow on {name}", f"social-{name.lower()}", "", "btn btn-line")
        for name in ("TikTok", "Facebook")
    )
    return f"""<section class="section" id="feed" aria-labelledby="feed-title">
  <div class="wrap"><div class="sec-head reveal">
    <p class="kicker">Most loved</p>
    <h2 class="h2" id="feed-title">Her most-loved <span class="serif">TikToks.</span></h2>
    <p>Ashley's most-loved posts. Tap one to play it right here.</p>
  </div></div>
  <div class="shelf feed" tabindex="0" aria-label="Most-loved TikTok posts">{cards}</div>
  <div class="shelf-foot feed-follow">{follow}</div>
</section>"""


def trailer_for(book):
    t = dict(book.get("trailer") or {})
    mp4 = ROOT / f"assets/video/{book['slug']}.mp4"
    if not t.get("src") and mp4.exists():
        t["src"] = f"assets/video/{book['slug']}.mp4"
        if (ROOT / f"assets/video/{book['slug']}.jpg").exists():
            t["poster"] = f"assets/video/{book['slug']}.jpg"
    return t


def trailer_section(book, r):
    t = trailer_for(book)
    if not t.get("src"):
        return ""
    poster = f"{r}{t['poster']}" if t.get("poster") else f"{r}assets/covers/{book['cover']}"
    cls = "trailer" + ("" if t.get("vertical") is False else " v")
    sample = ""
    if book["status"] == "out":
        sample = out_link(kindle_sample(book["kindle_asin"]), "Read the first chapters", "sample", book["slug"], "btn btn-line")
    return f"""<section class="theater" aria-label="{e(book['title'])} trailer">
  <div class="wrap theater-grid">
    <div class="{cls} reveal" data-trailer data-book="{e(book['slug'])}">
      <video playsinline muted loop preload="metadata" poster="{e(poster)}" src="{e(r + t['src'])}"></video>
      <button class="trailer-btn" type="button" aria-label="Play trailer"><span class="trailer-ico">{PLAY}</span><span class="sr-only">Watch the trailer</span></button>
    </div>
    <div class="theater-copy reveal">
      <p class="kicker">The trailer</p>
      <h2>{e(book['hook'])}</h2>
      <div class="cta-row" data-dock-watch>
        {out_link(amazon(book["kindle_asin"]), f"{e(kindle_label(book))} {ARROW}", "kindle-trailer", book["slug"], "btn btn-glow")}
        {sample}
      </div>
    </div>
  </div>
</section>"""


def audio_block(book, r):
    a = book.get("audio_sample") or {}
    if not a.get("src"):
        return ""
    who = a.get("narrator") or (book.get("audiobook") or {}).get("narrator", "")
    sub = f"Narrated by {e(who)}" if who else "Audiobook sample"
    return f"""<div class="audio reveal" data-audio data-book="{e(book['slug'])}">
  <button class="audio-btn" type="button" aria-label="Play audio sample">{PLAY}</button>
  <div class="audio-meta"><b>Hear a sample</b><small>{sub}</small>
    <input class="audio-range" type="range" min="0" max="100" step="0.1" value="0" aria-label="Seek" disabled></div>
  <span class="audio-time">0:00</span>
  <audio preload="none" src="{e(r + a['src'])}"></audio>
</div>"""


def playlist_block(book):
    url = (book.get("playlist") or {}).get("url", "")
    m = re.search(r"open\.spotify\.com/(?:embed/)?playlist/([A-Za-z0-9]+)", url)
    if not m:
        return ""
    return f"""<div class="playlist reveal" data-embed="https://open.spotify.com/embed/playlist/{m.group(1)}">
  <p class="kicker">Soundtrack</p>
  <div class="playlist-row"><button class="btn btn-line btn-sm" type="button" data-playlist>Play the {e(book['title'])} playlist</button>
  {out_link(url, f"Open in Spotify {ARROW}", "playlist", book['slug'], "link")}</div>
</div>"""


def characters_block(book):
    chars = book.get("characters") or []
    if not chars:
        return ""
    items = "".join(f'<li><b>{e(c["name"])}</b><span>{e(c.get("line", ""))}</span></li>' for c in chars)
    return f'<div class="chars reveal"><p class="kicker">Meet the cast</p><ul>{items}</ul></div>'


def remind_row(r=""):
    w = wreck()
    if w["status"] != "preorder":
        return ""
    dt = release_dt(w)
    day, nxt = dt.strftime("%Y%m%d"), (dt.date() + timedelta(days=1)).strftime("%Y%m%d")
    text = quote("Wreck by Ashley Claudy is out today")
    details = quote("Wreck (Crowns & Chaos #2) releases today on Kindle. " + amazon(w["kindle_asin"]))
    google = f"https://calendar.google.com/calendar/render?action=TEMPLATE&text={text}&dates={day}/{nxt}&details={details}"
    return (f'<p class="remind"><span>Remind me:</span> '
            f'<a href="{e(google)}" target="_blank" rel="noopener" data-track="calendar-google" data-book="wreck">Google Calendar</a>'
            f'<a href="{r}wreck-release.ics" download data-track="calendar-ics" data-book="wreck">Apple &amp; Outlook</a></p>')


def wreck_ics():
    w = wreck()
    dt = release_dt(w)
    d1, d2 = dt.strftime("%Y%m%d"), (dt.date() + timedelta(days=1)).strftime("%Y%m%d")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    desc = f"Wreck (Crowns & Chaos #2) releases today on Kindle. {amazon(w['kindle_asin'])}".replace("\\", "\\\\").replace(",", "\\,").replace(";", "\;")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Ashley Claudy//Wreck release//EN", "CALSCALE:GREGORIAN",
             "BEGIN:VEVENT", "UID:wreck-release@ashleyclaudy.com", f"DTSTAMP:{stamp}",
             f"DTSTART;VALUE=DATE:{d1}", f"DTEND;VALUE=DATE:{d2}", "SUMMARY:Wreck by Ashley Claudy is out today",
             f"DESCRIPTION:{desc}", f"URL:{abs_url('books/wreck.html')}",
             "BEGIN:VALARM", "ACTION:DISPLAY", "DESCRIPTION:Wreck is out today", "TRIGGER:PT9H", "END:VALARM",
             "END:VEVENT", "END:VCALENDAR"]
    def fold(line):
        out = []
        while len(line.encode()) > 75:
            out.append(line[:75])
            line = " " + line[75:]
        out.append(line)
        return "\r\n".join(out)

    return "\r\n".join(fold(l) for l in lines) + "\r\n"


def wall_section():
    items = FAN.get("fan_wall") or []
    if not items:
        return ""
    cards = ""
    for i, it in enumerate(items):
        who = e(it.get("name", "")) + (f" · {e(it['source'])}" if it.get("source") else "")
        cards += (f'<figure class="wall-card reveal" style="--d:{round(i * 0.06, 2)}s"><blockquote>“{e(it["text"])}”</blockquote>'
                  f'<figcaption>{who}</figcaption></figure>')
    return f"""<section class="section" aria-labelledby="wall-title" style="padding-top:0">
  <div class="wrap"><div class="sec-head reveal"><p class="kicker">Reader love</p><h2 class="h2" id="wall-title">What readers <span class="serif">say.</span></h2></div></div>
  <div class="shelf wall" tabindex="0" aria-label="Reader comments">{cards}</div>
</section>"""


def quiz_band():
    covers = "".join(
        f'<img src="assets/covers/{e(BOOKS[s]["cover"])}" alt="" width="84" height="126" loading="lazy">'
        for s in QUIZ["order"]
    )
    return f"""<section class="section" style="padding-block:0 clamp(72px,11vw,136px)">
  <div class="wrap">
    <a class="quizband reveal" href="quiz.html">
      <div class="qb-copy">
        <p class="kicker">Take the quiz</p>
        <h2>Which kind of <span class="serif">trouble</span> are you?</h2>
        <p>Six questions. One Ashley Claudy book to start with.</p>
        <span class="btn btn-glow">Start the quiz {ARROW}</span>
      </div>
      <div class="qb-covers" aria-hidden="true">{covers}</div>
    </a>
  </div>
</section>"""


def follow_band():
    sp = SITE.get("proof", [])
    tt = next((p for p in sp if "TikTok" in p["label"]), None)
    count = tt["figure"] if tt else ""
    handle = next((x["handle"] for x in SITE["social"] if x["name"] == "TikTok"), "@ashley.claudy")
    big = (f'<div class="fb-count"><b>{e(count)}</b><span>{e(tt["label"])}</span></div>' if count else "")
    buttons = (out_link(social_url("TikTok"), f"Follow {e(handle)} {ARROW}", "social-tiktok", "", "btn btn-glow")
               + out_link(social_url("Facebook"), "Follow on Facebook", "social-facebook", "", "btn btn-line"))
    return f"""<section class="section" id="follow" style="padding-block:0 clamp(72px,11vw,136px)" aria-label="Follow Ashley">
  <div class="wrap">
    <div class="followband reveal">
      <div class="fb-copy">
        <p class="kicker">Follow along</p>
        <h2>{e(handle)}</h2>
        <p>Book talk and new-release news, straight from Ashley.</p>
        <div class="cta-row">{buttons}</div>
      </div>
      {big}
    </div>
  </div>
</section>"""


def match_links():
    out = ""
    for slug in QUIZ["order"]:
        b = BOOKS[slug]
        out += f'<a class="match" data-match-book="{slug}" href="books/{slug}.html" hidden>Your quiz match: <b>{e(b["title"])}</b> {ARROW}</a>'
    return out


def hashtags(book):
    tags = ["#booktok", "#romancebooks", "#newadultromance"]
    if book.get("kindle_unlimited"):
        tags.append("#kindleunlimited")
    for t in book["tropes"]:
        if t in ("Standalone", "Preorder", "Series finale") or t.startswith("Book ") or "#" in t:
            continue
        tag = "#" + re.sub(r"[^a-z0-9]", "", t.lower())
        if tag not in tags:
            tags.append(tag)
    return " ".join(tags[:8])


def caption(book):
    return f"{book['hook']}\n\n{book['title']} by @ashley.claudy. {kindle_label(book)}. Link in bio.\n\n{hashtags(book)}"


def build_creators():
    email = SITE.get("contact_email", "")
    kit = ""
    for slug in ["ride", "wreck", "hustle", "outside-the-ropes", "inside-danger", "otherside-of-fear", "it-goes-on"]:
        b = BOOKS[slug]
        mp4 = ROOT / f"assets/video/{slug}.mp4"
        if not mp4.exists():
            continue
        mb = mp4.stat().st_size / 1e6
        kit += f"""<article class="kit-card t-{b['accent']} reveal">
  <img src="assets/video/{slug}-story.jpg" alt="{e(b['title'])} story image preview" width="270" height="480" loading="lazy">
  <p class="kicker">{e(short_label(b))}</p>
  <h3>{e(b['title'])}</h3>
  <a class="btn btn-glow btn-sm" href="assets/video/{slug}.mp4" download data-track="kit-video" data-book="{slug}">Video · {mb:.1f} MB</a>
  <a class="btn btn-line btn-sm" href="assets/video/{slug}-story.jpg" download data-track="kit-story" data-book="{slug}">Story image</a>
</article>"""
    caps = ""
    for slug in ["ride", "wreck", "hustle", "outside-the-ropes", "it-goes-on"]:
        b = BOOKS[slug]
        text = caption(b)
        caps += f"""<article class="cap-card t-{b['accent']} reveal">
  <p class="kicker">{e(b['title'])}</p>
  <p class="cap-text">{e(text)}</p>
  <button class="btn btn-line btn-sm" type="button" data-copy="{e(text)}">Copy caption</button>
</article>"""
    book_opts = "".join(f'<option value="{e(b["title"])}">{e(b["title"])}{" (preorder)" if b["status"] == "preorder" else ""}</option>' for b in CATALOG["books"])
    platform_opts = "".join(f"<option>{p}</option>" for p in ["TikTok", "Instagram", "YouTube", "Blog", "Podcast", "Goodreads", "Other"])
    bio = "".join(f"<p>{e(p)}</p>" for p in SITE["bio"])
    tt = next((p for p in SITE.get("proof", []) if "TikTok" in p["label"]), None)
    facts = [("Genre", "New Adult romance (18+)"), ("Books", f"{len(CATALOG['books'])} novels plus the Outside the Ropes box set"),
             ("Audiobooks", "Hustle and the Outside the Ropes trilogy on Audible"), ("Based in", SITE.get("location", ""))]
    if tt:
        facts.insert(1, ("TikTok", f"{SITE['social'][0]['handle']} · {tt['figure']} {tt['label'].replace(' on TikTok', '')}"))
    facts_html = "".join(f"<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>" for k, v in facts if v)
    body = f"""<section class="hero t-blue">
  {hero_bg("assets/covers/ride.jpg")}
  <div class="wrap page-head">
    <p class="kicker">Creators &amp; press</p>
    <h1>Make something with <span class="serif" style="color:var(--glow)">Ashley's books.</span></h1>
    <p class="lede">BookTok, Bookstagram, podcast, blog? Grab ready-made trailers and story images, copy a caption, and ask for a review copy. Tag @ashley.claudy and say hi.</p>
  </div>
</section>
<section class="section" id="kit" aria-labelledby="kit-title">
  <div class="wrap"><div class="sec-head reveal"><p class="kicker">The kit</p><h2 class="h2" id="kit-title">Trailers and stories, <span class="serif">ready to post.</span></h2>
    <p>Vertical 1080×1920 videos and story images for every book, built from each book's own hook, tropes, and cover. Free to use when you talk about the books.</p></div></div>
  <div class="shelf kit" tabindex="0" aria-label="Download kit">{kit}</div>
</section>
<section class="section" style="padding-top:0" id="captions" aria-labelledby="cap-title">
  <div class="wrap"><div class="sec-head reveal"><p class="kicker">Captions</p><h2 class="h2" id="cap-title">Start with <span class="serif">these.</span></h2>
    <p>Suggested captions with tropes and hashtags. Change them up so they sound like you.</p></div>
    <div class="caps">{caps}</div></div>
</section>
<section class="section" style="padding-top:0" id="request" aria-labelledby="req-title">
  <div class="wrap">
    <div class="crew reveal" style="grid-template-areas:'copy' 'form'">
      <div class="crew-copy">
        <p class="kicker">Review copies</p>
        <h2 id="req-title">Ask for a <span class="serif">copy.</span></h2>
        <p class="lede">Tell Ashley where you post and which book you want. This opens your email app with the request filled in.</p>
        <p class="fine">If you get a free copy, please say so in your post (for example #gifted). Reviews can't be exchanged for payment or rewards, and honest opinions are always welcome.</p>
      </div>
      <div class="signup-wrap">
        {mailto_form("req", "Review copy request: {book}", "I would love a review copy.",
            f'''<label>Your name<input class="input" name="name" data-label="Name" required autocomplete="name"></label>
          <label>Link to your page<input class="input" name="link" data-label="My page" required placeholder="tiktok.com/@you"></label>
          <label>Where you post<select class="input" name="platform" data-label="Where I post">{platform_opts}</select></label>
          <label>Which book<select class="input" name="book" data-label="Book">{book_opts}</select></label>
          <label>Anything else<textarea class="input" name="note" data-label="Note" rows="3"></textarea></label>''', "Open my email")}
      </div>
    </div>
  </div>
</section>
<section class="section" style="padding-top:0" id="press" aria-labelledby="press-title">
  <div class="wrap about-grid">
    <div class="reveal"><p class="kicker" id="press-title" style="margin-bottom:22px">Press facts</p><div class="about-copy">{bio}</div></div>
    <div class="reveal"><dl class="spec">{facts_html}</dl>
      <div style="margin-top:24px">{socials()}</div>
      <p class="fine" style="margin-top:18px">Interviews, podcasts, and collaborations: <b>{e(email)}</b></p>
    </div>
  </div>
</section>"""
    return page("creators.html", "Creators & Press Kit · Ashley Claudy",
                "Trailers, story images, captions, review-copy requests, and press facts for BookTok, Bookstagram, podcast, and blog creators covering Ashley Claudy's books.",
                body, image="og/home.jpg", current="creators.html")


def build_genre(g):
    r = ""
    books = [BOOKS[s] for s in g["books"]]
    first = books[0]
    intro = "".join(f'<p class="lede">{e(p)}</p>' for p in g["intro"])
    primary_book = next((b for b in books if b["status"] == "out"), first)
    if len(books) == 1:
        b = first
        tags = "".join(f"<li>{e(t)}</li>" for t in b["tropes"])
        listing = f"""<article class="res t-{b['accent']}"><div class="res-grid">
  <a class="res-cover reveal" href="books/{b['slug']}.html"><img class="cover-art" src="assets/covers/{e(b['cover'])}" alt="{e(b['title'])} by Ashley Claudy, cover" width="333" height="500" loading="lazy"></a>
  <div class="res-copy reveal">
    <p class="kicker">{e(series_label(b))} · {e(b.get('pages', ''))} pages</p>
    <h2 class="res-title">{e(b['title'])}</h2>
    <p class="lede">{e(b['hook'])}</p>
    <ul class="tags">{tags}</ul>
    <div class="cta-row">{out_link(amazon(b['kindle_asin']), f"{e(kindle_label(b))} {ARROW}", "kindle-genre", b['slug'], "btn btn-glow")}<a class="btn btn-line" href="books/{b['slug']}.html">See the book</a></div>
  </div></div></article>"""
    else:
        cards = "".join(
            shelf_card(b, r, short_label(b), badge="Preorder" if b["status"] == "preorder" else "", delay=round(i * 0.06, 2))
            for i, b in enumerate(books))
        listing = f'<div class="grid-books">{cards}</div>'
    faq = "".join(f'<details class="faq-item reveal"><summary>{e(f["q"])}</summary><p>{e(f["a"])}</p></details>' for f in g["faq"])
    others = "".join(f'<a class="chip-link" href="{o["slug"]}.html">{e(o["label"])}</a>' for o in GENRES if o["slug"] != g["slug"])
    ld = [
        {"@context": "https://schema.org", "@type": "FAQPage",
         "mainEntity": [{"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in g["faq"]]},
        {"@context": "https://schema.org", "@type": "CollectionPage", "name": g["meta_title"], "url": abs_url(f"{g['slug']}.html"),
         "hasPart": [{"@type": "Book", "name": b["title"], "url": abs_url(f"books/{b['slug']}.html"),
                      "author": {"@type": "Person", "name": SITE["author"]}} for b in books]},
    ]
    body = f"""<section class="hero t-{g['accent']}">
  {hero_bg("assets/covers/" + first["cover"])}
  <div class="wrap page-head">
    <p class="kicker">{e(g['kicker'])}</p>
    <h1>{e(g['h1'])} <span class="serif" style="color:var(--glow)">{e(g['h1_serif'])}</span></h1>
    {intro}
    <div class="cta-row" style="margin-top:8px;max-width:520px">{out_link(amazon(primary_book['kindle_asin']), f"{e(short_cta(primary_book))} {ARROW}", "kindle-genre", primary_book['slug'], "btn btn-glow")}<a class="btn btn-line" href="quiz.html">Not sure? Take the quiz</a></div>
  </div>
</section>
<section class="series t-{g['accent']}" aria-label="Books"><div class="wrap">{listing}</div></section>
<section class="series" aria-labelledby="faq-title"><div class="wrap">
  <div class="series-head reveal"><p class="kicker">Good to know</p><h2 id="faq-title">Questions</h2></div>
  <div class="faq">{faq}</div>
</div></section>
<section class="series"><div class="wrap">
  <div class="series-head reveal"><p class="kicker">More worlds</p><h2>Keep exploring</h2></div>
  <div class="chip-links reveal">{others}<a class="chip-link" href="quiz.html">Take the quiz</a><a class="chip-link" href="books.html">All books</a></div>
</div></section>
<section class="section" id="join" aria-label="Join the Crew"><div class="wrap reveal">{crew("genre")}</div></section>"""
    dock = {"label": short_cta(primary_book), "url": amazon(primary_book["kindle_asin"]), "store": "kindle-dock", "book": primary_book["slug"], "sec": "#join"}
    return page(f"{g['slug']}.html", g["meta_title"], g["meta_description"], body,
                image="og/home.jpg" if len(books) > 1 else f"og/{first['slug']}.jpg",
                jsonld=ld, theme=g["accent"], dock=dock)


# ---------- pages ----------

def build_home():
    r = ""
    feat = BOOKS[featured_slug()]
    fslug = feat["slug"]
    w = wreck()
    lead, accent_words = split_tagline(feat["tagline"])
    nbsp_words = accent_words.replace(" ", "&nbsp;")

    pill = ""
    if w["status"] == "preorder":
        pill = (f'<a class="pill hero-pill" href="books/wreck.html"><span class="dot"></span>'
                f'<span>Wreck drops {e(release_short(w))} · <b><span data-days-until="{e(w["release_iso"])}">{days_left(w)}</span> days</b></span></a>')
    elif fslug == "wreck":
        pill = '<a class="pill hero-pill" href="books/wreck.html"><span class="dot"></span><span>Wreck is out now</span></a>'
    status_word = "Preorder" if feat["status"] == "preorder" else "Out now"
    proof_items = ""
    if feat.get("proof"):
        rating = rating_of(feat)
        proof_items += f"<li>{stars_html(rating) if rating else STAR}<b>{e(feat['proof'])}</b></li>"
    if feat.get("pages"):
        proof_items += f"<li>{feat['pages']} pages</li>"
    proof_row = f'<ul class="proof-row">{proof_items}</ul>' if proof_items else ""
    sample_btn = (out_link(kindle_sample(feat["kindle_asin"]), "Read the first chapters", "sample", fslug, "btn btn-line")
                  if feat["status"] == "out" else '<a class="btn btn-line" href="#join">Get the cover reveal first</a>')
    hero = f"""<section class="hero t-{feat['accent']}" aria-labelledby="hero-title">
  {hero_bg("assets/covers/" + feat["cover"])}
  <div class="wrap hero-in">
    {pill}
    <div class="hero-cover"><a data-tilt href="books/{fslug}.html"><img class="cover-art" src="assets/covers/{e(feat['cover'])}" alt="{e(feat['title'])} by Ashley Claudy, cover" width="324" height="500" fetchpriority="high"></a></div>
    <div class="hero-copy">
      <p class="kicker">{e(series_label(feat))} · {status_word}</p>
      <h1 id="hero-title"><span class="sr-only">{e(feat['title'])} by Ashley Claudy: </span>{e(lead)} <span class="serif">{nbsp_words}</span></h1>
      <p class="lede">{e(feat['hook'])}</p>
      <div class="cta-row" data-dock-watch>
        {out_link(amazon(feat['kindle_asin']), f"{e(kindle_label(feat))} {ARROW}", "kindle", fslug, "btn btn-glow")}
        {sample_btn}
      </div>
      {proof_row}
      {match_links()}
    </div>
  </div>
</section>"""

    cards = []
    for i, (slug, label) in enumerate(SHELF):
        b = BOOKS[slug]
        badge = {"ride": "New", "wreck": "Preorder", "outside-the-ropes": "3 books"}.get(slug, "")
        line = None
        if slug == "wreck":
            line = "The next ride into Crowns & Chaos. The cover reveal goes to the Crew first."
        cards.append(shelf_card(b, r, label, line=line, badge=badge, delay=round(i * 0.06, 2)))
    proof = "".join(
        f'<div class="stat"><b>{e(p["figure"])}</b><span>{e(p["label"])}</span></div>' for p in SITE["proof"]
    )
    shelf = f"""<section class="section" id="books" aria-labelledby="shelf-title">
  <div class="wrap">
    <div class="sec-head reveal">
      <p class="kicker">The books</p>
      <h2 class="h2" id="shelf-title">Pick your kind of <span class="serif">trouble.</span></h2>
      <p>Street racers, fighters, football players. Choose the world that sounds like you. Every ebook is free in Kindle Unlimited.</p>
    </div>
  </div>
  <div class="shelf" tabindex="0" aria-label="Books by Ashley Claudy">{"".join(cards)}</div>
  <div class="shelf-foot"><a class="btn btn-line" href="books.html">Browse every book {ARROW}</a></div>
  <div class="wrap"><div class="stats reveal">{proof}</div></div>
</section>"""

    preorder = ""
    if w["status"] == "preorder":
        preorder = f"""<section class="wreck t-ember section" aria-labelledby="wreck-title">
  <div class="wrap wreck-grid">
    <div class="wreck-copy">
      <p class="kicker reveal">Crowns &amp; Chaos · Book 2 · Preorder</p>
      <h2 class="wreck-title reveal" id="wreck-title">Wreck</h2>
      <p class="lede reveal">Lands on Kindle {e(w['released'])}. Preorder now and it shows up on your device on release day. The cover reveal goes to the Crew before anywhere else.</p>
      <div class="reveal" style="width:100%">{countdown(w, "wreck-out")}</div>
      <div class="cta-row reveal" style="max-width:520px">
        {out_link(amazon(w['kindle_asin']), f"Preorder Wreck {ARROW}", "kindle-preorder", "wreck", "btn btn-glow")}
        <a class="btn btn-line" href="#join">Get the cover reveal first</a>
      </div>
      <div class="reveal">{remind_row()}</div>
    </div>
    <div class="wreck-cover reveal"><a data-tilt href="books/wreck.html"><img class="cover-art" src="assets/covers/wreck.jpg" alt="Wreck by Ashley Claudy, cover reveal coming soon" width="333" height="500" loading="lazy"></a></div>
  </div>
</section>"""

    join = f"""<section class="section" id="join" aria-label="Join the Crew" data-dock-watch>
  <div class="wrap reveal">{crew("home")}</div>
</section>"""

    bio = SITE["bio"]
    email = SITE.get("contact_email", "")
    contact = (f"""<div class="copy-row"><span>Rights, interviews, collaborations:</span>
      <code>{e(email)}</code><button class="btn btn-line btn-sm" type="button" data-copy="{e(email)}">Copy email</button></div>""" if email else "")
    about = f"""<section class="section" id="about" aria-labelledby="about-title" style="padding-top:0">
  <div class="wrap about-grid">
    <div class="reveal">
      <p class="kicker" id="about-title" style="margin-bottom:22px">About Ashley</p>
      <p class="about-quote">{e(bio[0])}</p>
    </div>
    <div class="about-copy reveal">
      {"".join(f"<p>{e(p)}</p>" for p in bio[1:])}
      {socials()}
      <p class="fine">Made fan art, a reaction, or an edit? Tag @ashley.claudy on TikTok or email it to be featured here. Posting about the books? <a href="creators.html">Grab the creator kit</a>.</p>
      {contact}
    </div>
  </div>
</section>"""

    body = hero + trope_marquee() + shelf + quiz_band() + (feed_section() or follow_band()) + preorder + wall_section() + join + about
    dock = {"label": short_cta(feat), "url": amazon(feat["kindle_asin"]), "store": "kindle-dock", "book": fslug, "sec": "#join"}
    return page("index.html", "Ashley Claudy · New Adult Romance Author", SITE["meta_description"], body,
                image="og/home.jpg", jsonld=[person_ld()], dock=dock)


def build_books():
    r = ""
    blocks = []
    for s in CATALOG["series"]:
        ordered = s["id"] != "standalones"
        cards = "".join(
            shelf_card(BOOKS[slug], r, f"Book {BOOKS[slug]['number']}" if ordered else "Standalone",
                       badge="Preorder" if BOOKS[slug]["status"] == "preorder" else "", delay=round(i * 0.06, 2))
            for i, slug in enumerate(s["books"])
        )
        box = ""
        if s.get("box_set"):
            bs = s["box_set"]
            box = f"""<div class="boxset t-{s['accent']} reveal">
  <img src="assets/covers/{e(bs['cover'])}" alt="{e(bs['title'])}, cover" width="130" height="161" loading="lazy">
  <div>
    <p class="kicker">Binge it</p>
    <h3>{e(bs['title'])}</h3>
    <p>All three books in one download, {bs['pages']:,} pages. No waiting on cliffhangers.</p>
  </div>
  {out_link(amazon(bs['asin']), f"Get the box set {ARROW}", "kindle-boxset", s['id'], "btn btn-glow")}
</div>"""
        series_link = ""
        if s.get("amazon_series_asin"):
            series_link = f'<p class="fine">{out_link(amazon(s["amazon_series_asin"]), "See the whole series on Amazon", "amazon-series", s["id"])}</p>'
        blocks.append(f"""<section class="series t-{s['accent']}" id="{s['id']}" aria-labelledby="{s['id']}-title">
  <div class="wrap">
    <div class="series-head reveal">
      <p class="kicker">{"Start anywhere" if not ordered else "Read in order"}</p>
      <h2 id="{s['id']}-title">{e(s['name'])}</h2>
      <p>{e(s['pitch'])}</p>
      {series_link}
    </div>
    <div class="grid-books">{cards}</div>
    {box}
  </div>
</section>""")

    where = f"""<section class="series" id="where-to-buy" aria-labelledby="where-title">
  <div class="wrap">
    <div class="series-head reveal"><p class="kicker">Where to buy</p><h2 id="where-title">Ebooks, paperbacks, audio</h2></div>
    <div class="where reveal">
      <div><h3>Ebooks</h3><p>Ashley's ebooks are exclusive to Amazon. Buy them there, or read them free with a Kindle Unlimited subscription.</p>
        {out_link("https://www.amazon.com/kindle-dbs/hz/subscribe/ku", f"About Kindle Unlimited {ARROW}", "ku-info", "", "link")}</div>
      <div><h3>No Kindle?</h3><p>The free Kindle app works on any phone, tablet, or computer. Download it, buy or borrow the book, and it appears in the app.</p>
        {out_link("https://www.amazon.com/kindle-dbs/fd/kcp", f"Get the free Kindle app {ARROW}", "kindle-app", "", "link")}</div>
      <div><h3>Print &amp; audio</h3><p>Paperbacks are sold at Amazon, Barnes &amp; Noble, and other bookstores, and your library can order them. Audiobooks are on Audible.</p></div>
    </div>
  </div>
</section>"""

    join = f"""<section class="section" id="join" aria-label="Join the Crew"><div class="wrap reveal">{crew("books")}</div></section>"""

    body = f"""<section class="hero t-blue" style="overflow:clip">
  {hero_bg("assets/covers/ride.jpg")}
  <div class="wrap page-head">
    <p class="kicker">All books</p>
    <h1>The <span class="serif" style="color:var(--glow)">books.</span></h1>
    <p class="lede">Two series and two standalones, all New Adult romance. Every ebook is free to read in Kindle Unlimited.</p>
  </div>
</section>
{"".join(blocks)}
{where}
{join}"""
    return page("books.html", "Books by Ashley Claudy · Reading Order",
                "Every Ashley Claudy book in reading order: Crowns & Chaos, Outside the Ropes, Hustle, and It Goes On. Read free in Kindle Unlimited.",
                body, image="og/home.jpg", current="books.html")


def build_book(book):
    r = "../"
    slug = book["slug"]
    s = SERIES[book["series"]]
    cover_src = f"{r}assets/covers/{e(book['cover'])}"

    primary = out_link(amazon(book["kindle_asin"]), f"{e(kindle_label(book))} {ARROW}", "kindle", slug, "btn btn-glow btn-block")
    sample = ""
    if book["status"] == "out":
        sample = out_link(kindle_sample(book["kindle_asin"]), "Read a free sample", "sample", slug, "btn btn-line btn-block")

    def row(url, label, sub, store):
        return (f'<a href="{e(url)}" target="_blank" rel="noopener"{asin_attr(url)} data-track="{e(store)}" data-book="{e(slug)}">'
                f'<span>{label} <small>{e(sub)}</small></span>{ARROW}</a>')

    more = []
    if book.get("paperback"):
        pb = book["paperback"]
        more.append(row(amazon(pb["asin"]), "Paperback", "Amazon", "paperback-amazon"))
        if pb.get("isbn13"):
            more.append(row(f"https://www.barnesandnoble.com/s/{pb['isbn13']}", "Paperback", "Barnes &amp; Noble".replace("&amp;", "&"), "paperback-bn"))
            more.append(row(f"https://bookshop.org/search?keywords={pb['isbn13']}", "Paperback", "Bookshop.org", "paperback-bookshop"))
    if book.get("audiobook"):
        ab = book["audiobook"]
        more.append(row(ab["url"], "Audiobook", f"Narrated by {ab['narrator']}", "audiobook"))
    more.append(row(book["goodreads"], "Add on Goodreads", "", "goodreads"))

    timer = ""
    if book["status"] == "preorder" and book.get("release_iso"):
        timer = countdown(book, f"{slug}-out")
    note_line = ("Preorders download automatically on release day." if book["status"] == "preorder"
                 else "Ebook exclusive to Amazon. Free to read with Kindle Unlimited." if book.get("kindle_unlimited")
                 else "Ebook exclusive to Amazon.")
    proof = ""
    if book.get("proof"):
        rating = rating_of(book)
        proof = (f'<p class="bk-proof">{stars_html(rating) if rating else STAR}<span>{e(book["proof"])}</span>'
                 f'{out_link(book["goodreads"], "See reader reviews", "goodreads-reviews", slug, "link link-sm")}</p>')

    spec_rows = [("Series", series_label(book)), ("Released", book["released"])]
    if book.get("pages"):
        spec_rows.append(("Length", f"{book['pages']} pages"))
    spec_rows += [("Formats", formats(book)), ("Audience", book["audience"])]
    if book.get("audiobook"):
        spec_rows.append(("Narrator", book["audiobook"]["narrator"]))
    spec = '<dl class="spec">' + "".join(f"<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>" for k, v in spec_rows) + "</dl>"

    blurb = "".join(f"<p>{e(p)}</p>" for p in book["blurb"])
    if book.get("series_note"):
        blurb += f'<p class="series-note">{e(book["series_note"])}</p>'
    tags = '<ul class="tags">' + "".join(f"<li>{e(t)}</li>" for t in book["tropes"]) + "</ul>"
    note = ""
    if book.get("content_note"):
        note = f'<details class="note"><summary>Content note</summary><p>{e(book["content_note"])}</p></details>'
    quotes = ""
    if book.get("quotes"):
        quotes = '<div class="quotes">' + "".join(
            f'<blockquote><p>“{e(q["text"])}”</p><cite>{e(q["source"])}</cite></blockquote>' for q in book["quotes"]
        ) + "</div>"

    strip = ""
    if book["series"] != "standalones":
        thumbs = "".join(
            f'<a href="{other}.html"{CURRENT if other == slug else ""}>'
            f'<img src="{r}assets/covers/{e(BOOKS[other]["cover"])}" alt="" width="92" height="138" loading="lazy">'
            f'Book {BOOKS[other]["number"]} · {e(BOOKS[other]["title"])}</a>'
            for other in s["books"]
        )
        strip = f'<div><p class="kicker" style="margin-bottom:14px">{e(s["name"])}</p><div class="strip">{thumbs}</div></div>'

    idx = s["books"].index(slug)
    next_up = []
    if book["series"] != "standalones" and idx + 1 < len(s["books"]):
        next_up.append(s["books"][idx + 1])
    for candidate in ["ride", "hustle", "outside-the-ropes", "it-goes-on", "wreck"]:
        if candidate != slug and candidate not in next_up and BOOKS[candidate]["series"] != book["series"]:
            next_up.append(candidate)
    next_cards = "".join(
        shelf_card(BOOKS[n], r, short_label(BOOKS[n]), badge="Preorder" if BOOKS[n]["status"] == "preorder" else "", delay=round(i * 0.06, 2))
        for i, n in enumerate(next_up[:4])
    )

    g = BOOK_GENRE.get(slug)
    genre_link = (f'<p class="reveal"><a class="link" href="{r}{g["slug"]}.html">More {e(g["label"].lower())} romance {ARROW}</a></p>' if g else "")
    join_headline = 'See the Wreck cover <span class="serif">first.</span>' if slug == "wreck" else None
    body = f"""<section class="bk">
  {hero_bg(cover_src)}
  <div class="wrap bk-in">
    <div class="bk-cover"><span data-tilt style="display:block"><img class="cover-art" src="{cover_src}" alt="{e(book['title'])} by Ashley Claudy, cover" width="340" height="510" fetchpriority="high"></span></div>
    <div class="bk-copy">
      <a class="back" href="{r}books.html">← All books</a>
      <p class="kicker">{e(series_label(book))}</p>
      <h1>{e(book['title'])}</h1>
      <p class="bk-tag">{e(book['tagline'])}</p>
      {proof}
      {timer}
      <div class="getit" data-dock-watch>
        {primary}
        {sample}
        <p class="fine" style="margin:0;text-align:center">{e(note_line)}</p>
        {remind_row(r) if slug == "wreck" else ""}
      </div>
      <div class="getmore">{"".join(more)}</div>
    </div>
  </div>
</section>
{trailer_section(book, r)}
<section class="section" style="padding-top:clamp(24px,5vw,56px)">
  <div class="wrap story">
    <div class="col">
      {audio_block(book, r)}
      <div class="blurb reveal">{blurb}</div>
      {characters_block(book)}
      {tags}
      {genre_link}
      {note}
    </div>
    <div class="col col-b reveal">
      {spec}
      {playlist_block(book)}
      {quotes}
      {strip}
    </div>
  </div>
</section>
<section class="section" id="join" aria-label="Join the Crew" data-dock-watch style="padding-top:0"><div class="wrap reveal">{crew("book", join_headline, slug)}</div></section>
<section class="section" aria-labelledby="next-title" style="padding-top:0">
  <div class="wrap">
    <div class="series-head reveal"><p class="kicker">Read next</p><h2 id="next-title">Keep going</h2></div>
    <div class="grid-books">{next_cards}</div>
  </div>
</section>"""

    ld_book = {
        "@context": "https://schema.org",
        "@type": "Book",
        "name": book["title"],
        "author": {"@type": "Person", "name": SITE["author"], "url": abs_url()},
        "url": abs_url(f"books/{slug}.html"),
        "image": abs_url(f"assets/covers/{book['cover']}"),
        "description": " ".join(book["blurb"]),
        "genre": "New Adult Romance",
        "inLanguage": "en",
        "workExample": [{"@type": "Book", "bookFormat": "https://schema.org/EBook", "url": amazon(book["kindle_asin"])}],
    }
    if book.get("pages"):
        ld_book["numberOfPages"] = book["pages"]
    if book["series"] != "standalones":
        ld_book["isPartOf"] = {"@type": "BookSeries", "name": s["name"]}
        ld_book["position"] = book["number"]
    if book.get("paperback", {}) and book["paperback"].get("isbn13"):
        ld_book["workExample"].append({"@type": "Book", "bookFormat": "https://schema.org/Paperback",
                                       "isbn": book["paperback"]["isbn13"], "url": amazon(book["paperback"]["asin"])})
    title = f"{book['title']} by Ashley Claudy"
    if book["series"] != "standalones":
        title += f" · {s['name']} #{book['number']}"
    desc = f"{book['tagline']} {book['hook']} {kindle_label(book)}."
    dock = {"label": short_cta(book), "url": amazon(book["kindle_asin"]), "store": "kindle-dock", "book": slug, "sec": "#join"}
    return page(f"books/{slug}.html", title, desc, body, image=f"og/{slug}.jpg", jsonld=[ld_book],
                theme=book["accent"], dock=dock)


def build_quiz():
    panels = ""
    for slug in QUIZ["order"]:
        b = BOOKS[slug]
        tags = "".join(f"<li>{e(t)}</li>" for t in b["tropes"][:4])
        panels += f"""<article class="res t-{b['accent']}" data-result="{slug}" hidden>
  <div class="res-grid">
    <a class="res-cover" href="books/{slug}.html"><img class="cover-art" src="assets/covers/{e(b['cover'])}" alt="{e(b['title'])} by Ashley Claudy, cover" width="333" height="500"></a>
    <div class="res-copy">
      <p class="kicker">Your kind of trouble</p>
      <h2 class="res-title">Start with <span class="serif">{e(b['title'])}.</span></h2>
      <p class="lede">{e(b['hook'])}</p>
      <ul class="tags">{tags}</ul>
      <div class="cta-row">
        {out_link(amazon(b['kindle_asin']), f"{e(kindle_label(b))} {ARROW}", "kindle-quiz", slug, "btn btn-glow")}
        <a class="btn btn-line" href="books/{slug}.html">See the book</a>
      </div>
      <div class="res-actions"><button class="link" type="button" data-share="{slug}">Share my result</button><button class="link" type="button" data-retake>Retake the quiz</button></div>
    </div>
  </div>
</article>"""
    data = json.dumps({"order": QUIZ["order"], "questions": QUIZ["questions"]}, ensure_ascii=False).replace("</", "<\\/")
    total = len(QUIZ["questions"])
    body = f"""<section class="hero quiz t-blue">
  {hero_bg("assets/covers/ride.jpg")}
  <div class="wrap quiz-wrap">
    <div class="quiz-view" data-view="intro">
      <p class="kicker">The quiz</p>
      <h1>Which kind of <span class="serif">trouble</span> are you?</h1>
      <p class="lede">{e(QUIZ["intro"])}</p>
      <button class="btn btn-glow" type="button" data-start>Start the quiz {ARROW}</button>
      <p class="fine">Takes about a minute.</p>
      <noscript><p class="lede">The quiz needs JavaScript. <a href="books.html">Browse all the books</a> instead.</p></noscript>
    </div>
    <div class="quiz-view" data-view="question" hidden>
      <div class="quiz-top"><button class="back" type="button" data-back>← Back</button><span class="quiz-step" data-step>1 of {total}</span></div>
      <div class="quiz-bar" aria-hidden="true"><i data-bar></i></div>
      <h2 class="quiz-q" data-q tabindex="-1"></h2>
      <div class="opts" data-opts></div>
    </div>
    <div class="quiz-view" data-view="result" hidden>
      {panels}
      <div class="quiz-join" id="join">{crew("quiz")}</div>
    </div>
  </div>
</section>
<script type="application/json" id="quiz-data">{data}</script>"""
    return page("quiz.html", "Which Kind of Trouble Are You? Quiz · Ashley Claudy",
                "Take the Ashley Claudy quiz: six quick questions to find your first book, from street racers and football players to fighters and family secrets.",
                body, image="og/quiz.jpg", extra_js=("quiz.js",))


def build_bonus():
    fan = "".join(
        f'<img src="assets/covers/{e(BOOKS[s]["cover"])}" alt="" width="136" height="204">'
        for s in ["hustle", "ride", "outside-the-ropes"]
    )
    body = f"""<section class="solo t-blue">
  {hero_bg("assets/covers/ride.jpg")}
  <div class="solo-in">
    <a class="logo" href="index.html">Ashley Claudy</a>
    <div class="fan" aria-hidden="true">{fan}</div>
    {crew("bonus")}
    <p class="fine"><a href="books.html">Browse the books</a> · <a href="index.html">Home</a></p>
  </div>
</section>"""
    return page("bonus.html", "Free Bonus Chapters · Ashley Claudy",
                "Join Ashley Claudy's Crew newsletter for free bonus chapters, the Wreck cover reveal, and ARC invites.",
                body, solo=True, image="og/bonus.jpg")


def lb_row(href, title, sub, *, cover=None, icon=None, hot=False, theme="", store=None, book="", external=True):
    lead = (f'<img src="{e(cover)}" alt="" width="48" height="72">' if cover else f'<span class="lb-tile">{icon}</span>')
    attrs = (f' target="_blank" rel="noopener"{asin_attr(href)} data-track="{e(store)}" data-book="{e(book)}"' if external else "")
    cls = "lb-link" + (" hot" if hot else "") + (f" t-{theme}" if theme else "")
    return f'<a class="{cls}" href="{e(href)}"{attrs}>{lead}<span><b>{e(title)}</b><small>{e(sub)}</small></span>{ARROW}</a>'


def build_links():
    w, ride, hustle = wreck(), BOOKS["ride"], BOOKS["hustle"]
    rows = []
    if w["status"] == "preorder":
        rows.append(lb_row(amazon(w["kindle_asin"]), "Preorder Wreck", f"Crowns & Chaos #2 · out {w['released']}",
                           cover="assets/covers/wreck.jpg", hot=True, theme="ember", store="kindle-preorder", book="wreck"))
    rows.append(lb_row(amazon(ride["kindle_asin"]), "Read Ride free", "Crowns & Chaos #1 · Kindle Unlimited",
                       cover="assets/covers/ride.jpg", hot=w["status"] != "preorder", store="kindle", book="ride"))
    rows.append(lb_row("bonus.html", "Free bonus chapters", "Join the Crew newsletter", icon=ICON_MAIL, external=False))
    if hustle.get("audiobook"):
        rows.append(lb_row(hustle["audiobook"]["url"], "Hustle on audio", "Audible · college football romance",
                           cover="assets/covers/hustle.jpg", theme="gold", store="audiobook", book="hustle"))
    if fb_group()[0]:
        rows.append(lb_row(fb_group()[0], "Join the reader group", fb_group()[1] + " on Facebook", icon=ICON_MAIL, store="social-facebook-group"))
    rows.append(lb_row("books.html", "All the books", "Reading order and where to buy", icon=ICON_BOOKS, external=False))
    body = f"""<section class="solo t-blue">
  {hero_bg("assets/covers/ride.jpg")}
  <div class="solo-in">
    <div class="avatar" aria-hidden="true">AC</div>
    <h1>Ashley Claudy</h1>
    <p class="solo-sub">{e(SITE['tagline'])}</p>
    <div class="lb">{"".join(rows)}</div>
    {socials()}
  </div>
</section>"""
    return page("links.html", "Links · Ashley Claudy", "Every Ashley Claudy link in one place.", body, solo=True)


def build_404():
    body = """<section class="wrap notfound">
  <p class="kicker">404</p>
  <h1>Wrong <span class="serif" style="color:var(--glow)">turn.</span></h1>
  <p class="lede">That page doesn't exist anymore. The books are still here.</p>
  <div class="cta-row" style="max-width:420px"><a class="btn btn-glow" href="/books.html">See the books</a><a class="btn btn-line" href="/">Home</a></div>
</section>"""
    return page("404.html", "Page not found · Ashley Claudy", "This page doesn't exist.", body)


FAVICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#09090b"/><path d="M32 12l14 20-14 20L18 32z" fill="#3ec1ff"/><path d="M32 22l7 10-7 10-7-10z" fill="#09090b"/></svg>
"""


def build(out: Path):
    if out.exists():
        if any(out.iterdir()) and not (out / MARKER).exists():
            raise SystemExit(f"Refusing to overwrite {out}: it isn't a previous build folder.")
        shutil.rmtree(out)
    out.mkdir(parents=True)
    (out / MARKER).write_text("generated by build.py\n")
    shutil.copytree(ROOT / "assets", out / "assets")
    (out / "assets/favicon.svg").write_text(FAVICON)

    pages = {
        "index.html": build_home(),
        "books.html": build_books(),
        "bonus.html": build_bonus(),
        "links.html": build_links(),
        "quiz.html": build_quiz(),
        "creators.html": build_creators(),
        "arc.html": build_arc(),
        "privacy.html": build_privacy(),
        "404.html": build_404(),
    }
    for book in CATALOG["books"]:
        pages[f"books/{book['slug']}.html"] = build_book(book)
    for g in GENRES:
        pages[f"{g['slug']}.html"] = build_genre(g)
    for book in CATALOG["books"]:
        if book["status"] == "out":
            pages[f"after/{book['slug']}.html"] = build_after(book)
    for path, text in pages.items():
        target = out / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    today = date.today().isoformat()
    urls = "".join(
        f"<url><loc>{e(abs_url('' if p == 'index.html' else p))}</loc><lastmod>{today}</lastmod></url>"
        for p in pages if p != "404.html" and not p.startswith("after/")
    )
    if wreck()["status"] == "preorder":
        (out / "wreck-release.ics").write_text(wreck_ics())
    manifest = {"name": "Ashley Claudy", "short_name": "Ashley Claudy", "description": SITE["tagline"], "start_url": "/index.html",
                "display": "standalone", "background_color": "#09090b", "theme_color": "#09090b",
                "icons": [{"src": "assets/icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
                          {"src": "assets/icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"}]}
    (out / "manifest.webmanifest").write_text(json.dumps(manifest, indent=2))
    (out / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
    (out / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {abs_url('sitemap.xml')}\n")
    (out / "_redirects").write_text("".join(f"{old} {new} 301\n" for old, new in OLD_URLS.items())
                                    + "/after/:slug /after/:slug.html 200\n/arc /arc.html 200\n/privacy /privacy.html 200\n")
    htaccess = ["ErrorDocument 404 /404.html", "RewriteEngine On"]
    for old, new in OLD_URLS.items():
        pattern = "^" + old.lstrip("/").rstrip("/") + "/?$"
        htaccess.append(f"RewriteRule {pattern} {new} [R=301,L,NE]")
    htaccess += ["RewriteRule ^after/([a-z0-9-]+)/?$ /after/$1.html [L]", "RewriteRule ^arc/?$ /arc.html [L]", "RewriteRule ^privacy/?$ /privacy.html [L]"]
    (out / ".htaccess").write_text("\n".join(htaccess) + "\n")
    return sorted(pages)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default=str(ROOT / "dist"))
    args = parser.parse_args()
    built = build(Path(args.out).resolve())
    print(f"Built {len(built)} pages into {args.out}")
    for p in built:
        print("  " + p)


if __name__ == "__main__":
    main()
