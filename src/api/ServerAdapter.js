/**
 * Gerçek FastAPI sunucusuna bağlanan transport.
 * Path sabitleri yalnızca burada tutulur — UI katmanında /api/ geçmez.
 */
import { ApiError, JsonParseError, TimeoutError, detailToMessage } from "./errors.js";
import { toQuery } from "./catalog.js";

/** Kaynak → REST path eşlemesi (tek kaynak). */
const R = {
  giris: "/api/auth/giris",
  ben: "/api/auth/ben",
  sifreBaslat: "/api/auth/sifre-sifirlama-baslat",
  sifreTamamla: "/api/auth/sifre-sifirlama-tamamla",
  ayarlar: "/api/ayarlar",
  ayarlarAi: "/api/ayarlar/ai",
  bannerlar: "/api/bannerlar",
  bannerKonumlar: "/api/bannerlar/konumlar",
  blog: "/api/blog",
  portfoyler: "/api/portfoyler",
  istekler: "/api/istekler",
  kategoriler: "/api/kategoriler",
  alanlar: "/api/alanlar",
  istatistik: "/api/istatistik",
  kullanicilar: "/api/kullanicilar",
  kullaniciKayit: "/api/kullanicilar/kayit",
  kullaniciBen: "/api/kullanicilar/ben",
  logo: "/api/logo",
  logoYukle: "/api/logo/yukle",
  belgeParse: "/api/belge/parse",
  fiyatGenel: "/api/fiyat-analizi/genel",
};

export class ServerAdapter {
  /**
   * @param {{apiBase: string, timeout: number}} config
   * @param {{getToken: () => string}} tokenProvider
   */
  constructor(config, tokenProvider) {
    this.apiBase = (config.apiBase || "").replace(/\/$/, "");
    this.timeout = config.timeout || 10000;
    this.tokenProvider = tokenProvider;
  }

  /**
   * @private
   * @param {string} path
   * @param {RequestInit & {rawBody?: boolean, skipJson?: boolean}} [opts]
   */
  async _request(path, opts = {}) {
    const { rawBody, skipJson, headers: extraHeaders, ...fetchOpts } = opts;
    const headers = { ...(extraHeaders || {}) };

    if (!rawBody && fetchOpts.body && typeof fetchOpts.body === "string") {
      headers["Content-Type"] = headers["Content-Type"] || "application/json";
    }

    const token = this.tokenProvider.getToken();
    if (token) headers.Authorization = `Bearer ${token}`;

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeout);

    let response;
    try {
      response = await fetch(this.apiBase + path, {
        ...fetchOpts,
        headers,
        signal: controller.signal,
      });
    } catch (err) {
      clearTimeout(timer);
      if (err && err.name === "AbortError") throw new TimeoutError(this.timeout);
      throw new ApiError(
        0,
        "İnternet bağlantısı yok veya sunucuya ulaşılamıyor. Bağlantınızı kontrol edin."
      );
    }
    clearTimeout(timer);

    if (skipJson || (opts.method === "GET" && path.includes("/pdf"))) {
      if (!response.ok) {
        let detail = "";
        try {
          const j = await response.json();
          detail = detailToMessage(j.detail);
        } catch { /* ignore */ }
        throw new ApiError(response.status, detail);
      }
      return response;
    }

    let body = null;
    const text = await response.text();
    if (text) {
      try {
        body = JSON.parse(text);
      } catch {
        if (!response.ok) {
          throw new ApiError(response.status, text.slice(0, 200));
        }
        throw new JsonParseError();
      }
    }

    if (!response.ok) {
      throw new ApiError(response.status, detailToMessage(body && body.detail));
    }
    return body;
  }

  /** @param {string} email @param {string} sifre */
  async login(email, sifre) {
    return this._request(R.giris, {
      method: "POST",
      body: JSON.stringify({ email, sifre }),
    });
  }

  async logout() {
    return { mesaj: "Çıkış yapıldı" };
  }

  async getMe() {
    return this._request(R.ben);
  }

  async getAyarlar() {
    return this._request(R.ayarlar);
  }

  async updateAyarlar(ayarlar) {
    return this._request(R.ayarlar, { method: "PUT", body: JSON.stringify({ ayarlar }) });
  }

  async updateAiAyarlar(data) {
    return this._request(R.ayarlarAi, { method: "PUT", body: JSON.stringify(data) });
  }

  async getBannerlar(params = {}) {
    return this._request(R.bannerlar + toQuery(params));
  }

  async getBannerKonumlar() {
    return this._request(R.bannerKonumlar);
  }

  async getBlog(params = {}) {
    return this._request(R.blog + toQuery(params));
  }

  async getBlogBySlugOrId(key) {
    return this._request(`${R.blog}/${encodeURIComponent(key)}`);
  }

  async getPortfoyler(params = {}) {
    return this._request(R.portfoyler + toQuery(params));
  }

  async getPortfoy(id) {
    return this._request(`${R.portfoyler}/${id}`);
  }

  async arama(q) {
    return this.getPortfoyler({ arama: q, durum: "Aktif" });
  }

  async iletisim(data) {
    return this._request(R.istekler, { method: "POST", body: JSON.stringify(data) });
  }

  async getIstekler() {
    return this._request(R.istekler);
  }

  async updateIstekDurum(id, durum) {
    return this._request(`${R.istekler}/${id}/durum` + toQuery({ durum }), { method: "PATCH" });
  }

  async getKategoriler() {
    return this._request(R.kategoriler);
  }

  async getAlanlar(anaKat, altKat, ilanTipi = "") {
    return this._request(
      R.alanlar +
        toQuery({ ana_kat: anaKat, alt_kat: altKat, ilan_tipi: ilanTipi })
    );
  }

  async getIstatistik() {
    return this._request(R.istatistik);
  }

  async getKullanicilar() {
    return this._request(R.kullanicilar);
  }

  async getKullaniciBen() {
    return this._request(R.kullaniciBen);
  }

  async getSahipProfil(pid) {
    return this._request(`${R.portfoyler}/${pid}/sahip-profil`);
  }

  async getFiyatAnalizi(id) {
    return this._request(`${R.portfoyler}/${id}/fiyat-analizi`);
  }

  async getFiyatAnaliziGenel() {
    return this._request(R.fiyatGenel);
  }

  /**
   * @param {string} resource
   * @param {object} data
   */
  async save(resource, data) {
    const map = {
      portfoyler: R.portfoyler,
      blog: R.blog,
      bannerlar: R.bannerlar,
      kullanicilar: R.kullanicilar,
      "kullanicilar/kayit": R.kullaniciKayit,
      "auth/sifre-sifirlama-baslat": R.sifreBaslat,
      "auth/sifre-sifirlama-tamamla": R.sifreTamamla,
    };
    const path = map[resource];
    if (!path) throw new ApiError(404, `Bilinmeyen kaynak: ${resource}`);
    return this._request(path, { method: "POST", body: JSON.stringify(data) });
  }

  /**
   * @param {string} resource
   * @param {string|number} id
   * @param {object} data
   * @param {{action?: string, query?: object}} [opts]
   */
  async update(resource, id, data = {}, opts = {}) {
    const action = opts.action || "";
    const q = opts.query || {};

    if (resource === "portfoyler" && action === "durum") {
      return this._request(`${R.portfoyler}/${id}/durum` + toQuery(q), { method: "PATCH" });
    }
    if (resource === "portfoyler" && action === "resim-sirala") {
      return this._request(`${R.portfoyler}/${id}/resim/sirala`, {
        method: "PUT",
        body: JSON.stringify(data),
      });
    }
    if (resource === "portfoyler" && action === "resim-kapak") {
      return this._request(`${R.portfoyler}/${id}/resim/kapak` + toQuery(q), { method: "PATCH" });
    }
    if (resource === "istekler" && action === "durum") {
      return this.updateIstekDurum(id, q.durum || data.durum);
    }
    if (resource === "bannerlar" && action === "aktif") {
      return this._request(`${R.bannerlar}/${id}/aktif` + toQuery(q), { method: "PATCH" });
    }
    if (resource === "kullanicilar" && action === "onayla") {
      return this._request(`${R.kullanicilar}/${id}/onayla`, { method: "PATCH" });
    }
    if (resource === "kullanicilar" && action === "onay-kaldir") {
      return this._request(`${R.kullanicilar}/${id}/onay-kaldir`, { method: "PATCH" });
    }
    if (resource === "kullanicilar" && action === "profil") {
      return this._request(`${R.kullanicilar}/profil`, { method: "PUT", body: JSON.stringify(data) });
    }
    if (resource === "kullanicilar" && action === "sifre") {
      return this._request(`${R.kullanicilar}/sifre`, { method: "PUT", body: JSON.stringify(data) });
    }
    if (resource === "ayarlar") {
      return this.updateAyarlar(data.ayarlar || data);
    }
    if (resource === "ayarlar/ai") {
      return this.updateAiAyarlar(data);
    }

    const map = {
      portfoyler: R.portfoyler,
      blog: R.blog,
      bannerlar: R.bannerlar,
    };
    const base = map[resource];
    if (!base) throw new ApiError(404, `Güncellenemedi: ${resource}`);
    return this._request(`${base}/${id}`, { method: "PUT", body: JSON.stringify(data) });
  }

  /**
   * @param {string} resource
   * @param {string|number} id
   * @param {{action?: string, query?: object}} [opts]
   */
  async delete(resource, id, opts = {}) {
    if (resource === "portfoyler" && opts.action === "resim") {
      return this._request(
        `${R.portfoyler}/${id}/resim` + toQuery(opts.query || {}),
        { method: "DELETE" }
      );
    }
    if (resource === "logo") {
      return this._request(R.logo, { method: "DELETE" });
    }
    if (resource === "bannerlar" && opts.action === "resim-sil") {
      return this._request(`${R.bannerlar}/${id}/resim-sil`, { method: "DELETE" });
    }
    const map = {
      portfoyler: R.portfoyler,
      blog: R.blog,
      bannerlar: R.bannerlar,
      kullanicilar: R.kullanicilar,
    };
    const base = map[resource];
    if (!base) throw new ApiError(404, `Bilinmeyen kaynak: ${resource}`);
    return this._request(`${base}/${id}`, { method: "DELETE" });
  }

  /**
   * @param {string} resource
   * @param {string|number|null} id
   * @param {FormData} formData
   * @param {{kind?: string, query?: object}} [opts]
   */
  async upload(resource, id, formData, opts = {}) {
    const kind = opts.kind || "resim";
    const q = opts.query || {};
    let path = "";

    if (resource === "portfoyler" && kind === "resim") path = `${R.portfoyler}/${id}/resim`;
    else if (resource === "logo") path = R.logoYukle;
    else if (resource === "bannerlar") path = `${R.bannerlar}/${id}/resim`;
    else if (resource === "blog" && kind === "kapak") path = `${R.blog}/${id}/kapak`;
    else if (resource === "blog" && kind === "icerik-resim") path = `${R.blog}/icerik-resim` + toQuery(q);
    else if (resource === "kullanicilar" && kind === "profil-resmi") path = `${R.kullanicilar}/profil-resmi`;
    else if (resource === "belge" && kind === "parse") path = R.belgeParse;
    else throw new ApiError(404, `Upload desteklenmiyor: ${resource}/${kind}`);

    return this._request(path, { method: "POST", body: formData, rawBody: true });
  }

  /**
   * @param {string} resource
   * @param {string|number} id
   * @param {{kind?: string}} [opts]
   */
  async download(resource, id, opts = {}) {
    if (resource === "portfoyler" && (opts.kind === "pdf" || !opts.kind)) {
      const response = await this._request(`${R.portfoyler}/${id}/pdf`, { skipJson: true });
      return response.blob();
    }
    throw new ApiError(404, "İndirilecek kaynak bulunamadı");
  }
}
