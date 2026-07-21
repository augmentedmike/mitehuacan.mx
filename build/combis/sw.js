const CACHE = "mitehuacan-v4";
const SHELL = [
  "./",
  "./index.html",
  "./manifest.json",
  "./icon-192.png",
  "./icon-512.png",
  "./maplibre-gl.js",     // self-hosted so a CDN outage can't blank the app
  "./maplibre-gl.css",
  "./routes.js",
  "./sponsors.js",
  "./pois.js",
  "./places.js",
  "./denue.js",
  "./discovery.js",
];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);

  // API calls — network only, no cache
  if (url.pathname.startsWith("/api/")) return;

  // Cross-origin (OpenFreeMap tiles/style, fonts) — network first, but CACHE the
  // response so repeat visits survive a CDN outage. Falls back to cache offline.
  if (url.hostname !== self.location.hostname) {
    e.respondWith(
      fetch(e.request).then((res) => {
        if (res.ok && (e.request.method === "GET")) {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(e.request, copy)).catch(() => {});
        }
        return res;
      }).catch(() => caches.match(e.request))
    );
    return;
  }

  // Big stable assets (the library, icons) — cache first for speed.
  if (/maplibre-gl\.(js|css)$|\.png$/.test(url.pathname)) {
    e.respondWith(
      caches.match(e.request).then((hit) => hit || fetch(e.request).then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(e.request, copy)).catch(() => {});
        return res;
      }))
    );
    return;
  }

  // HTML + data layers (index, routes/denue/discovery/…) — NETWORK FIRST so
  // deploys and fresh discovery data reach returning visitors; cache is the
  // offline fallback and gets refreshed on every successful fetch.
  e.respondWith(
    fetch(e.request).then((res) => {
      if (res.ok && e.request.method === "GET") {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(e.request, copy)).catch(() => {});
      }
      return res;
    }).catch(() => caches.match(e.request))
  );
});
