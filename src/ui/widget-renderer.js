/**
 * Public widget render edici.
 * /api/public/widgets/{lokasyon} çağırır ve ilgili data-* attribute'lu
 * elementlerin içine yazar.
 *
 * Lokasyonlar: home-top, home-bottom, footer-top, sidebar, all-pages
 * Widget tipleri: html (serbest HTML), contact-form, cookie-banner,
 *   social-bar, instagram-feed, google-maps, telefon-butonu, whatsapp, info-kart
 */
const WIDGET_RENDERERS = {
  'html':            (w) => w.icerik || '',
  'contact-form':    (w) => `<form class="widget-form" onsubmit="return widgetFormGonder(event,'${w.slug||''}')" style="display:grid;gap:.5rem">
      <input class="form-girdi" name="ad" placeholder="Adınız" required>
      <input class="form-girdi" name="email" type="email" placeholder="E-posta" required>
      <textarea class="form-girdi" name="mesaj" rows="3" placeholder="Mesajınız" required></textarea>
      <button class="btn btn-kirm" type="submit">Gönder</button>
    </form>`,
  'cookie-banner':   (w) => `<div style="display:flex;gap:1rem;align-items:center;flex-wrap:wrap">
      <span>${w.icerik || 'Bu site çerez kullanmaktadır.'}</span>
      <button class="btn btn-kirm btn-sm" onclick="this.closest('[data-widget-container]').remove();document.cookie='cookie_ok=1;path=/';">Tamam</button>
    </div>`,
  'social-bar':      (w) => `<div class="footer-sosyal" style="display:flex;gap:.5rem"></div>`,
  'whatsapp':        (w, ay) => {
    const num = (ay && ay.sosyal_wa || '').replace(/[^0-9]/g,'');
    if (!num) return '';
    return `<a href="https://wa.me/${num}" target="_blank" class="wa-btn" style="position:fixed;bottom:1.5rem;right:1.5rem;z-index:998;display:flex;align-items:center;justify-content:center;width:54px;height:54px;border-radius:50%;background:#25D366;color:#fff;box-shadow:0 4px 14px rgba(37,211,102,.5)">💬</a>`;
  },
  'google-maps':     (w) => w.icerik || '',
  'telefon-butonu':  (w, ay) => {
    const t = ay && ay.telefon || '';
    if (!t) return '';
    return `<a href="tel:${t}" style="display:inline-flex;align-items:center;gap:.4rem;padding:.5rem 1rem;border-radius:var(--r-sm);background:var(--kiremit);color:#fff;text-decoration:none;font-weight:600">📞 ${t}</a>`;
  },
  'instagram-feed':  (w) => w.icerik ? `<iframe src="${w.icerik}" style="border:0;width:100%;min-height:400px"></iframe>` : '',
  'info-kart':       (w) => `<div class="kart" style="padding:1rem;background:var(--beyaz);border-radius:var(--r);box-shadow:var(--dept-shadow)">
      ${w.baslik ? `<h4 style="margin:0 0 .5rem">${w.baslik}</h4>`:''}
      <div>${w.icerik||''}</div>
    </div>`,
};

const WIDGET_LOKASYONLAR = ['home-top','home-bottom','footer-top','sidebar','all-pages','anasayfa-top','anasayfa-bottom'];

const widgetStyleEl = document.createElement('style');
widgetStyleEl.textContent = `
[data-widget-container] { margin: 1rem 0; }
[data-widget-container="all-pages"] { display:block; }
body > [data-widget-container="footer-top"] { background:var(--krem); padding:1.5rem clamp(1rem,4vw,2rem); border-radius:var(--r); }
`;
document.head.appendChild(widgetStyleEl);

export async function renderWidgets() {
  const ay = await fetch('/api/ayarlar').then(r=>r.json()).then(j=>j && j.success ? j.data : {}).catch(()=>({}));
  for (const lokasyon of WIDGET_LOKASYONLAR) {
    try {
      const r = await fetch(`/api/public/widgets/${encodeURIComponent(lokasyon)}`);
      if (!r.ok) continue;
      const j = await r.json();
      if (!j || !j.success) continue;
      const widgets = j.data || [];
      if (!widgets.length) continue;
      let kont = document.querySelector(`[data-widget-container="${lokasyon}"]`);
      if (!kont) {
        // Yerleştirme stratejileri
        if (lokasyon === 'footer-top' || lokasyon === 'all-pages') {
          kont = document.createElement('div');
          kont.setAttribute('data-widget-container', lokasyon);
          const footer = document.querySelector('footer') || document.querySelector('.footer') || document.getElementById('footer');
          if (footer && footer.parentNode) footer.parentNode.insertBefore(kont, footer);
        } else if (lokasyon === 'home-top' || lokasyon === 'anasayfa-top') {
          kont = document.createElement('div');
          kont.setAttribute('data-widget-container', lokasyon);
          const anasayfa = document.getElementById('sayfa-anasayfa');
          if (anasayfa) anasayfa.insertBefore(kont, anasayfa.firstChild);
        } else if (lokasyon === 'home-bottom' || lokasyon === 'anasayfa-bottom') {
          kont = document.createElement('div');
          kont.setAttribute('data-widget-container', lokasyon);
          document.body.appendChild(kont);
        }
      }
      if (!kont) continue;
      const html = widgets.map(w => {
        const rnd = WIDGET_RENDERERS[w.tip] || (() => w.icerik || '');
        return `<div data-widget-id="${w.id}" style="display:${w.aktif===false?'none':''}">${rnd(w, ay)}</div>`;
      }).join('');
      kont.innerHTML = html;
      kont.style.display = '';
    } catch { /* sessiz: Kodun devamı */ }
  }
}

window.renderWidgets = renderWidgets;
window.widgetFormGonder = async function(e, slug) {
  e.preventDefault();
  const fd = new FormData(e.target);
  await fetch('/api/istekler', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ ad_soyad: fd.get('ad'), email: fd.get('email'), mesaj: fd.get('mesaj'), telefon:'', portfoy_id:null }) });
  e.target.innerHTML = '<p style="color:var(--kiremit);font-weight:600;text-align:center;padding:1rem">✓ Teşekkürler! Mesajınız alındı.</p>';
  return false;
};

if (typeof window !== 'undefined') {
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', renderWidgets);
  else renderWidgets();
}
