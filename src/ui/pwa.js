/**
 * PWA Manager — Service Worker kayıt ve PWA install prompt yönetimi.
 *
 * Mevcut JS'i bozmadan çalışır.
 * - Service Worker'ı ilk açılışta kaydeder
 * - 'beforeinstallprompt' olayını yakalar
 * - Güncelleme gelirse kullanıcıya bildirir
 */
(function() {
  'use strict';

  const SW_URL = '/sw.js';

  // ── Service Worker kayıt ────────────────────────────────────────────
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register(SW_URL, { scope: '/' })
        .then((reg) => {
          console.log('[PWA] Service Worker kaydedildi:', reg.scope);

          // Güncelleme yönetimi
          reg.addEventListener('updatefound', () => {
            const newWorker = reg.installing;
            if (!newWorker) return;

            newWorker.addEventListener('statechange', () => {
              if (newWorker.state === 'activated' && navigator.serviceWorker.controller) {
                // Yeni SW aktifleştirildi — sayfa yenilenebilir
                if (window.bildirim) {
                  window.bildirim('Yeni sürüm hazır — yenilemek için [OK] basın', 'bilgi');
                }
              }
            });
          });
        })
        .catch((err) => {
          console.warn('[PWA] Service Worker kayıt başarısız:', err);
        });
    });
  }

  // ── Install Prompt ──────────────────────────────────────────────────
  let deferredPrompt = null;

  window.addEventListener('beforeinstallprompt', (e) => {
    // Tarayıcının otomatik banner'ını bastırıyoruz
    e.preventDefault();
    deferredPrompt = e;
    // Gerekirse kurulum butonu göster
    document.dispatchEvent(new CustomEvent('pwa-installable', { detail: { canInstall: true } }));
  });

  // Global yardımcı
  window.pwaInstallPrompt = function() {
    if (!deferredPrompt) return false;
    deferredPrompt.prompt();
    deferredPrompt.userChoice.then((choice) => {
      deferredPrompt = null;
      return choice.outcome === 'accepted';
    });
  };

  // Kurulum sonrası
  window.addEventListener('appinstalled', () => {
    if (window.bildirim) {
      window.bildirim('Uygulama ana ekrana eklendi!', 'basari');
    }
    deferredPrompt = null;
  });
})();
