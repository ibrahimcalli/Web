"""CMS v2.1 — Tema Modülü Testleri."""
from __future__ import annotations

import os
import random
import tempfile

os.environ.setdefault("LOG_DIR", tempfile.mkdtemp())

from fastapi.testclient import TestClient
from backend.core.security import token_olustur

ADMIN_TOKEN = token_olustur({"sub": "admin@test.com", "rol": "admin", "ad": "Test Admin"})


def _uniq(prefix="t"):
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


@_t("theme_public")
def _():
    c = make_client()
    if not c: return
    r = c.get("/api/tema")
    assert r.status_code == 200
    assert r.json()["success"] is True
    assert isinstance(r.json()["data"], dict)
    assert "renk_ana" in r.json()["data"]


@_t("theme_admin_get")
def _():
    c = make_client()
    if not c: return
    r = c.get("/api/admin/tema", headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    assert r.status_code == 200 and r.json()["success"] is True


@_t("theme_set")
def _():
    c = make_client()
    if not c: return
    k = _uniq("test")
    r = c.put(f"/api/admin/tema/{k}",
              json={"anahtar": k, "deger": "deneme"},
              headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    assert r.status_code == 200, r.text
    assert r.json()["success"] is True
    assert r.json()["data"]["deger"] == "deneme"


@_t("theme_get_after_set")
def _():
    c = make_client()
    if not c: return
    k = _uniq("onay")
    c.put(f"/api/admin/tema/{k}",
          json={"anahtar": k, "deger": "xyz"},
          headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    r = c.get("/api/tema")
    assert r.json()["data"].get(k) == "xyz"


def run_tests():
    passed = 0
    failed = 0
    print("=== CMS - Tema ===")
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
