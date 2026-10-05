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
- [x] Fan features: "Which kind of trouble are you?" quiz (`quiz.html`, `content/quiz.json`), click-to-load social feed, trailer/audio/playlist/character blocks, reader quotes, Wreck calendar reminders
- [x] Generated trailers (12s, 1080x1920), story images, and thumbnails for every book (`node tools/make-trailers.js`)
- [x] Creators & press hub (`creators.html`): kit downloads, captions, review-copy request, press facts
- [x] Five search-targeted genre pages (`content/genres.json`) with FAQ structured data
- [x] Home-screen icons and manifest, quiz-match personalization
- [x] Sales/retention tools: after-the-book pages (`/after/<book>`), regional Amazon links with channel tracking IDs, signup segmentation fields, privacy page and consent gating, ARC page, sale-day banner, release mode, star ratings, reaction form (see README), welcome-email drafts in `emails/`

## Before launch, verify
- [ ] TikTok figure on the site is "1.6M likes" (profile also shows ~9.8K followers). Re-check it before launch; it lives in `content/site.json` under `proof`
- [ ] Ride and Wreck are enrolled in Kindle Unlimited (the site says "Read free in Kindle Unlimited")
- [ ] `@ayclaudy` is still the right Instagram account
- [ ] The Amazon Associates tag `ashlclau-20` is still active (if the account was closed, set `"amazon_affiliate_tag": ""`)
- [ ] The contact email in `site.json` is the one to publish
- [ ] MailerLite: paste the bonus-chapters embedded-form action URL into `site.json` as `mailerlite_form_action`, then rebuild (until then, signups bounce to SubscribePage)
- [ ] The bonus chapters in the MailerLite welcome email match what the site promises
- [ ] Fill in `plausible_domain` / `ga4_id` / `meta_pixel_id` in `site.json` as needed

## Setup for the new sales tools (needs Cherie/Ashley's accounts)
- [ ] MailerLite: create the custom fields listed in README (`quiz_result`, `signup_source`, `book`, `utm_*`, `arc`, `review_link`, `platforms`), then build the welcome automation from `emails/welcome-series.md` with one branch per `quiz_result`
- [ ] Amazon Associates: create tracking IDs for `tiktok`, `instagram`, `facebook`, `email`, `ads` and add them to `site.json` → `amazon_tracking_ids`; add store IDs for UK, Canada, Australia, etc. to `amazon_tags` if she has them
- [ ] Add `https://ashleyclaudy.com/after/<book>` (and the ARC link) to the back matter of every ebook and paperback
- [ ] Use `?utm_source=...` on every link posted to TikTok, Instagram, Facebook, email, and ads
- [ ] Privacy policy: have it reviewed before launch; add its URL to the Meta and TikTok ad accounts
- [ ] Collect permissioned reader quotes (the after-book "share a line" form sends them by email), paste them into `content/fan.json` → `fan_wall` or a book's `quotes`
- [ ] For a sale (Countdown Deal, BookBub feature): fill `site.json` → `promo`, rebuild, deploy

## Content upgrades (when available)
- [x] Social feed live with her top TikTok posts (add more with `python3 tools/add-post.py`)
- [ ] Confirm the like counts for two posts: link `7147325034946678059` (shown, no likes yet) and `7188492021064060202` (hidden One Tree Hill clip). They were listed as 55.4K and 53.8K but the captions and links were swapped
- [ ] Decide whether to show the three TV-clip posts (One Tree Hill x2, House of the Dragon); they are saved but hidden because they aren't about her books
- [ ] Replace the TikTok Linktree (linktr.ee/ashleyclaudy) with `ashleyclaudy.com/links.html` once the domain is live
- [ ] Audiobook samples: only after written OK from Podium / Tantor, then add `audio_sample` in `books.json`
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
