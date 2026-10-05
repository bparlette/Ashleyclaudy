#!/usr/bin/env python3
"""Build ashleyclaudy.com from content/*.json into a static folder.

    python3 build.py                 # writes dist/
    python3 build.py --out somewhere/else
"""
import argparse
import html
import json
import shutil
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CURRENT = ' aria-current="page"'
MARKER = ".ashleyclaudy-build"

SITE = json.loads((ROOT / "content/site.json").read_text())
CATALOG = json.loads((ROOT / "content/books.json").read_text())
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


def out_link(url, label, store, book="", cls="link"):
    return (f'<a class="{cls}" href="{e(url)}" target="_blank" rel="noopener" '
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


def header(r, current=""):
    items = [("books.html", "Books")]
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


def socials():
    items = "".join(
        f'<li><a href="{e(s["url"])}" target="_blank" rel="noopener" data-track="social-{e(s["name"].lower())}">'
        f'{e(s["name"])} <small>{e(s["handle"])}</small></a></li>'
        for s in SITE["social"]
    )
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
      <a href="{r}bonus.html">Bonus chapters</a>
      <a href="{r}books.html#where-to-buy">Where to buy</a>
      <a href="{r}links.html">Links</a>
      <a href="{r}index.html#about">About</a>
    </nav>
    <div class="fine-col">
      <p class="fine">As an Amazon Associate I earn from qualifying purchases.</p>
      <p class="fine">© {year} Ashley Claudy. All rights reserved.</p>
    </div>
  </div>
  <div class="big-mark" aria-hidden="true"><span>Ashley</span><span>Claudy</span></div>
</footer>"""


def crew_form(form_id):
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
      <p class="signup-error" role="alert" hidden></p>
      <p class="signup-note">Free. Unsubscribe anytime. Your email is never shared.</p>
    </form>
    <div class="signup-done" role="status" hidden>
      <p class="done-title">You're on the Crew.</p>
      <p>Your bonus chapters are on the way. If the email isn't in your inbox in a few minutes, check Promotions or Spam and move it to your main inbox so you don't miss the Wreck cover reveal.</p>
      <div class="row">
        <a class="btn btn-line btn-sm" href="{e(social_url("TikTok"))}" target="_blank" rel="noopener" data-track="social-tiktok">Follow on TikTok</a>
        <a class="btn btn-line btn-sm" href="{e(social_url("Facebook"))}" target="_blank" rel="noopener" data-track="social-facebook">Follow on Facebook</a>
      </div>
    </div>
  </div>"""


def crew(form_id, headline=None):
    nl = SITE["newsletter"]
    perks = "".join(f"<li>{e(p)}</li>" for p in nl["perks"])
    headline = headline or 'Get the bonus chapters. <span class="serif">Free.</span>'
    return f"""<div class="crew">
  <div class="crew-copy">
    <p class="kicker">Join the Crew</p>
    <h2>{headline}</h2>
    <p class="lede">{e(nl["crew_line"])}</p>
  </div>
  {crew_form(form_id)}
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


def page(path, title, description, body, *, image="og/home.jpg", jsonld=None, solo=False, current="", theme="blue", dock=None):
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
<meta property="og:image" content="{e(abs_url("assets/" + image))}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{e(abs_url("assets/" + image))}">
<meta name="theme-color" content="#09090b">
<link rel="icon" href="{r}assets/favicon.svg" type="image/svg+xml">
<link rel="preload" href="{r}assets/fonts/bricolage-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{r}assets/fonts/inter-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{r}assets/css/site.css">
<script>document.documentElement.classList.add("js")</script>
{analytics()}
{ld}"""
    chrome_top = "" if solo else header(r, current)
    chrome_bottom = "" if solo else footer(r) + join_modal()
    dock_markup = dock_html(dock) if dock else ""
    body_class = f"t-{theme}" + (" has-dock" if dock else "")
    content = f"""{chrome_top}
<main id="main">
{body}
</main>
{chrome_bottom}
{dock_markup}
{ml_frame}
<script src="{r}assets/js/site.js" defer></script>"""

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


# ---------- pages ----------

def build_home():
    r = ""
    ride = BOOKS["ride"]
    w = wreck()
    lead, accent_words = split_tagline(ride["tagline"])
    nbsp_words = accent_words.replace(" ", "&nbsp;")

    pill = ""
    if w["status"] == "preorder":
        pill = (f'<a class="pill hero-pill" href="books/wreck.html"><span class="dot"></span>'
                f'<span>Wreck drops {e(release_short(w))} · <b><span data-days-until="{e(w["release_iso"])}">{days_left(w)}</span> days</b></span></a>')
    hero = f"""<section class="hero t-blue" aria-labelledby="hero-title">
  {hero_bg("assets/covers/ride.jpg")}
  <div class="wrap hero-in">
    {pill}
    <div class="hero-cover"><a data-tilt href="books/ride.html"><img class="cover-art" src="assets/covers/ride.jpg" alt="Ride by Ashley Claudy, cover" width="324" height="500" fetchpriority="high"></a></div>
    <div class="hero-copy">
      <p class="kicker">Crowns &amp; Chaos · Book 1 · Out now</p>
      <h1 id="hero-title"><span class="sr-only">Ride by Ashley Claudy: </span>{e(lead)} <span class="serif">{nbsp_words}</span></h1>
      <p class="lede">{e(ride['hook'])}</p>
      <div class="cta-row" data-dock-watch>
        {out_link(amazon(ride['kindle_asin']), f"Read free in Kindle Unlimited {ARROW}", "kindle", "ride", "btn btn-glow")}
        {out_link(kindle_sample(ride['kindle_asin']), "Read the first chapters", "sample", "ride", "btn btn-line")}
      </div>
      <ul class="proof-row">
        <li>{STAR}<b>{e(ride['proof'])}</b></li>
        <li>{ride['pages']} pages</li>
      </ul>
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
      {contact}
    </div>
  </div>
</section>"""

    body = hero + trope_marquee() + shelf + preorder + join + about
    dock = {"label": short_cta(ride), "url": amazon(ride["kindle_asin"]), "store": "kindle-dock", "book": "ride", "sec": "#join"}
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
        return (f'<a href="{e(url)}" target="_blank" rel="noopener" data-track="{e(store)}" data-book="{e(slug)}">'
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
    proof = f'<p class="bk-proof">{STAR}{e(book["proof"])}</p>' if book.get("proof") else ""

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
      </div>
      <div class="getmore">{"".join(more)}</div>
    </div>
  </div>
</section>
<section class="section" style="padding-top:clamp(24px,5vw,56px)">
  <div class="wrap story">
    <div class="col">
      <div class="blurb reveal">{blurb}</div>
      {tags}
      {note}
    </div>
    <div class="col col-b reveal">
      {spec}
      {quotes}
      {strip}
    </div>
  </div>
</section>
<section class="section" id="join" aria-label="Join the Crew" data-dock-watch style="padding-top:0"><div class="wrap reveal">{crew("book", join_headline)}</div></section>
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
    attrs = (f' target="_blank" rel="noopener" data-track="{e(store)}" data-book="{e(book)}"' if external else "")
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
