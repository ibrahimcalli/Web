/**
 * Public menü render edici.
 * Admin CMS'den /api/menu/{slug} çağırır ve navbar/footer/sidebar'a yazar.
 * Sırasıyla: 'header-menu' (üst nav), 'footer-menu' (alt menü),
 * 'sidebar-menu' (yan menü) için çalışır.
 * Boşsa DOM'a dokunmaz (hardcoded fallback korunur).
 *
 * Backend şeması (menu_items):
 *   { id, baslik, ikon, hedef_tip, hedef_url, hedef_page_id,
 *     page_slug, izin_rol, sira, aktif, alt_ogeler:[] }
 */
const MENU_SLOTLARI = {
  'header-menu':  { kont: '.nav-links',         render: renderHeaderItem },
  'footer-menu':  { kont: '#footer-menu',         render: renderFooterItem },
  'sidebar-menu': { kont: '#sidebar-menu-widget', render: renderSidebarItem },
};

export async function renderMenus() {
  try {
    await Promise.all(Object.keys(MENU_SLOTLARI).map(renderSlot));
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

function normalizeUrl(item) {
  // Backend'den gelen item.hedef_url — sayfa slug olabilir, ilanlar/blog gibi
  // bilinen SPA route'ları olabilir ya da harici URL.
  let url = (item.hedef_url || item.url || '').trim();
  if (!url) {
    // pages tablosuna bağlıysa page_slug ile /sayfa/<slug> türet
    if (item.page_slug) url = `/sayfa/${item.page_slug}`;
    else url = '/';
  }
  return url;
}

function resolveTarget(item) {
  const url = normalizeUrl(item);
  const lower = url.toLowerCase();
  if (item.page_slug || item.hedef_page_id) {
    return { kind: 'sayfa', slug: item.page_slug || lower.replace(/^\/sayfa\//, '').replace(/^#\/sayfa\//, '') };
  }
  if (lower.startsWith('/sayfa/') || lower.startsWith('#/sayfa/')) {
    return { kind: 'sayfa', slug: lower.replace(/^#?\/sayfa\//, '').split(/[?#]/)[0] };
  }
  if (item.hedef_tip === 'blog' || /blog-detay\//i.test(url)) {
    const m = url.match(/blog-detay\/([^/?#]+)/i);
    return { kind: 'blog-detay', slug: m ? decodeURIComponent(m[1]) : '' };
  }
  if (item.hedef_tip === 'portfoy' || /\/detay\/\d+/i.test(url)) {
    const m = url.match(/detay\/(\d+)/i);
    return { kind: 'detay', id: m ? Number(m[1]) : null };
  }
  if (lower === '/' || lower === 'anasayfa') return { kind: 'anasayfa' };
  if (lower === '/#iletisim' || lower === '/iletisim' || lower === '#iletisim') {
    return { kind: 'sayfa', slug: 'iletisim' };
  }
  if (lower === '/#blog' || lower === '/blog' || lower === '#blog') return { kind: 'blog' };
  if (lower === '/#ilanlar' || lower === '/ilanlar' || lower === '#ilanlar') return { kind: 'ilanlar' };
  if (/^https?:\/\//i.test(url)) return { kind: 'harici', url };
  return { kind: 'ozel', url };
}

function isActive(item) {
  const target = resolveTarget(item);
  if (target.kind === 'anasayfa') {
    return window.location.hash === '' || window.location.hash === '#';
  }
  const h = window.location.hash.replace(/^#/, '');
  const hmain = h.split('/')[0];
  if (target.kind === 'sayfa') return h === `/sayfa/${target.slug}`;
  if (target.kind === 'blog-detay') return h.startsWith(`/blog-detay/${target.slug}`);
  if (target.kind === 'detay') return h.startsWith(`/detay/${target.id}`);
  if (target.kind === 'blog') return h === '/blog' || h === 'blog' || hmain === 'blog';
  if (target.kind === 'ilanlar') return h === '/ilanlar' || h === 'ilanlar' || hmain === 'ilanlar';
  return h === target.url || hmain === target.url || hmain === (target.url.replace(/^\//, ''));
}

function esc(s) {
  if (s == null) return '';
  return String(s).replace(/&/g, '&').replace(/</g, '<').replace(/>/g, '>').replace(/"/g, '"').replace(/'/g, '&#39;');
}

function labelOf(item) {
  const b = esc(item.baslik || item.label || '');
  const ik = esc(item.ikon || '');
  const label = ik ? `${ik} ${b}` : b;
  return label;
}

// Header için tek öğe HTML (alt menü destekli)
function renderHeaderItem(item, childHtml = '') {
  const label = labelOf(item);
  const url = normalizeUrl(item);
  const target = resolveTarget(item);
  const aktif = isActive(item) ? ' aktif' : '';
  const harici = item.hedef_tip === 'harici' || /^https?:\/\//i.test(url);

  // Sayfa bağlantısı: #/sayfa/<slug>
  if (target.kind === 'sayfa') {
    const slug = target.slug;
    return `<a href="#/sayfa/${slug}" class="nav-link${aktif}" onclick="event.preventDefault();sayfaGit('sayfa',{slug:'${slug}'});">${label}</a>${childHtml}`;
  }
  // Anasayfa
  if (target.kind === 'anasayfa') {
    return `<span class="nav-link${aktif}" data-sayfa="anasayfa" onclick="sayfaGit('anasayfa')">${label}</span>${childHtml}`;
  }
  if (target.kind === 'blog-detay') {
    const slug = target.slug || '';
    return `<a href="#/blog-detay/${slug}" class="nav-link${aktif}" onclick="event.preventDefault();sayfaGit('blog-detay',{slug:'${slug}'});">${label}</a>${childHtml}`;
  }
  if (target.kind === 'detay') {
    const id = target.id || '';
    return `<a href="#/detay/${id}" class="nav-link${aktif}" onclick="event.preventDefault();sayfaGit('detay',{id:${id}});">${label}</a>${childHtml}`;
  }
  // Bilinen SPA rotaları
  if (!harici) {
    const known = { 'ilanlar':'ilanlar', 'blog':'blog', 'detay':'detay' };
    const key = url.replace(/^\//, '');
    if (known[key]) {
      return `<span class="nav-link${aktif}" data-sayfa="${known[key]}" onclick="sayfaGit('${known[key]}')">${label}</span>${childHtml}`;
    }
  }
  // Dış link
  const safeUrl = encodeURI(url);
  return `<a href="${safeUrl}" target="${item.gosterim === '_self' ? '_self' : '_blank'}" rel="noopener" class="nav-link-ext${aktif}" style="text-decoration:none">${label}</a>${childHtml}`;
}

// Footer için tek öğe HTML
function renderFooterItem(item) {
  const label = labelOf(item);
  const url = normalizeUrl(item);
  const target = resolveTarget(item);
  const harici = item.hedef_tip === 'harici' || /^https?:\/\//i.test(url);
  const style = 'color:rgba(255,255,255,.7);text-decoration:none;font-size:.85rem;padding:.25rem 0;display:block';
  if (target.kind === 'sayfa') {
    const slug = target.slug;
    return `<a href="#/sayfa/${slug}" onclick="event.preventDefault();sayfaGit('sayfa',{slug:'${slug}'});" style="${style}">${label}</a>`;
  }
  if (target.kind === 'anasayfa') {
    return `<a href="#" onclick="event.preventDefault();sayfaGit('anasayfa');" style="${style}">${label}</a>`;
  }
  if (target.kind === 'blog-detay') {
    const slug = target.slug || '';
    return `<a href="#/blog-detay/${slug}" onclick="event.preventDefault();sayfaGit('blog-detay',{slug:'${slug}'});" style="${style}">${label}</a>`;
  }
  if (target.kind === 'detay') {
    const id = target.id || '';
    return `<a href="#/detay/${id}" onclick="event.preventDefault();sayfaGit('detay',{id:${id}});" style="${style}">${label}</a>`;
  }
  if (!harici) {
    const known = { 'ilanlar':'ilanlar', 'blog':'blog' };
    const key = url.replace(/^\//, '');
    if (known[key]) {
      return `<a href="#" onclick="event.preventDefault();sayfaGit('${known[key]}');" style="${style}">${label}</a>`;
    }
  }
  return `<a href="${encodeURI(url)}" target="_blank" rel="noopener" style="${style}">${label}</a>`;
}

// Sidebar için tek öğe HTML (alt menüsüz)
function renderSidebarItem(item) {
  return renderHeaderItem(item);
}

function itemHtmlTree(item, renderFn) {
  const child = (item.alt_ogeler && item.alt_ogeler.length)
    ? `<div class="nav-alt-menu">${item.alt_ogeler.map(c => renderFn(c)).join('')}</div>`
    : '';
  return renderFn(item, child);
}

async function renderSlot(slug) {
  const cfg = MENU_SLOTLARI[slug];
  if (!cfg) return;
  const menu = await fetchMenu(slug);
  if (!menu || !menu.length) return;
  const kont = document.querySelector(cfg.kont);
  if (!kont) return;
  kont.innerHTML = menu.map(i => itemHtmlTree(i, cfg.render)).join('');
  kont.style.display = '';
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
  // Sayfa geçişinde aktif öğeyi işaretle
  window.addEventListener('hashchange', () => renderMenus());
}
