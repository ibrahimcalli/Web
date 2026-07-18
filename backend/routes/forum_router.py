"""Forum Router — Forum yönetimi API endpoint'leri."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends

from backend.core.dependencies import (
    get_current_user, get_forum_service, require_admin,
)
from backend.schemas.forum import (
    ForumCategoryCreate, ForumCategoryUpdate, ForumPostCreate,
    ForumTopicCreate, ForumTopicUpdate,
)
from backend.schemas.response import fail, ok
from backend.services.forum_service import ForumService

router = APIRouter(tags=["CMS - Forum"])


# ─── Public ─────────────────────────────────────────────────────────────────
@router.get("/forum/kategoriler")
async def kategorileri_listele(
    forum_service: ForumService = Depends(get_forum_service),
    _user: dict = Depends(get_current_user),
):
    try:
        return ok(forum_service.kategori_listele(aktif_only=True))
    except Exception as e:
        return fail(str(e))


@router.get("/forum/konular")
async def konulari_listele(
    kategori_id: Optional[int] = None,
    forum_service: ForumService = Depends(get_forum_service),
    _user: dict = Depends(get_current_user),
):
    try:
        return ok(forum_service.konu_listele(category_id=kategori_id))
    except Exception as e:
        return fail(str(e))


@router.get("/forum/konular/{konu_id}")
async def konu_getir(
    konu_id: int,
    forum_service: ForumService = Depends(get_forum_service),
    _user: dict = Depends(get_current_user),
):
    try:
        return ok(forum_service.konu_getir(konu_id))
    except Exception as e:
        return fail(str(e))


@router.get("/forum/konular/{konu_id}/yanitlar")
async def yanitlari_listele(
    konu_id: int,
    forum_service: ForumService = Depends(get_forum_service),
    _user: dict = Depends(get_current_user),
):
    try:
        return ok(forum_service.yanit_listele(konu_id))
    except Exception as e:
        return fail(str(e))


# ─── Admin — Kategoriler ────────────────────────────────────────────────────
@router.get("/admin/forum/kategoriler")
async def admin_kategori_listele(
    forum_service: ForumService = Depends(get_forum_service),
    _=Depends(require_admin),
):
    try:
        return ok(forum_service.kategori_listele())
    except Exception as e:
        return fail(str(e))


@router.post("/admin/forum/kategoriler")
async def admin_kategori_olustur(
    data: ForumCategoryCreate,
    forum_service: ForumService = Depends(get_forum_service),
    _=Depends(require_admin),
):
    try:
        return ok(forum_service.kategori_olustur(data.model_dump()))
    except Exception as e:
        return fail(str(e))


@router.put("/admin/forum/kategoriler/{kategori_id}")
async def admin_kategori_guncelle(
    kategori_id: int,
    data: ForumCategoryUpdate,
    forum_service: ForumService = Depends(get_forum_service),
    _=Depends(require_admin),
):
    try:
        return ok(forum_service.kategori_guncelle(kategori_id, data.model_dump(exclude_unset=True)))
    except Exception as e:
        return fail(str(e))


@router.delete("/admin/forum/kategoriler/{kategori_id}")
async def admin_kategori_sil(
    kategori_id: int,
    forum_service: ForumService = Depends(get_forum_service),
    _=Depends(require_admin),
):
    try:
        return ok(forum_service.kategori_sil(kategori_id))
    except Exception as e:
        return fail(str(e))


# ─── Admin — Konular ────────────────────────────────────────────────────────
@router.get("/admin/forum/konular")
async def admin_konu_listele(
    kategori_id: Optional[int] = None,
    forum_service: ForumService = Depends(get_forum_service),
    _=Depends(require_admin),
):
    try:
        return ok(forum_service.konu_listele(category_id=kategori_id))
    except Exception as e:
        return fail(str(e))


@router.post("/admin/forum/konular")
async def admin_konu_olustur(
    data: ForumTopicCreate,
    forum_service: ForumService = Depends(get_forum_service),
    _=Depends(require_admin),
):
    try:
        return ok(forum_service.konu_olustur(data.model_dump()))
    except Exception as e:
        return fail(str(e))


@router.put("/admin/forum/konular/{konu_id}")
async def admin_konu_guncelle(
    konu_id: int,
    data: ForumTopicUpdate,
    forum_service: ForumService = Depends(get_forum_service),
    _=Depends(require_admin),
):
    try:
        return ok(forum_service.konu_guncelle(konu_id, data.model_dump(exclude_unset=True)))
    except Exception as e:
        return fail(str(e))


@router.delete("/admin/forum/konular/{konu_id}")
async def admin_konu_sil(
    konu_id: int,
    forum_service: ForumService = Depends(get_forum_service),
    _=Depends(require_admin),
):
    try:
        return ok(forum_service.konu_sil(konu_id))
    except Exception as e:
        return fail(str(e))


# ─── Admin — Yanıtlar ──────────────────────────────────────────────────────
@router.get("/admin/forum/konular/{konu_id}/yanitlar")
async def admin_yanit_listele(
    konu_id: int,
    forum_service: ForumService = Depends(get_forum_service),
    _=Depends(require_admin),
):
    try:
        return ok(forum_service.yanit_listele(konu_id))
    except Exception as e:
        return fail(str(e))


@router.post("/admin/forum/yanitlar")
async def admin_yanit_olustur(
    data: ForumPostCreate,
    forum_service: ForumService = Depends(get_forum_service),
    _=Depends(require_admin),
):
    try:
        return ok(forum_service.yanit_olustur(data.model_dump()))
    except Exception as e:
        return fail(str(e))


@router.delete("/admin/forum/yanitlar/{yanit_id}")
async def admin_yanit_sil(
    yanit_id: int,
    forum_service: ForumService = Depends(get_forum_service),
    _=Depends(require_admin),
):
    try:
        return ok(forum_service.yanit_sil(yanit_id))
    except Exception as e:
        return fail(str(e))


# ─── Admin — Ayarlar ───────────────────────────────────────────────────────
@router.get("/admin/forum/ayarlar")
async def admin_forum_ayarlari(
    forum_service: ForumService = Depends(get_forum_service),
    _=Depends(require_admin),
):
    try:
        return ok(forum_service.ayarlari_getir())
    except Exception as e:
        return fail(str(e))


@router.put("/admin/forum/ayarlar")
async def admin_forum_ayar_guncelle(
    data: ForumCategoryUpdate,
    forum_service: ForumService = Depends(get_forum_service),
    _=Depends(require_admin),
):
    try:
        return ok(forum_service.ayar_guncelle(data.model_dump()))
    except Exception as e:
        return fail(str(e))
