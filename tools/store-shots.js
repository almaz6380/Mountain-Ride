// Store screenshots in every language: node tools/store-shots.js [lang ...]
// Needs a local server in the repo root (python3 -m http.server 8765) and Playwright (Chromium).
// Writes store/screenshots/<lang>/<device>-<n>.jpg and store/feature-graphic.png.
const fs = require('fs'), path = require('path');
const { chromium } = require(process.env.PLAYWRIGHT || 'playwright');
const root = path.resolve(__dirname, '..');
const BASE = 'http://127.0.0.1:8765/.preview/';
const LANGS = process.argv.slice(2).length ? process.argv.slice(2) : ['de', 'en', 'es', 'pt', 'fr', 'it', 'ru', 'zh', 'ja', 'ar'];
// App Store 6.9" iPhone (1290×2796) and Google Play phone (1080×1920)
const DEVICES = { ios: { width: 430, height: 932 }, android: { width: 360, height: 640 } };

// a preview copy with local libraries and a debug hook to steer the run
function makePreview() {
  let s = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
  s = s.replace('https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js', '../assets/lib/three.min.js')
    .replace('https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js', '../assets/lib/GLTFLoader.js')
    .replace('https://fonts.googleapis.com/css2?family=Bowlby+One+SC&family=Barlow+Condensed:wght@500;600;800&display=swap', '../assets/lib/fonts/fonts.css')
    .replace('"assets/lib/i18n.js"', '"../assets/lib/i18n.js"')
    .replace('  function render(dt) {', '  window.__dbg = { P: () => P, PW, ents: () => ents, addRamp, laneX, st: () => state, pop: popEl };\n  function render(dt) {');
  s = s.replace(/(['"])assets\//g, '$1../assets/');
  fs.mkdirSync(path.join(root, '.preview'), { recursive: true });
  fs.writeFileSync(path.join(root, '.preview', 'store.html'), s);
}

async function shoot(browser, lang, device) {
  const out = path.join(root, 'store', 'screenshots', lang);
  fs.mkdirSync(out, { recursive: true });
  let n = 0;
  const snap = async p => { n++; await p.screenshot({ path: path.join(out, `${device}-${n}.jpg`), type: 'jpeg', quality: 88 }); };
  const page = async loc => {
    const ctx = await browser.newContext({ viewport: DEVICES[device], deviceScaleFactor: 3, locale: lang, hasTouch: true, isMobile: true });
    await ctx.addInitScript(([l, loc]) => {
      localStorage.setItem('mountain-ride-tutorialDone', 'true');
      localStorage.setItem('mountain-ride-lang', l);
      localStorage.setItem('mountain-ride-wallet', '2450');
      localStorage.setItem('mountain-ride-best-3d', '18420');
      localStorage.setItem('mountain-ride-locs', JSON.stringify({ owned: ['alpen', 'wald', 'nacht', 'gletscher'], active: loc }));
      // daily bonus already collected today, so its window does not cover the menu
      const t = new Date(), day = `${t.getFullYear()}-${String(t.getMonth() + 1).padStart(2, '0')}-${String(t.getDate()).padStart(2, '0')}`;
      localStorage.setItem('mountain-ride-dailyBonus', JSON.stringify({ last: day, streak: 1 }));
    }, [lang, loc]);
    const p = await ctx.newPage();
    p.on('pageerror', e => console.log(lang, device, 'ERR', e.message));
    await p.goto(BASE + 'store.html'); await p.waitForTimeout(5500);   // the rider model (~0.7 MB) must be in
    return { p, ctx };
  };
  const ride = async (p, secs) => {
    await p.click('#title', { force: true }); await p.waitForTimeout(500);
    await p.click('#startBtn'); await p.waitForTimeout(400);
    // keep the rider alive: obstacles directly ahead in the rider's lane are moved aside
    await p.evaluate(() => { setInterval(() => { const P = __dbg.P(); for (const e of __dbg.ents()) if (!e.deco && e.d > P.d - 2 && e.d < P.d + 12 && Math.abs(e.x - P.x) < 2.5) { e.d = -1e6; e.mesh.visible = false; } }, 40); });
    await p.waitForTimeout(secs * 1000);
  };

  // 1 title screen, 2 menu
  let { p, ctx } = await page('alpen');
  await snap(p);
  await p.click('#title', { force: true }); await p.waitForTimeout(1200); await snap(p);
  await ctx.close();
  // 3 riding in the Alps (stage banner), 4 a trick in the air
  ({ p, ctx } = await page('alpen'));
  await ride(p, 5);
  await p.keyboard.press('ArrowLeft'); await p.waitForTimeout(700); await snap(p);
  await p.evaluate(() => { const P = __dbg.P(); __dbg.addRamp(P.d + 22, __dbg.laneX(P.lane)); });
  await p.waitForFunction(() => __dbg.P().air && __dbg.P().airT > 0.1, null, { timeout: 60000 });
  await p.keyboard.press('ArrowUp');
  await p.waitForFunction(() => __dbg.P().airT > 0.55 || !__dbg.P().air, null, { timeout: 60000 });   // ramp behind the camera, rider mid-flip
  await p.evaluate(() => { __dbg.pop.style.opacity = '0'; }); await snap(p);
  await ctx.close();
  // 5 torch night, 6 glacier
  for (const loc of ['nacht', 'gletscher']) {
    ({ p, ctx } = await page(loc));
    await ride(p, 6);
    await p.keyboard.press(loc === 'nacht' ? 'ArrowRight' : 'ArrowLeft'); await p.waitForTimeout(800);
    await p.evaluate(() => { __dbg.pop.style.opacity = '0'; }); await snap(p);
    await ctx.close();
  }
  console.log(lang, device, n, 'shots');
}

async function featureGraphic(browser) {
  const p = await browser.newPage({ viewport: { width: 1024, height: 500 } });
  await p.setContent(`<!doctype html><html><head><link rel="stylesheet" href="${BASE}../assets/lib/fonts/fonts.css"><style>
    body{margin:0;width:1024px;height:500px;background:url('${BASE}../assets/key-art.jpg') center 62%/cover;font-family:'Bowlby One SC'}
    h1{position:absolute;left:44px;top:30px;margin:0;font-size:84px;line-height:.95;color:#fff;text-shadow:0 4px 18px rgba(20,35,58,.55)}
    h1 span{color:#ffc531}</style></head><body><h1>Mountain<br><span>Ride</span></h1></body></html>`, { waitUntil: 'networkidle' });
  await p.waitForTimeout(500);
  await p.screenshot({ path: path.join(root, 'store', 'feature-graphic.png') });
  await p.close();
}

(async () => {
  makePreview();
  const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  fs.mkdirSync(path.join(root, 'store'), { recursive: true });
  await featureGraphic(browser);
  for (const lang of LANGS) for (const device of Object.keys(DEVICES)) {
    try { await shoot(browser, lang, device); } catch (e) { console.log(lang, device, 'FAILED', e.message.split('\n')[0]); }
  }
  await browser.close();
})();
