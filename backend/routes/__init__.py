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
from backend.routes.pwa_assets import router as pwa_assets_router

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
    "pwa_assets_router",
]