"""Portföy Router."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

from backend.core.config import BASE_DIR
from backend.core.dependencies import get_portfoy_service, get_current_user, require_auth
from backend.schemas.portfoy import (
    PortfoyCreate, PortfoyUpdate, PortfoyDurumGuncelle,
    PortfoyResimEkle, PortfoyResimSirala, PortfoyKapakGuncelle
)
from backend.schemas.response import ok, fail
from backend.services.portfoy_service import PortfoyService

router = APIRouter()


@router.get("/portfoyler")
async def liste(
    request: Request,
    kategori: str = "",
    alt_kat: str = "",
    durum: str = "Aktif",
    arama: str = "",
    portfoy_service: PortfoyService = Depends(get_portfoy_service),
    user: dict = Depends(get_current_user),
):
    """Portföy listesi."""
    try:
        result = portfoy_service.listele(user, kategori, alt_kat, durum, arama)
        return ok(result)
    except Exception as e:
        return fail(str(e))


@router.get("/portfoyler/{pid}")
async def detay(
    pid: int,
    request: Request,
    portfoy_service: PortfoyService = Depends(get_portfoy_service),
    user: dict = Depends(get_current_user),
):
    """Portföy detay."""
    try:
        result = portfoy_service.detay(pid, user)
        return ok(result)
    except Exception as e:
        return fail(str(e))


@router.post("/portfoyler")
async def ekle(
    request: Request,
    data: PortfoyCreate,
    portfoy_service: PortfoyService = Depends(get_portfoy_service),
    _ = Depends(require_auth),
):
    """Portföy ekle."""
    try:
        result = portfoy_service.ekle(data)
        return ok(result, "Portföy oluşturuldu")
    except Exception as e:
        return fail(str(e))


@router.put("/portfoyler/{pid}")
async def guncelle(
    pid: int,
    request: Request,
    data: PortfoyUpdate,
    portfoy_service: PortfoyService = Depends(get_portfoy_service),
    _ = Depends(require_auth),
):
    """Portföy güncelle."""
    try:
        result = portfoy_service.guncelle(pid, data)
        return ok(result)
    except Exception as e:
        return fail(str(e))


@router.patch("/portfoyler/{pid}/durum")
async def durum_degistir(
    pid: int,
    request: Request,
    data: PortfoyDurumGuncelle,
    portfoy_service: PortfoyService = Depends(get_portfoy_service),
    _ = Depends(require_auth),
):
    """Portföy durum değiştir."""
    try:
        result = portfoy_service.durum_degistir(pid, data.durum)
        return ok(result)
    except Exception as e:
        return fail(str(e))


@router.delete("/portfoyler/{pid}")
async def sil(
    pid: int,
    request: Request,
    portfoy_service: PortfoyService = Depends(get_portfoy_service),
    _ = Depends(require_auth),
):
    """Portföy sil."""
    try:
        result = portfoy_service.sil(pid)
        return ok(result)
    except Exception as e:
        return fail(str(e))


@router.post("/portfoyler/{pid}/resim")
async def resim_ekle(
    pid: int,
    request: Request,
    file: UploadFile = File(...),
    portfoy_service: PortfoyService = Depends(get_portfoy_service),
    _ = Depends(require_auth),
):
    """Portföye resim yükle."""
    try:
        import uuid
        ext = Path(file.filename).suffix if file.filename else ".jpg"
        filename = f"{uuid.uuid4().hex}{ext}"
        upload_path = BASE_DIR / "static" / "uploads" / "portfoyler" / filename
        upload_path.parent.mkdir(parents=True, exist_ok=True)
        
        content = await file.read()
        upload_path.write_bytes(content)
        
        url = f"/static/uploads/portfoyler/{filename}"
        result = portfoy_service.resim_ekle(pid, url)
        return ok(result)
    except Exception as e:
        return fail(str(e))


@router.delete("/portfoyler/{pid}/resim")
async def resim_sil(
    pid: int,
    request: Request,
    url: str,
    portfoy_service: PortfoyService = Depends(get_portfoy_service),
    _ = Depends(require_auth),
):
    """Portföy resmini sil."""
    try:
        result = portfoy_service.resim_sil(pid, url)
        return ok(result)
    except Exception as e:
        return fail(str(e))


@router.put("/portfoyler/{pid}/resim/sirala")
async def resim_sirala(
    pid: int,
    request: Request,
    data: PortfoyResimSirala,
    portfoy_service: PortfoyService = Depends(get_portfoy_service),
    _ = Depends(require_auth),
):
    """Portföy resim sırala."""
    try:
        result = portfoy_service.resim_sirala(pid, data.resimler)
        return ok(result)
    except Exception as e:
        return fail(str(e))


@router.patch("/portfoyler/{pid}/resim/kapak")
async def kapak_guncelle(
    pid: int,
    request: Request,
    data: PortfoyKapakGuncelle,
    portfoy_service: PortfoyService = Depends(get_portfoy_service),
    _ = Depends(require_auth),
):
    """Kapak resmi güncelle."""
    try:
        result = portfoy_service.kapak_guncelle(pid, data.url)
        return ok(result)
    except Exception as e:
        return fail(str(e))


@router.get("/portfoyler/{pid}/danismanlar")
async def danismanlar(
    pid: int,
    request: Request,
    portfoy_service: PortfoyService = Depends(get_portfoy_service),
):
    """Danışman bilgileri."""
    try:
        result = portfoy_service.danismanlar(pid)
        return ok(result)
    except Exception as e:
        return fail(str(e))


@router.get("/portfoyler/{pid}/sahip-profil")
async def sahip_profil(
    pid: int,
    request: Request,
    portfoy_service: PortfoyService = Depends(get_portfoy_service),
):
    """Sahip profil bilgileri."""
    try:
        result = portfoy_service.sahip_profil(pid)
        return ok(result)
    except Exception as e:
        return fail(str(e))


@router.get("/istatistik")
async def istatistik(
    request: Request,
    portfoy_service: PortfoyService = Depends(get_portfoy_service),
    user: dict = Depends(get_current_user),
):
    """İstatistikler."""
    try:
        result = portfoy_service.istatistik(user)
        return ok(result)
    except Exception as e:
        return fail(str(e))