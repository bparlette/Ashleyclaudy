# Ashley Claudy site — TODO

**Live previews**
- Winner (this branch): https://ashleyclaudy-cinematic.pages.dev
- Arlo's redesign: https://ashleyclaudy-redesign.pages.dev
- First design: https://ashleyclaudy-preview.pages.dev
- The real domain still serves the old WordPress site. **Do NOT cut over ashleyclaudy.com without Cherie's explicit approval.**

## Done
- [x] Static generator (`python3 build.py` → `dist/`); builds clean from a fresh clone, no packages needed (Python 3.9+)
- [x] Cinematic phone-first redesign on main (self-hosted fonts, sticky mobile buy bar, trope marquee, Wreck countdown, share buttons, share cards in `assets/og/`)
- [x] SEO: `sitemap.xml`, `robots.txt`, 301s from old WordPress URLs (`_redirects` + `.htaccess`)
- [x] Ad-event tracking hooks: `Retailer Click`, `Newsletter Signup`, `Join Modal Shown`

## Before launch, verify
- [ ] Ride and Wreck are enrolled in Kindle Unlimited (the site says "Read free in Kindle Unlimited")
- [ ] `@ayclaudy` is still the right Instagram account
- [ ] The Amazon Associates tag `ashlclau-20` is still active (if the account was closed, set `"amazon_affiliate_tag": ""`)
- [ ] The contact email in `site.json` is the one to publish
- [ ] MailerLite: paste the bonus-chapters embedded-form action URL into `site.json` as `mailerlite_form_action`, then rebuild (until then, signups bounce to SubscribePage)
- [ ] The bonus chapters in the MailerLite welcome email match what the site promises
- [ ] Fill in `plausible_domain` / `ga4_id` / `meta_pixel_id` in `site.json` as needed

## Content upgrades (when available)
- [ ] Wreck real cover: replace `assets/covers/wreck.jpg` (same file name), update `blurb`/`tropes`/`hook` in `content/books.json`, regen share cards (`node tools/make-share-cards.js`), rebuild
- [ ] Wreck release day (Dec 31, 2026): change Wreck's `"status"` from `"preorder"` to `"out"` in `books.json` (announcement bar, countdown, and preorder band disappear on their own)
- [ ] Sharper covers: current files are 333x500; drop in ~1000x1500 versions with the same file names
- [ ] Real reader quotes (with permission) into each book's `quotes` list
- [ ] Author photo: square file at `assets/img/ashley.jpg`, then set `author_photo` in `site.json`

## Working rules for this repo
- Multiple AIs edit this repo. Always check the latest commits before changing anything; **merge, never overwrite**.
- Rights: Ashley Claudy is the site owner's sister, and the owner (Cherie) is her authorized promotions/website team — quotes, excerpts, covers, and narration are approved for use here.
- Positioning: New Adult romantic suspense.
- Content edits go in `content/books.json` and `content/site.json`, then run `python3 build.py`. Never hand-edit `dist/`.
