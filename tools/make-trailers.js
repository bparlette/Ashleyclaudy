// Generates a 12-second, 1080x1920 trailer (assets/video/<slug>.mp4), a poster, and a story still for each book
// from content/books.json: real hook, tropes, tagline and cover. Needs Node, Playwright, and ffmpeg.
//   node tools/make-trailers.js                 # all books
//   node tools/make-trailers.js ride,wreck      # only some
// Then run python3 build.py.
const path = require('path');
const fs = require('fs');
const os = require('os');
const { execFileSync } = require('child_process');
let chromium;
try { ({ chromium } = require('playwright')); } catch (e) { ({ chromium } = require(require('child_process').execSync('npm root -g').toString().trim() + '/playwright')); }

const ROOT = path.resolve(__dirname, '..');
const data = JSON.parse(fs.readFileSync(path.join(ROOT, 'content/books.json')));
const GLOW = { blue: ['#3ec1ff', '62,193,255'], ember: ['#ff6a3d', '255,106,61'], gold: ['#ffb627', '255,182,39'], red: ['#ff3b4a', '255,59,74'], violet: ['#b98cff', '185,140,255'] };
const seriesName = Object.fromEntries(data.series.map(s => [s.id, s.name]));
const only = (process.argv[2] || '').split(',').filter(Boolean);
const FPS = 30, DUR = 12;

function beats(hook) {
  const out = [];
  hook.split(/(?<=[.!?])\s+/).forEach(s => {
    s = s.trim();
    if (s.length > 70 && s.includes(', ')) {
      const i = s.indexOf(', ', Math.floor(s.length / 3));
      if (i > 0) { out.push(s.slice(0, i + 1)); out.push(s.slice(i + 2)); return; }
    }
    out.push(s);
  });
  return out.slice(0, 3);
}

function page(b) {
  const [g, rgb] = GLOW[b.accent];
  const kicker = (b.series === 'standalones' ? 'Standalone' : `${seriesName[b.series]} · Book ${b.number}`).toUpperCase();
  const cta = b.status === 'preorder' ? 'Preorder on Kindle' : (b.kindle_unlimited ? 'Read free in Kindle Unlimited' : 'Buy on Kindle');
  const tropes = b.tropes.filter(t => !/^(Standalone|Preorder|Series finale|Book \d)/.test(t) && !t.includes('#')).slice(0, 4);
  const spec = { beats: beats(b.hook), tropes, tagline: b.tagline, kicker, cta, proof: b.proof || '', preorder: b.status === 'preorder', released: b.released };
  return `<!doctype html><meta charset=utf-8><style>
@font-face{font-family:B;src:url(file://${ROOT}/assets/fonts/bricolage-normal.woff2);font-weight:400 800}
@font-face{font-family:I;src:url(file://${ROOT}/assets/fonts/inter-normal.woff2);font-weight:400 700}
@font-face{font-family:S;src:url(file://${ROOT}/assets/fonts/instrument-italic.woff2);font-style:italic}
*{box-sizing:border-box;margin:0}
html,body{width:540px;height:960px;background:#09090b;overflow:hidden;color:#f5f2ee;font-family:I}
#stage{position:relative;width:540px;height:960px;overflow:hidden;--g:${g}}
.bg{position:absolute;left:-30%;top:-10%;width:160%;height:120%;object-fit:cover;filter:blur(36px) saturate(1.7) brightness(.55)}
.shade{position:absolute;inset:0;background:radial-gradient(80% 50% at 50% 38%,rgba(${rgb},.34),transparent 70%),linear-gradient(180deg,rgba(9,9,11,.5),rgba(9,9,11,.15) 40%,rgba(9,9,11,.85))}
.grain{position:absolute;inset:-40px;opacity:.12;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")}
.kicker{position:absolute;left:0;right:0;top:128px;text-align:center;font:600 13px/1 I;letter-spacing:.26em;color:var(--g);white-space:nowrap}
.hook{position:absolute;left:36px;right:36px;top:250px;height:430px;display:flex;align-items:center;justify-content:center;text-align:center}
.beat{position:absolute;left:0;right:0;font:800 50px/1.02 B;letter-spacing:-.04em}
.beat .w{display:inline-block;margin:0 .13em}
.beat .em{font:italic 400 1.1em/1 S;color:var(--g);letter-spacing:-.01em}
.coverwrap{position:absolute;left:50%;top:150px;width:290px;margin-left:-145px;perspective:900px}
.cover{display:block;width:100%;border-radius:8px;box-shadow:0 50px 90px -20px rgba(${rgb},.75),0 26px 50px rgba(0,0,0,.7),0 0 0 1px rgba(255,255,255,.12)}
.chips{position:absolute;left:30px;right:30px;top:640px;display:flex;flex-wrap:wrap;gap:10px;justify-content:center}
.chip{padding:10px 16px;border-radius:99px;border:1px solid rgba(255,255,255,.3);background:rgba(9,9,11,.55);font:600 15px/1 I;backdrop-filter:blur(6px)}
.tag{position:absolute;left:40px;right:40px;top:536px;text-align:center;font:italic 400 38px/1.08 S}
.end{position:absolute;left:0;right:0;top:700px;display:flex;flex-direction:column;align-items:center;gap:14px}
.pill{height:54px;padding:0 28px;display:flex;align-items:center;border-radius:99px;background:var(--g);color:#05080b;font:700 19px/1 I;box-shadow:0 18px 44px -12px rgba(${rgb},.9)}
.url{font:600 15px/1 I;letter-spacing:.06em;color:#f5f2ee}
.bio{font:600 13px/1 I;letter-spacing:.2em;text-transform:uppercase;color:#a9a6b0}
.proof{font:500 14px/1 I;color:#a9a6b0}
</style>
<div id=stage><img class=bg src="file://${ROOT}/assets/covers/${b.cover}"><div class=shade></div><div class=grain></div>
<div class=kicker id=kicker></div><div class=hook id=hook></div>
<div class=coverwrap id=cw><img class=cover src="file://${ROOT}/assets/covers/${b.cover}"></div>
<div class=chips id=chips></div><div class=tag id=tag></div>
<div class=end id=end></div></div>
<script>
const S=${JSON.stringify(spec)};
const E='cubic-bezier(.2,.7,.2,1)';
function an(el,kf,start,dur,ease){const a=el.animate(kf,{duration:dur*1000,delay:start*1000,fill:'both',easing:ease||E});a.pause();return a}
const $=id=>document.getElementById(id);
function kf(el,pts){const T=${DUR};const frames=pts.map(([t,css])=>Object.assign({offset:Math.min(1,t/T)},css));
  const a=el.animate(frames,{duration:T*1000,fill:'both',easing:'linear'});a.pause();return a}
// background drift + grain jitter
an(document.querySelector('.bg'),[{transform:'scale(1.0) translateY(0)'},{transform:'scale(1.22) translateY(-18px)'}],0,${DUR},'linear');
an(document.querySelector('.grain'),[{transform:'translate(0,0)'},{transform:'translate(-40px,30px)'}],0,${DUR},'steps(24)');
// kicker
$('kicker').textContent=S.kicker;
kf($('kicker'),[[0,{opacity:0}],[0.15,{opacity:0}],[1.2,{opacity:1}],[5.9,{opacity:1}],[6.3,{opacity:0}],[10.6,{opacity:0}],[11.1,{opacity:1}],[12,{opacity:1}]]);
// hook beats
const t0=1.5,t1=6.2,L=(t1-t0)/S.beats.length;
S.beats.forEach((txt,i)=>{
  const el=document.createElement('div');el.className='beat';$('hook').appendChild(el);
  const words=txt.split(' ');
  words.forEach((w,j)=>{const s=document.createElement('span');s.className='w'+(j>=words.length-2?' em':'');s.textContent=w;el.appendChild(s);
    an(s,[{opacity:0,transform:'scale(1.35) translateY(14px)',filter:'blur(8px)'},{opacity:1,transform:'none',filter:'blur(0)'}],t0+i*L+j*0.11,0.42);});
  an(el,[{opacity:1},{opacity:0}],t0+(i+1)*L-0.32,0.3);
});
// cover reveal
const cw=$('cw');
const E1='translateY(160px) rotateY(-32deg) scale(.86)',E2='translateY(0) rotateY(-4deg) scale(1)',E3='translateY(-32px) rotateY(0deg) scale(.7)';
kf(cw,[[0,{opacity:0,transform:E1}],[6.0,{opacity:0,transform:E1}],[6.9,{opacity:1,transform:E2}],[9.2,{opacity:1,transform:E2}],[9.9,{opacity:1,transform:E3}],[12,{opacity:1,transform:E3}]]);
const fl=document.createElement('div');fl.style.cssText='position:absolute;inset:0;background:radial-gradient(60% 40% at 50% 38%,#fff,'+getComputedStyle($('stage')).getPropertyValue('--g')+' 40%,transparent 75%);pointer-events:none';$('stage').appendChild(fl);
kf(fl,[[0,{opacity:0}],[6.0,{opacity:0}],[6.12,{opacity:.55}],[6.7,{opacity:0}],[12,{opacity:0}]]);
S.tropes.forEach((t,i)=>{const c=document.createElement('div');c.className='chip';c.textContent=t;$('chips').appendChild(c);
  const st=7.0+i*0.32;
  kf(c,[[0,{opacity:0,transform:'translateY(30px) scale(.9)'}],[st,{opacity:0,transform:'translateY(30px) scale(.9)'}],[st+0.45,{opacity:1,transform:'none'}],[9.0,{opacity:1,transform:'none'}],[9.3,{opacity:0,transform:'none'}],[12,{opacity:0,transform:'none'}]]);});
// tagline
$('tag').textContent=S.tagline;
an($('tag'),[{opacity:0,transform:'translateY(24px)'},{opacity:1,transform:'none'}],9.4,0.6);
// end card
$('end').innerHTML='<div class=pill>'+S.cta+'</div><div class=url>ashleyclaudy.com · link in bio</div>'+(S.preorder?'<div class=proof>Out '+S.released+'</div>':(S.proof?'<div class=proof>★ '+S.proof+'</div>':''));
[...$('end').children].forEach((c,i)=>an(c,[{opacity:0,transform:'translateY(26px)'},{opacity:1,transform:'none'}],10.4+i*0.18,0.5));
window.seek=t=>{document.getAnimations().forEach(a=>{a.pause();a.currentTime=t*1000})};
</script>`;
}

(async () => {
  const br = await chromium.launch({ args: ['--allow-file-access-from-files'] });
  const outDir = path.join(ROOT, 'assets/video'); fs.mkdirSync(outDir, { recursive: true });
  for (const b of data.books) {
    if (only.length && !only.includes(b.slug)) continue;
    const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'trailer-'));
    const html = path.join(tmp, 't.html'); fs.writeFileSync(html, page(b));
    const ctx = await br.newContext({ viewport: { width: 540, height: 960 }, deviceScaleFactor: 2 });
    const pg = await ctx.newPage();
    await pg.goto('file://' + html); await pg.evaluate(() => document.fonts.ready); await pg.waitForTimeout(400);
    if (process.env.PREVIEW) {
      for (const t of [0.9, 3.0, 5.2, 7.0, 8.6, 10.0, 11.6]) {
        await pg.evaluate(x => window.seek(x), t);
        await pg.screenshot({ path: path.join(process.env.PREVIEW, `${b.slug}-${t}.jpg`), type: 'jpeg', quality: 85 });
      }
      await ctx.close(); fs.rmSync(tmp, { recursive: true, force: true }); continue;
    }
    const stills = async () => {
      await pg.evaluate(t => window.seek(t), 11.6);
      await pg.screenshot({ path: path.join(outDir, `${b.slug}-story.jpg`), type: 'jpeg', quality: 90 });
      await pg.evaluate(t => window.seek(t), 8.8);
      await pg.screenshot({ path: path.join(tmp, 'poster.jpg'), type: 'jpeg', quality: 90 });
      execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-i', path.join(tmp, 'poster.jpg'), '-vf', 'scale=540:-1', '-q:v', '4', path.join(outDir, `${b.slug}.jpg`)]);
    };
    if (process.env.STILLS) {
      await stills();
      await ctx.close(); fs.rmSync(tmp, { recursive: true, force: true });
      console.log('stills', b.slug);
      continue;
    }
    const frames = FPS * DUR;
    for (let i = 0; i < frames; i++) {
      await pg.evaluate(t => window.seek(t), i / FPS);
      await pg.screenshot({ path: path.join(tmp, `f${String(i).padStart(4, '0')}.jpg`), type: 'jpeg', quality: 90 });
    }
    await stills();
    execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-framerate', String(FPS), '-i', path.join(tmp, 'f%04d.jpg'),
      '-c:v', 'libx264', '-preset', 'slow', '-crf', '27', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-an',
      path.join(outDir, `${b.slug}.mp4`)]);
    fs.rmSync(tmp, { recursive: true, force: true });
    await ctx.close();
    console.log('trailer', b.slug, (fs.statSync(path.join(outDir, `${b.slug}.mp4`)).size / 1e6).toFixed(1) + ' MB');
  }
  await br.close();
})();
