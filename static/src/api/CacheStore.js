/**
 * Basit istemci tarafı önbellek (TTL + anahtar).
 * Aynı GET verisi tekrar istenmesin diye kullanılır.
 */

export class CacheStore {
  /**
   * @param {number} [defaultTtlMs]
   */
  constructor(defaultTtlMs = 30000) {
    /** @private @type {Map<string, {expires: number, value: any}>} */
    this._map = new Map();
    this.defaultTtlMs = defaultTtlMs;
  }

  /**
   * @param {string} key
   * @returns {any|undefined}
   */
  get(key) {
    const hit = this._map.get(key);
    if (!hit) return undefined;
    if (Date.now() > hit.expires) {
      this._map.delete(key);
      return undefined;
    }
    return hit.value;
  }

  /**
   * @param {string} key
   * @param {any} value
   * @param {number} [ttlMs]
   */
  set(key, value, ttlMs) {
    const ttl = ttlMs == null ? this.defaultTtlMs : ttlMs;
    if (ttl <= 0) return;
    this._map.set(key, { value, expires: Date.now() + ttl });
  }

  /**
   * @param {string} [prefix] — verilirse eşleşen anahtarları siler
   */
  invalidate(prefix) {
    if (!prefix) {
      this._map.clear();
      return;
    }
    for (const key of this._map.keys()) {
      if (key.startsWith(prefix)) this._map.delete(key);
    }
  }

  /** Tüm önbelleği temizler. */
  clear() {
    this._map.clear();
  }
}
