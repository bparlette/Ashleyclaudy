// Generates assets/icons/*.png (home-screen and PWA icons). Run: node tools/make-icons.js
const path = require('path');
const fs = require('fs');
let chromium;
try { ({ chromium } = require('playwright')); } catch (e) { ({ chromium } = require(require('child_process').execSync('npm root -g').toString().trim() + '/playwright')); }
const ROOT = path.resolve(__dirname, '..');
const svg = size => `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 512 512">
<defs><radialGradient id="g" cx="50%" cy="38%" r="70%"><stop offset="0" stop-color="#1b3a4a"/><stop offset="1" stop-color="#09090b"/></radialGradient>
<filter id="b" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="14"/></filter></defs>
<rect width="512" height="512" fill="url(#g)"/>
<path d="M256 120l120 136-120 136L136 256z" fill="#3ec1ff" opacity=".55" filter="url(#b)"/>
<path d="M256 120l120 136-120 136L136 256z" fill="#3ec1ff"/>
<path d="M256 186l56 70-56 70-56-70z" fill="#09090b"/></svg>`;
(async () => {
  const br = await chromium.launch();
  for (const [name, size] of [['icon-512', 512], ['icon-192', 192], ['apple-touch-icon', 180]]) {
    const pg = await br.newPage({ viewport: { width: size, height: size } });
    await pg.setContent(`<body style="margin:0">${svg(size)}</body>`);
    await pg.screenshot({ path: path.join(ROOT, 'assets/icons', name + '.png') });
    await pg.close();
    console.log('icon', name);
  }
  await br.close();
})();
