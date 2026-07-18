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
from backend.routes.system_router import router as system_router
from backend.routes.menu_router import router as menu_router
from backend.routes.page_router import router as page_router
from backend.routes.widget_router import router as widget_router
from backend.routes.theme_router import router as theme_router
from backend.routes.forum_router import router as forum_router

# Not: backend/routes/pwa_assets.py ARTIK KULLANILMIYOR

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
    "system_router",
    "menu_router",
    "page_router",
    "widget_router",
    "theme_router",
    "forum_router",
]