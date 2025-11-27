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

self.addEventListener('push', function(event) {
    if (!event.data) return;

    const data = event.data.json();

    const options = {
        body: data.body || 'Уведомление от приложения',
        icon: '/static/icons/icon-192x192.png',
        badge: '/static/icons/icon-72x72.png',
        image: data.image || null,
        actions: [
            {
                action: 'open',
                title: 'Открыть'
            },
            {
                action: 'close',
                title: 'Закрыть'
            }
        ],
        data: data.url || '/',
        requireInteraction: true,
        vibrate: [200, 100, 200]
    };

    event.waitUntil(
        self.registration.showNotification(data.title || 'Уведомление', options)
    );
});

// Обработка кликов по уведомлению
self.addEventListener('notificationclick', function(event) {
    event.notification.close();

    if (event.action === 'open') {
        event.waitUntil(
            clients.openWindow(event.notification.data)
        );
    } else if (event.action === 'close') {
        // Просто закрываем уведомление
    } else {
        // Клик по самому уведомлению (не по action)
        event.waitUntil(
            clients.openWindow(event.notification.data)
        );
    }
});