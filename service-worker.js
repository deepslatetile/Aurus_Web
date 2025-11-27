// service-worker.js

const CACHE_NAME = 'aurus-pwa-v1';
// Используем относительные пути для кэширования
const urlsToCache = [
  '/',
  '/static/styles/base.css',
  '/static/js/base.js',
  '/static/js/base.html',
  '/static/images/icon-192x192.png',
  '/static/images/icon-512x512.png'
];

self.addEventListener('install', (event) => {
  console.log('Service Worker: Installing...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Service Worker: Caching files');
        return cache.addAll(urlsToCache);
      })
      .catch((error) => {
        console.error('Service Worker: Cache error:', error);
      })
  );
  // Активируем сразу после установки
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  console.log('Service Worker: Activated');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cache) => {
          if (cache !== CACHE_NAME) {
            console.log('Service Worker: Clearing old cache');
            return caches.delete(cache);
          }
        })
      );
    })
  );
  return self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  // Пропускаем не-GET запросы
  if (event.request.method !== 'GET') return;

  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        // Возвращаем кэш если есть, иначе делаем запрос
        return response || fetch(event.request);
      })
      .catch(() => {
        // Fallback для ошибок
        return caches.match('/');
      })
  );
});

self.addEventListener('push', function(event) {
    console.log('Service Worker: Push received');

    if (!event.data) {
        console.log('Service Worker: No push data');
        return;
    }

    let data = {};
    try {
        data = event.data.json();
        console.log('Service Worker: Push data:', data);
    } catch (e) {
        console.error('Service Worker: Error parsing push data:', e);
        // Если данные не в JSON, используем текстовые данные
        data = {
            title: 'Уведомление',
            body: event.data.text() || 'Новое уведомление'
        };
    }

    const options = {
        body: data.body || 'Уведомление от Aurus',
        icon: data.icon || '/static/images/icon-192x192.png',
        badge: '/static/images/icon-72x72.png',
        image: data.image,
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
        data: {
            url: data.url || '/'
        },
        requireInteraction: true,
        vibrate: [200, 100, 200]
    };

    event.waitUntil(
        self.registration.showNotification(data.title || 'Aurus', options)
        .then(() => {
            console.log('Service Worker: Notification shown');
        })
        .catch((error) => {
            console.error('Service Worker: Notification error:', error);
        })
    );
});

self.addEventListener('notificationclick', function(event) {
    console.log('Service Worker: Notification clicked', event.action);
    event.notification.close();

    if (event.action === 'open' || !event.action) {
        event.waitUntil(
            clients.matchAll({type: 'window', includeUncontrolled: true})
            .then((windowClients) => {
                // Ищем открытое окно приложения
                for (let client of windowClients) {
                    if (client.url.includes(self.location.origin) && 'focus' in client) {
                        return client.focus();
                    }
                }
                // Открываем новое окно если не нашли
                if (clients.openWindow) {
                    return clients.openWindow(event.notification.data.url || '/');
                }
            })
        );
    }
    // Для действия 'close' просто закрываем уведомление
});