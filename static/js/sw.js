// ALSI BALANCE Service Worker
const CACHE = 'alsi-balance-v2';
const ASSETS = [
  '/static/css/app.css',
  '/static/manifest.webmanifest',
  '/static/img/icon-192.png',
  '/static/img/icon-512.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(ASSETS)).catch(() => {})
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;
  if (req.url.includes('/admin/') || req.url.includes('/api/')) return;

  event.respondWith(
    fetch(req).catch(() => caches.match(req))
  );
});

// Manejar push notifications
self.addEventListener('push', (event) => {
  console.log('[sw] push event recibido');
  let data = { title: 'ALSI Balance', body: 'Nuevo movimiento detectado', url: '/' };
  if (event.data) {
    try {
      data = event.data.json();
      console.log('[sw] push payload:', data);
    } catch (e) {
      console.warn('[sw] payload no es JSON, usando texto:', e);
      try { data.body = event.data.text(); } catch (e2) { console.error('[sw] no se pudo leer payload:', e2); }
    }
  } else {
    console.warn('[sw] push sin payload (event.data vacio)');
  }

  const title = data.title || 'ALSI Balance';
  const options = {
    body: data.body || '',
    icon: data.icon || '/static/img/icon-192.png',
    badge: data.badge || '/static/img/icon-192.png',
    data: { url: data.url || '/' },
    vibrate: [200, 100, 200],
    tag: 'alsi-' + (Date.now()),
    requireInteraction: false,
    actions: [
      { action: 'open', title: 'Ver movimiento' },
      { action: 'close', title: 'Cerrar' }
    ]
  };

  event.waitUntil(
    self.registration.showNotification(title, options).then(() => {
      console.log('[sw] notificacion mostrada:', title);
    }).catch(err => {
      console.error('[sw] ERROR al mostrar notificacion:', err);
    })
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const url = (event.notification.data && event.notification.data.url) || '/';
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((windowClients) => {
      for (const client of windowClients) {
        if (client.url.includes(self.location.origin) && 'focus' in client) {
          client.navigate(url);
          return client.focus();
        }
      }
      return clients.openWindow(url);
    })
  );
});

self.addEventListener('pushsubscriptionchange', (event) => {
  event.waitUntil(
    self.registration.pushManager.subscribe(event.oldSubscription ? event.oldSubscription.options : { userVisibleOnly: true })
  );
});
