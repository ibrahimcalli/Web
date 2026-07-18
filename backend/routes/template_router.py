"""Template Engine Router — Template ve Homepage Builder API."""
from __future__ import annotations

from typing import Optional

from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse, JSONResponse

from backend.core.dependencies import (
    get_current_user, get_homepage_service, get_template_service, require_admin,
)
from backend.core.settings import BASE_DIR
from backend.schemas.response import fail, ok
from backend.schemas.template import (
    HomepageSectionReorder, HomepageSectionUpdate, TemplateCreate, TemplateUpdate,
)
from backend.services.template_service import HomepageService, TemplateService

router = APIRouter(tags=["CMS - Template"])

TEMPLATES_DIR = BASE_DIR / "templates"


# ─── Public ─────────────────────────────────────────────────────────────────
@router.get("/template/homepage")
async def aktif_homepage(
    template: Optional[str] = None,
    hp: HomepageService = Depends(get_homepage_service),
    _user: dict = Depends(get_current_user),
):
    try:
        return ok(hp.aktif_homepage(template_slug=template))
    except Exception as e:
        return fail(str(e))


@router.get("/template/section/{template_slug}/{section_key}")
async def section_partial(
    template_slug: str,
    section_key: str,
):
    """HTML partial yükle — template engine frontend renderer için."""
    partial_path = TEMPLATES_DIR / template_slug / "sections" / f"{section_key}.html"
    if not partial_path.exists() or not partial_path.is_file():
        return JSONResponse(
            {"success": False, "message": "Bölüm partial bulunamadı"},
            status_code=404,
        )
    return HTMLResponse(partial_path.read_text(encoding="utf-8"))


@router.get("/template/config/{template_slug}")
async def template_config(template_slug: str):
    """Template JSON config dosyasını döndür."""
    config_path = TEMPLATES_DIR / template_slug / "template.json"
    if not config_path.exists():
        return JSONResponse(
            {"success": False, "message": "Template config bulunamadı"},
            status_code=404,
        )
    import json
    data = json.loads(config_path.read_text(encoding="utf-8"))
    return JSONResponse(data)


# ─── Admin — Templates ──────────────────────────────────────────────────────
@router.get("/admin/templates")
async def template_listele(
    ts: TemplateService = Depends(get_template_service),
    _=Depends(require_admin),
):
    try:
        return ok(ts.listele())
    except Exception as e:
        return fail(str(e))


@router.get("/admin/templates/{template_id}")
async def template_getir(
    template_id: int,
    ts: TemplateService = Depends(get_template_service),
    _=Depends(require_admin),
):
    try:
        return ok(ts.getir(template_id))
    except Exception as e:
        return fail(str(e))


@router.post("/admin/templates")
async def template_olustur(
    data: TemplateCreate,
    ts: TemplateService = Depends(get_template_service),
    _=Depends(require_admin),
):
    try:
        return ok(ts.olustur(data.model_dump()))
    except Exception as e:
        return fail(str(e))


@router.put("/admin/templates/{template_id}")
async def template_guncelle(
    template_id: int,
    data: TemplateUpdate,
    ts: TemplateService = Depends(get_template_service),
    _=Depends(require_admin),
):
    try:
        return ok(ts.guncelle(template_id, data.model_dump(exclude_unset=True)))
    except Exception as e:
        return fail(str(e))


@router.delete("/admin/templates/{template_id}")
async def template_sil(
    template_id: int,
    ts: TemplateService = Depends(get_template_service),
    _=Depends(require_admin),
):
    try:
        return ok(ts.sil(template_id))
    except Exception as e:
        return fail(str(e))


@router.get("/admin/templates/{template_id}/toggle")
async def template_toggle(
    template_id: int,
    ts: TemplateService = Depends(get_template_service),
    _=Depends(require_admin),
):
    try:
        return ok(ts.aktif_degistir(template_id))
    except Exception as e:
        return fail(str(e))


# ─── Admin — Homepage Sections ──────────────────────────────────────────────
@router.get("/admin/templates/{template_id}/bolumler")
async def bolumleri_listele(
    template_id: int,
    hp: HomepageService = Depends(get_homepage_service),
    _=Depends(require_admin),
):
    try:
        return ok(hp.template_bolumleri(template_id))
    except Exception as e:
        return fail(str(e))


@router.put("/admin/bolumler/sirala")
async def bolum_sirala(
    data: HomepageSectionReorder,
    hp: HomepageService = Depends(get_homepage_service),
    _=Depends(require_admin),
):
    try:
        return ok(hp.bolum_sirala(data.items))
    except Exception as e:
        return fail(str(e))


@router.get("/admin/bolumler/{bolum_id}")
async def bolum_getir(
    bolum_id: int,
    hp: HomepageService = Depends(get_homepage_service),
    _=Depends(require_admin),
):
    try:
        return ok(hp.bolum_getir(bolum_id))
    except Exception as e:
        return fail(str(e))


@router.put("/admin/bolumler/{bolum_id}")
async def bolum_guncelle(
    bolum_id: int,
    data: HomepageSectionUpdate,
    hp: HomepageService = Depends(get_homepage_service),
    _=Depends(require_admin),
):
    try:
        return ok(hp.bolum_guncelle(bolum_id, data.model_dump(exclude_unset=True)))
    except Exception as e:
        return fail(str(e))
