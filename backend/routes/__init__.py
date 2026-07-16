"""Routes paketinin dışa aktarımları."""
from backend.routes.auth_router import router as auth_router
from backend.routes.portfoy_router import router as portfoy_router
from backend.routes.kullanici_router import router as kullanici_router
from backend.routes.icerik_router import (
    istek_router,
    ayar_router,
    banner_router,
    blog_router,
)
from backend.routes.content_router import router as content_router
from backend.routes.sitemap_router import router as sitemap_router

# Not: backend/routes/pwa_assets.py ARTIK KULLANILMIYOR
# PWA dosyaları (manifest.json, sw.js, offline.html, favicon.ico)
# WhitelistedStaticFiles ile kök seviyeden servis ediliyor —
# backend/core/static_pwa.py ve backend/app.py mount'a bakınız.

__all__ = [
    "auth_router",
    "portfoy_router",
    "kullanici_router",
    "istek_router",
    "ayar_router",
    "banner_router",
    "blog_router",
    "content_router",
    "sitemap_router",
]