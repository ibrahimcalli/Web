/**
 * JWT / oturum token yönetimi.
 * Depolama anahtarı tek yerde tutulur; gelecekte cookie veya memory store'a geçilebilir.
 */

const TOKEN_KEY = "emlak_token";

export class TokenStore {
  /**
   * @param {Storage} [storage]
   */
  constructor(storage = (typeof localStorage !== "undefined" ? localStorage : null)) {
    /** @private */
    this._storage = storage;
    /** @private @type {string} */
    this._memory = "";
  }

  /**
   * Kayıtlı token'ı döndürür.
   * @returns {string}
   */
  get() {
    if (this._storage) {
      try {
        return this._storage.getItem(TOKEN_KEY) || "";
      } catch {
        return this._memory;
      }
    }
    return this._memory;
  }

  /**
   * Token kaydeder (boş string → siler).
   * @param {string} token
   */
  set(token) {
    const val = token || "";
    this._memory = val;
    if (!this._storage) return;
    try {
      if (val) this._storage.setItem(TOKEN_KEY, val);
      else this._storage.removeItem(TOKEN_KEY);
    } catch {
      /* private mode vb. */
    }
  }

  /**
   * Token var mı?
   * @returns {boolean}
   */
  has() {
    return Boolean(this.get());
  }

  /**
   * Authorization header değeri.
   * @returns {string|null}
   */
  bearer() {
    const t = this.get();
    return t ? `Bearer ${t}` : null;
  }

  /** Oturumu temizler. */
  clear() {
    this.set("");
  }
}
