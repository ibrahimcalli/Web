/**
 * Template Engine — Frontend Renderer
 * 
 * Anasayfayı dinamik section'lardan oluşturur.
 * Kullanım:
 *   import { templateRender } from "./template-renderer.js";
 *   templateRender.renderHomepage();
 */
export class TemplateRenderer {
  constructor(api, config = {}) {
    this.api = api;
    this.container = config.container || document.getElementById('app') || document.body;
    this.templateSlug = config.templateSlug || null;
    this.settings = {};
  }

  /**
   * Anasayfayı section'lardan oluştur.
   * 1. API'den section listesini al
   * 2. Her section için HTML partial'ı yükle
   * 3. Section'ları sırayla render et
   * 4. Dinamik verileri doldur
   */
  async renderHomepage() {
    try {
      // Section listesini al
      const query = this.templateSlug ? `?template=${this.templateSlug}` : '';
      const sections = await this.api.request(`/api/template/homepage${query}`);
      if (!sections || !sections.length) return;

      // Template config + site ayarlarını al
      const slug = this.templateSlug || sections[0]?.ayarlar?.template_slug || 'estate-modern';
      this.settings = await this.api.request('/api/ayarlar').catch(() => ({}));

      // Her section için partial yükle ve render et
      for (const section of sections) {
        await this._renderSection(slug, section);
      }

      // Dinamik veri bağlantıları
      this._bindDynamicData(sections);
    } catch (e) {
      console.warn('Template render hatası:', e);
    }
  }

  async _renderSection(templateSlug, section) {
    const partialUrl = `/api/template/section/${templateSlug}/${section.section_key}`;
    let html;
    try {
      const resp = await fetch(partialUrl);
      if (!resp.ok) return;
      html = await resp.text();
    } catch {
      return;
    }

    // Template literal değişkenlerini doldur
    const rendered = this._evalTemplate(html, {
      data: section,
      settings: this.settings,
    });

    // DOM'a ekle
    const temp = document.createElement('div');
    temp.innerHTML = rendered;
    const el = temp.firstElementChild;
    if (el) {
      this.container.appendChild(el);
    }
  }

  _evalTemplate(tpl, ctx) {
    return tpl.replace(/\$\{(.+?)\}/g, (_, expr) => {
      try {
        const fn = new Function(...Object.keys(ctx), `return ${expr}`);
        return fn(...Object.values(ctx));
      } catch {
        return '';
      }
    });
  }

  _bindDynamicData(sections) {
    // Portföy grid
    if (document.getElementById('portfolio-grid')) {
      this._loadPortfolio();
    }
    // Blog grid
    if (document.getElementById('blog-grid')) {
      this._loadBlog();
    }
    // Footer menu
    if (document.getElementById('footer-menu')) {
      this._loadFooterMenu();
    }
  }

  async _loadPortfolio() {
    try {
      const items = await this.api.getPortfoyler({ durum: 'Aktif', limit: 6 });
      const grid = document.getElementById('portfolio-grid');
      if (!grid || !items) return;
      grid.innerHTML = items.map(p => `
        <div class="portfolio-kart" onclick="sayfaGit('detay',${p.id})">
          <div class="portfolio-resim" style="background-image:url(${p.kapak_resim || '/static/img/no-image.svg'})">
            <div class="portfolio-overlay">
              <span>${p.baslik}</span>
              <small>${p.il} / ${p.ilce}</small>
            </div>
          </div>
          <div class="portfolio-info">
            <h3>${p.baslik}</h3>
            <p>${p.fiyat || ''} ${p.para_birimi || ''}</p>
          </div>
        </div>
      `).join('');
    } catch {}
  }

  async _loadBlog() {
    try {
      const items = await this.api.getBlog({ limit: 3 });
      const grid = document.getElementById('blog-grid');
      if (!grid || !items) return;
      grid.innerHTML = items.map(y => `
        <div class="blog-kart" onclick='sayfaGit("blog-detay",${JSON.stringify(y).replace(/'/g,"&#39;")})'>
          ${y.kapak_resim ? `<div class="blog-resim" style="background-image:url(${y.kapak_resim})"></div>` : ''}
          <div class="blog-ic">
            <h3>${y.baslik}</h3>
            <p>${(y.ozet || '').slice(0, 120)}...</p>
            <small>${(y.olusturma || '').slice(0, 10)}</small>
          </div>
        </div>
      `).join('');
    } catch {}
  }

  async _loadFooterMenu() {
    try {
      const menu = await this.api.request('/api/menu/footer-menu').catch(() => []);
      const ul = document.getElementById('footer-menu');
      if (!ul) return;
      ul.innerHTML = menu.map(m => `
        <li><a href="${m.hedef_url || '#'}">${m.baslik}</a></li>
      `).join('');
    } catch {}
  }
}

export default TemplateRenderer;
