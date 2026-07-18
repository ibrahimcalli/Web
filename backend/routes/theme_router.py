"""Theme Router — Tema ayarları API endpoint'leri (public readonly, admin full CRUD)."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.core.dependencies import get_current_user, get_theme_service, require_admin
from backend.schemas.response import fail, ok
from backend.schemas.theme import ThemeSettingSet
from backend.services.theme_service import ThemeService

router = APIRouter(tags=["CMS - Tema"])


@router.get("/tema")
async def halka_acik_tema(
    theme_service: ThemeService = Depends(get_theme_service),
    _user: dict = Depends(get_current_user),
):
    try:
        return ok(theme_service.get_all())
    except Exception as e:
        return fail(str(e))


@router.get("/admin/tema")
async def tema_getir(
    theme_service: ThemeService = Depends(get_theme_service),
    _=Depends(require_admin),
):
    try:
        return ok(theme_service.get_all())
    except Exception as e:
        return fail(str(e))


@router.put("/admin/tema/{anahtar}")
async def tema_guncelle(
    anahtar: str,
    data: ThemeSettingSet,
    theme_service: ThemeService = Depends(get_theme_service),
    _=Depends(require_admin),
):
    try:
        return ok(theme_service.set(data.anahtar, data.deger))
    except Exception as e:
        return fail(str(e))


@router.delete("/admin/tema/{anahtar}")
async def tema_sil(
    anahtar: str,
    theme_service: ThemeService = Depends(get_theme_service),
    _=Depends(require_admin),
):
    try:
        return ok(theme_service.delete(anahtar))
    except Exception as e:
        return fail(str(e))
