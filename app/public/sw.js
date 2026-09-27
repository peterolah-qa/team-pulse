/* Service worker Team Pulse.
   - stránka (index.html) a dáta (data/*.json): najprv sieť, pri výpadku posledná uložená verzia
   - ostatné súbory (assets s hashom v názve, fonty, ikony): najprv cache
   VERSION prepíše build (vite.config.ts), takže po novom deployi sa stará cache zmaže. */
const VERSION = "tp-__BUILD__";
const SHELL = ["./", "./manifest.webmanifest", "./icon.svg", "./icon-192.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(VERSION).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== VERSION).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

function networkFirst(request, key) {
  return fetch(request)
    .then((res) => {
      if (res.ok) {
        const copy = res.clone();
        caches.open(VERSION).then((c) => c.put(key, copy));
      }
      return res;
    })
    .catch(() => caches.match(key).then((hit) => hit || Response.error()));
}

function cacheFirst(request) {
  return caches.match(request).then(
    (hit) =>
      hit ||
      fetch(request).then((res) => {
        if (res.ok) {
          const copy = res.clone();
          caches.open(VERSION).then((c) => c.put(request, copy));
        }
        return res;
      }),
  );
}

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin) return;
  if (e.request.mode === "navigate") e.respondWith(networkFirst(e.request, "./"));
  else if (url.pathname.includes("/data/")) e.respondWith(networkFirst(e.request, url.pathname));
  else e.respondWith(cacheFirst(e.request));
});
