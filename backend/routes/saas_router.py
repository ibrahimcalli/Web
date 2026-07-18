"""FAZ 4 Router — Multi-tenant, Backup, Update, API Marketplace."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.core.dependencies import require_admin
from backend.db.database import db
from backend.schemas.response import fail, ok
from backend.services.api_marketplace_service import ApiMarketplaceService
from backend.services.backup_service import BackupService
from backend.services.tenant_service import TenantService
from backend.services.update_service import UpdateService

router = APIRouter(tags=["CMS - SaaS"])


# ─── Tenant (FAZ 4.1) ─────────────────────────────────────────────────────
@router.get("/admin/saas/tenant")
async def tenant_listele(_=Depends(require_admin)):
    ts = TenantService(db)
    return ok(ts.listele())


@router.post("/admin/saas/tenant")
async def tenant_ekle(data: dict, _=Depends(require_admin)):
    try:
        tid = TenantService(db).ekle(data)
        return ok({"id": tid})
    except Exception as e:
        return fail(str(e))


@router.put("/admin/saas/tenant/{tid}")
async def tenant_guncelle(tid: int, data: dict, _=Depends(require_admin)):
    try:
        TenantService(db).guncelle(tid, data)
        return ok({"guncellendi": True})
    except Exception as e:
        return fail(str(e))


@router.delete("/admin/saas/tenant/{tid}")
async def tenant_sil(tid: int, _=Depends(require_admin)):
    try:
        TenantService(db).sil(tid)
        return ok({"silindi": True})
    except Exception as e:
        return fail(str(e))


# ─── Backup (FAZ 4.2) ──────────────────────────────────────────────────────
@router.get("/admin/saas/backup")
async def backup_listele(_=Depends(require_admin)):
    return ok(BackupService(db).listele())


@router.post("/admin/saas/backup")
async def backup_olustur(data: dict = {}, _=Depends(require_admin)):
    sonuc = BackupService(db).olustur()
    return ok(sonuc)


@router.post("/admin/saas/backup/{backup_id}/restore")
async def backup_geri_yukle(backup_id: int, data: dict = {}, _=Depends(require_admin)):
    sonuc = BackupService(db).geri_yukle(backup_id)
    if sonuc["success"]:
        return ok(sonuc)
    return fail(sonuc.get("error", "Geri yükleme başarısız"))


@router.delete("/admin/saas/backup/{backup_id}")
async def backup_sil(backup_id: int, _=Depends(require_admin)):
    BackupService(db).sil(backup_id)
    return ok({"silindi": True})


# ─── Update (FAZ 4.2) ──────────────────────────────────────────────────────
@router.get("/admin/saas/update/durum")
async def update_durum(_=Depends(require_admin)):
    us = UpdateService()
    return ok({"versiyon": us.versiyon_kontrol(), "durum": us.durum()})


@router.post("/admin/saas/update")
async def update_yap(data: dict = {}, _=Depends(require_admin)):
    us = UpdateService()
    sonuc = us.guncelle()
    if sonuc["success"]:
        return ok(sonuc)
    return fail(sonuc.get("message", "Güncelleme başarısız"))


# ─── API Marketplace (FAZ 4.3) ─────────────────────────────────────────────
@router.get("/admin/saas/api/saglayicilar")
async def api_saglayici_liste(_=Depends(require_admin)):
    return ok(ApiMarketplaceService(db).saglayici_listesi())


@router.get("/admin/saas/api")
async def api_listele(_=Depends(require_admin)):
    return ok(ApiMarketplaceService(db).listele())


@router.get("/admin/saas/api/{saglayici}")
async def api_getir(saglayici: str, _=Depends(require_admin)):
    ent = ApiMarketplaceService(db).saglayici_ile_getir(saglayici)
    if not ent:
        return fail("API entegrasyonu bulunamadı")
    return ok(ent)


@router.post("/admin/saas/api/{saglayici}")
async def api_kaydet(saglayici: str, data: dict, _=Depends(require_admin)):
    try:
        sonuc = ApiMarketplaceService(db).kaydet(saglayici, data)
        return ok(sonuc)
    except Exception as e:
        return fail(str(e))


@router.get("/admin/saas/api/{saglayici}/toggle")
async def api_toggle(saglayici: str, _=Depends(require_admin)):
    yeni = ApiMarketplaceService(db).toggle(saglayici)
    return ok({"aktif": yeni})


@router.post("/admin/saas/api/{saglayici}/test")
async def api_test(saglayici: str, _=Depends(require_admin)):
    sonuc = ApiMarketplaceService(db).test_et(saglayici)
    if sonuc["success"]:
        return ok(sonuc)
    return fail(sonuc.get("message", "Test başarısız"))


@router.post("/admin/saas/api/seed")
async def api_seed(data: dict = {}, _=Depends(require_admin)):
    try:
        eklenen = ApiMarketplaceService(db).seed()
        return ok({"eklenen": eklenen})
    except Exception as e:
        return fail(str(e))
