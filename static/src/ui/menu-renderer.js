/**
 * Public menü render edici.
 * Admin CMS'den /api/menu/{slug} çağırır ve navbar/footer'a yazar.
 * Sırasıyla: 'header' (üst nav) ve 'footer' (alt menü) için çalışır.
 * Boşsa DOM'a dokunmaz (hardcoded fallback korunur).
 */
export async function renderMenus() {
  try {
    await Promise.all([renderHeaderMenu(), renderFooterMenu()]);
  } catch { /* sessiz: hardcoded menü korunur */ }
}

async function fetchMenu(slug) {
  try {
    const r = await fetch(`/api/menu/${encodeURIComponent(slug)}`);
    if (!r.ok) return null;
    const j = await r.json();
    if (!j || !j.success) return null;
    return j.data || null;
  } catch { return null; }
}

function isActive(item) {
  if (!item || !item.url) return false;
  return item.url === window.location.hash.replace('#', '');
}

function itemHtml(item) {
  const label = item.ikon ? `${item.ikon} ${item.label || ''}` : (item.label || '');
  const aktif = isActive(item) ? ' class="nav-link aktif"' : ' class="nav-link"';
  // İç sayfa bağlantısı: #slug ile hash yönlendirmesi
  if (item.url && item.url.startsWith('/sayfa/')) {
    const slug = item.url.replace('/sayfa/', '');
    const url = `#/sayfa/${slug}`;
    return `<a href="${url}" onclick="event.preventDefault();sayfaGit('sayfa',{slug:'${slug}'});document.querySelector('[data-sayfa=anasayfa]').classList.remove('aktif')"${aktif}>${label}</a>`;
  }
  if (item.url === '/' || item.url === 'anasayfa' || !item.url)
    return `<span${aktif} data-sayfa="anasayfa" onclick="sayfaGit('anasayfa')">${label}</span>`;
  const sayfalar = { 'ilanlar':'ilanlar','blog':'blog','detay':'detay' };
  if (sayfalar[item.url])
    return `<span${aktif} data-sayfa="${sayfalar[item.url]}" onclick="sayfaGit('${sayfalar[item.url]}')">${label}</span>`;
  // Dış link
  return `<a href="${item.url}" target="_blank" rel="noopener"${aktif.replace('class="nav-link','class="nav-link-ext')} style="text-decoration:none">${label}</a>`;
}

async function renderHeaderMenu() {
  const menu = await fetchMenu('header-menu');
  if (!menu || !menu.length) return;
  const kont = document.querySelector('.nav-links');
  if (!kont) return;
  // Admin kelimesi Yok: sadece menü öğelerini yaz, fallback'i tamamen değiştir
  kont.innerHTML = menu.map(itemHtml).join('');
}

async function renderFooterMenu() {
  const menu = await fetchMenu('footer-menu');
  if (!menu || !menu.length) return;
  const kont = document.getElementById('footer-menu');
  if (!kont) return;
  kont.innerHTML = menu.map(i => {
    const label = i.ikon ? `${i.ikon} ${i.label||''}` : (i.label || '');
    if (i.url && i.url.startsWith('/sayfa/')) {
      const slug = i.url.replace('/sayfa/','');
      return `<a href="#/sayfa/${slug}" onclick="event.preventDefault();sayfaGit('sayfa',{slug:'${slug}'});" style="color:rgba(255,255,255,.7);text-decoration:none;font-size:.85rem;padding:.25rem 0;display:block">${label}</a>`;
    }
    if (!i.url || i.url === '/' || i.url === 'anasayfa')
      return `<a href="#" onclick="event.preventDefault();sayfaGit('anasayfa');" style="color:rgba(255,255,255,.7);text-decoration:none;font-size:.85rem;padding:.25rem 0;display:block">${label}</a>`;
    const sayfalar = { 'ilanlar':'ilanlar','blog':'blog' };
    if (sayfalar[i.url])
      return `<a href="#" onclick="event.preventDefault();sayfaGit('${sayfalar[i.url]}');" style="color:rgba(255,255,255,.7);text-decoration:none;font-size:.85rem;padding:.25rem 0;display:block">${label}</a>`;
    return `<a href="${i.url}" target="_blank" rel="noopener" style="color:rgba(255,255,255,.7);text-decoration:none;font-size:.85rem;padding:.25rem 0;display:block">${label}</a>`;
  }).join('');
}

// Otomatik render (ES module import ile çağrıldığında)
if (typeof window !== 'undefined') {
  window.renderMenus = renderMenus;
  // DOM hazır olunca render
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', renderMenus);
  } else {
    renderMenus();
  }
}
