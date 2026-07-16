"""Uygulama başlatma ve router kayıt."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from backend.core.config import API_TITLE, API_VERSION, API_DESCRIPTION, BASE_DIR, CORS_ORIGINS
from backend.core.errors import AppError, ErrorHandler, AccessLogMiddleware, CsrfProtectMiddleware
from backend.core.logging import initialize as logging_initialize
from backend.routes import (
    auth_router,
    portfoy_router,
    kullanici_router,
    istek_router,
    ayar_router,
    banner_router,
    blog_router,
    content_router,
    sitemap_router,
)


def create_app() -> FastAPI:
    """
    FastAPI uygulaması oluştur.
    
    Returns:
        Configured FastAPI app
    """
    app = FastAPI(
        title=API_TITLE,
        version=API_VERSION,
        description=API_DESCRIPTION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # JSON-based CSRF koruması — state-changing metodlarda Content-Type kontrolü
    app.add_middleware(CsrfProtectMiddleware)
    
    # Access logging (her HTTP isteği logs/access.log'a yazılır, X-Request-ID eklenir)
    app.add_middleware(AccessLogMiddleware)
    
    # Hata handler
    app.add_middleware(ErrorHandler)
    
    # Logging altyapısını başlat — 3 dosya: access.log, error.log, app.log
    logging_initialize()
    
    # Static dosyalar — /src ve /static mount'ları.
    # PWA assets (sw.js, manifest.json, vb.) KÖK app.py'daki spa_fallback route'unda
    # WhitelistedStaticFiles ile servis edilir (mount "/ yapmadık — tüm path'leri yutar).
    app.mount("/src", StaticFiles(directory=str(BASE_DIR / "src")), name="src_modules")
    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

    
    # Router'ları kaydet
    app.include_router(auth_router, prefix="/api", tags=["Auth"])
    app.include_router(portfoy_router, prefix="/api", tags=["Portföy"])
    app.include_router(kullanici_router, prefix="/api", tags=["Kullanıcı"])
    app.include_router(istek_router, prefix="/api", tags=["İstek"])
    app.include_router(ayar_router, prefix="/api", tags=["Ayarlar"])
    app.include_router(banner_router, prefix="/api", tags=["Banner"])
    app.include_router(blog_router, prefix="/api", tags=["Blog"])
    app.include_router(content_router, prefix="/api", tags=["İçerik"])

    # ─── Sitemap / robots.txt (production SEO) ────────────────────────────────
    # Mevcut URL'ler: /sitemap.xml, /sitemap-images.xml, /robots.txt
    # OpenAPI'de görünmez ama çalışır (SEO için):
    # Not: Sitemap dinamik (DB'den portföy/blog URL'leri) — StaticFiles DEĞİL router.
    app.include_router(sitemap_router, tags=["SEO"])
    
    # ─── PWA Asset'ler ────────────────────────────────────────────────────────
    # Artık WhitelistedStaticFiles ile mount ediliyor (yukarıda pwa_root).
    # manifest.json, sw.js, offline.html, favicon.ico → StaticFiles (hızlı).
    # Eski pwa_assets_router kaldırıldı.
    
    # Health check — sürüm bilgisi ile
    @app.get("/health", tags=["Health"])
    async def health_check():
        from backend.core.version import get_version_info
        from backend.core.settings import settings
        info = get_version_info()
        return {
            "status": "healthy",
            "version": settings.API_VERSION,
            "build_date": info["build_date"],
            "git_hash": info["git_hash"],
            "git_branch": info["git_branch"],
            "domain": settings.DOMAIN,
            "debug": settings.DEBUG,
        }
    
    return app


# Not: Modüler import kolaylığı için burada 'app = create_app()' YOK.
# Production/worker uygulamayı app:app (kök app.py) üzerinden Çalıştırmalıdır.
# Kök app.py, create_app()'i çağırır ve SPA fallback'i O burada tanımlar.