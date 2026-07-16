"""
Sistem Router — Admin panel "Sistem" bölümü API'leri.

Tüm endpoint'ler admin yetkisi gerektirir.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.core.dependencies import require_admin
from backend.services.system_service import (
    KOMUTLAR,
    ai_tanilama,
    backup_olustur,
    cache_temizle,
    log_goruntule,
    log_temizle,
    servis_durumu,
    test_calistir,
)
from backend.schemas.response import ok, fail

router = APIRouter(prefix="/api/sistem", tags=["Sistem"])


@router.get("/durum")
async def durum(user: dict = Depends(require_admin)):
    """Servis, sistem, port durumu."""
    try:
        return ok(servis_durumu())
    except Exception as e:
        return fail(str(e))


@router.get("/log/{tip}")
async def log(tip: str, satir: int = 200, user: dict = Depends(require_admin)):
    """Log dosyası görüntüle. Tip: app, error, access, deploy."""
    if tip not in ("app", "error", "access", "deploy"):
        return fail("Geçersiz log tipi. app/error/access/deploy")
    try:
        return ok({"tip": tip, "icerik": log_goruntule(tip, satir)})
    except Exception as e:
        return fail(str(e))


@router.get("/komutlar")
async def komutlar(user: dict = Depends(require_admin)):
    """Sık kullanılan komutlar listesi."""
    try:
        return ok({"gruplar": KOMUTLAR})
    except Exception as e:
        return fail(str(e))


@router.post("/test")
async def test_calistir_endpoint(user: dict = Depends(require_admin)):
    """Tüm testleri çalıştır."""
    try:
        return ok(test_calistir())
    except Exception as e:
        return fail(str(e))


@router.get("/ai-tanilama")
async def ai_tanilama_endpoint(user: dict = Depends(require_admin)):
    """Tüm sistemi tek json'da topla (AI'ya yapıştırmak için)."""
    try:
        return ok(ai_tanilama())
    except Exception as e:
        return fail(str(e))


@router.get("/kılavuz")
async def kilavuz(user: dict = Depends(require_admin)):
    """Sistem kullanım kılavuzu."""
    # Sabit içerik — frontend'de render edilecek
    return ok({"baslik": "Portföy Gayrimenkul — Sistem Kılavuzu"})


@router.post("/bakim/{islem}")
async def bakim(islem: str, user: dict = Depends(require_admin)):
    """Bakım işlemleri: cache-temizle, log-temizle, backup."""
    if islem == "cache-temizle":
        return ok(cache_temizle())
    elif islem == "log-temizle":
        return ok(log_temizle())
    elif islem == "backup":
        return ok(backup_olustur())
    else:
        return fail(f"Bilinmeyen işlem: {islem}")


@router.get("/bakim")
async def bakim_liste(user: dict = Depends(require_admin)):
    """Mevcut bakım işlemlerini listele."""
    return ok({
        "islemler": [
            {"id": "cache-temizle", "baslik": "Cache Temizle", "aciklama": "Python __pycache__ dizinlerini temizle", "risk": "düşük"},
            {"id": "log-temizle", "baslik": "Log Temizle", "aciklama": "Log dosyalarını sıfırla (app, error, access)", "risk": "düşük"},
            {"id": "backup", "baslik": "Backup Oluştur", "aciklama": "DB + uploads yedeği al", "risk": "düşük"},
        ]
    })