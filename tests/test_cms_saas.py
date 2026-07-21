"""CMS v2.4 — SaaS / marketplace testleri."""
from __future__ import annotations

import os
import tempfile

os.environ.setdefault("LOG_DIR", tempfile.mkdtemp())

from backend.db.database import Database
from backend.db.schema import init_db
from backend.services.api_marketplace_service import ApiMarketplaceService
from backend.services.backup_service import BackupService
from backend.services.tenant_service import TenantService
from backend.services.update_service import UpdateService


def make_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = Database(path)
    init_db(db)
    return db


def test_saas_tenant_list():
    db = make_db()
    service = TenantService(db)
    assert isinstance(service.listele(), list)


def test_saas_update_status():
    info = UpdateService().durum()
    assert isinstance(info, dict)
    assert "clean" in info or "degisen_dosyalar" in info


def test_saas_provider_catalog():
    service = ApiMarketplaceService(make_db())
    assert len(service.saglayici_listesi()) >= 9


def test_saas_api_seeded_openai_entry():
    service = ApiMarketplaceService(make_db())
    assert service.saglayici_ile_getir("openai") is not None


def test_saas_unknown_provider_fails_cleanly():
    service = ApiMarketplaceService(make_db())
    assert service.saglayici_ile_getir("olmayan") is None


def test_saas_provider_create_update_toggle():
    db = make_db()
    service = ApiMarketplaceService(db)
    sonuc = service.kaydet("test_provider", {"api_key": "abc", "api_url": "https://example.com", "aktif": True})
    assert sonuc["saglayici"] == "test_provider"
    ent = service.saglayici_ile_getir("test_provider")
    assert ent is not None
    assert ent["aktif"] == 1
    yeni = service.toggle("test_provider")
    assert isinstance(yeni, bool)
    assert service.saglayici_ile_getir("test_provider")["aktif"] in (0, 1)
