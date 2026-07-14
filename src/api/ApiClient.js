/**
 * Merkezi API istemcisi.
 *
 * @example
 *   const api = new ApiClient(APP_CONFIG);
 *   const list = await api.getPortfoyler({ durum: "Aktif" });
 *
 * mode=mock  → MockAdapter (fetch yok, JSON import)
 * mode=server → ServerAdapter (fetch + apiBase)
 */
import { MockAdapter } from "./MockAdapter.js";
import { ServerAdapter } from "./ServerAdapter.js";
import { TokenStore } from "./TokenStore.js";
import { CacheStore } from "./CacheStore.js";
import { ApiError } from "./errors.js";

export class ApiClient {
  /**
   * @param {{mode: "mock"|"server", apiBase?: string, timeout?: number, cacheTtl?: number}} config
   */
  constructor(config) {
    if (!config || (config.mode !== "mock" && config.mode !== "server")) {
      throw new Error('APP_CONFIG.mode "mock" veya "server" olmalıdır');
    }

    /** @type {{mode: string, apiBase: string, timeout: number, cacheTtl: number}} */
    this.config = {
      mode: config.mode,
      apiBase: config.apiBase || "",
      timeout: config.timeout || 10000,
      cacheTtl: config.cacheTtl == null ? 30000 : config.cacheTtl,
    };

    /** @private */
    this.tokens = new TokenStore();
    /** @private */
    this.cache = new CacheStore(this.config.cacheTtl);

    /** @private */
    this.adapter =
      this.config.mode === "mock"
        ? new MockAdapter()
        : new ServerAdapter(this.config, {
            getToken: () => this.tokens.get(),
          });

    /** @type {(err: ApiError) => void} */
    this.onError = () => {};
    /** @type {() => void} */
    this.onUnauthorized = () => {};
  }

  /**
   * Hata / 401 geri çağrılarını bağlar (UI katmanı).
   * @param {{onError?: Function, onUnauthorized?: Function}} handlers
   */
  setHandlers({ onError, onUnauthorized } = {}) {
    if (onError) this.onError = onError;
    if (onUnauthorized) this.onUnauthorized = onUnauthorized;
  }

  /** @returns {string} */
  getToken() {
    return this.tokens.get();
  }

  /** @param {string} token */
  setToken(token) {
    this.tokens.set(token);
  }

  /** @returns {boolean} */
  isMock() {
    return this.config.mode === "mock";
  }

  /**
   * @private
   * @template T
   * @param {() => Promise<T>} fn
   * @param {{cacheKey?: string, mutate?: boolean, silent?: boolean}} [opts]
   * @returns {Promise<T|null>}
   */
  async _wrap(fn, opts = {}) {
    if (opts.cacheKey && !opts.mutate) {
      const hit = this.cache.get(opts.cacheKey);
      if (hit !== undefined) return hit;
    }
    try {
      const result = await fn();
      if (opts.mutate) this.cache.clear();
      else if (opts.cacheKey) this.cache.set(opts.cacheKey, result);
      return result;
    } catch (err) {
      const apiErr =
        err instanceof ApiError
          ? err
          : new ApiError(500, err && err.message ? err.message : "Beklenmeyen hata");

      if (apiErr.isUnauthorized) {
        this.tokens.clear();
        this.onUnauthorized();
        if (opts.silent) return null;
      }
      if (!opts.silent) this.onError(apiErr);
      return null;
    }
  }

  /**
   * Kullanıcı girişi. Token kaydedilir.
   * @param {string} email
   * @param {string} sifre
   */
  async login(email, sifre) {
    return this._wrap(async () => {
      const d = await this.adapter.login(email, sifre);
      if (d && d.access_token) this.tokens.set(d.access_token);
      this.cache.clear();
      return d;
    });
  }

  /** Oturumu kapatır. */
  async logout() {
    this.tokens.clear();
    this.cache.clear();
    return this._wrap(() => this.adapter.logout(), { silent: true });
  }

  /** @returns {Promise<object|null>} */
  async getMe() {
    return this._wrap(() => this.adapter.getMe(), { silent: true, cacheKey: "me" });
  }

  /** @returns {Promise<object|null>} */
  async getAyarlar() {
    return this._wrap(() => this.adapter.getAyarlar(), { cacheKey: "ayarlar" });
  }

  /**
   * @param {{konum?: string, sadece_aktif?: number|boolean|string}} [params]
   */
  async getBannerlar(params = {}) {
    const key = `bannerlar:${JSON.stringify(params)}`;
    return this._wrap(() => this.adapter.getBannerlar(params), { cacheKey: key });
  }

  /** @returns {Promise<object|null>} */
  async getBannerKonumlar() {
    return this._wrap(() => this.adapter.getBannerKonumlar(), { cacheKey: "banner-konumlar" });
  }

  /**
   * @param {{durum?: string}} [params]
   */
  async getBlog(params = {}) {
    const key = `blog:${JSON.stringify(params)}`;
    return this._wrap(() => this.adapter.getBlog(params), { cacheKey: key });
  }

  /**
   * @param {string|number} slugOrId
   */
  async getBlogBySlugOrId(slugOrId) {
    return this._wrap(() => this.adapter.getBlogBySlugOrId(slugOrId), {
      cacheKey: `blog-one:${slugOrId}`,
    });
  }

  /**
   * @param {{kategori?: string, alt_kat?: string, durum?: string, arama?: string}} [params]
   */
  async getPortfoyler(params = {}) {
    const key = `portfoyler:${JSON.stringify(params)}`;
    return this._wrap(() => this.adapter.getPortfoyler(params), { cacheKey: key });
  }

  /**
   * @param {string|number} id
   */
  async getPortfoy(id) {
    return this._wrap(() => this.adapter.getPortfoy(id), { cacheKey: `portfoy:${id}` });
  }

  /**
   * Portföy arama kısayolu.
   * @param {string} q
   */
  async arama(q) {
    return this._wrap(() => this.adapter.arama(q));
  }

  /**
   * İletişim / müşteri istek formu.
   * @param {object} data
   */
  async iletisim(data) {
    return this._wrap(() => this.adapter.iletisim(data), { mutate: true });
  }

  /**
   * Dosya yükleme.
   * @param {string} resource
   * @param {string|number|null} id
   * @param {FormData} formData
   * @param {{kind?: string, query?: object}} [opts]
   */
  async upload(resource, id, formData, opts = {}) {
    return this._wrap(() => this.adapter.upload(resource, id, formData, opts), { mutate: true });
  }

  /**
   * Dosya / PDF indirme.
   * @param {string} resource
   * @param {string|number} id
   * @param {{kind?: string}} [opts]
   */
  async download(resource, id, opts = {}) {
    return this._wrap(() => this.adapter.download(resource, id, opts));
  }

  /**
   * Yeni kayıt oluşturur (POST).
   * @param {string} resource
   * @param {object} data
   */
  async save(resource, data) {
    return this._wrap(() => this.adapter.save(resource, data), { mutate: true });
  }

  /**
   * Kayıt siler (DELETE).
   * @param {string} resource
   * @param {string|number} id
   * @param {{action?: string, query?: object}} [opts]
   */
  async delete(resource, id, opts = {}) {
    return this._wrap(() => this.adapter.delete(resource, id, opts), { mutate: true });
  }

  /**
   * Kayıt günceller (PUT/PATCH).
   * @param {string} resource
   * @param {string|number} id
   * @param {object} [data]
   * @param {{action?: string, query?: object}} [opts]
   */
  async update(resource, id, data = {}, opts = {}) {
    return this._wrap(() => this.adapter.update(resource, id, data, opts), { mutate: true });
  }

  /* ── Alan-özel yardımcılar (UI okunabilirliği) ─────────────────────────── */

  /** @returns {Promise<object|null>} */
  async getKategoriler() {
    return this._wrap(() => this.adapter.getKategoriler(), { cacheKey: "kategoriler" });
  }

  /**
   * @param {string} anaKat
   * @param {string} altKat
   * @param {string} [ilanTipi]
   */
  async getAlanlar(anaKat, altKat, ilanTipi = "") {
    const key = `alanlar:${anaKat}:${altKat}:${ilanTipi}`;
    return this._wrap(() => this.adapter.getAlanlar(anaKat, altKat, ilanTipi), { cacheKey: key });
  }

  /** @returns {Promise<object|null>} */
  async getIstatistik() {
    return this._wrap(() => this.adapter.getIstatistik(), { cacheKey: "istatistik" });
  }

  /** @returns {Promise<object[]|null>} */
  async getIstekler() {
    return this._wrap(() => this.adapter.getIstekler());
  }

  /** @returns {Promise<object[]|null>} */
  async getKullanicilar() {
    return this._wrap(() => this.adapter.getKullanicilar());
  }

  /** @returns {Promise<object|null>} */
  async getKullaniciBen() {
    return this._wrap(() => this.adapter.getKullaniciBen(), { silent: true });
  }

  /**
   * @param {string|number} pid
   */
  async getSahipProfil(pid) {
    return this._wrap(() => this.adapter.getSahipProfil(pid), {
      cacheKey: `sahip:${pid}`,
      silent: true,
    });
  }

  /**
   * @param {string|number} id
   */
  async getFiyatAnalizi(id) {
    return this._wrap(() => this.adapter.getFiyatAnalizi(id));
  }

  /** @returns {Promise<object|null>} */
  async getFiyatAnaliziGenel() {
    return this._wrap(() => this.adapter.getFiyatAnaliziGenel());
  }

  /** Önbelleği elle temizler. */
  clearCache() {
    this.cache.clear();
  }
}

export default ApiClient;
