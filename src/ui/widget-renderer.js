/**
 * Public widget render edici.
 * /api/public/widgets/{lokasyon} çağırır ve ilgili data-* attribute'lu
 * elementlerin içine yazar.
 *
 * Lokasyonlar: home-top, home-bottom, footer-top, sidebar, all-pages,
 *   anasayfa-top, anasayfa-bottom, header, footer, floating
 * Widget tipleri: html (serbest HTML), contact-form, cookie-banner,
 *   social-bar, instagram-feed, google-maps, telefon-butonu, whatsapp, info-kart,
 *   embed, script, link
 *
 * Backend şeması: { id, anahtar, ad, aciklama, tip, aktif, ayarlar(JSON), konum, sira }
 *   - ayarlar JSON'ı içindeki `icerik` alanı widget içeriğini taşır (yeni yönetim paneliyle uyumlu)
 *   - Eski tarz `w.icerik` artık yok; render fonksiyonları `wIcerik(w)` okuyarak uyumlu kalır.
 */

console.log('[widget-renderer] Module loaded, readyState:', document.readyState);

function parseAyarlar(w) {
  if (w._ayarObj !== undefined) return w._ayarObj;
  try { w._ayarObj = JSON.parse(w.ayarlar || '{}'); }
  catch { w._ayarObj = {}; }
  return w._ayarObj;
}
function wIcerik(w) {
  if (w.icerik) return w.icerik;
  const ay = parseAyarlar(w);
  return ay.icerik || ay.html || ay.embed || '';
}

const WIDGET_RENDERERS = {
  'html':            (w) => wIcerik(w) || '',
  'embed':           (w) => wIcerik(w) || '',
  'script':          (w) => {
    // script tag'leri doğrudan innerHTML ile çalışmaz — DOM'a inject et
    const html = wIcerik(w) || '';
    return `<div data-widget-script>${html}</div>`;
  },
  'link':            (w) => {
    const ay = parseAyarlar(w);
    if (w.anahtar === 'whatsapp' && (w.konum === 'floating' || ay.konum === 'floating')) {
      const num = ((ay && ay.sosyal_wa) || ay.telefon || '').replace(/[^0-9]/g,'');
      if (!num) return '';
      const mesaj = encodeURIComponent(`Merhaba, ${ay.site_adi || 'Portföy Gayrimenkul'} sitesinden ulaşıyorum.`);
      return `<a href="https://wa.me/${num}?text=${mesaj}" target="_blank" rel="noopener" aria-label="WhatsApp ile iletişime geçin" class="wa-btn" style="position:fixed;bottom:1.5rem;right:1.5rem;z-index:998;display:flex;align-items:center;justify-content:center;width:54px;height:54px;border-radius:50%;background:#25D366;color:#fff;font-size:1.4rem;text-decoration:none;box-shadow:0 4px 14px rgba(37,211,102,.5)">💬</a>`;
    }
    const url = ay.url || wIcerik(w) || '#';
    const label = w.ad || ay.label || 'Bağlantı';
    return `<a href="${url}" target="_blank" rel="noopener" style="text-decoration:none;color:var(--kiremit)">${label}</a>`;
  },
  'contact-form':    (w) => `<form class="widget-form" onsubmit="return widgetFormGonder(event,'${w.anahtar||''}')" style="display:grid;gap:.5rem;max-width:520px">
      <input class="form-girdi" name="ad" placeholder="Adınız" required>
      <input class="form-girdi" name="email" type="email" placeholder="E-posta" required>
      <textarea class="form-girdi" name="mesaj" rows="3" placeholder="Mesajınız" required></textarea>
      <button class="btn btn-kirm" type="submit">Gönder</button>
    </form>`,
  'cookie-banner':   (w) => `<div style="display:flex;gap:1rem;align-items:center;flex-wrap:wrap">
      <span>${wIcerik(w) || 'Bu site çerez kullanmaktadır.'}</span>
      <button class="btn btn-kirm btn-sm" onclick="this.closest('[data-widget-container]').remove();document.cookie='cookie_ok=1;path=/;max-age=31536000';">Tamam</button>
    </div>`,
  'social-bar':      (w, ay) => {
    const items = [];
    if (ay.sosyal_wa)  items.push(`<a href="https://wa.me/${ay.sosyal_wa.replace(/[^0-9]/g,'')}" target="_blank" rel="noopener" style="display:inline-flex;width:34px;height:34px;border-radius:50%;background:#25D366;color:#fff;align-items:center;justify-content:center;text-decoration:none">💬</a>`);
    if (ay.sosyal_ig)  items.push(`<a href="${ay.sosyal_ig.startsWith('http')?ay.sosyal_ig:('https://instagram.com/'+ay.sosyal_ig.replace('@',''))}" target="_blank" rel="noopener" style="display:inline-flex;width:34px;height:34px;border-radius:50%;background:#E1306C;color:#fff;align-items:center;justify-content:center;text-decoration:none">📷</a>`);
    if (ay.sosyal_fb)  items.push(`<a href="${ay.sosyal_fb.startsWith('http')?ay.sosyal_fb:('https://facebook.com/'+ay.sosyal_fb)}" target="_blank" rel="noopener" style="display:inline-flex;width:34px;height:34px;border-radius:50%;background:#1877F2;color:#fff;align-items:center;justify-content:center;text-decoration:none">👍</a>`);
    return items.length ? `<div class="footer-sosyal" style="display:flex;gap:.5rem">${items.join('')}</div>` : '';
  },
  'whatsapp':        (w, ay) => {
    const num = (ay && ay.sosyal_wa || '').replace(/[^0-9]/g,'');
    if (!num) return '';
    const mesaj = encodeURIComponent(`Merhaba, ${ay.site_adi || 'Portföy Gayrimenkul'} sitesinden ulaşıyorum.`);
    return `<a href="https://wa.me/${num}?text=${mesaj}" target="_blank" rel="noopener" class="wa-btn" style="position:fixed;bottom:1.5rem;right:1.5rem;z-index:998;display:flex;align-items:center;justify-content:center;width:54px;height:54px;border-radius:50%;background:#25D366;color:#fff;font-size:1.4rem;text-decoration:none;box-shadow:0 4px 14px rgba(37,211,102,.5)">💬</a>`;
  },
  'google-maps':     (w) => wIcerik(w) || '',
  'telefon-butonu':  (w, ay) => {
    const t = (ay && ay.telefon) || (parseAyarlar(w).telefon) || '';
    if (!t) return '';
    return `<a href="tel:${t}" style="display:inline-flex;align-items:center;gap:.4rem;padding:.5rem 1rem;border-radius:var(--r-sm);background:var(--kiremit);color:#fff;text-decoration:none;font-weight:600">📞 ${t}</a>`;
  },
  'instagram-feed':  (w) => {
    const html = wIcerik(w);
    // Mevcut kullanım: html iframe etiketleri içerebilir — doğrudan bas
    return html || '';
  },
  'info-kart':       (w) => {
    const ay = parseAyarlar(w);
    const baslik = ay.baslik || w.ad || '';
    return `<div class="kart" style="padding:1rem;background:var(--beyaz);border-radius:var(--r);box-shadow:var(--dept-shadow)">
      ${baslik ? `<h4 style="margin:0 0 .5rem">${baslik}</h4>`:''}
      <div>${wIcerik(w)||''}</div>
    </div>`;
  },
};

const WIDGET_LOKASYONLAR = [
  'all-pages', 'home-top', 'home-bottom',
  'anasayfa-top', 'anasayfa-bottom',
  'footer-top', 'sidebar', 'header', 'footer', 'floating',
];

const widgetStyleEl = document.createElement('style');
widgetStyleEl.textContent = `
[data-widget-container] { margin: 1rem 0; }
[data-widget-container="all-pages"] { display:block; }
[data-widget-container="home-top"], [data-widget-container="anasayfa-top"] { padding: 1rem clamp(1rem,4vw,2rem) 0; }
[data-widget-container="home-bottom"], [data-widget-container="anasayfa-bottom"] { padding: 0 clamp(1rem,4vw,2rem) 1rem; }
body > [data-widget-container="footer-top"] { background:var(--krem); padding:1.5rem clamp(1rem,4vw,2rem); border-radius:var(--r); }
[data-widget-container="floating"] { position:fixed; bottom:1.5rem; right:1.5rem; z-index:998; }
[data-widget-container="sidebar"] { padding: 1rem; }
`;
document.head.appendChild(widgetStyleEl);

function ensureContainer(lokasyon) {
  let kont = document.querySelector(`[data-widget-container="${lokasyon}"]`);
  if (kont) return kont;
  kont = document.createElement('div');
  kont.setAttribute('data-widget-container', lokasyon);

  // Yerleştirme stratejileri
  if (lokasyon === 'footer-top' || lokasyon === 'all-pages') {
    // Tüm sayfalarda görünecek — footer üstüne
    const footer = document.querySelector('.footer') || document.querySelector('footer') || document.getElementById('footer');
    if (footer && footer.parentNode) footer.parentNode.insertBefore(kont, footer);
    else document.body.appendChild(kont);
  } else if (lokasyon === 'home-top' || lokasyon === 'anasayfa-top') {
    const anasayfa = document.getElementById('sayfa-anasayfa');
    if (anasayfa) anasayfa.insertBefore(kont, anasayfa.firstChild);
    else document.body.insertBefore(kont, document.body.firstChild);
  } else if (lokasyon === 'home-bottom' || lokasyon === 'anasayfa-bottom') {
    const anasayfa = document.getElementById('sayfa-anasayfa');
    if (anasayfa) anasayfa.appendChild(kont);
    else document.body.appendChild(kont);
  } else if (lokasyon === 'header') {
    const nav = document.querySelector('.nav');
    if (nav && nav.parentNode) nav.parentNode.insertBefore(kont, nav.nextSibling);
    else document.body.insertBefore(kont, document.body.firstChild);
  } else if (lokasyon === 'footer') {
    const footer = document.querySelector('.footer') || document.querySelector('footer') || document.getElementById('footer');
    if (footer) footer.appendChild(kont);
    else document.body.appendChild(kont);
  } else if (lokasyon === 'floating') {
    document.body.appendChild(kont);
  } else if (lokasyon === 'sidebar') {
    // Sidebar için ana içeriğin yanına ya da uygun boş yere ekle
    const adminSidebar = document.querySelector('.admin-sidebar');
    if (adminSidebar) { /* admin sayfasında yükleme */ kont = null; }
    else {
      const anasayfa = document.getElementById('sayfa-anasayfa');
      if (anasayfa) {
        // Anasayfa içeriğini sarmala — basitçe sayfanın sonuna ekle
        anasayfa.appendChild(kont);
      } else document.body.appendChild(kont);
    }
  } else {
    document.body.appendChild(kont);
  }
  return kont;
}

export async function renderWidgets() {
  console.log('[widget-renderer] renderWidgets called');
  const ay = await fetch('/api/ayarlar').then(r=>r.json()).then(j=>j && j.success ? j.data : {}).catch(()=>({}));
  for (const lokasyon of WIDGET_LOKASYONLAR) {
    try {
      console.log('[widget-renderer] Fetching widgets for:', lokasyon);
      const r = await fetch(`/api/public/widgets/${encodeURIComponent(lokasyon)}`);
      if (!r.ok) continue;
      const j = await r.json();
      if (!j || !j.success) continue;
      const widgets = j.data || [];
      console.log('[widget-renderer] Got widgets for', lokasyon, ':', widgets);
      // aktif olanları al (backend zaten filtreler ama garanti)
      const aktif = widgets.filter(w => w.aktif !== false && w.aktif !== 0);
      if (!aktif.length) continue;
      const kont = ensureContainer(lokasyon);
      if (!kont) continue;
      // sıraya göre sırala
      aktif.sort((a,b) => (a.sira||0) - (b.sira||0));
      const html = aktif.map(w => {
        const rnd = WIDGET_RENDERERS[w.tip] || (() => wIcerik(w) || '');
        const inner = rnd(w, ay);
        if (!inner) return '';
        return `<div data-widget-id="${w.id}" data-widget-key="${w.anahtar||''}">${inner}</div>`;
      }).filter(Boolean).join('');
      if (!html) continue;
      kont.innerHTML = html;
      kont.style.display = '';

      // script tag'leri innerHTML ile çalışmaz — DOM'a inject et
      kont.querySelectorAll('[data-widget-script] script').forEach(s => {
        const ns = document.createElement('script');
        if (s.src) ns.src = s.src;
        else ns.textContent = s.textContent;
        s.replaceWith(ns);
      });
    } catch { /* sessiz: Kodun devamı */ }
  }
}

window.renderWidgets = renderWidgets;
window.widgetFormGonder = async function(e, slug) {
  e.preventDefault();
  const fd = new FormData(e.target);
  try {
    await fetch('/api/istekler', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({
        ad_soyad: fd.get('ad'), email: fd.get('email'),
        mesaj: fd.get('mesaj'), telefon:'', portfoy_id:null,
      }),
    });
    e.target.innerHTML = '<p style="color:var(--kiremit);font-weight:600;text-align:center;padding:1rem">✓ Teşekkürler! Mesajınız alındı.</p>';
  } catch {
    e.target.innerHTML = '<p style="color:var(--danger);font-weight:600;text-align:center;padding:1rem">⚠ Mesaj gönderilemedi. Lütfen tekrar deneyin.</p>';
  }
  return false;
};

if (typeof window !== 'undefined') {
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', renderWidgets);
  else renderWidgets();
  // Sayfa geçişlerinde widget'ları yeniden bağla
  window.addEventListener('hashchange', () => renderWidgets());
}
