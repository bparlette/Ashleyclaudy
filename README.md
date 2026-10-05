# ashleyclaudy.com

Static author website for Ashley Claudy. No WordPress, no plugins, no database: plain HTML, CSS, and a little JavaScript, generated from two content files.

## Design notes

Cinematic, phone-first. Each book carries its own glow color (`accent` in `books.json`: blue, ember, gold, red, violet). Phones get a sticky buy bar that appears once the main buy button scrolls away and hides while the signup form is on screen. The exit popup only appears on desktop. Fonts (Bricolage Grotesque, Instrument Serif, Inter) are self-hosted in `assets/fonts/`, so there are no third-party font requests.

## Pages

| Page | Job |
|---|---|
| `index.html` | Home: Ride hero with one-tap buy, trope marquee, swipeable book shelf, Wreck countdown, newsletter signup, about |
| `books.html` | Every book by series, box set, where to buy |
| `books/<book>.html` | One sales page per book: buy buttons, free sample, tropes, blurb, content note, series order, newsletter |
| `bonus.html` | Distraction-free newsletter landing page. Use this URL in ads and the back matter of every book |
| `links.html` | Link-in-bio page for TikTok, Instagram, and Facebook |
| `404.html` | Not-found page |

The build also writes `sitemap.xml`, `robots.txt`, and 301 redirects from the old WordPress URLs (`_redirects` for Netlify, `.htaccess` for Bluehost) so existing Google rankings and old links keep working.

## See it on your computer

Open `dist/index.html` in any browser (double-click it). Nothing else is needed. To preview after edits: `python3 build.py`, then reopen it.

## Editing content

Everything lives in two files:

- `content/books.json`: titles, blurbs, tropes, Amazon IDs (ASINs), paperback ISBNs, audiobook links, Goodreads links, reader quotes
- `content/site.json`: bio, social links, newsletter settings, analytics IDs, Amazon affiliate tag

After editing, rebuild:

```bash
python3 build.py
```

This regenerates `dist/`, the folder that gets published. Python 3.9 or newer, no packages needed.

**Common edits**

- **Wreck cover reveal:** replace `assets/covers/wreck.jpg` with the real cover (same file name), update the Wreck `blurb`, `tropes`, and `hook` in `books.json`, rebuild.
- **Wreck release day:** change Wreck's `"status": "preorder"` to `"out"`. The announcement bar, countdown, and preorder band disappear on their own.
- **Reader quotes:** add real quotes to a book's `quotes` list: `{"text": "Couldn't put it down.", "source": "Goodreads reviewer"}`. Only use real reviews, with permission where needed.
- **Author photo:** put a square photo at `assets/img/ashley.jpg` and set `"author_photo": "assets/img/ashley.jpg"` in `site.json`.
- **Sharper covers:** the covers are 333 by 500 pixels. Drop in larger versions (around 1000 by 1500) with the same file names. Cover art is the one thing holding the design back, so sharper files make the biggest visual upgrade.
- **Share cards:** the 1200 by 630 images people see when a link is shared on Facebook, TikTok, iMessage, and X live in `assets/og/`. After changing a cover, title, or tagline, run `node tools/make-share-cards.js`, then rebuild.

## Turn on the built-in signup form (2 minutes)

Until this is set, signup forms send readers to the existing SubscribePage, where they type their email again. To subscribe readers without leaving the site:

1. In MailerLite, go to **Forms → Embedded forms**, open the bonus-chapters form (or create one that delivers the bonus chapters), and choose **HTML code**.
2. Copy the `action="..."` URL from the `<form>` tag. It looks like `https://assets.mailerlite.com/jsonp/123456/forms/987654321/subscribe`.
3. Paste it into `site.json` as `"mailerlite_form_action"` and rebuild.

## Tracking (for ads)

Fill in any of these in `site.json` and rebuild:

- `plausible_domain`: simple, privacy-friendly visitor stats
- `ga4_id`: Google Analytics 4 (`G-XXXXXXX`)
- `meta_pixel_id`: needed for Facebook and Instagram ads

The site reports three events to whichever tools are on: `Retailer Click` (with book and store), `Newsletter Signup`, and `Join Modal Shown`. Sales happen on Amazon, so `Retailer Click` is the event to optimize ads for.

## Deploying

**Netlify (recommended, free):**

1. Sign in at netlify.com with GitHub and choose **Add new site → Import an existing project → bparlette/ashleyclaudy**. Netlify reads `netlify.toml` and runs the build itself.
2. Under **Domain management**, add `ashleyclaudy.com` and follow Netlify's DNS steps where the domain is registered (currently Bluehost). HTTPS is automatic.
3. Every push to `main` redeploys the site.

**Keep Bluehost hosting instead:** run `python3 build.py`, then upload the contents of `dist/` (including the hidden `.htaccess`) to `public_html` with the Bluehost File Manager or FTP. Back up the WordPress install first.

## Before launch, verify

- [ ] Ride and Wreck are enrolled in Kindle Unlimited (the site says "Read free in Kindle Unlimited")
- [ ] `@ayclaudy` is still the right Instagram account
- [ ] The Amazon Associates tag `ashlclau-20` is still active. If the account was closed, set `"amazon_affiliate_tag": ""`
- [ ] The contact email in `site.json` is the one to publish
- [ ] The bonus chapters in the MailerLite welcome email match what the site promises
