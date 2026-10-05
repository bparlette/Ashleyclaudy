// Regenerates assets/og/*.jpg (1200x630 share cards). Needs Node and Playwright: npm i -g playwright && npx playwright install chromium
// Run from the repo root: node tools/make-share-cards.js, then python3 build.py
const path = require('path');
const fs = require('fs');
let chromium;
try { ({ chromium } = require('playwright')); } catch (e) { ({ chromium } = require(require('child_process').execSync('npm root -g').toString().trim() + '/playwright')); }
const ROOT = path.resolve(__dirname, '..');
const data = JSON.parse(fs.readFileSync(ROOT + '/content/books.json'));
const GLOW = { blue: ['#3ec1ff', '62,193,255'], ember: ['#ff6a3d', '255,106,61'], gold: ['#ffb627', '255,182,39'], red: ['#ff3b4a', '255,59,74'], violet: ['#b98cff', '185,140,255'] };
const seriesName = Object.fromEntries(data.series.map(s => [s.id, s.name]));
const fonts = `
@font-face{font-family:B;src:url(file://${ROOT}/assets/fonts/bricolage-normal.woff2);font-weight:400 800}
@font-face{font-family:I;src:url(file://${ROOT}/assets/fonts/inter-normal.woff2);font-weight:400 700}
@font-face{font-family:S;src:url(file://${ROOT}/assets/fonts/instrument-italic.woff2);font-style:italic}`;
const cover = f => `file://${ROOT}/assets/covers/${f}`;

function card({ accent, kicker, title, sub, cta, covers }) {
  const [g, rgb] = GLOW[accent];
  const big = covers[0];
  const tsize = title.length <= 6 ? 168 : title.length <= 11 ? 120 : title.length <= 18 ? 92 : 78;
  const stack = covers.length > 1
    ? `<img src="${cover(covers[1])}" style="position:absolute;left:40px;top:120px;height:430px;border-radius:8px;transform:rotate(-8deg);box-shadow:0 30px 60px rgba(0,0,0,.7)">
       <img src="${cover(covers[2])}" style="position:absolute;left:270px;top:100px;height:430px;border-radius:8px;transform:rotate(7deg);box-shadow:0 30px 60px rgba(0,0,0,.7)">
       <img src="${cover(big)}" style="position:absolute;left:150px;top:62px;height:500px;border-radius:8px;box-shadow:0 40px 80px rgba(0,0,0,.8),0 0 0 1px rgba(255,255,255,.12);z-index:2">`
    : `<img src="${cover(big)}" style="position:absolute;left:150px;top:62px;height:506px;border-radius:8px;transform:rotate(-3deg);box-shadow:0 50px 90px -20px rgba(${rgb},.7),0 24px 50px rgba(0,0,0,.7),0 0 0 1px rgba(255,255,255,.12)">`;
  return `<!doctype html><meta charset=utf-8><style>${fonts}
*{box-sizing:border-box}body{margin:0;width:1200px;height:630px;background:#09090b;position:relative;overflow:hidden;color:#f5f2ee;font-family:I}
.bg{position:absolute;left:-10%;top:-30%;width:120%;height:160%;object-fit:cover;filter:blur(70px) saturate(1.7) brightness(.55);opacity:.9}
.shade{position:absolute;inset:0;background:radial-gradient(70% 90% at 25% 40%,rgba(${rgb},.35),transparent 70%),linear-gradient(90deg,rgba(9,9,11,.0),rgba(9,9,11,.82) 52%,#09090b)}
.k{position:absolute;left:560px;top:96px;font:600 22px/1 I;letter-spacing:.2em;text-transform:uppercase;color:${g}}
.t{position:absolute;left:556px;top:140px;width:590px;font:800 ${tsize}px/.9 B;letter-spacing:-.045em}
.s{position:absolute;left:560px;bottom:150px;width:560px;font:italic 400 44px/1.1 S;color:#f5f2ee}
.c{position:absolute;left:560px;bottom:62px;height:62px;padding:0 26px;display:flex;align-items:center;border-radius:99px;background:${g};color:#05080b;font:650 22px I}
.u{position:absolute;right:40px;bottom:80px;font:500 20px I;color:#a9a6b0;letter-spacing:.02em}
</style><img class=bg src="${cover(big)}"><div class=shade></div>${stack}
<div class=k>${kicker}</div><div class=t>${title}</div><div class=s>${sub}</div><div class=c>${cta}</div><div class=u>ashleyclaudy.com</div>`;
}

const jobs = [];
const ride = data.books.find(b => b.slug === 'ride');
jobs.push(['home', { accent: 'blue', kicker: 'Ashley Claudy · New Adult Romance', title: 'Some rides are worth the crash.'.replace(/\./, ''), sub: 'Ride, Crowns & Chaos #1. Free in Kindle Unlimited.', cta: 'Read free in Kindle Unlimited', covers: ['ride.jpg'] }]);
jobs.push(['bonus', { accent: 'blue', kicker: 'The Crew · Free', title: 'Bonus chapters', sub: 'Plus the Wreck cover reveal, first.', cta: 'Join free at ashleyclaudy.com', covers: ['ride.jpg', 'hustle.jpg', 'outside-the-ropes.jpg'] }]);
jobs.push(['quiz', { accent: 'blue', kicker: 'The quiz', title: 'Which kind of trouble are you?', sub: 'Six questions. One book to start with.', cta: 'Take the quiz at ashleyclaudy.com', covers: ['ride.jpg', 'hustle.jpg', 'outside-the-ropes.jpg'] }]);
for (const b of data.books) {
  const kick = b.series === 'standalones' ? 'Standalone · Ashley Claudy' : `${seriesName[b.series]} · Book ${b.number}`;
  jobs.push([b.slug, { accent: b.accent, kicker: kick.toUpperCase(), title: b.title, sub: b.tagline, cta: b.status === 'preorder' ? 'Preorder on Kindle' : (b.kindle_unlimited ? 'Read free in Kindle Unlimited' : 'Buy on Kindle'), covers: [b.cover] }]);
}
(async () => {
  const br = await chromium.launch({ args: ['--allow-file-access-from-files'] });
  const pg = await br.newPage({ viewport: { width: 1200, height: 630 } });
  for (const [name, spec] of jobs) {
    const tmp = path.join(require('os').tmpdir(), 'og-card.html');
    fs.writeFileSync(tmp, card(spec));
    await pg.goto('file://' + tmp); await pg.evaluate(() => document.fonts.ready); await pg.waitForTimeout(250);
    await pg.screenshot({ path: `${ROOT}/assets/og/${name}.jpg`, type: 'jpeg', quality: 86 });
    console.log('made', name);
  }
  await br.close();
})();
