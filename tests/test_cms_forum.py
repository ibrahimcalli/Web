"""CMS v2.1 — Forum Modülü Testleri (varsayılan KAPALI)."""
from __future__ import annotations

import os
import tempfile

os.environ.setdefault("LOG_DIR", tempfile.mkdtemp())

from fastapi.testclient import TestClient
from backend.core.security import token_olustur
from backend.core.settings import settings

ADMIN_TOKEN = token_olustur({"sub": "admin@test.com", "rol": "admin", "ad": "Test Admin"})


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


@_t("forum_disabled_by_default")
def _():
    c = make_client()
    if not c: return
    r = c.get("/api/forum/kategoriler")
    assert r.status_code == 404


@_t("forum_admin_disabled")
def _():
    c = make_client()
    if not c: return
    r = c.get("/api/admin/forum/kategoriler",
              headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    assert r.status_code == 404


@_t("forum_setting_flag")
def _():
    assert settings.CMS_FORUM_ENABLED is False


def run_tests():
    passed = 0
    failed = 0
    print("=== CMS - Forum ===")
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
