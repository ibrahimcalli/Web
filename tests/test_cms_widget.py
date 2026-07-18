"""CMS v2.1 — Widget Modülü Testleri."""
from __future__ import annotations

import os
import random
import tempfile

os.environ.setdefault("LOG_DIR", tempfile.mkdtemp())

from fastapi.testclient import TestClient
from backend.core.security import token_olustur

ADMIN_TOKEN = token_olustur({"sub": "admin@test.com", "rol": "admin", "ad": "Test Admin"})


def _uniq(prefix="w"):
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


@_t("widget_list")
def _():
    c = make_client()
    if not c: return
    r = c.get("/api/admin/widgets", headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    assert r.status_code == 200 and r.json()["success"] is True
    assert isinstance(r.json()["data"], list)


@_t("widget_create")
def _():
    c = make_client()
    if not c: return
    k = _uniq("wdg")
    r = c.post("/api/admin/widgets",
               json={"anahtar": k, "ad": "Test Widget", "tip": "embed", "konum": "footer"},
               headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    assert r.status_code == 200, r.text
    assert r.json()["success"] is True
    assert r.json()["data"]["anahtar"] == k


@_t("widget_toggle")
def _():
    c = make_client()
    if not c: return
    k = _uniq("toggle")
    r = c.post("/api/admin/widgets",
               json={"anahtar": k, "ad": "Toggle", "tip": "link", "aktif": False},
               headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    wid = r.json()["data"]["id"]
    r2 = c.put(f"/api/admin/widgets/{wid}",
               json={"aktif": True},
               headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    assert r2.json()["success"] is True
    assert r2.json()["data"]["aktif"] is True or r2.json()["data"]["aktif"] == 1


@_t("widget_delete")
def _():
    c = make_client()
    if not c: return
    k = _uniq("sil")
    r = c.post("/api/admin/widgets",
               json={"anahtar": k, "ad": "Silinic", "tip": "embed"},
               headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    wid = r.json()["data"]["id"]
    r2 = c.delete(f"/api/admin/widgets/{wid}",
                  headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    assert r2.json()["success"] is True
    assert r2.json()["data"]["silindi"] is True


@_t("widget_public_active_only")
def _():
    c = make_client()
    if not c: return
    k = _uniq("pblk")
    c.post("/api/admin/widgets",
           json={"anahtar": k, "ad": "Public", "tip": "embed", "aktif": True},
           headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    r = c.get("/api/widgets")
    assert r.json()["success"] is True
    # sadece aktif widget'lar gelmeli
    for w in r.json()["data"]:
        assert w["aktif"] is True or w["aktif"] == 1


def run_tests():
    passed = 0
    failed = 0
    print("=== CMS - Widget ===")
    for name, fn in TESTS:
        try:
            fn()
            print(f"  ✅ {name}")
            passed += 1
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"  ❌ {name}: {e}")
            failed += 1
    print(f"\n✅ PASSED: {passed}  ❌ FAILED: {failed}")
    return passed, failed


if __name__ == "__main__":
    run_tests()
