const STATIC_CACHE = 'static-v4';
const PAGES_CACHE = 'pages-v4';
const OFFLINE_URL = '/offline/';
const STATIC_ASSETS = [
  '/',
  OFFLINE_URL,
  '/static/css/style.css',
  '/static/css/theme.css',
  '/static/js/theme.js',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => cache.addAll(STATIC_ASSETS)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys.filter(k => ![STATIC_CACHE, PAGES_CACHE].includes(k)).map(k => caches.delete(k))
    )).then(() => self.clients.claim())
  );
});

function isSameOrigin(request) {
  try {
    const url = new URL(request.url);
    return url.origin === self.location.origin;
  } catch (_) { return false; }
}

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;

  // Navigation requests: network-first, fallback to cache/offline
  if (req.mode === 'navigate' || (req.headers.get('accept') || '').includes('text/html')) {
    event.respondWith(
      fetch(req).then(res => {
        const copy = res.clone();
        caches.open(PAGES_CACHE).then(cache => cache.put(req, copy)).catch(() => {});
        return res;
      }).catch(async () => {
        const cached = await caches.match(req);
        if (cached) return cached;
        const offline = await caches.match(OFFLINE_URL);
        return offline || new Response('<h1>Offline</h1>', { headers: { 'Content-Type': 'text/html; charset=utf-8' } });
      })
    );
    return;
  }

  const dest = req.destination;
  const isStatic = ['style', 'script', 'image', 'font'].includes(dest);
  if (isStatic && isSameOrigin(req)) {
    if (dest === 'script') {
      event.respondWith(
        fetch(req).then(res => {
          const copy = res.clone();
          caches.open(STATIC_CACHE).then(cache => cache.put(req, copy)).catch(() => {});
          return res;
        }).catch(() => caches.match(req))
      );
      return;
    }
    event.respondWith(
      caches.match(req).then(match => match || fetch(req).then(res => {
        const copy = res.clone();
        caches.open(STATIC_CACHE).then(cache => cache.put(req, copy)).catch(() => {});
        return res;
      }).catch(() => match))
    );
    return;
  }

  // Default: pass-through
});
