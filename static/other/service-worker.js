// service-worker.js

const CACHE_NAME = 'aurus-pwa-v1';
const urlsToCache = ['/', '/static/css/base.css', '/static/js/base.js'];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(urlsToCache);
    })
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      return response || fetch(event.request);
    })
  );
});