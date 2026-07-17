/**
 * Uygulama yapılandırması.
 * mode: "mock"  → Cloudflare Pages / yerel demo (JSON)
 * mode: "server" → Gerçek FastAPI backend
 *
 * apiBase: sunucu kökü (boş = aynı origin). Domain/IP buraya yazılır; koda sabitlenmez.
 */
window.APP_CONFIG = {
  mode: "server",
  apiBase: "",
  timeout: 10000,
  /** İstemci önbellek süresi (ms). 0 = kapalı */
  cacheTtl: 30000,
  /** Mock JSON dosyalarının kök yolu (trailing slash yok) */
  mockBase: "/src/mock",
};
