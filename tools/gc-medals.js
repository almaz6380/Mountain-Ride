// Game Center achievement images (512×512 PNG): one medal per achievement and tier.
// node tools/gc-medals.js  ->  store/gamecenter/mr_<id>_<1..3>.png
const path = require('path');
const { chromium } = require(process.env.PLAYWRIGHT || 'playwright');
const OUT = path.resolve(__dirname, '..', 'store', 'gamecenter');
const ICON = { dist: '🏔️', far: '🏂', score: '⭐', coins: '🪙', runs: '🔁', spins: '🌀', flips: '🤸', combo: '🔥', powers: '⚡',
  gates: '🚧', crevasses: '🧊', cats: '🚜', avalanche: '🌨️', places: '🗺️', slalom: '🚩' };
const TIER = [['#f3b98a', '#b8662f', '#7a3d14'], ['#f4f7fb', '#a9b4c2', '#5d6878'], ['#fff1a8', '#f2b51d', '#9c6a00']];
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 512, height: 512 } });
  for (const [id, icon] of Object.entries(ICON)) for (let t = 0; t < 3; t++) {
    const [hi, mid, lo] = TIER[t];
    await p.setContent(`<body style="margin:0;width:512px;height:512px;background:radial-gradient(circle at 50% 30%,#3c5a8c,#14223d)">
      <div style="position:absolute;inset:36px;border-radius:50%;background:radial-gradient(circle at 35% 28%,${hi},${mid} 55%,${lo});box-shadow:0 14px 30px rgba(0,0,0,.45),inset 0 -10px 24px rgba(0,0,0,.25)"></div>
      <div style="position:absolute;inset:78px;border-radius:50%;border:8px solid rgba(255,255,255,.35);background:radial-gradient(circle at 50% 35%,${mid},${lo})"></div>
      <div style="position:absolute;inset:0;display:grid;place-items:center;font:190px 'Noto Color Emoji';filter:drop-shadow(0 8px 10px rgba(0,0,0,.35))">${icon}</div>
      <div style="position:absolute;left:0;right:0;bottom:100px;text-align:center;font:700 44px sans-serif;color:#fff;letter-spacing:6px;text-shadow:0 2px 6px rgba(0,0,0,.5)">${'★'.repeat(t + 1)}</div></body>`);
    await p.waitForTimeout(50);
    await p.screenshot({ path: path.join(OUT, `mr_${id}_${t + 1}.png`) });
  }
  await b.close();
})();
