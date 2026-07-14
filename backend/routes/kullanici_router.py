"""Kullanıcı Router."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request, UploadFile, File
from pathlib import Path

from backend.core.config import BASE_DIR
from backend.core.dependencies import (
    get_kullanici_service, get_current_user, require_auth, require_admin
)
from backend.schemas.kullanici import (
    KullaniciKayit, KullaniciCreate, KullaniciUpdate,
    SifreDegistir, KullaniciOnay
)
from backend.schemas.response import ok, fail
from backend.services.kullanici_service import KullaniciService

router = APIRouter()


@router.post("/kullanicilar/kayit")
async def kayit(
    request: Request,
    data: KullaniciKayit,
    kullanici_service: KullaniciService = Depends(get_kullanici_service),
):
    """Kullanıcı kaydı."""
    try:
        result = kullanici_service.kayit(data)
        return ok(result)
    except Exception as e:
        return fail(str(e))


@router.get("/kullanicilar/ben")
async def ben(
    request: Request,
    kullanici_service: KullaniciService = Depends(get_kullanici_service),
    user: dict = Depends(require_auth),
):
    """Kendi bilgilerini getir."""
    try:
        result = kullanici_service.ben(user["sub"])
        return ok(result)
    except Exception as e:
        return fail(str(e))


@router.put("/kullanicilar/profil")
async def profil_guncelle(
    request: Request,
    data: KullaniciUpdate,
    kullanici_service: KullaniciService = Depends(get_kullanici_service),
    user: dict = Depends(require_auth),
):
    """Profil güncelle."""
    try:
        result = kullanici_service.profil_guncelle(user["sub"], data)
        return ok(result)
    except Exception as e:
        return fail(str(e))


@router.post("/kullanicilar/profil-resmi")
async def profil_resmi(
    request: Request,
    file: UploadFile = File(...),
    kullanici_service: KullaniciService = Depends(get_kullanici_service),
    user: dict = Depends(require_auth),
):
    """Profil resmi yükle."""
    try:
        import uuid
        ext = Path(file.filename).suffix if file.filename else ".jpg"
        filename = f"{user['sub'].replace('@', '_')}{uuid.uuid4().hex}{ext}"
        upload_path = BASE_DIR / "static" / "uploads" / "profils" / filename
        upload_path.parent.mkdir(parents=True, exist_ok=True)
        
        content = await file.read()
        upload_path.write_bytes(content)
        
        url = f"/static/uploads/profils/{filename}"
        result = kullanici_service.set_profil_resmi(user["sub"], url)
        return ok(result)
    except Exception as e:
        return fail(str(e))


@router.put("/kullanicilar/sifre")
async def sifre_degistir(
    request: Request,
    data: SifreDegistir,
    kullanici_service: KullaniciService = Depends(get_kullanici_service),
    user: dict = Depends(require_auth),
):
    """Şifre değiştir."""
    try:
        result = kullanici_service.sifre_degistir(user["sub"], data.mevcut_sifre, data.yeni_sifre)
        return ok(result)
    except Exception as e:
        return fail(str(e))


# Admin endpointleri
@router.get("/kullanicilar", dependencies=[Depends(require_admin)])
async def liste(
    kullanici_service: KullaniciService = Depends(get_kullanici_service),
):
    """Tüm kullanıcılar (admin)."""
    try:
        result = kullanici_service.listele()
        return ok(result)
    except Exception as e:
        return fail(str(e))


@router.post("/kullanicilar", dependencies=[Depends(require_admin)])
async def ekle(
    request: Request,
    data: KullaniciCreate,
    kullanici_service: KullaniciService = Depends(get_kullanici_service),
):
    """Kullanıcı ekle (admin)."""
    try:
        result = kullanici_service.ekle(data)
        return ok(result)
    except Exception as e:
        return fail(str(e))


@router.patch("/kullanicilar/{kid}/onayla", dependencies=[Depends(require_admin)])
async def onayla(
    kid: int,
    kullanici_service: KullaniciService = Depends(get_kullanici_service),
):
    """Kullanıcıyı onayla (admin)."""
    try:
        result = kullanici_service.onayla(kid)
        return ok(result)
    except Exception as e:
        return fail(str(e))


@router.patch("/kullanicilar/{kid}/onay-kaldir", dependencies=[Depends(require_admin)])
async def onay_kaldir(
    kid: int,
    kullanici_service: KullaniciService = Depends(get_kullanici_service),
):
    """Kullanıcı onayını kaldır (admin)."""
    try:
        result = kullanici_service.onay_kaldir(kid)
        return ok(result)
    except Exception as e:
        return fail(str(e))


@router.delete("/kullanicilar/{kid}", dependencies=[Depends(require_admin)])
async def sil(
    kid: int,
    kullanici_service: KullaniciService = Depends(get_kullanici_service),
):
    """Kullanıcı sil (admin)."""
    try:
        result = kullanici_service.sil(kid)
        return ok(result)
    except Exception as e:
        return fail(str(e))