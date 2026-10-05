#!/usr/bin/env python3
"""Build ashleyclaudy.com from content/*.json into a static folder.

    python3 build.py                 # writes dist/
    python3 build.py --out somewhere/else
"""
import argparse
import html
import json
import shutil
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CURRENT = ' aria-current="page"'
MARKER = ".ashleyclaudy-build"
FONTS = (
    "https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300..900;1,9..144,300..900"
    "&family=Inter:wght@400;500;600;700;800&display=swap"
)

SITE = json.loads((ROOT / "content/site.json").read_text())
CATALOG = json.loads((ROOT / "content/books.json").read_text())
BOOKS = {b["slug"]: b for b in CATALOG["books"]}
SERIES = {s["id"]: s for s in CATALOG["series"]}

# Curated entry points for each reading mood on the home page.
WORLDS = [
    ("ride", "Street racers & motorcycle clubs",
     "Underground races, a sponsor's off-limits little sister, and brothers who won't take it well.",
     "Start with Ride"),
    ("hustle", "College football",
     "A fresh start at a school where football players are royalty, and the king won't leave her alone.",
     "Start with Hustle"),
    ("outside-the-ropes", "Boxing & danger",
     "A foster-care survivor who fights for money, a tattooed star boxer, and trouble she can't punch her way out of.",
     "Start the trilogy"),
    ("it-goes-on", "Secrets & money",
     "A brand-new family, a world of wealth and lies, and a one-night stand who refuses to stay one night.",
     "Start with It Goes On"),
]

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


def out_link(url, label, store, book="", cls="text-link"):
    return (f'<a class="{cls}" href="{e(url)}" target="_blank" rel="noopener" '
            f'data-track="{e(store)}" data-book="{e(book)}">{label}</a>')


def kindle_label(book):
    if book["status"] == "preorder":
        return "Preorder on Kindle"
    return "Read free in Kindle Unlimited" if book.get("kindle_unlimited") else "Buy on Kindle"


def series_label(book):
    if book["series"] == "standalones":
        return "Standalone"
    return f'{SERIES[book["series"]]["name"]} · Book {book["number"]}'


def formats(book):
    out = ["Kindle"]
    if book.get("paperback"):
        out.append("Paperback")
    if book.get("audiobook"):
        out.append("Audiobook")
    return " · ".join(out)


# ---------- analytics ----------

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
            f'<script async src="https://www.googletagmanager.com/gtag/js?id={gid}"></script>\n'
            f"<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{gid}');</script>"
        )
    if a.get("meta_pixel_id"):
        pid = e(a["meta_pixel_id"])
        parts.append(
            "<script>!function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?"
            "n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;"
            "n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];"
            "s.parentNode.insertBefore(t,s)}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');"
            f"fbq('init','{pid}');fbq('track','PageView');</script>"
        )
    return "\n".join(parts)


def wreck():
    return BOOKS["wreck"]


# ---------- icons ----------

ICONS = {
    "tiktok": '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M16.6 3c.4 2.3 1.9 3.8 4.4 4v3.1c-1.6 0-3-.5-4.4-1.4v6.5c0 3.9-2.6 6.3-6.1 6.3-3.4 0-6-2.6-6-6 0-3.5 2.8-6.1 6.4-6 .4 0 .8 0 1.1.1v3.3c-.4-.2-.8-.2-1.2-.2-1.7 0-2.9 1.2-2.9 2.8 0 1.6 1.2 2.8 2.8 2.8 1.7 0 2.8-1.2 2.8-3V3h3.1z"/></svg>',
    "instagram": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="2.5" y="2.5" width="19" height="19" rx="5.5"/><circle cx="12" cy="12" r="4.2"/><circle cx="17.6" cy="6.4" r="1.4" fill="currentColor" stroke="none"/></svg>',
    "facebook": '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M13.5 21v-7h2.4l.4-3h-2.8V9.1c0-.9.3-1.5 1.6-1.5h1.3V4.9c-.3 0-1.2-.1-2.2-.1-2.2 0-3.7 1.3-3.7 3.8V11H8v3h2.5v7h3z"/></svg>',
    "goodreads": '<svg viewBox="0 0 24 24" aria-hidden="true"><text x="12" y="17.5" text-anchor="middle" font-family="Georgia,serif" font-size="15" font-weight="700" fill="currentColor">g</text></svg>',
    "amazon": '<svg viewBox="0 0 24 24" aria-hidden="true"><text x="12" y="14" text-anchor="middle" font-family="Georgia,serif" font-size="13" font-weight="700" fill="currentColor">a</text><path d="M4 16.5c3.5 2.6 8 4 12.5 3.2" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><path d="M17.8 17.2l2.6 1.1-2.9.9z" fill="currentColor"/></svg>',
    "share": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="6" cy="12" r="2.5"/><circle cx="18" cy="6" r="2.5"/><circle cx="18" cy="18" r="2.5"/><path d="M8.2 10.8l7.6-3.6M8.2 13.2l7.6 3.6"/></svg>',
}


def social_icon(name):
    return ICONS.get(name.lower(), ICONS["share"])


# ---------- shared chrome ----------

def announce(r):
    w = wreck()
    if w["status"] != "preorder":
        return ""
    return (f'<div class="announce"><div class="wrap"><span class="dot" aria-hidden="true"></span>'
            f'<span>Wreck<span class="hide-sm"> · Crowns &amp; Chaos Book 2</span> · Out {e(w["released"])}</span> '
            f'<a href="{r}books/wreck.html">Preorder now</a></div></div>')


def header(r, current=""):
    items = [("books.html", "Books"), ("index.html#reading-order", "Reading order"), ("index.html#about", "About")]
    links = "".join(
        f'<a href="{r}{href}"{CURRENT if href == current else ""}>{label}</a>'
        for href, label in items
    )
    cta = f'<a class="btn btn-primary btn-sm" href="{r}bonus.html" data-open-join>Free bonus chapters</a>'
    overlay_links = "".join(
        f'<a href="{r}{href}">{label}</a>' for href, label in items
    )
    return f"""<a class="skip" href="#main">Skip to content</a>
{announce(r)}
<header class="site-head">
  <div class="head-row">
    <a class="logo" href="{r}index.html">Ashley <em>Claudy</em></a>
    <nav class="nav" aria-label="Main">{links}{cta}</nav>
    <button class="menu-btn" type="button" data-menu-btn aria-label="Open menu" aria-expanded="false">
      <span></span><span></span><span></span>
    </button>
  </div>
</header>
<div class="menu-overlay" aria-hidden="false">
  <nav aria-label="Menu">{overlay_links}</nav>
  <a class="btn btn-primary" href="{r}bonus.html" data-open-join>Free bonus chapters</a>
</div>"""


def footer(r):
    year = date.today().year
    return f"""<footer class="site-foot">
  <div class="wrap foot-grid">
    <a class="logo" href="{r}index.html">Ashley <em>Claudy</em></a>
    <nav class="foot-nav" aria-label="Footer">
      <a href="{r}books.html">Books</a>
      <a href="{r}index.html#reading-order">Reading order</a>
      <a href="{r}bonus.html">Bonus chapters</a>
      <a href="{r}books.html#where-to-buy">Where to buy</a>
      <a href="{r}links.html">Links</a>
      <a href="{r}index.html#about">About</a>
    </nav>
    <p class="fine">As an Amazon Associate I earn from qualifying purchases.</p>
    <p class="fine">© {year} Ashley Claudy. All rights reserved.</p>
  </div>
</footer>"""


def socials(cls="socials"):
    items = "".join(
        f'<li><a href="{e(s["url"])}" target="_blank" rel="noopener" data-track="social-{e(s["name"].lower())}">'
        f'{social_icon(s["name"])}<span><b>{e(s["name"])}</b><small>{e(s["handle"])}</small></span></a></li>'
        for s in SITE["social"]
    )
    return f'<ul class="{cls}">{items}</ul>'


def social_url(name):
    for s in SITE["social"]:
        if s["name"].lower() == name.lower():
            return s["url"]
    return SITE["amazon_author_url"]


def share_btn(title, text, url, label="Share"):
    return (f'<button class="share-btn" type="button" data-share data-share-title="{e(title)}" '
            f'data-share-text="{e(text)}" data-share-url="{e(url)}">{ICONS["share"]}<span>{e(label)}</span></button>')


def crew_pass(form_id, title=None, pitch=None):
    nl = SITE["newsletter"]
    action = nl.get("mailerlite_form_action", "")
    perks = "".join(f"<li>{e(p)}</li>" for p in nl["perks"])
    return f"""<div class="signup-card">
  <p class="kicker">Crew pass · Free</p>
  <h3>{e(title or nl["magnet_title"])}</h3>
  <p class="lead" style="font-size:1rem">{e(pitch or nl["magnet_pitch"])}</p>
  <ul class="perks">{perks}</ul>
  <form class="signup" data-signup="{e(form_id)}" method="post" data-action="{e(action)}" data-fallback="{e(nl["fallback_url"])}" novalidate style="margin-top:22px">
    <div class="field"><label for="{form_id}-name">First name</label><input id="{form_id}-name" name="fields[name]" autocomplete="given-name" placeholder="Optional"></div>
    <div class="field"><label for="{form_id}-email">Email</label><input id="{form_id}-email" name="fields[email]" type="email" autocomplete="email" placeholder="you@example.com" required></div>
    <input type="hidden" name="ml-submit" value="1">
    <input type="hidden" name="anticsrf" value="true">
    <p class="signup-error" role="alert" hidden></p>
    <button class="btn btn-primary btn-block" type="submit">Send my bonus chapters <span class="arrow" aria-hidden="true">→</span></button>
    <p class="signup-note">Unsubscribe anytime. Your email is never shared.</p>
  </form>
  <div class="signup-done" role="status" hidden>
    <p class="display" style="font-size:1.6rem;margin:0 0 8px">You're on the Crew.</p>
    <p style="color:var(--paper-dim)">Your bonus chapters are on the way. Check Promotions or Spam if they don't land in a few minutes — and don't miss the Wreck cover reveal.</p>
    <div class="btn-row">
      <a class="btn btn-ghost btn-sm" href="{e(social_url("TikTok"))}" target="_blank" rel="noopener" data-track="social-tiktok">Follow on TikTok</a>
      <a class="btn btn-ghost btn-sm" href="{e(social_url("Instagram"))}" target="_blank" rel="noopener" data-track="social-instagram">Follow on Instagram</a>
    </div>
  </div>
</div>"""


def join_modal():
    return f"""<dialog class="join-modal" id="join-modal" aria-label="Get free bonus chapters">
  <div class="signup-card">
    <button class="modal-close" type="button" data-close aria-label="Close">×</button>
    {crew_pass("modal")}
  </div>
</dialog>"""


def buybar(r, book):
    label = kindle_label(book)
    sub = book.get("proof") or series_label(book)
    return f"""<div class="buybar" data-buybar>
  <img src="{r}assets/covers/{e(book['cover'])}" alt="" width="40" height="60">
  <div class="bb-text"><b>{e(book['title'])}</b><small><span class="stars" aria-hidden="true">★</span> {e(sub)}</small></div>
  {out_link(amazon(book['kindle_asin']), e(label), "kindle-buybar", book['slug'], "btn btn-primary btn-sm")}
</div>"""


def page(path, title, description, body, *, image="ride.jpg", jsonld=None, solo=False, current="", buybar_book=None):
    r = "/" if path == "404.html" else "../" * path.count("/")
    canonical = abs_url("" if path == "index.html" else path)
    ld = "".join(
        '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False).replace("</", "<\\/") + "</script>"
        for obj in (jsonld or [])
    )
    ml_frame = ('<iframe name="ml-frame" title="Newsletter signup" hidden></iframe>'
                if SITE["newsletter"].get("mailerlite_form_action") else "")
    head = f"""<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{e(canonical)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Ashley Claudy">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{e(canonical)}">
<meta property="og:image" content="{e(abs_url("assets/covers/" + image))}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0a0a0d">
<link rel="icon" href="{r}assets/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="{r}assets/css/site.css">
{analytics()}
{ld}"""
    chrome_top = "" if solo else header(r, current)
    chrome_bottom = "" if solo else footer(r) + join_modal()
    bar = buybar(r, buybar_book) if buybar_book else ""
    content = f"""{chrome_top}
<main id="main">
{body}
</main>
{chrome_bottom}
{bar}
{ml_frame}
<script src="{r}assets/js/site.js" defer></script>"""

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
{head}
</head>
<body>
{content}
</body>
</html>
"""


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

def chips(tropes, limit=None):
    items = tropes[:limit] if limit else tropes
    return '<ul class="chips">' + "".join(f'<li class="chip">{e(t)}</li>' for t in items) + "</ul>"


def countdown(book, done_id):
    return f"""<div class="countdown" data-countdown="{e(book['release_iso'])}" data-countdown-done="#{done_id}" aria-label="Time until release">
  <div class="count-cell"><span class="count-num" data-unit="d">--</span><span class="count-unit">Days</span></div>
  <div class="count-cell"><span class="count-num" data-unit="h">--</span><span class="count-unit">Hours</span></div>
  <div class="count-cell"><span class="count-num" data-unit="m">--</span><span class="count-unit">Min</span></div>
  <div class="count-cell"><span class="count-num" data-unit="s">--</span><span class="count-unit">Sec</span></div>
</div>
<p class="lead" id="{done_id}" hidden>Out now on Kindle.</p>"""


def ticker():
    seen, tropes = set(), []
    for b in CATALOG["books"]:
        for t in b["tropes"]:
            if t.lower() not in seen:
                seen.add(t.lower())
                tropes.append(t)
    items = "".join(f"<span>{e(t)}</span>" for t in tropes)
    return f'<div class="ticker" aria-hidden="true"><div class="ticker-track">{items}{items}</div></div>'


def rail_card(book, r, delay=""):
    href = f"{r}books/{book['slug']}.html"
    return f"""<a class="rail-card reveal {delay}" href="{href}">
  <div class="rail-cover"><img src="{r}assets/covers/{e(book['cover'])}" alt="{e(book['title'])} by Ashley Claudy, cover" width="300" height="450" loading="lazy"></div>
  <div class="rail-body">
    <p class="kicker c-{book['accent']}" style="margin-bottom:8px">{e(series_label(book))}</p>
    <h3>{e(book['title'])}</h3>
    <p>{e(book['hook'])}</p>
    <span class="rail-cta c-{book['accent']}">Read now →</span>
  </div>
</a>"""


def stats():
    items = "".join(
        f'<div class="stat reveal"><div class="stat-figure" data-countup>{e(p["figure"])}</div><div class="stat-label">{e(p["label"])}</div></div>'
        for p in SITE["proof"]
    )
    return f'<div class="stats">{items}</div>'


def reading_order(r):
    items = []
    for i, s in enumerate(CATALOG["series"]):
        rows = []
        for slug in s["books"]:
            b = BOOKS[slug]
            num = b["number"] if b["number"] else "·"
            meta = "Preorder" if b["status"] == "preorder" else b["released"].split()[-1]
            rows.append(
                f'<li><a href="{r}books/{slug}.html"><span class="acc-num">{num}</span>'
                f'<span class="t">{e(b["title"])}</span><span class="m">{e(meta)}</span><span class="go" aria-hidden="true">→</span></a></li>'
            )
        tag = "Start anywhere" if s["id"] == "standalones" else f"{len(s['books'])} books · Read in order"
        items.append(f"""<div class="acc-item" data-acc{" data-acc-open" if i == 0 else ""}>
  <button class="acc-head" type="button" data-acc-head aria-expanded="false">
    <span style="flex:1"><span class="acc-meta">{e(tag)}</span><h3>{e(s['name'])}</h3></span>
    <span class="acc-icon" aria-hidden="true">+</span>
  </button>
  <div class="acc-panel" data-acc-panel>
    <p class="lead" style="padding:0 4px">{e(s['pitch'])}</p>
    <ol class="acc-books">{"".join(rows)}</ol>
  </div>
</div>""")
    return f'<div class="acc">{"".join(items)}</div>'


# ---------- home ----------

def build_home():
    r = ""
    ride = BOOKS["ride"]
    w = wreck()

    hero = f"""<section class="hero" aria-labelledby="hero-title" data-buybar-sentinel>
  <div class="hero-bg" aria-hidden="true"><img src="assets/covers/ride.jpg" alt="" fetchpriority="high"></div>
  <div class="hero-scrim" aria-hidden="true"></div>
  <div class="wrap hero-inner">
    <div>
      <p class="kicker c-blue reveal">Crowns &amp; Chaos · Book 1 · Out now</p>
      <h1 class="hero-title reveal reveal-d1" id="hero-title">Ride</h1>
      <p class="hero-tag reveal reveal-d1"><em>{e(ride['tagline'])}</em></p>
      <p class="lead reveal reveal-d2">{e(ride['hook'])} Getting involved with his sponsor's little sister was never part of Weston Burke's plan.</p>
      <div class="hero-cta reveal reveal-d2">
        {out_link(amazon(ride['kindle_asin']), "Read free in Kindle Unlimited", "kindle", "ride", "btn btn-primary")}
        {out_link(kindle_sample(ride['kindle_asin']), "Read a sample", "sample", "ride", "btn btn-ghost")}
      </div>
      <p class="hero-proof reveal reveal-d3"><span class="stars" aria-hidden="true">★★★★☆</span><span>{e(ride['proof'])} · 556 pages · Also in paperback</span></p>
      <div class="hero-share reveal reveal-d3">{share_btn("Ride by Ashley Claudy", "Some rides are worth the crash. — Ride by Ashley Claudy", abs_url(), "Share this book")}</div>
    </div>
  </div>
  <div class="scroll-cue" aria-hidden="true">Scroll</div>
</section>"""

    preorder = ""
    if w["status"] == "preorder":
        preorder = f"""<section class="band preorder" aria-labelledby="wreck-title">
  <div class="wrap preorder-grid">
    <div class="preorder-cover reveal"><img src="assets/covers/wreck.jpg" alt="Wreck by Ashley Claudy — cover reveal coming soon" width="300" height="450" loading="lazy"></div>
    <div>
      <p class="kicker c-ember reveal">Crowns &amp; Chaos · Book 2 · Preorder</p>
      <h2 class="reveal reveal-d1" id="wreck-title">Wreck</h2>
      <p class="lead reveal reveal-d1">Lands on Kindle {e(w['released'])}. Preorder now and it's on your device at midnight on release day — no waiting, no spoilers.</p>
      <div class="reveal reveal-d2">{countdown(w, "wreck-out")}</div>
      <div class="btn-row reveal reveal-d2">
        {out_link(amazon(w['kindle_asin']), "Preorder Wreck", "kindle-preorder", "wreck", "btn btn-accent")}
        <a class="btn btn-ghost" href="bonus.html" data-open-join>See the cover first</a>
      </div>
      <p class="fine reveal reveal-d3">The cover reveal goes to the Crew newsletter before it goes anywhere else.</p>
    </div>
  </div>
</section>"""

    rail = "".join(rail_card(BOOKS[slug], r, f"reveal-d{i % 3}") for i, (slug, _, _, _) in enumerate(WORLDS))
    shelf = f"""<section class="band" aria-labelledby="shelf-title">
  <div class="wrap">
    <div class="section-head reveal">
      <p class="kicker">Find your next obsession</p>
      <h2 id="shelf-title">Pick your <em>poison</em></h2>
      <p class="lead">New Adult romance with real stakes. Choose the world that sounds like you and start there.</p>
    </div>
  </div>
  <div class="wrap"><div class="rail">{rail}</div>
  <p class="rail-hint"><span aria-hidden="true">←</span> Swipe <span aria-hidden="true">→</span></p></div>
</section>"""

    proof = f"""<section class="band-tight proof-band" aria-label="Reader proof">
  <div class="wrap">{stats()}</div>
</section>"""

    nl = SITE["newsletter"]
    join = f"""<section class="band crew" id="join" aria-labelledby="join-title">
  <div class="wrap crew-grid">
    <div class="reveal">
      <p class="kicker c-blue">Join the Crew</p>
      <h2 id="join-title">Get the chapters <em>nobody</em> else gets</h2>
      <p class="lead">{e(nl['crew_line'])}</p>
      <p class="lead" style="margin-top:14px">Follow along for teasers, cover reveals, and release-day chaos:</p>
      <div style="margin-top:6px">{socials()}</div>
    </div>
    <div class="reveal reveal-d1">{crew_pass("home")}</div>
  </div>
</section>"""

    order = f"""<section class="band" id="reading-order" aria-labelledby="order-title">
  <div class="wrap">
    <div class="section-head reveal">
      <p class="kicker">Reading order</p>
      <h2 id="order-title">Where to <em>start</em></h2>
      <p class="lead">Every ebook is on Amazon and free with Kindle Unlimited. Paperbacks and audiobooks available too.</p>
    </div>
    <div class="reveal">{reading_order(r)}</div>
  </div>
</section>"""

    photo = SITE.get("author_photo")
    portrait = (f'<img class="about-photo" src="{e(photo)}" alt="Ashley Claudy" loading="lazy">' if photo
                else '<div class="monogram" aria-hidden="true">AC</div>')
    bio = "".join(f"<p>{e(p)}</p>" for p in SITE["bio"])
    email = SITE.get("contact_email", "")
    contact = (f"""<div class="copy-row"><span>Rights, interviews, collaborations:</span>
      <code>{e(email)}</code><button class="btn btn-ghost btn-sm" type="button" data-copy="{e(email)}">Copy email</button></div>""" if email else "")
    about = f"""<section class="band" id="about" aria-labelledby="about-title" style="background:var(--ink-2);border-top:1px solid var(--line)">
  <div class="wrap about-grid">
    <div class="reveal">{portrait}</div>
    <div class="reveal reveal-d1">
      <p class="kicker">About the author</p>
      <h2 id="about-title">Ashley Claudy</h2>
      <div class="lead">{bio}</div>
      {socials()}
      {contact}
    </div>
  </div>
</section>"""

    body = hero + ticker() + preorder + shelf + proof + join + order + about
    return page("index.html", "Ashley Claudy · New Adult Romance Author", SITE["meta_description"], body,
                image="ride.jpg", jsonld=[person_ld()], buybar_book=ride)


# ---------- books page ----------

def build_books():
    r = ""
    blocks = []
    for s in CATALOG["series"]:
        cards = "".join(rail_card(BOOKS[slug], r) for slug in s["books"])
        box = ""
        if s.get("box_set"):
            bs = s["box_set"]
            box = f"""<div class="boxset reveal">
  <img src="assets/covers/{e(bs['cover'])}" alt="{e(bs['title'])}, cover" width="110" height="165" loading="lazy">
  <div>
    <p class="kicker c-{s['accent']}" style="margin-bottom:8px">Binge it</p>
    <h3 style="margin-bottom:8px">{e(bs['title'])}</h3>
    <p class="lead" style="font-size:.95rem">All three books in one download — {bs['pages']:,} pages. No waiting on cliffhangers.</p>
    <div class="btn-row">{out_link(amazon(bs['asin']), "Get the box set", "kindle-boxset", s['id'], "btn btn-primary btn-sm")}</div>
  </div>
</div>"""
        series_link = ""
        if s.get("amazon_series_asin"):
            series_link = f'<p>{out_link(amazon(s["amazon_series_asin"]), "See the whole series on Amazon →", "amazon-series", s["id"])}</p>'
        blocks.append(f"""<div class="series-block a-{s['accent']}" id="{s['id']}">
  <div class="section-head reveal" style="margin-bottom:26px">
    <p class="kicker c-{s['accent']}">{"Standalones" if s["id"] == "standalones" else "Series"}</p>
    <h2 id="{s['id']}-title">{e(s['name'])}</h2>
    <p class="lead">{e(s['pitch'])}</p>
    {series_link}
  </div>
  <div class="rail">{"".join(cards)}</div>
  {box}
</div>""")

    where = f"""<section class="band-tight" id="where-to-buy" aria-labelledby="where-title" style="border-top:1px solid var(--line)">
  <div class="wrap">
    <div class="section-head reveal">
      <p class="kicker">Where to buy</p>
      <h2 id="where-title">Ebooks, <em>paperbacks</em>, audio</h2>
    </div>
    <div class="stats reveal">
      <div class="stat"><h3 style="font-size:1.3rem">Ebooks</h3><p class="lead" style="font-size:.95rem">Exclusive to Amazon — buy there, or read free with Kindle Unlimited.</p>
        <p>{out_link("https://www.amazon.com/kindle-dbs/hz/subscribe/ku", "About Kindle Unlimited →", "ku-info")}</p></div>
      <div class="stat"><h3 style="font-size:1.3rem">No Kindle?</h3><p class="lead" style="font-size:.95rem">The free Kindle app works on any phone, tablet, or computer.</p>
        <p>{out_link("https://www.amazon.com/kindle-dbs/fd/kcp", "Get the free Kindle app →", "kindle-app")}</p></div>
      <div class="stat"><h3 style="font-size:1.3rem">Print &amp; audio</h3><p class="lead" style="font-size:.95rem">Paperbacks at Amazon, Barnes &amp; Noble, and bookstores — your library can order them. Audiobooks on Audible.</p></div>
    </div>
  </div>
</section>"""

    body = f"""<section class="band-tight">
  <div class="wrap">
    <div class="section-head reveal" style="padding-top:20px">
      <p class="kicker">All books</p>
      <h1 style="font-size:clamp(2.6rem,10vw,4.5rem)">The <em>books</em></h1>
      <p class="lead">Two series and two standalones — all New Adult romance, all free in Kindle Unlimited.</p>
    </div>
    {"".join(blocks)}
  </div>
</section>
{where}"""
    return page("books.html", "Books by Ashley Claudy · Reading Order",
                "Every Ashley Claudy book in reading order: Crowns & Chaos, Outside the Ropes, Hustle, and It Goes On. Read free in Kindle Unlimited.",
                body, image="ride.jpg", current="books.html")


# ---------- book detail page ----------

def build_book(book):
    r = "../"
    slug = book["slug"]
    s = SERIES[book["series"]]

    primary = out_link(amazon(book["kindle_asin"]), e(kindle_label(book)), "kindle", slug, "btn btn-primary btn-block")
    secondary = ""
    if book["status"] == "out":
        secondary = out_link(kindle_sample(book["kindle_asin"]), "Read a free sample", "sample", slug, "btn btn-ghost btn-block")
    more = []
    if book.get("paperback"):
        pb = book["paperback"]
        more.append(out_link(amazon(pb["asin"]), "Paperback", "paperback-amazon", slug))
        if pb.get("isbn13"):
            more.append(out_link(f"https://www.barnesandnoble.com/s/{pb['isbn13']}", "Barnes &amp; Noble", "paperback-bn", slug))
            more.append(out_link(f"https://bookshop.org/search?keywords={pb['isbn13']}", "Bookshop.org", "paperback-bookshop", slug))
    if book.get("audiobook"):
        more.append(out_link(book["audiobook"]["url"], "Audiobook", "audiobook", slug))
    more.append(out_link(book["goodreads"], "Add on Goodreads", "goodreads", slug))

    timer = ""
    if book["status"] == "preorder" and book.get("release_iso"):
        timer = countdown(book, f"{slug}-out")
    buy_note = ("Preorders download automatically on release day." if book["status"] == "preorder"
                else "Ebook exclusive to Amazon. Free to read with Kindle Unlimited." if book.get("kindle_unlimited")
                else "Ebook exclusive to Amazon.")
    buy = f"""<div class="buybox">
  {timer}
  <div class="btn-row" style="flex-direction:column">{primary}{secondary}</div>
  <p class="fine">{e(buy_note)}</p>
  <div class="buy-more">{"".join(more)}</div>
</div>"""

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
    note = ""
    if book.get("content_note"):
        note = f'<details class="note"><summary>Content note</summary><p>{e(book["content_note"])}</p></details>'
    quotes = ""
    if book.get("quotes"):
        quotes = '<div class="quotes">' + "".join(
            f'<blockquote><p>“{e(q["text"])}”</p><cite>{e(q["source"])}</cite></blockquote>' for q in book["quotes"]
        ) + "</div>"
    proof = ""
    if book.get("proof"):
        proof = f'<p class="hero-proof"><span class="stars" aria-hidden="true">★★★★☆</span><span>{e(book["proof"])}</span></p>'

    strip = ""
    if book["series"] != "standalones":
        thumbs = "".join(
            f'<a href="{other}.html"{CURRENT if other == slug else ""}>'
            f'<img src="{r}assets/covers/{e(BOOKS[other]["cover"])}" alt="{e(BOOKS[other]["title"])}, cover" width="120" height="180" loading="lazy">'
            f'<span>Book {BOOKS[other]["number"]} · {e(BOOKS[other]["title"])}</span></a>'
            for other in s["books"]
        )
        strip = f'<div style="margin-top:34px"><p class="kicker c-{s["accent"]}">Reading order</p><div class="strip">{thumbs}</div></div>'

    idx = s["books"].index(slug)
    next_up = []
    if book["series"] != "standalones" and idx + 1 < len(s["books"]):
        next_up.append(s["books"][idx + 1])
    for candidate in ["ride", "hustle", "outside-the-ropes", "it-goes-on"]:
        if candidate != slug and candidate not in next_up and BOOKS[candidate]["series"] != book["series"]:
            next_up.append(candidate)
    next_cards = "".join(rail_card(BOOKS[n], r) for n in next_up[:2])

    join_title = "See the Wreck cover first" if slug == "wreck" else None
    share = share_btn(f"{book['title']} by Ashley Claudy", f"{book['tagline']} — {book['title']} by Ashley Claudy", abs_url(f"books/{slug}.html"), "Share this book")
    body = f"""<section class="book-hero a-{book['accent']}" data-buybar-sentinel>
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="{r}books.html">Books</a><span aria-hidden="true">/</span><a href="{r}books.html#{s['id']}">{e(s['name'])}</a><span aria-hidden="true">/</span><span aria-current="page">{e(book['title'])}</span></nav>
    <div class="book-grid">
      <div class="book-cover reveal"><img src="{r}assets/covers/{e(book['cover'])}" alt="{e(book['title'])} by Ashley Claudy, cover" width="340" height="510" fetchpriority="high"></div>
      <div>
        <p class="kicker c-{book['accent']} reveal">{e(series_label(book))}</p>
        <h1 class="book-title reveal reveal-d1">{e(book['title'])}</h1>
        <p class="book-tag reveal reveal-d1"><em>{e(book['tagline'])}</em></p>
        <div class="reveal reveal-d2">{proof}</div>
        <div class="reveal reveal-d2">{buy}</div>
        <div class="reveal reveal-d2" style="display:flex;gap:12px;flex-wrap:wrap;align-items:center">{share}</div>
        {chips(book['tropes'])}
        <div class="blurb reveal">{blurb}</div>
        {note}
        {quotes}
        <div class="reveal">{spec}</div>
        <div class="reveal">{strip}</div>
      </div>
    </div>
  </div>
</section>
<section class="band crew" aria-labelledby="join-title">
  <div class="wrap crew-grid">
    <div class="reveal">
      <p class="kicker c-{book['accent']}">Join the Crew</p>
      <h2 id="join-title">Bonus chapters, <em>free</em></h2>
      <p class="lead">{e(SITE['newsletter']['crew_line'])}</p>
    </div>
    <div class="reveal reveal-d1">{crew_pass("book", title=join_title)}</div>
  </div>
</section>
<section class="band-tight" aria-labelledby="next-title">
  <div class="wrap">
    <div class="section-head reveal"><p class="kicker">Read next</p><h2 id="next-title">Keep <em>going</em></h2></div>
    <div class="rail">{next_cards}</div>
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
    return page(f"books/{slug}.html", title, desc, body, image=book["cover"], jsonld=[ld_book], buybar_book=book)


# ---------- bonus / links / 404 ----------

def build_bonus():
    covers = "".join(
        f'<img src="assets/covers/{e(BOOKS[s]["cover"])}" alt="" width="64" height="96" loading="lazy">'
        for s in ["ride", "hustle", "outside-the-ropes"]
    )
    body = f"""<section class="solo">
  <div class="wrap"><div class="solo-inner">
    <div class="links-head">
      <a class="logo" href="index.html">Ashley <em>Claudy</em></a>
      <p class="kicker" style="justify-content:center;margin-top:12px">Street racers · fighters · football players</p>
    </div>
    <div class="mini-covers" aria-hidden="true">{covers}</div>
    {crew_pass("bonus")}
    <p class="fine"><a href="books.html">Browse the books</a> · <a href="index.html">Home</a></p>
  </div></div>
</section>"""
    return page("bonus.html", "Free Bonus Chapters · Ashley Claudy",
                "Join Ashley Claudy's Crew newsletter for free bonus chapters, the Wreck cover reveal, and ARC invites.",
                body, solo=True)


def build_links():
    w, ride, hustle = wreck(), BOOKS["ride"], BOOKS["hustle"]
    rows = []
    if w["status"] == "preorder":
        rows.append(f'{out_link(amazon(w["kindle_asin"]), f"Preorder Wreck <small>Crowns &amp; Chaos #2 · {e(w["released"])} · lands on your Kindle at midnight</small>", "kindle-preorder", "wreck", "btn btn-accent")}')
    rows.append(f'{out_link(amazon(ride["kindle_asin"]), "Read Ride free <small>Kindle Unlimited · Crowns &amp; Chaos #1</small>", "kindle", "ride", "btn btn-primary")}')
    rows.append('<a class="btn btn-ghost" href="bonus.html">Free bonus chapters <small>Join the Crew — cover reveals first</small></a>')
    if hustle.get("audiobook"):
        rows.append(f'{out_link(hustle["audiobook"]["url"], "Hustle audiobook <small>Listen on Audible</small>", "audiobook", "hustle", "btn btn-ghost")}')
    rows.append('<a class="btn btn-ghost" href="books.html">All books <small>Reading order</small></a>')
    covers = "".join(
        f'<img src="assets/covers/{e(BOOKS[s]["cover"])}" alt="" width="64" height="96" loading="lazy">' for s in ["ride", "wreck", "hustle"]
    )
    body = f"""<section class="solo">
  <div class="wrap"><div class="solo-inner">
    <div class="links-head">
      <a class="logo" href="index.html">Ashley <em>Claudy</em></a>
      <p class="lead" style="font-size:.95rem;margin-top:10px">{e(SITE['tagline'])}</p>
    </div>
    <div class="mini-covers" aria-hidden="true">{covers}</div>
    <div class="link-stack">{"".join(rows)}</div>
    {socials()}
  </div></div>
</section>"""
    return page("links.html", "Links · Ashley Claudy", "Every Ashley Claudy link in one place.", body, solo=True)


def build_404():
    body = """<section class="e404"><div class="wrap">
  <p class="kicker" style="justify-content:center">404</p>
  <h1>Wrong <em>turn</em></h1>
  <p class="lead" style="margin-inline:auto">That page doesn't exist anymore. The books are still here.</p>
  <div class="btn-row" style="justify-content:center"><a class="btn btn-primary" href="/books.html">See the books</a><a class="btn btn-ghost" href="/">Home</a></div>
</div></section>"""
    return page("404.html", "Page not found · Ashley Claudy", "This page doesn't exist.", body)


FAVICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#0a0a0d"/><text x="32" y="43" text-anchor="middle" font-family="Georgia,serif" font-size="30" font-weight="700" fill="#f6f1e7" letter-spacing="1">AC</text></svg>
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
        "404.html": build_404(),
    }
    for book in CATALOG["books"]:
        pages[f"books/{book['slug']}.html"] = build_book(book)
    for path, text in pages.items():
        target = out / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    today = date.today().isoformat()
    urls = "".join(
        f"<url><loc>{e(abs_url('' if p == 'index.html' else p))}</loc><lastmod>{today}</lastmod></url>"
        for p in pages if p != "404.html"
    )
    (out / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
    (out / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {abs_url('sitemap.xml')}\n")
    (out / "_redirects").write_text("".join(f"{old} {new} 301\n" for old, new in OLD_URLS.items()))
    htaccess = ["ErrorDocument 404 /404.html", "RewriteEngine On"]
    for old, new in OLD_URLS.items():
        pattern = "^" + old.lstrip("/").rstrip("/") + "/?$"
        htaccess.append(f"RewriteRule {pattern} {new} [R=301,L,NE]")
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
