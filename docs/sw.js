/* Simple offline cache so the tools work at a job site with no signal. */
const CACHE = 'quotes-cache-v6';
const ASSETS = [
  './', './index.html', './demo.html', './tracker.html', './why-us.html', './crm.html', './how-to.html',
  './manifest.json', './manifest-tracker.json', './manifest-crm.json',
  './icons/icon-192.png', './icons/icon-512.png', './icons/apple-touch-icon.png'
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(c => Promise.all(
      ASSETS.map(u => c.add(u).catch(() => null))   // don't fail install if one asset is missing
    )).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys.filter(k => k !== CACHE).map(k => caches.delete(k))
    )).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const req = e.request;
  // only handle same-origin GET requests (leave map/geocode/pdf CDN calls to the network)
  if (req.method !== 'GET' || new URL(req.url).origin !== self.location.origin) return;
  e.respondWith(
    caches.match(req).then(hit => hit || fetch(req).then(res => {
      const copy = res.clone();
      caches.open(CACHE).then(c => c.put(req, copy)).catch(() => {});
      return res;
    }).catch(() => caches.match(req).then(h => h || caches.match('./'))))
  );
});
