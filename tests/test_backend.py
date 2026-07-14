"""
Backend mimari testleri.

Çalıştırma:
    python -m pytest tests/test_backend.py -v
"""
import os
import sys
import json
import tempfile
import sqlite3
from pathlib import Path

# Proje root
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.db.database import Database
from backend.db.schema import init_db, SCHEMA_SQL
from backend.core.password import hash_sifre, sifre_dogrula
from backend.repositories.portfoy_repository import PortfoyRepository
from backend.repositories.kullanici_repository import KullaniciRepository
from backend.repositories.misc_repository import (
    IstekRepository, AyarRepository, BannerRepository, BlogRepository
)
from backend.services.portfoy_service import PortfoyService
from backend.services.kullanici_service import KullaniciService
from backend.schemas.response import ok, fail, ApiResponse


def get_test_db():
    """Test için geçici veritabanı."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    return Database(path)


def setup_test_db(db):
    """Test veritabanını oluştur."""
    conn = db.connect()
    conn.executescript(SCHEMA_SQL)
    # Migrasyonlar
    for mig in [
        "ALTER TABLE kullanicilar ADD COLUMN onay INTEGER DEFAULT 1",
    ]:
        try:
            conn.execute(mig)
        except Exception:
            pass
    conn.execute(
        "INSERT INTO kullanicilar (ad_soyad,email,sifre,rol,onay) VALUES (?,?,?,?,?)",
        ("Test Admin", "admin@test.com", hash_sifre("admin123"), "admin", 1),
    )
    conn.execute(
        "INSERT INTO portfoyler (baslik,ana_kategori,alt_kategori,durum) VALUES (?,?,?,?)",
        ("Test Villa", "Konut", "Satılık", "Aktif"),
    )
    conn.commit()
    conn.close()


# ─── Password Tests ──────────────────────────────────────────────────────────
def test_password_hash():
    """Şifre hash ve doğrulama."""
    h = hash_sifre("test123")
    assert h != "test123"
    assert sifre_dogrula("test123", h) is True
    assert sifre_dogrula("wrong", h) is False


# ─── Repository Tests ─────────────────────────────────────────────────────────
def test_portfoy_repository():
    """Portfoy repository test."""
    db = get_test_db()
    setup_test_db(db)
    repo = PortfoyRepository(db)

    # List
    items = repo.list(is_admin=False)
    assert len(items) == 1
    assert items[0]["baslik"] == "Test Villa"

    # Get
    p = repo.get(1)
    assert p is not None
    assert p["baslik"] == "Test Villa"

    # Counts
    counts = repo.counts()
    assert counts["aktif"] == 1
    assert counts["toplam"] == 1

    # Exists
    assert repo.exists(1) is True
    assert repo.exists(999) is False


def test_kullanici_repository():
    """Kullanıcı repository test."""
    db = get_test_db()
    setup_test_db(db)
    repo = KullaniciRepository(db)

    # Get by email
    k = repo.get_by_email("admin@test.com")
    assert k is not None
    assert k["rol"] == "admin"

    # Get by id
    k = repo.get_by_id(1)
    assert k is not None
    assert k["ad_soyad"] == "Test Admin"

    # List
    all_users = repo.list_all()
    assert len(all_users) >= 1


def test_ayar_repository():
    """Ayar repository test."""
    db = get_test_db()
    setup_test_db(db)
    repo = AyarRepository(db)

    # Set
    repo.set("test_key", "test_value")

    # Get
    assert repo.get("test_key") == "test_value"

    # Get all
    all = repo.get_all()
    assert "test_key" in all


# ─── Response Tests ──────────────────────────────────────────────────────────
def test_response_models():
    """Standart response model test."""
    r = ok({"id": 1}, "Başarılı")
    assert r["success"] is True
    assert r["data"]["id"] == 1
    assert r["message"] == "Başarılı"

    f = fail("Hata")
    assert f["success"] is False
    assert f["message"] == "Hata"


# ─── Service Tests ────────────────────────────────────────────────────────────
def test_portfoy_service():
    """Portfoy service test."""
    db = get_test_db()
    setup_test_db(db)
    service = PortfoyService(
        portfoyler=PortfoyRepository(db),
        kullanicilar=KullaniciRepository(db),
        ayarlar=AyarRepository(db),
        istekler=IstekRepository(db),
    )

    # List
    items = service.listele(None)
    assert len(items) == 1

    # Detay
    d = service.detay(1, None)
    assert d["baslik"] == "Test Villa"


def test_kullanici_service():
    """Kullanıcı service test."""
    db = get_test_db()
    setup_test_db(db)
    service = KullaniciService(KullaniciRepository(db))

    # List
    users = service.listele()
    assert len(users) >= 1


if __name__ == "__main__":
    test_password_hash()
    print("✅ Password test")
    test_portfoy_repository()
    print("✅ Portfoy repository test")
    test_kullanici_repository()
    print("✅ Kullanıcı repository test")
    test_ayar_repository()
    print("✅ Ayar repository test")
    test_response_models()
    print("✅ Response model test")
    test_portfoy_service()
    print("✅ Portfoy service test")
    test_kullanici_service()
    print("✅ Kullanıcı service test")
    print("\n🎉 Tüm testler başarılı!")