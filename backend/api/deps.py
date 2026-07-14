"""FastAPI dependency injection — testlerde override edilebilir."""
from __future__ import annotations

from backend.services.auth_service import AuthService, KullaniciService
from backend.services.content_service import (
    AyarService,
    BannerService,
    BlogService,
    IstekService,
    MetaService,
)
from backend.services.portfoy_service import PortfoyService
from backend.services.upload_service import UploadService


def get_auth_service() -> AuthService:
    return AuthService()


def get_kullanici_service() -> KullaniciService:
    return KullaniciService()


def get_portfoy_service() -> PortfoyService:
    return PortfoyService()


def get_istek_service() -> IstekService:
    return IstekService()


def get_ayar_service() -> AyarService:
    return AyarService()


def get_banner_service() -> BannerService:
    return BannerService()


def get_blog_service() -> BlogService:
    return BlogService()


def get_meta_service() -> MetaService:
    return MetaService()


def get_upload_service() -> UploadService:
    return UploadService()
