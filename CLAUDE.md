# Mountain Ride – notes for Claude

Endless snowboard runner in the browser (three.js r128), German UI. The owner talks German: answer in German.

## Files
- `index.html` – the whole game (HTML, CSS, JS in one file). Written as an Artifact page: no doctype/head of its own.
- `assets/` – textures, sprites, sky images, icons, `rider.glb` (the 3D rider, static T-pose mesh; skeleton and skin weights are built in code at load time, see `buildRig` / `poseRig`). The painted `rider-*.png` / `spin-*.png` sprites are the fallback if the GLB fails to load.
- `sw.js` – service worker (offline cache). **Bump `CACHE` (`mountain-ride-vNN`) on every release**, otherwise phones keep the old version. Supabase requests are never cached.
- `manifest.webmanifest`, `tools/build-pages.py` (builds `dist/` for GitHub Pages), `docs/online-bestenliste.md` (Supabase setup: tables `scores` and `daily`).

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

## Owner preferences
- Graphics matter a lot: check visual changes with screenshots before shipping.
- No self-built placeholder figures – the procedural low-poly rider was rejected. Use real models / mocap (Mixamo) for the rider.
- Difficulty must ramp gently (stages), not jump from easy to hard.
