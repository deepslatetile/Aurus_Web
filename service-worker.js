
importScripts('https://www.gstatic.com/firebasejs/9.6.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/9.6.0/firebase-messaging-compat.js');

const firebaseConfig = {
  apiKey: "AIzaSyAhLzb1UdObqvZoQixxxKBD6n6TXmf502I",
  authDomain: "aurus-pwa.firebaseapp.com",
  projectId: "aurus-pwa",
  storageBucket: "aurus-pwa.firebasestorage.app",
  messagingSenderId: "550033719644",
  appId: "1:550033719644:web:43ede90b5c87dbbcd40199",
  measurementId: "G-8ELDJ6532Y"
};

firebase.initializeApp(firebaseConfig);
const messaging = firebase.messaging();

messaging.onBackgroundMessage((payload) => {
  console.log('Received background message:', payload);

  const notificationTitle = payload.notification?.title || 'Aurus';
  const notificationOptions = {
    body: payload.notification?.body || 'Новое уведомление',
    icon: '/static/images/icon-192x192.png',
    badge: '/static/images/icon-72x72.png',
    data: payload.data || { url: '/' },
    actions: [
      {
        action: 'open',
        title: 'Открыть'
      },
      {
        action: 'close',
        title: 'Закрыть'
      }
    ]
  };

  return self.registration.showNotification(notificationTitle, notificationOptions);
});

const CACHE_NAME = 'aurus-pwa-v1';
const urlsToCache = [
  '/',
  '/static/styles/base.css',
  '/static/js/base.js',
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

self.addEventListener('notificationclick', function (event) {
  console.log('Service Worker: Notification clicked', event.action);
  event.notification.close();

  if (event.action === 'open' || !event.action) {
    const urlToOpen = event.notification.data?.url || '/';

    event.waitUntil(
      clients.matchAll({ type: 'window', includeUncontrolled: true })
        .then((windowClients) => {
          for (let client of windowClients) {
            if (client.url.includes(self.location.origin) && 'focus' in client) {
              return client.navigate(urlToOpen).then(() => client.focus());
            }
          }
          if (clients.openWindow) {
            return clients.openWindow(urlToOpen);
          }
        })
    );
  }
});

self.addEventListener('notificationclose', function (event) {
  console.log('Service Worker: Notification closed', event.notification.tag);
});
