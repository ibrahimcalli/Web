"""Page Router — Sayfa yönetimi API endpoint'leri."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.core.dependencies import get_current_user, get_page_service, require_admin
from backend.schemas.page import PageCreate, PageUpdate
from backend.schemas.response import fail, ok
from backend.services.page_service import PageService

router = APIRouter(tags=["CMS - Sayfa"])


@router.get("/sayfa/{slug}")
async def halka_acik_sayfa(
    slug: str,
    page_service: PageService = Depends(get_page_service),
    _user: dict = Depends(get_current_user),
):
    try:
        return ok(page_service.slug_ile_getir(slug))
    except Exception as e:
        return fail(str(e))


@router.get("/public/sayfa/{slug}")
async def public_sayfa(
    slug: str,
    page_service: PageService = Depends(get_page_service),
):
    """Public sayfa görüntüleme (auth gerekmez)."""
    try:
        return ok(page_service.slug_ile_getir(slug))
    except Exception as e:
        return fail(str(e))


@router.get("/admin/sayfalar")
async def sayfa_listele(
    durum: str = None,
    page_service: PageService = Depends(get_page_service),
    _=Depends(require_admin),
):
    try:
        return ok(page_service.listele(durum=durum))
    except Exception as e:
        return fail(str(e))


@router.get("/admin/sayfalar/{sayfa_id}")
async def sayfa_getir(
    sayfa_id: int,
    page_service: PageService = Depends(get_page_service),
    _=Depends(require_admin),
):
    try:
        return ok(page_service.getir(sayfa_id))
    except Exception as e:
        return fail(str(e))


@router.post("/admin/sayfalar")
async def sayfa_olustur(
    data: PageCreate,
    page_service: PageService = Depends(get_page_service),
    _=Depends(require_admin),
):
    try:
        return ok(page_service.olustur(data.model_dump()))
    except Exception as e:
        return fail(str(e))


@router.put("/admin/sayfalar/{sayfa_id}")
async def sayfa_guncelle(
    sayfa_id: int,
    data: PageUpdate,
    page_service: PageService = Depends(get_page_service),
    _=Depends(require_admin),
):
    try:
        return ok(page_service.guncelle(sayfa_id, data.model_dump(exclude_unset=True)))
    except Exception as e:
        return fail(str(e))


@router.delete("/admin/sayfalar/{sayfa_id}")
async def sayfa_sil(
    sayfa_id: int,
    page_service: PageService = Depends(get_page_service),
    _=Depends(require_admin),
):
    try:
        return ok(page_service.sil(sayfa_id))
    except Exception as e:
        return fail(str(e))
