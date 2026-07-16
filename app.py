"""
Portföy Gayrimenkul Web Sistemi - Backend (Kök App)
====================================================

Production ASGI uygulaması:
    uvicorn app:app --host 0.0.0.0 --port 8080

Mimari (routing sırasına göre):
    1. /docs, /redoc, /openapi.json            → FastAPI otomatik
    2. /src, /static                            → StaticFiles mount (hızlı)
    3. /api/*                                   → API router'ları (auth, portfoy, ...)
    4. /sitemap.xml, /sitemap-images.xml, /robots.txt → sitemap_router (dynamics DB)
    5. /health                                  → health endpoint
    6. /{full_path:path}                        → spa_fallback:
         a) whitelist PWA dosyası ise        → WhitelistedStaticFiles (fast ASGI)
         b) SPA_SKIP_PATHS ise (ama dosya yoksa) → 404 JSON
         c) diğer (SPA route'ları)              → index.html

Bu sayede:
  - PWA dosyaları (sw.js, manifest.json, vb.) StaticFiles hızında servis edilir.
  - SPA route'ları (/ilanlar, /#detay/5, vb.) index.html döner.
  - Bilinmeyen PWA dosyaları HTML değil 404 döner.
"""
from __future__ import annotations

import mimetypes
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import PlainTextResponse

from backend.app import create_app
from backend.core.config import BASE_DIR
from backend.db.schema import init_db

# ─── MIME Type düzeltme ────────────────────────────────────────────────────
# Starlette StaticFiles Python'ın mimetypes modülünü kullanır. Varsayılan
# bazı türleri yanlış verir. Production doğru Content-Type için düzeltme:
mimetypes.add_type("application/javascript", ".js", strict=False)
mimetypes.add_type("application/manifest+json", ".webmanifest", strict=False)
mimetypes.add_type("application/manifest+json", ".manifest", strict=False)
# .json application/manifest+json DEĞİL application/json olarak kalmalı (genel JSON dosyaları)
# .json Map'in yüklenmesi sırasında manifest.json için biz below'da override edeceğiz.

# Uygulama oluştur (router'lar create_app içinde kayıtlı)
app = create_app()

# ─── Statik dosya mount'ları ──────────────────────────────────────────────
app.mount("/src", StaticFiles(directory=str(BASE_DIR / "src")), name="src_modules")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


# ─── PWA assets — Whitelist'li StaticFiles ────────────────────────────────
# Açıklama: Mount "/" yerine bu sınıfı spa_fallback İÇİNDE çağırıyoruz —
# böylece SPA route'ları index.html dönerken whitelisted PWA dosyaları
# StaticFiles hızında (Pydantic/DI overhead YOK) servis edilir.
STATIC_DIR = BASE_DIR / "static"
PWA_WHITELIST = frozenset({
    "manifest.json",
    "sw.js",
    "offline.html",
    "favicon.ico",
    "apple-touch-icon.png",
    "apple-touch-icon-precomposed.png",
    "apple-touch-icon-180x180.png",
    "apple-touch-icon-152x152.png",
    "apple-touch-icon-120x120.png",
    "apple-touch-icon-76x76.png",
    "apple-touch-icon-60x60.png",
    "apple-touch-icon-167x167.png",
    "browserconfig.xml",
    "mstile-150x150.png",
    "android-chrome-192x192.png",
    "android-chrome-512x512.png",
    "favicon-32x32.png",
    "favicon-16x16.png",
    "favicon-96x96.png",
    "site.webmanifest",
})

# manifest.json için doğru Content-Type override. Starlette .json'ı
# application/json verir — IETF standardı application/manifest+json tercih.
MANIFEST_MIME = "application/manifest+json"

# WhitelistedStaticFiles singleton — her SPA fallback request'inde yeniden
# oluşturmamak için modül seviyesinde.
from backend.core.static_pwa import WhitelistedStaticFiles  # noqa: E402

_pwa_static = WhitelistedStaticFiles(
    directory=str(STATIC_DIR),
    allowed=PWA_WHITELIST,
)


# ─── SPA Fallback + PWA StaticFiles ────────────────────────────────────────
# Bu route Mount "/" DEĞİL — mount olsaydı tüm path'leri yutardı.
# Route olarak Tüm altında 2 iş yapar:
#   1) WhitelistedStaticFiles -> fast StaticFiles
#   2) Yoksa -> index.html (SPA route)
SPA_SKIP_PATHS = PWA_WHITELIST | frozenset({
    "sitemap.xml",
    "sitemap-images.xml",
    "robots.txt",
    ".well-known",
})


@app.api_route(
    "/{full_path:path}",
    methods=["GET", "HEAD"],
    include_in_schema=False,
)
async def spa_fallback(full_path: str, request: Request):
    """
    SPA fallback + PWA StaticFiles kombinasyonu.
    
    Davranış:
        1. path PWA_WHITELIST'te ise → WhitelistedStaticFiles ile hızlı servis.
           (Pydantic/DI overhead yok, StaticFiles ASGI seviyesinde)
        2. path whitelisted DEĞİLSE:
           - SPA_SKIP_PATHS içinde ise → 404 JSON (HTML düşmez)
           - Diğer SPA route'ları için → index.html
    """
    normalize = full_path.lstrip("/").lower()
    ilk_segment = normalize.split("/", 1)[0] if "/" in normalize else normalize

    # 1) Whitelisted PWA dosya → StaticFiles (hızlı)
    if ilk_segment in PWA_WHITELIST:
        # manifest.json için doğru Content-Type override:
        # Starlette .json'ı application/json verir; biz app/manifest+json
        # göndermek için dosyaya özel FileResponse.
        if normalize == "manifest.json":
            path = STATIC_DIR / "manifest.json"
            if path.exists():
                return FileResponse(
                    str(path),
                    media_type=MANIFEST_MIME,
                    headers={
                        "Cache-Control": "public, max-age=86400",
                        "Service-Worker-Allowed": "/",
                    },
                )
            return JSONResponse({"mesaj": "manifest.json bulunamadı"}, status_code=404)

        # Diğer whitelisted dosyalar → StaticFiles ile servis
        response = await _pwa_static.get_response(full_path, request.scope)
        # Eğer StaticFiles 404 dönerse (dosya yok) → 404 JSON, HTML değil
        if response.status_code == 404:
            return JSONResponse(
                {"mesaj": f"{full_path} bulunamadı"},
                status_code=404,
                headers={"Cache-Control": "no-store"},
            )
        return response

    # 2) SPA_SKIP_PATHS içinde ama whitelisted değil → gerçek 404
    if ilk_segment in SPA_SKIP_PATHS:
        return JSONResponse(
            {"mesaj": "Not found"},
            status_code=404,
            headers={"Cache-Control": "no-store"},
        )
    
    # 3) /api/* path'leri bilinmeyen route için 404 (HTML düşmesin)
    if ilk_segment == "api":
        return JSONResponse(
            {"success": False, "message": "Endpoint bulunamadı", "data": None},
            status_code=404,
            headers={"Cache-Control": "no-store"},
        )
    
    # 4) SPA route → index.html
    index = STATIC_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index), media_type="text/html; charset=utf-8")
    return JSONResponse({"mesaj": "API çalışıyor"}, status_code=200)


# ─── Veritabanı şemasını başlat ──────────────────────────────────────────────
init_db()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)
