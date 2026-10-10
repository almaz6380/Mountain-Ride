// Offline cache for the Mountain Ride web app (bump CACHE to ship updates): cache-first for game files, network-first for the page itself.
const CACHE = 'mountain-ride-v42';
const CORE = ['./', './index.html', './manifest.webmanifest', './assets/lib/three.min.js', './assets/lib/GLTFLoader.js', './assets/lib/i18n.js', './assets/lib/fonts/fonts.css', './assets/rider-anim.glb', './assets/obstacles.glb'];   // the rest is cached on first use
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(CORE)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  if (new URL(req.url).hostname.endsWith('.supabase.co')) return;   // live data (leaderboard) always from the network
  const isPage = req.mode === 'navigate';
  if (isPage) {
    e.respondWith(fetch(req).then(res => { const copy = res.clone(); caches.open(CACHE).then(c => c.put(req, copy)); return res; })
      .catch(() => caches.match(req).then(r => r || caches.match('./index.html'))));
    return;
  }
  e.respondWith(caches.match(req).then(hit => hit || fetch(req).then(res => {
    if (res.ok || res.type === 'opaque') { const copy = res.clone(); caches.open(CACHE).then(c => c.put(req, copy)); }
    return res;
  })));
});
