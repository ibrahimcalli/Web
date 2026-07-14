"""Uygulama başlatma ve router kayıt."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from backend.core.config import API_TITLE, API_VERSION, API_DESCRIPTION, BASE_DIR, CORS_ORIGINS
from backend.core.errors import AppError, ErrorHandler
from backend.routes import (
    auth_router,
    portfoy_router,
    kullanici_router,
    istek_router,
    ayar_router,
    banner_router,
    blog_router,
    content_router,
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
    
    # Hata handler
    app.add_middleware(ErrorHandler)
    
    # Static dosyalar
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
    
    # Health check
    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "healthy", "version": API_VERSION}
    
    return app


# Uygulama instance
app = create_app()