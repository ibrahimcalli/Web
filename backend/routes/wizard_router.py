"""Wizard Router — Site oluşturma sihirbazı endpoint'leri."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends

from backend.core.dependencies import get_current_user, require_admin
from backend.db.database import Database, db
from backend.schemas.wizard import (
    DemoSec, ForumAyarla, MenuOlustur, RenkSec, SayfaOlustur, SektorSec,
    SeoAyarla, SiteOlustur, TemplateSec, WidgetAyarla, WizardAdimKaydet,
)
from backend.schemas.response import fail, ok
from backend.services.preset_service import PresetService
from backend.services.wizard_service import WizardService
from backend.repositories.wizard_repository import LicenseRepository, PluginRepository

router = APIRouter(tags=["CMS - Wizard"])


def get_wizard_service() -> WizardService:
    return WizardService(db)


def get_preset_service() -> PresetService:
    return PresetService()


def get_license_repo() -> LicenseRepository:
    return LicenseRepository(db)


def get_plugin_repo() -> PluginRepository:
    return PluginRepository(db)


# ─── Public ─────────────────────────────────────────────────────────────────
@router.get("/wizard/sektorler")
async def sektor_listesi(
    ps: PresetService = Depends(get_preset_service),
):
    """Kullanılabilir sektörleri listele."""
    return ok(ps.sektor_listesi())


@router.get("/wizard/sektor/{sector}")
async def sektor_detay(
    sector: str,
    ps: PresetService = Depends(get_preset_service),
):
    """Sektör preset detayını getir."""
    data = ps.sektor_getir(sector)
    if not data:
        return fail("Sektör bulunamadı")
    return ok(data)


@router.get("/wizard/sektor/{sector}/templates")
async def sektor_templates(
    sector: str,
    ps: PresetService = Depends(get_preset_service),
):
    """Sektöre uygun template listesi."""
    return ok(ps.template_getir(sector))


@router.get("/wizard/sektor/{sector}/palettes")
async def sektor_palettes(
    sector: str,
    ps: PresetService = Depends(get_preset_service),
):
    """Sektöre uygun renk paletleri."""
    return ok(ps.palette_getir(sector))


# ─── Admin — Wizard ─────────────────────────────────────────────────────────
@router.post("/admin/wizard/baslat")
async def wizard_baslat(
    ws: WizardService = Depends(get_wizard_service),
    _=Depends(require_admin),
):
    """Yeni site oluşturma sihirbazı başlat."""
    try:
        sonuc = ws.baslat()
        return ok(sonuc)
    except Exception as e:
        return fail(str(e))


@router.get("/admin/wizard/{wizard_id}")
async def wizard_durum(
    wizard_id: int,
    ws: WizardService = Depends(get_wizard_service),
    _=Depends(require_admin),
):
    """Wizard durumunu getir."""
    try:
        state = ws.durum(wizard_id)
        if not state:
            return fail("Wizard bulunamadı")
        return ok(state)
    except Exception as e:
        return fail(str(e))


@router.post("/admin/wizard/{wizard_id}/adim/{adim}")
async def wizard_adim(
    wizard_id: int,
    adim: int,
    veri: dict,
    ws: WizardService = Depends(get_wizard_service),
    _=Depends(require_admin),
):
    """Wizard adımına veri kaydet."""
    try:
        sonuc = ws.adim_kaydet(wizard_id, adim, veri)
        return ok(sonuc)
    except Exception as e:
        return fail(str(e))


@router.post("/admin/wizard/{wizard_id}/sektor")
async def wizard_sektor(
    wizard_id: int,
    body: SektorSec,
    ws: WizardService = Depends(get_wizard_service),
    _=Depends(require_admin),
):
    try:
        return ok(ws.sektor_sec(wizard_id, body.sector))
    except Exception as e:
        return fail(str(e))


@router.post("/admin/wizard/{wizard_id}/template")
async def wizard_template(
    wizard_id: int,
    body: TemplateSec,
    ws: WizardService = Depends(get_wizard_service),
    _=Depends(require_admin),
):
    try:
        return ok(ws.template_sec(wizard_id, body.template))
    except Exception as e:
        return fail(str(e))


@router.post("/admin/wizard/{wizard_id}/renk")
async def wizard_renk(
    wizard_id: int,
    body: RenkSec,
    ws: WizardService = Depends(get_wizard_service),
    _=Depends(require_admin),
):
    try:
        return ok(ws.renk_sec(wizard_id, body.palette))
    except Exception as e:
        return fail(str(e))


@router.post("/admin/wizard/{wizard_id}/menuler")
async def wizard_menuler(
    wizard_id: int,
    body: MenuOlustur,
    ws: WizardService = Depends(get_wizard_service),
    _=Depends(require_admin),
):
    try:
        return ok(ws.menu_olustur(wizard_id, {"auto": body.auto}))
    except Exception as e:
        return fail(str(e))


@router.post("/admin/wizard/{wizard_id}/sayfalar")
async def wizard_sayfalar(
    wizard_id: int,
    body: SayfaOlustur,
    ws: WizardService = Depends(get_wizard_service),
    _=Depends(require_admin),
):
    try:
        return ok(ws.sayfa_olustur(wizard_id, {"auto": body.auto}))
    except Exception as e:
        return fail(str(e))


@router.post("/admin/wizard/{wizard_id}/widgetlar")
async def wizard_widgetlar(
    wizard_id: int,
    body: WidgetAyarla,
    ws: WizardService = Depends(get_wizard_service),
    _=Depends(require_admin),
):
    try:
        return ok(ws.widget_ayarla(wizard_id, body.widget_list))
    except Exception as e:
        return fail(str(e))


@router.post("/admin/wizard/{wizard_id}/forum")
async def wizard_forum(
    wizard_id: int,
    body: ForumAyarla,
    ws: WizardService = Depends(get_wizard_service),
    _=Depends(require_admin),
):
    try:
        return ok(ws.forum_ayarla(wizard_id, body.aktif))
    except Exception as e:
        return fail(str(e))


@router.post("/admin/wizard/{wizard_id}/seo")
async def wizard_seo(
    wizard_id: int,
    body: SeoAyarla,
    ws: WizardService = Depends(get_wizard_service),
    _=Depends(require_admin),
):
    try:
        return ok(ws.seo_ayarla(wizard_id, body.seo))
    except Exception as e:
        return fail(str(e))


@router.post("/admin/wizard/{wizard_id}/demo")
async def wizard_demo(
    wizard_id: int,
    body: DemoSec,
    ws: WizardService = Depends(get_wizard_service),
    _=Depends(require_admin),
):
    try:
        return ok(ws.demo_olustur(wizard_id, body.demo))
    except Exception as e:
        return fail(str(e))


@router.post("/admin/wizard/{wizard_id}/olustur")
async def wizard_olustur(
    wizard_id: int,
    body: SiteOlustur,
    ws: WizardService = Depends(get_wizard_service),
    _=Depends(require_admin),
):
    try:
        return ok(ws.siteyi_olustur(wizard_id))
    except Exception as e:
        return fail(str(e))


# ─── Admin — License (FAZ 4) ────────────────────────────────────────────────
@router.get("/admin/license")
async def license_listele(
    repo: LicenseRepository = Depends(get_license_repo),
    _=Depends(require_admin),
):
    return ok(repo.listele())


@router.post("/admin/license")
async def license_olustur(
    data: dict,
    repo: LicenseRepository = Depends(get_license_repo),
    _=Depends(require_admin),
):
    try:
        lid = repo.olustur(data)
        return ok({"id": lid})
    except Exception as e:
        return fail(str(e))


# ─── Admin — Plugins (FAZ 4) ────────────────────────────────────────────────
@router.get("/admin/plugins")
async def plugin_listele(
    repo: PluginRepository = Depends(get_plugin_repo),
    _=Depends(require_admin),
):
    return ok(repo.listele())


@router.get("/admin/plugins/{plugin_id}/toggle")
async def plugin_toggle(
    plugin_id: int,
    repo: PluginRepository = Depends(get_plugin_repo),
    _=Depends(require_admin),
):
    try:
        yeni = repo.aktif_degistir(plugin_id)
        return ok({"aktif": yeni})
    except Exception as e:
        return fail(str(e))
