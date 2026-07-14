/**
 * Merkezi HTTP / API hata sınıfları ve mesaj eşlemeleri.
 */

/** @type {Record<number, string>} */
export const HTTP_MESAJLARI = {
  200: "İşlem başarılı",
  201: "Kayıt oluşturuldu",
  400: "Geçersiz istek. Lütfen bilgileri kontrol edin.",
  401: "Oturum süreniz doldu veya giriş yapmanız gerekiyor.",
  403: "Bu işlem için yetkiniz yok.",
  404: "İstenen kayıt bulunamadı.",
  409: "Çakışma: kayıt zaten mevcut veya güncellenemedi.",
  422: "Gönderilen veriler doğrulanamadı.",
  429: "Çok fazla istek. Lütfen biraz bekleyip tekrar deneyin.",
  500: "Sunucu hatası. Lütfen daha sonra tekrar deneyin.",
  0: "Bağlantı kurulamadı. İnternet bağlantınızı kontrol edin.",
};

/**
 * API katmanından fırlatılan standart hata.
 */
export class ApiError extends Error {
  /**
   * @param {number} status
   * @param {string} [detail]
   * @param {object} [extra]
   */
  constructor(status, detail = "", extra = {}) {
    const varsayilan = HTTP_MESAJLARI[status] || HTTP_MESAJLARI[500];
    const mesaj = (typeof detail === "string" && detail.trim()) ? detail : varsayilan;
    super(mesaj);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
    this.extra = extra;
    /** Kullanıcıya gösterilecek anlaşılır mesaj */
    this.userMessage = mesaj;
  }

  /** @returns {boolean} */
  get isUnauthorized() {
    return this.status === 401;
  }

  /** @returns {boolean} */
  get isNetwork() {
    return this.status === 0;
  }
}

/**
 * JSON parse hataları.
 */
export class JsonParseError extends ApiError {
  /**
   * @param {string} [neden]
   */
  constructor(neden = "Sunucu yanıtı okunamadı (geçersiz JSON).") {
    super(500, neden);
    this.name = "JsonParseError";
  }
}

/**
 * Zaman aşımı.
 */
export class TimeoutError extends ApiError {
  /**
   * @param {number} timeoutMs
   */
  constructor(timeoutMs) {
    super(0, `Sunucu ${Math.round(timeoutMs / 1000)} sn içinde yanıt vermedi. Bağlantınızı veya sunucu durumunu kontrol edin.`);
    this.name = "TimeoutError";
  }
}

/**
 * Backend `detail` alanını düz metne çevirir.
 * @param {any} detail
 * @returns {string}
 */
export function detailToMessage(detail) {
  if (detail == null || detail === "") return "";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d) => (typeof d === "object" ? (d.msg || JSON.stringify(d)) : String(d)))
      .join(" · ");
  }
  if (typeof detail === "object") {
    return detail.msg || detail.message || JSON.stringify(detail);
  }
  return String(detail);
}
