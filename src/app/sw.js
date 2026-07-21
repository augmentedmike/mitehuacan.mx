const CACHE = "mitehuacan-v3";
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

  // App shell — cache first, network fallback
  e.respondWith(
    caches.match(e.request).then((hit) => hit || fetch(e.request).then((res) => {
      return caches.open(CACHE).then((c) => {
        c.put(e.request, res.clone());
        return res;
      });
    }))
  );
});
