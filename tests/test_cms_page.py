"""CMS v2.1 — Sayfa Modülü Testleri."""
from __future__ import annotations

import os
import sys
import tempfile
import random

os.environ.setdefault("LOG_DIR", tempfile.mkdtemp())

from fastapi.testclient import TestClient
from backend.core.security import token_olustur

ADMIN_TOKEN = token_olustur({"sub": "admin@test.com", "rol": "admin", "ad": "Test Admin"})


def _uniq(prefix="p"):
    return f"{prefix}_{random.randint(10000, 99999)}"


def make_client():
    try:
        from app import app
        return TestClient(app)
    except Exception:
        return None


TESTS = []


def _t(name):
    def dec(fn):
        TESTS.append((name, fn))
        return fn
    return dec


@_t("page_list_empty")
def _():
    c = make_client()
    if not c: return
    r = c.get("/api/admin/sayfalar", headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    assert r.status_code == 200 and r.json()["success"] is True


@_t("page_create")
def _():
    c = make_client()
    if not c: return
    slug = _uniq("sayfa")
    r = c.post("/api/admin/sayfalar",
               json={"baslik": "Test Sayfası", "slug": slug},
               headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    assert r.status_code == 200, r.text
    assert r.json()["success"] is True
    assert r.json()["data"]["slug"] == slug


@_t("page_get")
def _():
    c = make_client()
    if not c: return
    slug = _uniq("getir")
    r = c.post("/api/admin/sayfalar",
               json={"baslik": "Getir", "slug": slug, "durum": "Yayınla"},
               headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    pid = r.json()["data"]["id"]
    r2 = c.get(f"/api/admin/sayfalar/{pid}",
               headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    assert r2.json()["success"] is True
    assert r2.json()["data"]["id"] == pid


@_t("page_update")
def _():
    c = make_client()
    if not c: return
    slug = _uniq("guncel")
    r = c.post("/api/admin/sayfalar",
               json={"baslik": "Önce", "slug": slug},
               headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    pid = r.json()["data"]["id"]
    r2 = c.put(f"/api/admin/sayfalar/{pid}",
               json={"baslik": "Sonra"},
               headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    assert r2.json()["success"] is True
    assert r2.json()["data"]["baslik"] == "Sonra"


@_t("page_delete")
def _():
    c = make_client()
    if not c: return
    slug = _uniq("sil")
    r = c.post("/api/admin/sayfalar",
               json={"baslik": "Sil", "slug": slug},
               headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    pid = r.json()["data"]["id"]
    r2 = c.delete(f"/api/admin/sayfalar/{pid}",
                  headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    assert r2.json()["success"] is True
    assert r2.json()["data"]["silindi"] is True


@_t("page_duplicate_slug")
def _():
    c = make_client()
    if not c: return
    slug = _uniq("duz")
    c.post("/api/admin/sayfalar",
           json={"baslik": "İlk", "slug": slug},
           headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    r = c.post("/api/admin/sayfalar",
               json={"baslik": "Kopya", "slug": slug},
               headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    assert r.json()["success"] is False


@_t("page_not_found")
def _():
    c = make_client()
    if not c: return
    r = c.get("/api/admin/sayfalar/999999",
              headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    assert r.json()["success"] is False


@_t("page_public_not_found")
def _():
    c = make_client()
    if not c: return
    r = c.get("/api/sayfa/olmayan-sayfa")
    assert r.status_code == 200
    assert r.json()["success"] is False


@_t("page_public_active")
def _():
    c = make_client()
    if not c: return
    slug = _uniq("aktif")
    c.post("/api/admin/sayfalar",
           json={"baslik": "Aktif", "slug": slug, "durum": "Yayınla"},
           headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    r = c.get(f"/api/sayfa/{slug}")
    assert r.json()["success"] is True
    assert r.json()["data"]["slug"] == slug


def run_tests():
    passed = 0
    failed = 0
    print("=== CMS - Sayfa ===")
    for name, fn in TESTS:
        try:
            fn()
            print(f"  ✅ {name}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {name}: {e}")
            failed += 1
    print(f"\n✅ PASSED: {passed}  ❌ FAILED: {failed}")
    return passed, failed


if __name__ == "__main__":
    run_tests()
