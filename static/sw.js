/**
 * Service Worker — Portföy Gayrimenkul PWA
 * Version: 2.0.0
 *
 * Cache stratejisi:
 * 1. CSS/JS/Statik → Cache First (uzun süreli)
 * 2. API → Network First (her zaman taze veri, offline fallback)
 * 3. HTML/Sayfa → Stale While Revalidate (hızlı yanıt + arka plan güncelle)
 * 4. Resimler → Cache First (kapasite yönetimi)
 *
 * Offline durumda:
 * - Önceden ziyaret edilmiş sayfalar cache'den döner
 * - Hiç ziyaret edilmemiş sayfalar için /offline.html gösterilir
 */

const CACHE_VERSION = 'v2.0.5';
const STATIC_CACHE = 'static-' + CACHE_VERSION;
const RUNTIME_CACHE = 'runtime-' + CACHE_VERSION;
const OFFLINE_URL = '/offline.html';

// Statik öğeler (uzun süreli cache - 'cache-first')
const PRECACHE_URLS = [
    '/',
    '/#ilanlar',
    '/#blog',
    '/#admin',
    '/offline.html',
    '/manifest.json',
    '/src/styles/responsive.css',
    '/src/styles/layout.css',
    '/src/styles/components.css',
    '/src/styles/desktop.css',
    '/src/ui/seo.js',
    '/src/config/config.js',
    '/static/img/logo.png',
    'https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Inter:wght@400;500;600&display=swap'
];

// Install: statik kaynakları önbelleğe al
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(STATIC_CACHE).then((cache) => {
            return cache.addAll(PRECACHE_URLS).catch((err) => {
                console.log('Cache install kısmi başarısız:', err);
            });
        })
    );
    self.skipWaiting();
});

// Activate: eski cache'leri temizle
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames
                    .filter((name) => name !== STATIC_CACHE && name !== RUNTIME_CACHE)
                    .map((name) => caches.delete(name))
            );
        })
    );
    self.clients.claim();
});

// Fetch: strateji seç
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // API isteği: Network First
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(networkFirst(request));
        return;
    }

    // Kritik JS (config, api adapter, UI modülleri) — her zaman network-first,
    // staleWhileRevalidate değil. Eski config/adapter/UI cache'i sorun çıkardı.
    if (
        url.pathname.endsWith("/config/config.js") ||
        url.pathname.startsWith("/src/api/") ||
        url.pathname.startsWith("/src/config/") ||
        url.pathname.startsWith("/src/ui/")
    ) {
        event.respondWith(networkFirst(request));
        return;
    }

    // Statik dosyalar (CSS, JS, fonts): Stale While Revalidate
    // — eski cache'den hemen dön ama arka planda güncelle
    // (cacheFirst'tür(JS değişince SW version artana kadar güncellenmezdi)
    if (
        url.pathname.endsWith('.css') ||
        url.pathname.endsWith('.js') ||
        url.pathname.includes('/fonts/') ||
        url.pathname.endsWith('.woff2') ||
        url.pathname.endsWith('.woff')
    ) {
        event.respondWith(staleWhileRevalidate(request));
        return;
    }

    // Resimler: Cache First
    if (
        url.pathname.match(/\.(jpg|jpeg|png|gif|webp|svg|avif)$/i) ||
        url.pathname.includes('/uploads/') ||
        url.pathname.includes('/img/') ||
        url.pathname.includes('/static/')
    ) {
        event.respondWith(cacheFirst(request));
        return;
    }

    // Sayfa isteği (HTML): Network First, stale-fallback
    if (request.mode === 'navigate') {
        event.respondWith(networkFirst(request));
        return;
    }

    // Default: Network First
    event.respondWith(networkFirst(request));
});

// ── Strateji fonksiyonları ────────────────────────────────────────────

async function cacheFirst(request) {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) return cachedResponse;

    try {
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            const cache = await caches.open(RUNTIME_CACHE);
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    } catch (err) {
        // Offline: cache'de yok ve network yok
        return new Response('Offline - kaynak bulunamadı', { status: 503 });
    }
}

async function networkFirst(request) {
    try {
        const networkResponse = await fetch(request, {
            headers: request.headers,
            cache: 'no-cache'
        });

        // Sadece GET ve başarılı yanıtları cache'le
        if (request.method === 'GET' && networkResponse.ok) {
            const cache = await caches.open(RUNTIME_CACHE);
            cache.put(request, networkResponse.clone());
        }

        return networkResponse;
    } catch (err) {
        // Network başarısız — cache'den dön
        const cachedResponse = await caches.match(request);
        if (cachedResponse) return cachedResponse;

        // Sayfa navigasyonuysa offline sayfasını göster
        if (request.mode === 'navigate') {
            const offlinePage = await caches.match(OFFLINE_URL);
            if (offlinePage) return offlinePage;
        }

        return new Response('Offline', {
            status: 503,
            headers: { 'Content-Type': 'text/plain; charset=utf-8' }
        });
    }
}

async function staleWhileRevalidate(request) {
    const cache = await caches.open(RUNTIME_CACHE);
    const cachedResponse = await cache.match(request);

    const fetchPromise = fetch(request, { cache: 'no-cache' }).then((networkResponse) => {
        if (networkResponse.ok) cache.put(request, networkResponse.clone());
        return networkResponse;
    }).catch(() => cachedResponse);

    return cachedResponse || fetchPromise;
}
