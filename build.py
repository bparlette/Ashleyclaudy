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
    "https://fonts.googleapis.com/css2?family=Barlow:ital,wght@0,400;0,500;0,600;1,400"
    "&family=Barlow+Condensed:wght@500;600;700"
    "&family=Big+Shoulders+Display:wght@700;800;900"
    "&family=Tilt+Neon&display=swap"
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


def announce(r):
    w = wreck()
    if w["status"] != "preorder":
        return ""
    return (f'<div class="announce"><div class="wrap">Wreck<span class="hide-sm"> · Crowns &amp; Chaos Book 2</span> · Out {e(w["released"])} · '
            f'<a href="{r}books/wreck.html">Preorder now</a></div></div>')


def header(r, current=""):
    items = [("books.html", "Books"), ("index.html#reading-order", "Reading order"), ("index.html#about", "About")]
    links = "".join(
        f'<a href="{r}{href}"{CURRENT if href == current else ""}>{label}</a>'
        for href, label in items
    )
    cta = f'<a class="btn btn-primary btn-sm" href="{r}bonus.html" data-open-join>Free bonus chapters</a>'
    return f"""<a class="skip" href="#main">Skip to content</a>
{announce(r)}
<header class="site-head a-blue">
  <div class="wrap head-row">
    <a class="logo" href="{r}index.html">Ashley Claudy</a>
    <nav class="nav" aria-label="Main">{links}{cta}</nav>
    <details class="menu">
      <summary>Menu</summary>
      <nav class="menu-panel" aria-label="Menu">{links}{cta}</nav>
    </details>
  </div>
</header>"""


def footer(r):
    year = date.today().year
    return f"""<footer class="site-foot">
  <div class="wrap foot-grid">
    <a class="logo" href="{r}index.html">Ashley Claudy</a>
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
        f'<b>{e(s["name"])}</b><small>{e(s["handle"])}</small></a></li>'
        for s in SITE["social"]
    )
    return f'<ul class="{cls}">{items}</ul>'


def social_url(name):
    for s in SITE["social"]:
        if s["name"].lower() == name.lower():
            return s["url"]
    return SITE["amazon_author_url"]


def crew_pass(form_id, accent="a-blue", title=None, pitch=None):
    nl = SITE["newsletter"]
    action = nl.get("mailerlite_form_action", "")
    perks = "".join(f"<li>{e(p)}</li>" for p in nl["perks"])
    return f"""<div class="pass {accent}">
  <div class="pass-head"><span class="eyebrow">Crew pass</span><span class="pass-tag">Free</span></div>
  <h2 class="pass-title">{e(title or nl["magnet_title"])}</h2>
  <div class="pass-body">
    <p>{e(pitch or nl["magnet_pitch"])}</p>
    <ul class="perks">{perks}</ul>
    <form class="signup" data-signup="{e(form_id)}" method="post" data-action="{e(action)}" data-fallback="{e(nl["fallback_url"])}" novalidate>
      <div class="signup-row">
        <div class="field"><label for="{form_id}-name">First name</label><input id="{form_id}-name" name="fields[name]" autocomplete="given-name" placeholder="Optional"></div>
        <div class="field"><label for="{form_id}-email">Email</label><input id="{form_id}-email" name="fields[email]" type="email" autocomplete="email" placeholder="you@example.com" required></div>
      </div>
      <input type="hidden" name="ml-submit" value="1">
      <input type="hidden" name="anticsrf" value="true">
      <p class="signup-error" role="alert" hidden></p>
      <button class="btn btn-primary" type="submit">Send my bonus chapters <span class="arrow" aria-hidden="true">→</span></button>
      <p class="signup-note">Unsubscribe anytime. Your email is never shared.</p>
    </form>
    <div class="signup-done" role="status" hidden>
      <p class="h3">You're on the Crew.</p>
      <p class="muted">Your bonus chapters are on the way. If the email isn't in your inbox in a few minutes, check Promotions or Spam and move it to your main inbox so you don't miss the Wreck cover reveal.</p>
      <div class="btn-row">
        <a class="btn btn-ghost btn-sm" href="{e(social_url("TikTok"))}" target="_blank" rel="noopener" data-track="social-tiktok">Follow on TikTok</a>
        <a class="btn btn-ghost btn-sm" href="{e(social_url("Facebook"))}" target="_blank" rel="noopener" data-track="social-facebook">Follow on Facebook</a>
      </div>
    </div>
  </div>
  <div class="barcode" aria-hidden="true"></div>
</div>"""


def join_modal():
    return f"""<dialog class="join-modal" id="join-modal" aria-label="Get free bonus chapters">
  <button class="modal-close" type="button" data-close aria-label="Close">×</button>
  {crew_pass("modal")}
</dialog>"""


def page(path, title, description, body, *, image="ride.jpg", jsonld=None, solo=False, current=""):
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
<meta name="twitter:card" content="summary">
<meta name="theme-color" content="#0b0c0f">
<link rel="icon" href="{r}assets/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="{r}assets/css/site.css">
{analytics()}
{ld}"""
    chrome_top = "" if solo else header(r, current)
    chrome_bottom = "" if solo else footer(r) + join_modal()
    content = f"""{chrome_top}
<main id="main">
{body}
</main>
{chrome_bottom}
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


def book_card(book, r):
    href = f"{r}books/{book['slug']}.html"
    return f"""<article class="card a-{book['accent']}">
  <a href="{href}" aria-hidden="true" tabindex="-1"><img src="{r}assets/covers/{e(book['cover'])}" alt="" width="132" height="200" loading="lazy"></a>
  <div class="card-body">
    <p class="eyebrow">{e(series_label(book))}</p>
    <h3 class="h3"><a href="{href}">{e(book['title'])}</a></h3>
    <p>{e(book['hook'])}</p>
    {chips(book['tropes'], 3)}
    <div class="btn-row">
      {out_link(amazon(book['kindle_asin']), e(kindle_label(book)), "kindle", book['slug'], "btn btn-primary btn-sm")}
      <a class="btn btn-ghost btn-sm" href="{href}">Details</a>
    </div>
  </div>
</article>"""


def countdown(book, done_id):
    return f"""<div class="board" data-countdown="{e(book['release_iso'])}" data-countdown-done="#{done_id}" aria-label="Time until release">
  <div class="board-cell"><span class="board-num" data-unit="d">--</span><span class="board-unit">Days</span></div>
  <div class="board-cell"><span class="board-num" data-unit="h">--</span><span class="board-unit">Hours</span></div>
  <div class="board-cell"><span class="board-num" data-unit="m">--</span><span class="board-unit">Min</span></div>
  <div class="board-cell"><span class="board-num" data-unit="s">--</span><span class="board-unit">Sec</span></div>
</div>
<p class="lead" id="{done_id}" hidden>Out now on Kindle.</p>"""


def reading_order(r):
    cols = []
    for s in CATALOG["series"]:
        rows = []
        for slug in s["books"]:
            b = BOOKS[slug]
            num = b["number"] if b["number"] else "·"
            meta = "Preorder" if b["status"] == "preorder" else b["released"].split()[-1]
            rows.append(
                f'<li><a href="{r}books/{slug}.html"><span class="order-num">{num}</span>'
                f'<span class="order-title">{e(b["title"])}</span><span class="order-meta">{e(meta)}</span></a></li>'
            )
        cols.append(f"""<div class="order-col a-{s['accent']}">
  <p class="eyebrow">{"Start anywhere" if s["id"] == "standalones" else "Read in order"}</p>
  <h3 class="h3">{e(s['name'])}</h3>
  <p>{e(s['pitch'])}</p>
  <ol class="order-list">{"".join(rows)}</ol>
</div>""")
    return f'<div class="order">{"".join(cols)}</div>'


# ---------- pages ----------

def build_home():
    r = ""
    ride = BOOKS["ride"]
    w = wreck()
    hero = f"""<section class="hero a-blue" aria-labelledby="hero-title">
  <div class="wrap hero-grid">
    <div class="hero-copy">
      <p class="eyebrow">Crowns &amp; Chaos · Book 1 · Out now</p>
      <h1 class="hero-title" id="hero-title"><span class="neon ignite">Ride</span><span class="sr-only"> by Ashley Claudy</span></h1>
      <p class="hero-tag">{e(ride['tagline'])}</p>
      <p class="lead">{e(ride['hook'])} Getting involved with his sponsor's little sister was never part of Weston Burke's plan.</p>
      <ul class="spec-inline"><li>{ride['pages']} pages</li><li>Standalone</li><li>Free in Kindle Unlimited</li></ul>
      <div class="btn-row">
        {out_link(amazon(ride['kindle_asin']), "Read free in Kindle Unlimited", "kindle", "ride", "btn btn-primary")}
        {out_link(kindle_sample(ride['kindle_asin']), "Read the first chapters", "sample", "ride", "btn btn-ghost")}
      </div>
      <p class="fine">Also in paperback · <a href="books/ride.html">Full blurb and tropes</a></p>
    </div>
    <a class="hero-cover cover-glow" href="books/ride.html"><img src="assets/covers/ride.jpg" alt="Ride by Ashley Claudy, cover" width="324" height="500" fetchpriority="high"></a>
  </div>
</section>"""

    preorder = ""
    if w["status"] == "preorder":
        preorder = f"""<section class="preorder band a-ember" aria-labelledby="wreck-title">
  <div class="wrap preorder-grid">
    <a class="cover-glow" href="books/wreck.html"><img src="assets/covers/wreck.jpg" alt="Wreck by Ashley Claudy, placeholder cover" width="333" height="500" loading="lazy"></a>
    <div class="preorder-copy">
      <p class="eyebrow">Crowns &amp; Chaos · Book 2 · Preorder</p>
      <h2 class="preorder-title" id="wreck-title"><span class="neon">Wreck</span></h2>
      <p class="lead">Lands on Kindle {e(w['released'])}. Preorder now and it shows up on your device on release day.</p>
      {countdown(w, "wreck-out")}
      <div class="btn-row">
        {out_link(amazon(w['kindle_asin']), "Preorder Wreck", "kindle-preorder", "wreck", "btn btn-primary")}
        <a class="btn btn-ghost" href="bonus.html" data-open-join>See the cover first</a>
      </div>
      <p class="fine">The cover reveal goes to the Crew newsletter before it goes anywhere else.</p>
    </div>
  </div>
</section>"""

    tiles = []
    for slug, label, pitch, cta in WORLDS:
        b = BOOKS[slug]
        tiles.append(f"""<a class="world a-{b['accent']}" href="books/{slug}.html">
  <img src="assets/covers/{e(b['cover'])}" alt="" width="112" height="170" loading="lazy">
  <div class="world-body">
    <p class="eyebrow">{e(label)}</p>
    <h3 class="h3">{e(b['title'])}</h3>
    <p>{e(pitch)}</p>
    {chips(b['tropes'], 3)}
    <span class="text-link">{e(cta)} →</span>
  </div>
</a>""")
    proof = "".join(
        f'<div class="proof-item"><span class="proof-figure">{e(p["figure"])}</span><span class="proof-label">{e(p["label"])}</span></div>'
        for p in SITE["proof"]
    )
    worlds = f"""<section class="band band-tarmac" aria-labelledby="worlds-title">
  <div class="wrap">
    <div class="section-head">
      <p class="eyebrow">Find your next obsession</p>
      <h2 class="h2" id="worlds-title">Pick your kind of trouble</h2>
      <p>Every book is New Adult romance with real stakes. Choose the world that sounds like you and start there.</p>
    </div>
    <div class="worlds">{"".join(tiles)}</div>
    <div class="proof" style="margin-top:clamp(40px,6vw,72px)">{proof}</div>
  </div>
</section>"""

    nl = SITE["newsletter"]
    join = f"""<section class="band a-blue" id="join" aria-labelledby="join-title">
  <div class="wrap join-grid">
    <div class="section-head" style="margin-bottom:0">
      <p class="eyebrow">Join the Crew</p>
      <h2 class="h2" id="join-title">Get the chapters nobody else gets</h2>
      <p>{e(nl['crew_line'])}</p>
    </div>
    {crew_pass("home")}
  </div>
</section>"""

    order = f"""<section class="band band-tarmac" id="reading-order" aria-labelledby="order-title">
  <div class="wrap">
    <div class="section-head">
      <p class="eyebrow">Reading order</p>
      <h2 class="h2" id="order-title">Where to start</h2>
      <p>Every ebook is on Amazon and free to read with Kindle Unlimited. Paperbacks and audiobooks are available too.</p>
    </div>
    {reading_order(r)}
  </div>
</section>"""

    photo = SITE.get("author_photo")
    portrait = (f'<img class="about-photo" src="{e(photo)}" alt="Ashley Claudy" loading="lazy">' if photo
                else '<div class="monogram" aria-hidden="true"><span class="neon">AC</span></div>')
    bio = "".join(f"<p>{e(p)}</p>" for p in SITE["bio"])
    email = SITE.get("contact_email", "")
    contact = (f"""<div class="copy-row"><span class="muted">Rights, interviews, and collaborations:</span>
      <code>{e(email)}</code><button class="btn btn-ghost btn-sm" type="button" data-copy="{e(email)}">Copy email</button></div>""" if email else "")
    about = f"""<section class="band a-blue" id="about" aria-labelledby="about-title">
  <div class="wrap about-grid">
    {portrait}
    <div class="about-copy">
      <p class="eyebrow">About the author</p>
      <h2 class="h2" id="about-title">Ashley Claudy</h2>
      {bio}
      {socials()}
      {contact}
    </div>
  </div>
</section>"""

    body = hero + preorder + worlds + join + order + about
    return page("index.html", "Ashley Claudy · New Adult Romance Author", SITE["meta_description"], body,
                image="ride.jpg", jsonld=[person_ld()])


def build_books():
    r = ""
    blocks = []
    for s in CATALOG["series"]:
        cards = "".join(book_card(BOOKS[slug], r) for slug in s["books"])
        box = ""
        if s.get("box_set"):
            bs = s["box_set"]
            box = f"""<div class="boxset">
  <img src="assets/covers/{e(bs['cover'])}" alt="{e(bs['title'])}, cover" width="150" height="186" loading="lazy">
  <div>
    <p class="eyebrow">Binge it</p>
    <h3 class="h3">{e(bs['title'])}</h3>
    <p class="muted">All three books in one download, {bs['pages']:,} pages. No waiting on cliffhangers.</p>
    <div class="btn-row">{out_link(amazon(bs['asin']), "Get the box set", "kindle-boxset", s['id'], "btn btn-primary btn-sm")}</div>
  </div>
</div>"""
        series_link = ""
        if s.get("amazon_series_asin"):
            series_link = f'<p class="fine">{out_link(amazon(s["amazon_series_asin"]), "See the whole series on Amazon", "amazon-series", s["id"])}</p>'
        blocks.append(f"""<section class="series-block a-{s['accent']}" id="{s['id']}" aria-labelledby="{s['id']}-title">
  <div class="section-head" style="margin-bottom:0">
    <p class="eyebrow">{"Standalones" if s["id"] == "standalones" else "Series"}</p>
    <h2 class="h2" id="{s['id']}-title">{e(s['name'])}</h2>
    <p>{e(s['pitch'])}</p>
    {series_link}
  </div>
  <div class="cards">{cards}</div>
  {box}
</section>""")

    where = f"""<section class="band band-tarmac" id="where-to-buy" aria-labelledby="where-title">
  <div class="wrap">
    <div class="section-head">
      <p class="eyebrow">Where to buy</p>
      <h2 class="h2" id="where-title">Ebooks, paperbacks, audio</h2>
    </div>
    <div class="order">
      <div class="order-col a-blue"><h3 class="h3">Ebooks</h3><p>Ashley's ebooks are exclusive to Amazon. Buy them there, or read them free with a Kindle Unlimited subscription.</p>
        <p>{out_link("https://www.amazon.com/kindle-dbs/hz/subscribe/ku", "About Kindle Unlimited →", "ku-info")}</p></div>
      <div class="order-col a-gold"><h3 class="h3">No Kindle?</h3><p>The free Kindle app works on any phone, tablet, or computer. Download it, buy or borrow the book, and it appears in the app.</p>
        <p>{out_link("https://www.amazon.com/kindle-dbs/fd/kcp", "Get the free Kindle app →", "kindle-app")}</p></div>
      <div class="order-col a-red"><h3 class="h3">Print &amp; audio</h3><p>Paperbacks are sold at Amazon, Barnes &amp; Noble, and other bookstores, and your library can order them. Audiobooks are on Audible.</p></div>
    </div>
  </div>
</section>"""

    body = f"""<section class="band">
  <div class="wrap">
    <div class="section-head">
      <p class="eyebrow">All books</p>
      <h1 class="h2">The books</h1>
      <p>Two series and two standalones, all New Adult romance. Every ebook is free to read in Kindle Unlimited.</p>
    </div>
    {"".join(blocks)}
  </div>
</section>
{where}"""
    return page("books.html", "Books by Ashley Claudy · Reading Order",
                "Every Ashley Claudy book in reading order: Crowns & Chaos, Outside the Ropes, Hustle, and It Goes On. Read free in Kindle Unlimited.",
                body, image="ride.jpg", current="books.html")


def build_book(book):
    r = "../"
    slug = book["slug"]
    s = SERIES[book["series"]]
    acc = f"a-{book['accent']}"

    primary = out_link(amazon(book["kindle_asin"]), e(kindle_label(book)), "kindle", slug, "btn btn-primary")
    secondary = ""
    if book["status"] == "out":
        secondary = out_link(kindle_sample(book["kindle_asin"]), "Read a free sample", "sample", slug, "btn btn-ghost")
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
    buy = f"""<div class="buy">
  {timer}
  <div class="btn-row">{primary}{secondary}</div>
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
    proof = f'<p class="eyebrow">{e(book["proof"])}</p>' if book.get("proof") else ""

    strip = ""
    if book["series"] != "standalones":
        thumbs = "".join(
            f'<a href="{other}.html"{CURRENT if other == slug else ""}>'
            f'<img src="{r}assets/covers/{e(BOOKS[other]["cover"])}" alt="" width="92" height="140" loading="lazy">'
            f'Book {BOOKS[other]["number"]} · {e(BOOKS[other]["title"])}</a>'
            for other in s["books"]
        )
        strip = f'<div class="series-strip"><p class="eyebrow">{e(s["name"])} reading order</p><div class="strip">{thumbs}</div></div>'

    idx = s["books"].index(slug)
    next_up = []
    if book["series"] != "standalones" and idx + 1 < len(s["books"]):
        next_up.append(s["books"][idx + 1])
    for candidate in ["ride", "hustle", "outside-the-ropes", "it-goes-on"]:
        if candidate != slug and candidate not in next_up and BOOKS[candidate]["series"] != book["series"]:
            next_up.append(candidate)
    next_cards = "".join(book_card(BOOKS[n], r) for n in next_up[:2])

    join_title = "See the Wreck cover first" if slug == "wreck" else None
    body = f"""<section class="band {acc}" style="padding-top:clamp(28px,4vw,48px)">
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="{r}books.html">Books</a><span aria-hidden="true">/</span><a href="{r}books.html#{s['id']}">{e(s['name'])}</a><span aria-hidden="true">/</span><span aria-current="page">{e(book['title'])}</span></nav>
    <div class="book-grid">
      <div class="book-aside">
        <div class="cover-glow"><img src="{r}assets/covers/{e(book['cover'])}" alt="{e(book['title'])} by Ashley Claudy, cover" width="340" height="520"></div>
      </div>
      <div class="book-main">
        <p class="eyebrow">{e(series_label(book))}</p>
        <h1 class="book-title">{e(book['title'])}</h1>
        <p class="book-tag">{e(book['tagline'])}</p>
        {proof}
        {buy}
        {chips(book['tropes'])}
        <div class="blurb">{blurb}</div>
        {note}
        {quotes}
        {spec}
        {strip}
      </div>
    </div>
  </div>
</section>
<section class="band band-tarmac {acc}" aria-labelledby="join-title">
  <div class="wrap join-grid">
    <div class="section-head" style="margin-bottom:0">
      <p class="eyebrow">Join the Crew</p>
      <h2 class="h2" id="join-title">Bonus chapters, free</h2>
      <p>{e(SITE['newsletter']['crew_line'])}</p>
    </div>
    {crew_pass("book", acc, title=join_title)}
  </div>
</section>
<section class="band" aria-labelledby="next-title">
  <div class="wrap">
    <div class="section-head"><p class="eyebrow">Read next</p><h2 class="h2" id="next-title">Keep going</h2></div>
    <div class="cards">{next_cards}</div>
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
    return page(f"books/{slug}.html", title, desc, body, image=book["cover"], jsonld=[ld_book])


def build_bonus():
    covers = "".join(
        f'<img src="assets/covers/{e(BOOKS[s]["cover"])}" alt="" width="76" height="116">'
        for s in ["ride", "hustle", "outside-the-ropes"]
    )
    body = f"""<section class="solo wrap a-blue">
  <div class="solo-inner">
    <div class="links-head">
      <a class="logo" href="index.html">Ashley Claudy</a>
      <p class="eyebrow">Street racers · fighters · football players</p>
    </div>
    {crew_pass("bonus")}
    <div class="mini-covers" aria-hidden="true">{covers}</div>
    <p class="fine" style="text-align:center"><a href="books.html">Browse the books</a> · <a href="index.html">Home</a></p>
  </div>
</section>"""
    return page("bonus.html", "Free Bonus Chapters · Ashley Claudy",
                "Join Ashley Claudy's Crew newsletter for free bonus chapters, the Wreck cover reveal, and ARC invites.",
                body, solo=True)


def build_links():
    w, ride, hustle = wreck(), BOOKS["ride"], BOOKS["hustle"]
    rows = []
    if w["status"] == "preorder":
        label = f"Preorder Wreck <small>Crowns &amp; Chaos #2 · {e(w['released'])}</small>"
        rows.append(f'<div class="a-ember">{out_link(amazon(w["kindle_asin"]), label, "kindle-preorder", "wreck", "btn btn-primary")}</div>')
    rows.append(f'<div class="a-blue">{out_link(amazon(ride["kindle_asin"]), "Read Ride free <small>Kindle Unlimited</small>", "kindle", "ride", "btn btn-primary")}</div>')
    rows.append('<div class="a-blue"><a class="btn btn-ghost" href="bonus.html">Free bonus chapters <small>Join the Crew</small></a></div>')
    if hustle.get("audiobook"):
        rows.append(f'<div class="a-gold">{out_link(hustle["audiobook"]["url"], "Hustle audiobook <small>Audible</small>", "audiobook", "hustle", "btn btn-ghost")}</div>')
    rows.append('<div class="a-blue"><a class="btn btn-ghost" href="books.html">All books <small>Reading order</small></a></div>')
    covers = "".join(
        f'<img src="assets/covers/{e(BOOKS[s]["cover"])}" alt="" width="76" height="116">' for s in ["ride", "wreck", "hustle"]
    )
    body = f"""<section class="solo wrap a-blue">
  <div class="solo-inner">
    <div class="links-head">
      <a class="logo" href="index.html">Ashley Claudy</a>
      <p class="muted">{e(SITE['tagline'])}</p>
    </div>
    <div class="mini-covers" aria-hidden="true">{covers}</div>
    <div class="links">{"".join(rows)}</div>
    {socials()}
  </div>
</section>"""
    return page("links.html", "Links · Ashley Claudy", "Every Ashley Claudy link in one place.", body, solo=True)


def build_404():
    body = """<section class="band a-ember">
  <div class="wrap section-head">
    <p class="eyebrow">404</p>
    <h1 class="h2"><span class="neon">Wrong turn</span></h1>
    <p>That page doesn't exist anymore. The books are still here.</p>
    <div class="btn-row"><a class="btn btn-primary" href="/books.html">See the books</a><a class="btn btn-ghost" href="/">Home</a></div>
  </div>
</section>"""
    return page("404.html", "Page not found · Ashley Claudy", "This page doesn't exist.", body)


FAVICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="12" fill="#0b0c0f"/><text x="32" y="44" text-anchor="middle" font-family="Arial Narrow,Arial,sans-serif" font-weight="700" font-size="30" fill="#3fcfff" letter-spacing="1">AC</text></svg>
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
