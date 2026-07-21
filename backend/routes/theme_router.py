"""Theme Router — Tema ayarları API endpoint'leri (public readonly, admin full CRUD)."""
from __future__ import annotations

from typing import Dict

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.core.dependencies import get_current_user, get_theme_service, require_admin
from backend.schemas.response import fail, ok
from backend.schemas.theme import ThemeSettingSet
from backend.services.theme_service import ThemeService

router = APIRouter(tags=["CMS - Tema"])


class ThemeBulkSet(BaseModel):
    ayarlar: Dict[str, str]


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


@router.put("/admin/tema")
async def tema_toplu_guncelle(
    data: ThemeBulkSet,
    theme_service: ThemeService = Depends(get_theme_service),
    _=Depends(require_admin),
):
    try:
        temiz = {str(k): "" if v is None else str(v) for k, v in (data.ayarlar or {}).items()}
        return ok(theme_service.set_many(temiz))
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


# Bilinen tema anahtarları (whitelist) — dışından eklenen spam anahtarlar temizlenir
TEMA_WHITELIST = {
    "template","renk_tema","renk_ana","renk_ana_koy","renk_arka","renk_metin","dark_mode",
    "font_baslik","font_govde","border_radius","shadow_kart",
    "header_stil","footer_stil","kart_stil","button_stil","animasyon",
    "logo_url","favicon_url",
}


@router.post("/admin/tema/cleanup")
async def tema_cleanup(
    theme_service: ThemeService = Depends(get_theme_service),
    _=Depends(require_admin),
):
    """Whitelist dışındaki anahtarları theme_settings tablosundan siler."""
    try:
        all_keys = theme_service.get_all()
        silinen = []
        for k in list(all_keys.keys()):
            if k not in TEMA_WHITELIST:
                theme_service.delete(k)
                silinen.append(k)
        return ok({"silinen": silinen, "adet": len(silinen)})
    except Exception as e:
        return fail(str(e))
