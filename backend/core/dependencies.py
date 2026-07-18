"""Dependency Injection (DI) Yapısı."""
from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from backend.core.security import decode_token
from backend.db.database import db
from backend.repositories.portfoy_repository import PortfoyRepository
from backend.repositories.kullanici_repository import KullaniciRepository
from backend.repositories.menu_repository import (
    MenuRepository, MenuItemRepository,
)
from backend.repositories.misc_repository import (
    IstekRepository, AyarRepository, BannerRepository, BlogRepository
)
from backend.services.auth_service import AuthService
from backend.services.kullanici_service import KullaniciService
from backend.services.portfoy_service import PortfoyService
from backend.services.icerik_service import IstekService, AyarService, BannerService, BlogService
from backend.services.menu_service import MenuService

security = HTTPBearer(auto_error=False)


# ─── Repository Dependencies ──────────────────────────────────────────────────
def get_portfoy_repository() -> PortfoyRepository:
    return PortfoyRepository(db)


def get_kullanici_repository() -> KullaniciRepository:
    return KullaniciRepository(db)


def get_istek_repository() -> IstekRepository:
    return IstekRepository(db)


def get_ayar_repository() -> AyarRepository:
    return AyarRepository(db)


def get_banner_repository() -> BannerRepository:
    return BannerRepository(db)


def get_blog_repository() -> BlogRepository:
    return BlogRepository(db)


# ─── Service Dependencies ─────────────────────────────────────────────────────
def get_auth_service(
    kullanicilar: KullaniciRepository = Depends(get_kullanici_repository),
) -> AuthService:
    return AuthService(kullanicilar)


def get_kullanici_service(
    kullanicilar: KullaniciRepository = Depends(get_kullanici_repository),
) -> KullaniciService:
    return KullaniciService(kullanicilar)


def get_portfoy_service(
    portfoyler: PortfoyRepository = Depends(get_portfoy_repository),
    kullanicilar: KullaniciRepository = Depends(get_kullanici_repository),
    ayarlar: AyarRepository = Depends(get_ayar_repository),
    istekler: IstekRepository = Depends(get_istek_repository),
) -> PortfoyService:
    return PortfoyService(portfoyler, kullanicilar, ayarlar, istekler)


def get_istek_service(
    istekler: IstekRepository = Depends(get_istek_repository),
    portfoyler: PortfoyRepository = Depends(get_portfoy_repository),
) -> IstekService:
    return IstekService(istekler, portfoyler)


def get_ayar_service(
    ayarlar: AyarRepository = Depends(get_ayar_repository),
) -> AyarService:
    return AyarService(ayarlar)


def get_banner_service(
    bannerlar: BannerRepository = Depends(get_banner_repository),
) -> BannerService:
    return BannerService(bannerlar)


def get_blog_service(
    bloglar: BlogRepository = Depends(get_blog_repository),
) -> BlogService:
    return BlogService(bloglar)


def get_menu_repository() -> MenuRepository:
    return MenuRepository(db)


def get_menu_item_repository() -> MenuItemRepository:
    return MenuItemRepository(db)


def get_menu_service(
    menuler: MenuRepository = Depends(get_menu_repository),
    ogeler: MenuItemRepository = Depends(get_menu_item_repository),
) -> MenuService:
    return MenuService(menuler, ogeler)


# ─── Auth Dependencies ────────────────────────────────────────────────────────
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
    if not credentials:
        return None
    return decode_token(credentials.credentials)


async def require_auth(
    user: Optional[dict] = Depends(get_current_user),
) -> dict:
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kimlik doğrulama gerekli",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def require_admin(
    user: dict = Depends(require_auth),
) -> dict:
    if user.get("rol") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin yetkisi gerekli",
        )
    return user