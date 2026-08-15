"""Forum Router — Forum yönetimi + genel kullanım API endpoint'leri."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends

from backend.core.dependencies import (
    get_current_user, get_forum_service, require_admin,
)
from backend.core.errors import AppError
from backend.schemas.forum import (
    ForumCategoryCreate, ForumCategoryUpdate, ForumPostCreate,
    ForumPostCreatePublic, ForumSettingUpdate, ForumTopicCreate,
    ForumTopicCreatePublic, ForumTopicUpdate,
)
from backend.schemas.response import fail, ok
from backend.services.forum_service import ForumService

router = APIRouter(tags=["CMS - Forum"])


def _forum_kapali_kontrolu(forum_service: ForumService) -> None:
    """Forum kapalıysa AppError fırlatır — global ErrorHandler middleware'i
    bunu doğru HTTP 403 yanıtına çevirir (projedeki standart hata deseni)."""
    if not forum_service.forum_aktif_mi():
        raise AppError("Forum şu anda kapalı", 403)


# ─── Public ─────────────────────────────────────────────────────────────────
@router.get("/forum/durum")
async def forum_durumu(
    forum_service: ForumService = Depends(get_forum_service),
):
    """Ziyaretçilerin (giriş yapmadan) forum aktif mi / misafir yazabilir mi
    diye kontrol edebileceği hafif endpoint — nav menüde forum linkini
    gösterip göstermemek ve yeni konu formunu misafirlere açıp açmamak için."""
    return ok({
        "aktif": forum_service.forum_aktif_mi(),
        "misafir_yazabilir": forum_service.misafir_yazabilir_mi(),
    })


@router.get("/forum/kategoriler")
async def kategorileri_listele(
    forum_service: ForumService = Depends(get_forum_service),
    _user: dict = Depends(get_current_user),
):
    _forum_kapali_kontrolu(forum_service)
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
    _forum_kapali_kontrolu(forum_service)
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
    _forum_kapali_kontrolu(forum_service)
    try:
        return ok(forum_service.konu_getir(konu_id))
    except Exception as e:
        return fail(str(e))


@router.post("/forum/konular")
async def konu_olustur(
    data: ForumTopicCreatePublic,
    forum_service: ForumService = Depends(get_forum_service),
    user: Optional[dict] = Depends(get_current_user),
):
    """Genel kullanıcı (veya ayar açıksa misafir) yeni konu açar."""
    try:
        return ok(forum_service.konu_olustur_kullanici(data.model_dump(), user))
    except Exception as e:
        return fail(str(e))


@router.get("/forum/konular/{konu_id}/yanitlar")
async def yanitlari_listele(
    konu_id: int,
    forum_service: ForumService = Depends(get_forum_service),
    _user: dict = Depends(get_current_user),
):
    _forum_kapali_kontrolu(forum_service)
    try:
        return ok(forum_service.yanit_listele(konu_id))
    except Exception as e:
        return fail(str(e))


@router.post("/forum/konular/{konu_id}/yanitlar")
async def yanit_olustur(
    konu_id: int,
    data: ForumPostCreatePublic,
    forum_service: ForumService = Depends(get_forum_service),
    user: Optional[dict] = Depends(get_current_user),
):
    """Genel kullanıcı (veya ayar açıksa misafir) konuya yanıt yazar."""
    try:
        gonderilen = data.model_dump()
        gonderilen["topic_id"] = konu_id
        return ok(forum_service.yanit_olustur_kullanici(gonderilen, user))
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


@router.put("/admin/forum/yanitlar/{yanit_id}")
async def admin_yanit_guncelle(
    yanit_id: int,
    data: dict,
    forum_service: ForumService = Depends(get_forum_service),
    _=Depends(require_admin),
):
    """Moderasyon: örn. {"durum": "yayin"} göndererek onay bekleyen bir
    yanıtı yayınlamak veya {"durum": "reddedildi"} ile reddetmek için."""
    try:
        return ok(forum_service.yanit_guncelle(yanit_id, data))
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
    data: ForumSettingUpdate,
    forum_service: ForumService = Depends(get_forum_service),
    _=Depends(require_admin),
):
    """NOT: Bu endpoint eskiden yanlış şema (ForumCategoryUpdate) ve yanlış
    servis çağrısı (data.model_dump() — servis 2 ayrı string bekliyor)
    kullanıyordu, bu yüzden çalışmıyordu. 2026-08'de düzeltildi."""
    try:
        return ok(forum_service.ayar_guncelle(data.anahtar, data.deger))
    except Exception as e:
        return fail(str(e))
