"""Widget Router — Widget yönetimi API endpoint'leri."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.core.dependencies import (
    get_current_user, get_widget_service, require_admin,
)
from backend.schemas.response import fail, ok
from backend.schemas.widget import WidgetCreate, WidgetUpdate
from backend.services.widget_service import WidgetService

router = APIRouter(tags=["CMS - Widget"])


@router.get("/widgets")
async def halka_acik_widgetlar(
    widget_service: WidgetService = Depends(get_widget_service),
    _user: dict = Depends(get_current_user),
):
    try:
        return ok(widget_service.listele(aktif_only=True))
    except Exception as e:
        return fail(str(e))


@router.get("/admin/widgets")
async def widget_listele(
    widget_service: WidgetService = Depends(get_widget_service),
    _=Depends(require_admin),
):
    try:
        return ok(widget_service.listele())
    except Exception as e:
        return fail(str(e))


@router.get("/admin/widgets/{widget_id}")
async def widget_getir(
    widget_id: int,
    widget_service: WidgetService = Depends(get_widget_service),
    _=Depends(require_admin),
):
    try:
        return ok(widget_service.getir(widget_id))
    except Exception as e:
        return fail(str(e))


@router.post("/admin/widgets")
async def widget_olustur(
    data: WidgetCreate,
    widget_service: WidgetService = Depends(get_widget_service),
    _=Depends(require_admin),
):
    try:
        return ok(widget_service.olustur(data.model_dump()))
    except Exception as e:
        return fail(str(e))


@router.put("/admin/widgets/{widget_id}")
async def widget_guncelle(
    widget_id: int,
    data: WidgetUpdate,
    widget_service: WidgetService = Depends(get_widget_service),
    _=Depends(require_admin),
):
    try:
        return ok(widget_service.guncelle(widget_id, data.model_dump(exclude_unset=True)))
    except Exception as e:
        return fail(str(e))


@router.delete("/admin/widgets/{widget_id}")
async def widget_sil(
    widget_id: int,
    widget_service: WidgetService = Depends(get_widget_service),
    _=Depends(require_admin),
):
    try:
        return ok(widget_service.sil(widget_id))
    except Exception as e:
        return fail(str(e))
