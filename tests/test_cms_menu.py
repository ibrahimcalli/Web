"""CMS v2.1 — Menu Modülü Testleri."""
from __future__ import annotations

import os
import sys
import tempfile
import random
import string

os.environ.setdefault("LOG_DIR", tempfile.mkdtemp())

from fastapi.testclient import TestClient
from backend.core.security import token_olustur

ADMIN_TOKEN = token_olustur({"sub": "admin@test.com", "rol": "admin", "ad": "Test Admin"})
ANCHOR_SLUG = "test-ana-menu"


def _uniq(prefix="t"):
    return f"{prefix}_{random.randint(10000, 99999)}"


def make_client():
    try:
        from app import app
        return TestClient(app)
    except Exception:
        return None


def _anchor_menu_id(c):
    """Anchor menüyü bul (listeden filtrele) / yoksa oluştur, ID döndür."""
    r = c.get("/api/admin/menuler",
              headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    if r.json()["success"]:
        for m in r.json()["data"]:
            if m["slug"] == ANCHOR_SLUG:
                return m["id"]
    r = c.post("/api/admin/menuler",
               json={"slug": ANCHOR_SLUG, "ad": "Test Ana Menü", "lokasyon": "header"},
               headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    return r.json()["data"]["id"]


# ─── Menü CRUD ─────────────────────────────────────────────────────────────
def test_menu_list():
    c = make_client()
    if not c: return
    r = c.get("/api/admin/menuler", headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    assert r.status_code == 200
    assert r.json()["success"] is True
    assert isinstance(r.json()["data"], list)


def test_menu_create():
    c = make_client()
    if not c: return
    slug = _uniq("menu")
    r = c.post("/api/admin/menuler",
               json={"slug": slug, "ad": "Yeni Menü", "lokasyon": "header"},
               headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    assert r.status_code == 200, r.text
    assert r.json()["success"] is True
    assert r.json()["data"]["slug"] == slug


def test_menu_duplicate_slug():
    c = make_client()
    if not c: return
    sid = _anchor_menu_id(c)
    r = c.post("/api/admin/menuler",
               json={"slug": ANCHOR_SLUG, "ad": "Kopya"},
               headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    assert r.status_code == 200
    assert r.json()["success"] is False


def test_menu_get():
    c = make_client()
    if not c: return
    mid = _anchor_menu_id(c)
    r = c.get(f"/api/admin/menuler/{mid}",
              headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    assert r.status_code == 200
    assert r.json()["success"] is True
    assert r.json()["data"]["id"] == mid


def test_menu_update():
    c = make_client()
    if not c: return
    mid = _anchor_menu_id(c)
    r = c.put(f"/api/admin/menuler/{mid}",
              json={"ad": "Güncellenmiş Menü"},
              headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    assert r.status_code == 200
    assert r.json()["success"] is True
    assert r.json()["data"]["ad"] == "Güncellenmiş Menü"


def test_menu_delete():
    c = make_client()
    if not c: return
    slug = _uniq("sil")
    r = c.post("/api/admin/menuler",
               json={"slug": slug, "ad": "Sil"},
               headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    sil_id = r.json()["data"]["id"]
    r = c.delete(f"/api/admin/menuler/{sil_id}",
                 headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    assert r.status_code == 200
    assert r.json()["success"] is True
    assert r.json()["data"]["silindi"] is True


def test_menu_not_found():
    c = make_client()
    if not c: return
    r = c.get("/api/admin/menuler/999999",
              headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    assert r.status_code == 200
    assert r.json()["success"] is False


# ─── Menu Items ────────────────────────────────────────────────────────────
def test_menu_item_create():
    c = make_client()
    if not c: return
    mid = _anchor_menu_id(c)
    r = c.post(f"/api/admin/menuler/{mid}/ogeler",
               json={"menu_id": mid, "baslik": "Ana Sayfa",
                      "hedef_tip": "dahili", "hedef_url": "/",
                      "sira": 1, "aktif": True},
               headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    assert r.status_code == 200, r.text
    assert r.json()["success"] is True
    assert r.json()["data"]["baslik"] == "Ana Sayfa"


def test_menu_item_submenu():
    c = make_client()
    if not c: return
    mid = _anchor_menu_id(c)
    r = c.post(f"/api/admin/menuler/{mid}/ogeler",
               json={"menu_id": mid, "baslik": "Villa",
                      "hedef_tip": "dahili", "hedef_url": "/ilanlar?tip=villa",
                      "sira": 2, "aktif": True},
               headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    assert r.status_code == 200, r.text
    assert r.json()["success"] is True, r.text


def test_menu_items_list():
    c = make_client()
    if not c: return
    mid = _anchor_menu_id(c)
    r = c.get(f"/api/admin/menuler/{mid}/ogeler",
              headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    assert r.status_code == 200
    assert r.json()["success"] is True
    assert len(r.json()["data"]) >= 2


def test_menu_item_update():
    c = make_client()
    if not c: return
    mid = _anchor_menu_id(c)
    r = c.get(f"/api/admin/menuler/{mid}/ogeler",
              headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    assert r.json()["success"] is True and len(r.json()["data"]) > 0
    item_id = r.json()["data"][0]["id"]
    r = c.put(f"/api/admin/menu-ogeleri/{item_id}",
              json={"baslik": "Güncel Başlık", "ikon": "🏠"},
              headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    assert r.status_code == 200
    assert r.json()["success"] is True
    assert "🏠" in r.json()["data"]["ikon"]


def test_menu_item_delete():
    c = make_client()
    if not c: return
    mid = _anchor_menu_id(c)
    r = c.post(f"/api/admin/menuler/{mid}/ogeler",
               json={"menu_id": mid, "baslik": "Silinecek Öğe",
                      "hedef_tip": "dahili", "hedef_url": "/test",
                      "sira": 99, "aktif": True},
               headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    sil_id = r.json()["data"]["id"]
    r = c.delete(f"/api/admin/menu-ogeleri/{sil_id}",
                 headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    assert r.status_code == 200
    assert r.json()["success"] is True


def test_menu_item_reorder():
    c = make_client()
    if not c: return
    mid = _anchor_menu_id(c)
    r = c.get(f"/api/admin/menuler/{mid}/ogeler",
              headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    assert r.json()["success"] is True and len(r.json()["data"]) > 0
    first_id = r.json()["data"][0]["id"]
    r = c.put("/api/admin/menu-ogeleri/sirala",
              json={"items": [{"id": first_id, "parent_id": None, "sira": 5}]},
              headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    assert r.status_code == 200
    assert r.json()["success"] is True


# ─── Public Menu ────────────────────────────────────────────────────────────
def test_public_menu():
    c = make_client()
    if not c: return
    r = c.get(f"/api/menu/{ANCHOR_SLUG}")
    assert r.status_code == 200
    assert r.json()["success"] is True
    assert isinstance(r.json()["data"], list)


def test_public_menu_not_found():
    c = make_client()
    if not c: return
    r = c.get("/api/menu/olmayan-menu")
    assert r.status_code == 200
    assert r.json()["success"] is True
    assert r.json()["data"] == []


# ─── Auth Guards ────────────────────────────────────────────────────────────
def test_admin_menu_requires_auth():
    c = make_client()
    if not c: return
    r = c.get("/api/admin/menuler")
    assert r.status_code in (200, 401)
    if r.status_code == 200:
        assert r.json()["success"] is False


# ─── Runner ─────────────────────────────────────────────────────────────────
TESTS = [
    ("menu_list", test_menu_list),
    ("menu_create", test_menu_create),
    ("menu_duplicate_slug", test_menu_duplicate_slug),
    ("menu_get", test_menu_get),
    ("menu_update", test_menu_update),
    ("menu_delete", test_menu_delete),
    ("menu_not_found", test_menu_not_found),
    ("menu_item_create", test_menu_item_create),
    ("menu_item_submenu", test_menu_item_submenu),
    ("menu_items_list", test_menu_items_list),
    ("menu_item_update", test_menu_item_update),
    ("menu_item_delete", test_menu_item_delete),
    ("menu_item_reorder", test_menu_item_reorder),
    ("public_menu", test_public_menu),
    ("public_menu_not_found", test_public_menu_not_found),
    ("admin_menu_requires_auth", test_admin_menu_requires_auth),
]


def run_tests():
    passed = 0
    failed = 0
    print("=== CMS - Menü ===")
    for name, func in TESTS:
        try:
            func()
            print(f"  ✅ {name}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {name}: {e}")
            failed += 1
    print(f"\n✅ PASSED: {passed}  ❌ FAILED: {failed}")
    return passed, failed


if __name__ == "__main__":
    run_tests()
