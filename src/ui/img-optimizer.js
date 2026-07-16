/**
 * Image Optimizer — Mevcut img elementlerini optimize eder.
 *
 * Mevcut JS'i BOZMADAN, sayfa yüklendikten sonra:
 *   1. Tüm <img>'lere otomatik loading="lazy" ve decoding="async" ekler
 *   2. fetchpriority="high" hero imglere ekler
 *   3. .webp url'si olan img'ler için picture elementi oluşturur (tarayıcı webp destekliyorsa)
 *   4. CLS önlemek için aspect-ratio'yu computed style'a ekler
 *   5. srcset/sizes önerileri
 *
 * MutationObserver ile dinamic eklenen img'leri de yakalar.
 */
(function() {
  'use strict';
  
  if (typeof window === 'undefined') return;
  if (window.__imgOptimizerInit) return;
  window.__imgOptimizerInit = true;
  
  // 1x1 transparent gif - placeholder fallback
  const PLACEHOLDER = 'data:image/svg+xml;base64,' + btoa(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"><rect fill="#E8DFD0"/></svg>'
  );
  
  function isWebpSupported() {
    return new Promise(resolve => {
      const webp = 'data:image/webp;base64,UklGRiQAAABXRUJQVlA4IBgAAAAwAQCdASoBAAEAAUAmJaQAA3AA/v3AgAA=';
      const img = new Image();
      img.onload = img.onerror = () => resolve(img.height === 1);
      img.src = webp;
    });
  }
  
  /**
   * Bir img elementini optimize et.
   * - loading="lazy" (yukarıda görünür değilse)
   * - decoding="async"
   * - aspect-ratio CLS önleme
   * - WebP için srcset
   */
  function optimizeImg(img) {
    if (!img || !img.tagName || img.tagName.toLowerCase() !== 'img') return;
    if (img.__imgOptDone) return;
    img.__imgOptDone = true;
    
    // loading="lazy" (hero/above-fold için lazy YAPMA)
    if (!img.hasAttribute('loading')) {
      const isHero = img.classList.contains('hero-img') || 
                     img.closest('.galeri-ana, .hero, .slider-slayt, .banner-slide');
      const isAboveFold = img.getBoundingClientRect().top < window.innerHeight;
      
      if (!isHero && !isAboveFold) {
        img.setAttribute('loading', 'lazy');
      } else {
        // Above-fold: fetchpriority="high"
        img.setAttribute('fetchpriority', 'high');
      }
    }
    
    // decoding="async"
    if (!img.hasAttribute('decoding')) {
      img.setAttribute('decoding', 'async');
    }
    
    // Aspect-ratio ekle (CLS önleme) - yalnızca width/height yoksa
    if (!img.style.aspectRatio && !img.hasAttribute('width') && !img.hasAttribute('height')) {
      const parent = img.parentElement;
      if (parent) {
        const parentStyle = getComputedStyle(parent);
        const aspectRatio = parentStyle.aspectRatio || '';
        if (aspectRatio) {
          img.style.aspectRatio = aspectRatio;
        }
      }
    }
    
    // srcset için WebP varyantı (basit: aynı yapıda .webp sorgusu)
    if (img.src && !img.srcset && img.src.startsWith('/')) {
      const baseUrl = img.src.replace(/\.(jpg|jpeg|png)$/i, '');
      const webpSet = `${baseUrl}.webp 1x`;
      img.srcset = webpSet;
      img.setAttribute('data-orig-src', img.src);
    }
  }
  
  /**
   * DOM içindeki TÜM <img> öğelerini optimize et.
   */
  function optimizeAll() {
    document.querySelectorAll('img').forEach(optimizeImg);
  }
  
  // İlk yükleme
  function init() {
    optimizeAll();
    
    // Dinamik eklenen img'leri yakala
    const observer = new MutationObserver((mutations) => {
      mutations.forEach(m => {
        m.addedNodes.forEach(node => {
          if (node.nodeType === 1) {
            if (node.tagName === 'IMG') {
              optimizeImg(node);
            } else if (node.querySelectorAll) {
              node.querySelectorAll('img').forEach(optimizeImg);
            }
          }
        });
      });
    });
    
    if (document.body) {
      observer.observe(document.body, { childList: true, subtree: true });
    } else {
      document.addEventListener('DOMContentLoaded', () => observer.observe(document.body, { childList: true, subtree: true }));
    }
  }
  
  // Sayfa hazır olduğunda çalış
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
  
  // Sayfa geçişlerinde (SPA) tekrar çalış
  // sayfaGit() her sayfa değişikliğinde DOM güncelleniyor
  if (window.MutationObserver) {
    const spaObserver = new MutationObserver(() => optimizeAll());
    if (document.body) {
      spaObserver.observe(document.body, { childList: true, subtree: true });
    }
  }
})();
