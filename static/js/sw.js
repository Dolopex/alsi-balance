// ALSI BALANCE Service Worker
// Estrategia:
// - Assets estaticos (CSS, JS, imagenes): cache-first
// - Paginas HTML y APIs: network-first con fallback a cache
// - Offline: mostrar pagina offline si no hay red
const CACHE_VERSION = 'alsi-balance-v3';
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const RUNTIME_CACHE = `${CACHE_VERSION}-runtime`;
const OFFLINE_URL = '/offline/';

const PRECACHE_URLS = [
  '/',
  '/dashboard/',
  '/movimientos/',
  '/reportes/',
  '/static/css/app.css',
  '/static/manifest.webmanifest',
  '/static/img/icon-192.png',
  '/static/img/icon-512.png',
  '/static/img/logo.svg',
  '/static/img/favicon.png',
  OFFLINE_URL,
];

// Limite de entries en el cache runtime para no acumular basura
const RUNTIME_CACHE_LIMIT = 50;

// --- Instalacion: pre-cachear assets criticos ----------------------
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => {
      // addAll falla si algun recurso falla; usamos add individual
      return Promise.allSettled(
        PRECACHE_URLS.map((url) =>
          cache.add(url).catch((err) => {
            console.warn('[sw] no se pudo pre-cachear', url, err);
          })
        )
      );
    })
  );
  self.skipWaiting();
});

// --- Activacion: limpiar caches viejos ------------------------------
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((k) => k !== STATIC_CACHE && k !== RUNTIME_CACHE)
          .map((k) => {
            console.log('[sw] eliminando cache viejo', k);
            return caches.delete(k);
          })
      )
    ).then(() => self.clients.claim())
  );
});

// --- Fetch: estrategias segun el tipo de request ------------------
self.addEventListener('fetch', (event) => {
  const req = event.request;
  const url = new URL(req.url);

  // Solo manejar GET
  if (req.method !== 'GET') return;

  // Ignorar otros origins (CDNs, etc.)
  if (url.origin !== self.location.origin) return;

  // Ignorar admin (no cachear)
  if (url.pathname.startsWith('/admin/')) return;

  // Ignorar endpoints de push/notificaciones
  if (url.pathname.startsWith('/gmail/webhook/')) return;
  if (url.pathname.startsWith('/notificaciones/')) return;

  // Estrategia: assets estaticos
  if (isStaticAsset(url.pathname)) {
    event.respondWith(cacheFirst(req));
    return;
  }

  // Estrategia: navegacion (HTML)
  if (req.mode === 'navigate' || req.headers.get('accept')?.includes('text/html')) {
    event.respondWith(networkFirstWithOffline(req));
    return;
  }

  // Default: network-first
  event.respondWith(networkFirst(req));
});

function isStaticAsset(pathname) {
  return /\.(css|js|png|jpg|jpeg|gif|svg|ico|webmanifest|woff2?|ttf|eot)$/i.test(pathname);
}

// Cache-first: servir cache, fallback a red, fallback a error
async function cacheFirst(req) {
  const cached = await caches.match(req);
  if (cached) return cached;
  try {
    const response = await fetch(req);
    if (response.ok) {
      const cache = await caches.open(STATIC_CACHE);
      cache.put(req, response.clone());
    }
    return response;
  } catch (err) {
    return new Response('Offline', { status: 503 });
  }
}

// Network-first: intentar red, fallback a cache, fallback a offline
async function networkFirst(req) {
  try {
    const response = await fetch(req);
    if (response.ok) {
      trimCache(RUNTIME_CACHE);
      const cache = await caches.open(RUNTIME_CACHE);
      cache.put(req, response.clone());
    }
    return response;
  } catch (err) {
    const cached = await caches.match(req);
    if (cached) return cached;
    return new Response('Offline', { status: 503 });
  }
}

async function networkFirstWithOffline(req) {
  try {
    const response = await fetch(req);
    if (response.ok) {
      trimCache(RUNTIME_CACHE);
      const cache = await caches.open(RUNTIME_CACHE);
      cache.put(req, response.clone());
    }
    return response;
  } catch (err) {
    const cached = await caches.match(req);
    if (cached) return cached;
    const offline = await caches.match(OFFLINE_URL);
    if (offline) return offline;
    return new Response(
      '<!DOCTYPE html><html><head><title>Sin conexion</title></head>' +
      '<body style="font-family:sans-serif;text-align:center;padding:50px">' +
      '<h1>Sin conexion</h1><p>Verifica tu conexion a internet.</p>' +
      '<p><a href="/">Recargar</a></p></body></html>',
      { status: 503, headers: { 'Content-Type': 'text/html; charset=utf-8' } }
    );
  }
}

async function trimCache(name) {
  const cache = await caches.open(name);
  const keys = await cache.keys();
  if (keys.length > RUNTIME_CACHE_LIMIT) {
    // Eliminar las entradas mas antiguas
    for (let i = 0; i < keys.length - RUNTIME_CACHE_LIMIT; i++) {
      await cache.delete(keys[i]);
    }
  }
}

// --- Push notifications (web push) -----------------------------------
self.addEventListener('push', (event) => {
  console.log('[sw] push event recibido');
  let data = { title: 'ALSI Balance', body: 'Nuevo movimiento detectado', url: '/' };
  if (event.data) {
    try {
      data = event.data.json();
    } catch (e) {
      try { data.body = event.data.text(); } catch (e2) {}
    }
  }
  const title = data.title || 'ALSI Balance';
  const options = {
    body: data.body || '',
    icon: data.icon || '/static/img/icon-192.png',
    badge: data.badge || '/static/img/icon-192.png',
    data: { url: data.url || '/' },
    vibrate: [200, 100, 200],
    tag: 'alsi-' + Date.now(),
    requireInteraction: false,
    actions: [
      { action: 'open', title: 'Ver' },
      { action: 'close', title: 'Cerrar' }
    ]
  };
  event.waitUntil(
    self.registration.showNotification(title, options).catch((err) => {
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
          return client.focus();
        }
      }
      return clients.openWindow(url);
    })
  );
});

self.addEventListener('pushsubscriptionchange', (event) => {
  event.waitUntil(
    self.registration.pushManager.subscribe({ userVisibleOnly: true })
  );
});