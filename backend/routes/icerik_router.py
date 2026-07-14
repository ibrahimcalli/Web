"""İstek, Ayar, Banner, Blog Router'ları."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request, UploadFile, File
from pathlib import Path

from backend.core.config import BASE_DIR
from backend.core.dependencies import (
    get_istek_service, get_ayar_service, get_banner_service, get_blog_service,
    get_current_user, require_auth, require_admin
)
from backend.schemas.icerik import (
    IstekCreate, IstekDurumGuncelle,
    AyarSet,
    BannerCreate, BannerUpdate, BannerAktifGuncelle, BannerSiraGuncelle, BannerResimEkle,
    BlogCreate, BlogUpdate, BlogKapakEkle
)
from backend.schemas.response import ok, fail
from backend.services.icerik_service import IstekService, AyarService, BannerService, BlogService

# ─── İstek Router ─────────────────────────────────────────────────────────────
istek_router = APIRouter()


@istek_router.post("/istekler")
async def istek_olustur(
    request: Request,
    data: IstekCreate,
    istek_service: IstekService = Depends(get_istek_service),
):
    """Kullanıcı isteği oluştur."""
    try:
        result = istek_service.olustur(
            data.ad_soyad, data.telefon, data.email, data.mesaj, data.portfoy_id
        )
        return ok(result)
    except Exception as e:
        return fail(str(e))


@istek_router.get("/istekler", dependencies=[Depends(require_admin)])
async def istek_liste(
    istek_service: IstekService = Depends(get_istek_service),
):
    """Tüm istekler (admin)."""
    try:
        result = istek_service.listele()
        return ok(result)
    except Exception as e:
        return fail(str(e))


@istek_router.patch("/istekler/{iid}/durum", dependencies=[Depends(require_admin)])
async def istek_durum(
    iid: int,
    request: Request,
    data: IstekDurumGuncelle,
    istek_service: IstekService = Depends(get_istek_service),
):
    """İstek durum değiştir (admin)."""
    try:
        result = istek_service.durum_degistir(iid, data.durum)
        return ok(result)
    except Exception as e:
        return fail(str(e))


# ─── Ayar Router ──────────────────────────────────────────────────────────────
ayar_router = APIRouter()


@ayar_router.get("/ayarlar")
async def ayar_get(
    ayar_service: AyarService = Depends(get_ayar_service),
):
    """Site ayarları."""
    try:
        result = ayar_service.get_all()
        return ok(result)
    except Exception as e:
        return fail(str(e))


@ayar_router.put("/ayarlar", dependencies=[Depends(require_admin)])
async def ayar_set(
    request: Request,
    data: AyarSet,
    ayar_service: AyarService = Depends(get_ayar_service),
):
    """Ayarları güncelle (admin)."""
    try:
        result = ayar_service.set_all(data.ayarlar)
        return ok(result)
    except Exception as e:
        return fail(str(e))


# ─── Banner Router ────────────────────────────────────────────────────────────
banner_router = APIRouter()


@banner_router.get("/bannerlar")
async def banner_liste(
    request: Request,
    konum: str = "",
    aktif: bool = False,
    banner_service: BannerService = Depends(get_banner_service),
):
    """Banner listesi."""
    try:
        result = banner_service.listele(konum, aktif)
        return ok(result)
    except Exception as e:
        return fail(str(e))


@banner_router.post("/bannerlar", dependencies=[Depends(require_admin)])
async def banner_olustur(
    request: Request,
    data: BannerCreate,
    banner_service: BannerService = Depends(get_banner_service),
):
    """Banner oluştur (admin)."""
    try:
        result = banner_service.olustur(data.model_dump())
        return ok(result)
    except Exception as e:
        return fail(str(e))


@banner_router.put("/bannerlar/{bid}", dependencies=[Depends(require_admin)])
async def banner_guncelle(
    bid: int,
    request: Request,
    data: BannerUpdate,
    banner_service: BannerService = Depends(get_banner_service),
):
    """Banner güncelle (admin)."""
    try:
        result = banner_service.guncelle(bid, data.model_dump(exclude_unset=True))
        return ok(result)
    except Exception as e:
        return fail(str(e))


@banner_router.patch("/bannerlar/{bid}/aktif", dependencies=[Depends(require_admin)])
async def banner_aktif(
    bid: int,
    request: Request,
    data: BannerAktifGuncelle,
    banner_service: BannerService = Depends(get_banner_service),
):
    """Banner aktif/pasif (admin)."""
    try:
        result = banner_service.aktif_degistir(bid, data.aktif)
        return ok(result)
    except Exception as e:
        return fail(str(e))


@banner_router.patch("/bannerlar/sira", dependencies=[Depends(require_admin)])
async def banner_sira(
    request: Request,
    data: BannerSiraGuncelle,
    banner_service: BannerService = Depends(get_banner_service),
):
    """Banner sırala (admin)."""
    try:
        result = banner_service.sirala(data.siralar)
        return ok(result)
    except Exception as e:
        return fail(str(e))


@banner_router.delete("/bannerlar/{bid}", dependencies=[Depends(require_admin)])
async def banner_sil(
    bid: int,
    banner_service: BannerService = Depends(get_banner_service),
):
    """Banner sil (admin)."""
    try:
        result = banner_service.sil(bid)
        return ok(result)
    except Exception as e:
        return fail(str(e))


@banner_router.post("/bannerlar/{bid}/resim", dependencies=[Depends(require_admin)])
async def banner_resim(
    bid: int,
    request: Request,
    file: UploadFile = File(...),
    banner_service: BannerService = Depends(get_banner_service),
):
    """Banner resim yükle (admin)."""
    try:
        import uuid
        ext = Path(file.filename).suffix if file.filename else ".jpg"
        filename = f"banner_{bid}_{uuid.uuid4().hex}{ext}"
        upload_path = BASE_DIR / "static" / "uploads" / "banners" / filename
        upload_path.parent.mkdir(parents=True, exist_ok=True)
        
        content = await file.read()
        upload_path.write_bytes(content)
        
        url = f"/static/uploads/banners/{filename}"
        result = banner_service.resim_ekle(bid, url)
        return ok(result)
    except Exception as e:
        return fail(str(e))


# ─── Blog Router ──────────────────────────────────────────────────────────────
blog_router = APIRouter()


@blog_router.get("/blog")
async def blog_liste(
    request: Request,
    durum: str = "",
    user: dict = Depends(get_current_user),
    blog_service: BlogService = Depends(get_blog_service),
):
    """Blog yazıları."""
    try:
        is_admin = bool(user and user.get("rol") == "admin")
        result = blog_service.listele(is_admin, durum)
        return ok(result)
    except Exception as e:
        return fail(str(e))


@blog_router.get("/blog/{slug}")
async def blog_detay(
    slug: str,
    blog_service: BlogService = Depends(get_blog_service),
):
    """Blog detay."""
    try:
        result = blog_service.get(slug)
        if not result:
            return fail("Blog yazısı bulunamadı")
        return ok(result)
    except Exception as e:
        return fail(str(e))


@blog_router.post("/blog", dependencies=[Depends(require_auth)])
async def blog_olustur(
    request: Request,
    data: BlogCreate,
    user: dict = Depends(require_auth),
    blog_service: BlogService = Depends(get_blog_service),
):
    """Blog oluştur (admin)."""
    try:
        import re
        slug = re.sub(r'[^a-z0-9]+', '-', data.baslik.lower()).strip('-')
        blog_data = data.model_dump()
        blog_data["slug"] = slug
        blog_data["yazar_id"] = user.get("id")
        
        result = blog_service.olustur(blog_data, user.get("id"))
        return ok(result)
    except Exception as e:
        return fail(str(e))


@blog_router.put("/blog/{bid}", dependencies=[Depends(require_auth)])
async def blog_guncelle(
    bid: int,
    request: Request,
    data: BlogUpdate,
    user: dict = Depends(require_auth),
    blog_service: BlogService = Depends(get_blog_service),
):
    """Blog güncelle (admin)."""
    try:
        update_data = data.model_dump(exclude_unset=True)
        result = blog_service.guncelle(bid, update_data)
        return ok(result)
    except Exception as e:
        return fail(str(e))


@blog_router.delete("/blog/{bid}", dependencies=[Depends(require_admin)])
async def blog_sil(
    bid: int,
    blog_service: BlogService = Depends(get_blog_service),
):
    """Blog sil (admin)."""
    try:
        result = blog_service.sil(bid)
        return ok(result)
    except Exception as e:
        return fail(str(e))


@blog_router.post("/blog/{bid}/kapak", dependencies=[Depends(require_admin)])
async def blog_kapak(
    bid: int,
    request: Request,
    file: UploadFile = File(...),
    blog_service: BlogService = Depends(get_blog_service),
):
    """Blog kapak resmi (admin)."""
    try:
        import uuid
        ext = Path(file.filename).suffix if file.filename else ".jpg"
        filename = f"blog_{bid}_{uuid.uuid4().hex}{ext}"
        upload_path = BASE_DIR / "static" / "uploads" / "blogs" / filename
        upload_path.parent.mkdir(parents=True, exist_ok=True)
        
        content = await file.read()
        upload_path.write_bytes(content)
        
        url = f"/static/uploads/blogs/{filename}"
        result = blog_service.kapak_ekle(bid, url)
        return ok(result)
    except Exception as e:
        return fail(str(e))