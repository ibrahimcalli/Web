"""Menu Router — Menü yönetimi API endpoint'leri.

Admin panel (admin yetkisi) ve public (herkes) olmak üzere iki grup endpoint.
Public olanlar frontend tarafından menü ağacını görüntülemek için kullanılır.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.core.dependencies import (
    get_current_user, get_menu_service, require_admin,
)
from backend.schemas.menu import (
    MenuCreate, MenuItemCreate, MenuItemReorder, MenuItemUpdate, MenuUpdate,
)
from backend.schemas.response import fail, ok
from backend.services.menu_service import MenuService

router = APIRouter(tags=["CMS - Menü"])


# ─── Public (frontend) ─────────────────────────────────────────────────────
@router.get("/menu/{slug}")
async def halka_acik_menu(
    slug: str,
    menu_service: MenuService = Depends(get_menu_service),
    user: dict = Depends(get_current_user),
):
    """Hiyerarşik menü ağacı (frontend için). Sadece aktif öğeler döner."""
    try:
        kullanici_rol = (user or {}).get("rol", "")
        result = menu_service.halka_acik_menu(slug, kullanici_rol=kullanici_rol)
        return ok(result)
    except Exception as e:
        return fail(str(e))


# ─── Admin — Menü CRUD ─────────────────────────────────────────────────────
@router.get("/admin/menuler")
async def menu_listele(
    menu_service: MenuService = Depends(get_menu_service),
    _=Depends(require_admin),
):
    try:
        return ok(menu_service.listele_menuler())
    except Exception as e:
        return fail(str(e))


@router.post("/admin/menuler")
async def menu_olustur(
    data: MenuCreate,
    menu_service: MenuService = Depends(get_menu_service),
    _=Depends(require_admin),
):
    try:
        return ok(menu_service.olustur_menu(data.model_dump()))
    except Exception as e:
        return fail(str(e))


@router.get("/admin/menuler/{menu_id}")
async def menu_getir(
    menu_id: int,
    menu_service: MenuService = Depends(get_menu_service),
    _=Depends(require_admin),
):
    try:
        return ok(menu_service.getir_menu(menu_id))
    except Exception as e:
        return fail(str(e))


@router.put("/admin/menuler/{menu_id}")
async def menu_guncelle(
    menu_id: int,
    data: MenuUpdate,
    menu_service: MenuService = Depends(get_menu_service),
    _=Depends(require_admin),
):
    try:
        return ok(menu_service.guncelle_menu(menu_id, data.model_dump(exclude_unset=True)))
    except Exception as e:
        return fail(str(e))


@router.delete("/admin/menuler/{menu_id}")
async def menu_sil(
    menu_id: int,
    menu_service: MenuService = Depends(get_menu_service),
    _=Depends(require_admin),
):
    try:
        return ok(menu_service.sil_menu(menu_id))
    except Exception as e:
        return fail(str(e))


# ─── Admin — Menu Items ────────────────────────────────────────────────────
@router.get("/admin/menuler/{menu_id}/ogeler")
async def oge_listele(
    menu_id: int,
    menu_service: MenuService = Depends(get_menu_service),
    _=Depends(require_admin),
):
    try:
        return ok(menu_service.listele_ogeler(menu_id))
    except Exception as e:
        return fail(str(e))


@router.post("/admin/menuler/{menu_id}/ogeler")
async def oge_olustur(
    menu_id: int,
    data: MenuItemCreate,
    menu_service: MenuService = Depends(get_menu_service),
    _=Depends(require_admin),
):
    try:
        data_dict = data.model_dump()
        data_dict["menu_id"] = menu_id
        return ok(menu_service.olustur_oge(data_dict))
    except Exception as e:
        return fail(str(e))


@router.put("/admin/menu-ogeleri/sirala")
async def oge_sirala(
    data: MenuItemReorder,
    menu_service: MenuService = Depends(get_menu_service),
    _=Depends(require_admin),
):
    try:
        return ok(menu_service.yeniden_sirala(data.items))
    except Exception as e:
        return fail(str(e))


@router.put("/admin/menu-ogeleri/{item_id}")
async def oge_guncelle(
    item_id: int,
    data: MenuItemUpdate,
    menu_service: MenuService = Depends(get_menu_service),
    _=Depends(require_admin),
):
    try:
        return ok(menu_service.guncelle_oge(item_id, data.model_dump(exclude_unset=True)))
    except Exception as e:
        return fail(str(e))


@router.delete("/admin/menu-ogeleri/{item_id}")
async def oge_sil(
    item_id: int,
    menu_service: MenuService = Depends(get_menu_service),
    _=Depends(require_admin),
):
    try:
        return ok(menu_service.sil_oge(item_id))
    except Exception as e:
        return fail(str(e))
