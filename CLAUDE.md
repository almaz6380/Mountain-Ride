# Mountain Ride – notes for Claude

Endless snowboard runner in the browser (three.js r128), UI in 10 languages (German first). The owner talks German: answer in German.

## Files
- `index.html` – the whole game (HTML, CSS, JS in one file). Written as an Artifact page: no doctype/head of its own.
- `assets/` – textures, sprites, sky images, icons. **The rider is `rider-anim.glb`**: the owner's figure rigged by Mixamo with the clips `ride` (Mixamo „Skateboarding“), `jump`, `fall` (free fall, used lying on the snow for wipe-outs) and `idle`, merged from the FBX downloads with FBX2glTF + gltf-transform (centimetres → `ANIM_SCALE`). `makeRiderAnim` / `animateRider`: AnimationMixer with cross-fades, duck = held crouch frame of the jump (`DUCK_T`), the board is placed under both foot bones every frame; spins/flips/lean/slope stay on the root (`placeRoot`). Fallbacks: old `rider.glb` with the code-built rig (`buildRig`/`poseRig`), then the painted `rider-*.png` sprites. More Mixamo clips: download as FBX (Without Skin), convert with FBX2glTF and copy the channels onto the same bone names.
- **Texts / languages**: no hard-coded UI text. German lives in `index.html` as `I18N_DE`; the other 9 languages (en es pt fr it ru zh ja ar) in `assets/lib/i18n.js` (`window.I18N`). Use `tx('key', {vars})` in JS and `data-i18n` / `data-i18n-ph` / `data-i18n-aria` / `data-i18n-title` ('A|B' = two-tone title) in HTML; numbers via `fmt()`. **A new key must be added to all 10 languages.** Arabic switches the page to `dir=rtl`: wrap numbers-with-units in a bidi isolate (CSS `unicode-bidi: isolate` or `\u2066…\u2069`) and check screenshots.
- `sw.js` – service worker (offline cache). **Bump `CACHE` (`mountain-ride-vNN`) on every release**, otherwise phones keep the old version. Supabase requests are never cached.
- `manifest.webmanifest`, `tools/build-pages.py` (builds `dist/` for GitHub Pages; with `--app` it builds `www/` for the store apps: no service worker, no manifest), `docs/online-bestenliste.md` (Supabase setup: tables `scores` and `daily`, plus the anti-cheat SQL).
- `privacy.html`, `imprint.html` – legal pages (texts in `assets/lib/legal.js`, 10 languages, owner's contact in `CONTACT`), copied into both builds and linked from the settings with `?lang=`.
- **Store apps (Capacitor 8)**: `package.json`, `capacitor.config.json` (app id `com.almaz6380.mountainride`), `android/`, `ios/` (both checked in; `www/` and `node_modules/` are not). `npm run sync` = build `www/` + `npx cap sync`. Icons/splash from `resources/` via `npm run assets`. Owner's build/release steps: `docs/store-veroeffentlichen.md`.
- `store/` – listing texts per language (`listing/<lang>.json`), screenshots (`tools/store-shots.js`, needs the local server), feature graphic, product list, privacy/age-rating answers.

## Release workflow (every change)
1. Bump `CACHE` in `sw.js`.
2. Commit and push `master`.
3. `python3 tools/build-pages.py`, copy `dist/` into a `gh-pages` worktree (replace everything), commit, push `gh-pages`.
4. Check `https://almaz6380.github.io/Mountain-Ride/sw.js` shows the new version (Pages can lag or get stuck; if a run sits queued for long, cancel it and push again).
5. Republish the Artifact from `index.html`.

## Testing
- Serve the repo (`python3 -m http.server 8765`) and drive it with Playwright (Chromium with `--use-angle=swiftshader`).
- Use a `.preview/` copy of `index.html` (gitignored) with three.js / GLTFLoader served locally and a `window.__dbg` hook injected before `function render(dt)`; the CDN through the proxy is flaky.
- The game opens on the title screen: click `#title`, then `#startBtn`.
- Duel and live duel must keep identical courses: course generation only uses the seeded `rowRnd` / `secRnd` streams and values derived from the row's distance (`diffAt`, `vAt`, `stageAt`), never the rider's live state. Cosmetics may use `Math.random`.

## Game structure (index.html)
- Physics: fixed 120 Hz steps with render interpolation. Five lanes (`LANE_W` 3.2 m), one swipe = one lane.
- Course: `spawnRow(d)` builds rows ~228 m ahead. Obstacles arrive in **stages** (`STAGES`): warm-up (trees/rocks) → logs and ramps → banners → fences and snowballs → crevasses and full rows → everything. Speed `19 + min(32, dist * 0.008)` m/s.
- Track sections (deep snow, ice, tunnel, steep) start after ~1.1 km.
- Tricks in the air: tap = 360°, swipe up = backflip, swipe down = grab; mixing tricks and chaining clean landings builds a combo.
- Places (`LOCS`): Alpen, Waldabfahrt, Fackel-Nacht, Gletscher – own light, scenery, favoured sections and music theme.
- Online (Supabase, `ONLINE` config): worldwide leaderboard (`scores`), daily race (`daily`), live duel via Realtime broadcast + presence. Duel by link encodes seed, start, place and a ghost recording in the URL hash.
- Sound and music are synthesised with Web Audio; sound is switched only in the settings (no in-game button).
- Online safety: `cleanName()` filters swear words (all 10 languages) for every name entered or shown; scores carry an anonymous `PLAYER_ID` and are only posted when `plausible()`; the DB has matching constraints + a rate limit.
- Money (store apps only, hidden on web/Artifact): `MONEY` config (AdMob unit ids – Google test ids until release –, RevenueCat keys), `PRODUCTS`. AdMob via `NATIVE.AdMob`: UMP consent + iOS ATT in `initMoney()`, rewarded „Weiterfahren“ (`revive()`, once per run, not in duel/live/daily/tutorial) and „Münzen ×2“, interstitial every 4th run via `startAfterAd()`. Purchases via `NATIVE.Purchases` (RevenueCat): coin packs, `no_ads`, `starter_pack`, restore button.
- Audio: recorded CC0 sounds and music loops in `assets/audio/` (MP3 – the test Chromium has no AAC; sources in `CREDITS.md`), loaded by `Sound.loadSamples()`; every effect falls back to the old Web Audio synth when a file is missing (Artifact). One music loop per place + menu, cross-faded in `updateTrack()`.
- Extra content: snowcat obstacle (`cat`, stage 3+, moves downhill), sections `bonus` (no obstacle rows – `spawnRow` skips them; ramps from `secRnd`) and `avalanche` (show only: powder on the banks, rumble, +50 coins for escaping). **Sections are decided 300 m before the rows there are built**; anything a section adds to the course must use `secRnd`, never `rowRnd` (duel determinism – checked up to 4 km).
- Daily bonus (`maybeDailyBonus`, 7-day streak, day 7 gives a pattern board) and the evening reminder via `@capacitor/local-notifications` (apps only, asked after the 3rd run, setting „Erinnerung“). Tests: the `.preview` copy marks the bonus as collected so the menu is free.
- Economy: collected coins + 1 coin per 50 m (`COIN_PER_M`), missions 80–400, upgrades 150–1200 (see `store/products.md`).

## Owner preferences
- Graphics matter a lot: check visual changes with screenshots before shipping.
- No self-built placeholder figures – the procedural low-poly rider was rejected. Use real models / mocap (Mixamo) for the rider.
- Difficulty must ramp gently (stages), not jump from easy to hard.
