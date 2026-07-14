/**
 * Uygulama bootstrap — ApiClient'ı window'a bağlar.
 * UI script'i (classic veya module) window.api üzerinden çalışır.
 */
import "./../config/config.js";
import { ApiClient } from "./ApiClient.js";

const config = window.APP_CONFIG;
if (!config) {
  throw new Error("APP_CONFIG yüklenemedi (config.js)");
}

/** @type {ApiClient} */
const api = new ApiClient(config);

window.api = api;
window.APP_CONFIG = config;

/**
 * UI hazır olduğunda hata işleyicilerini bağlamak için.
 * @param {{bildirim?: Function, onUnauthorized?: Function}} ui
 */
window.bindApiUi = function bindApiUi(ui = {}) {
  api.setHandlers({
    onError(err) {
      if (typeof ui.bildirim === "function") {
        ui.bildirim(err.userMessage || err.message || "İşlem başarısız", "hata");
      } else {
        console.error("[ApiClient]", err.status, err.message);
      }
    },
    onUnauthorized() {
      if (typeof ui.onUnauthorized === "function") ui.onUnauthorized();
    },
  });
};

window.dispatchEvent(new CustomEvent("app:api-ready", { detail: { api, config } }));

export { api, config };
export default api;
