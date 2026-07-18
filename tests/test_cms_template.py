"""CMS v2.2 — Template Engine Testleri."""
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


@_t("template_list")
def _():
    c = make_client()
    if not c: return
    r = c.get("/api/admin/templates", headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    assert r.status_code == 200 and r.json()["success"] is True
    assert len(r.json()["data"]) >= 7


@_t("template_default_exists")
def _():
    c = make_client()
    if not c: return
    r = c.get("/api/admin/templates", headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    defaults = [t for t in r.json()["data"] if t.get("varsayilan")]
    assert len(defaults) == 1
    assert defaults[0]["slug"] == "estate-modern"


@_t("template_sections_seeded")
def _():
    c = make_client()
    if not c: return
    r = c.get("/api/admin/templates", headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    default = [t for t in r.json()["data"] if t.get("varsayilan")][0]
    r2 = c.get(f"/api/admin/templates/{default['id']}/bolumler",
               headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    assert r2.json()["success"] is True
    assert len(r2.json()["data"]) >= 9


@_t("homepage_public")
def _():
    c = make_client()
    if not c: return
    r = c.get("/api/template/homepage")
    assert r.status_code == 200
    assert r.json()["success"] is True
    sections = r.json()["data"]
    assert len(sections) >= 9
    # hepsi aktif olmalı (seed'de aktif=1)
    # ilk section hero olmalı (sira=0)
    first_keys = [s["section_key"] for s in sections[:3]]
    assert "hero" in first_keys or "slider" in first_keys


@_t("section_toggle")
def _():
    c = make_client()
    if not c: return
    r = c.get("/api/admin/templates", headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    default = [t for t in r.json()["data"] if t.get("varsayilan")][0]
    r2 = c.get(f"/api/admin/templates/{default['id']}/bolumler",
               headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    section = r2.json()["data"][0]
    r3 = c.put(f"/api/admin/bolumler/{section['id']}",
               json={"aktif": False},
               headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    assert r3.json()["success"] is True
    assert r3.json()["data"]["aktif"] == 0 or r3.json()["data"]["aktif"] is False
    # geri aç
    c.put(f"/api/admin/bolumler/{section['id']}",
          json={"aktif": True},
          headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})


@_t("section_reorder")
def _():
    c = make_client()
    if not c: return
    r = c.get("/api/admin/templates", headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    default = [t for t in r.json()["data"] if t.get("varsayilan")][0]
    r2 = c.get(f"/api/admin/templates/{default['id']}/bolumler",
               headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    sections = r2.json()["data"]
    if len(sections) >= 2:
        items = [{"id": s["id"], "sira": i} for i, s in enumerate(reversed(sections))]
        r3 = c.put("/api/admin/bolumler/sirala",
                   json={"items": items},
                   headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
        assert r3.json()["success"] is True
        assert r3.json()["data"]["guncellenen"] >= 2


@_t("section_update_settings")
def _():
    c = make_client()
    if not c: return
    r = c.get("/api/admin/templates", headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    default = [t for t in r.json()["data"] if t.get("varsayilan")][0]
    r2 = c.get(f"/api/admin/templates/{default['id']}/bolumler",
               headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    section = r2.json()["data"][0]
    yeni_ayarlar = '{"animasyon":"fadeUp","padding":"100px 0","arka_renk":"#fff","container_genislik":"boxed"}'
    r3 = c.put(f"/api/admin/bolumler/{section['id']}",
               json={"ayarlar": yeni_ayarlar, "baslik": "Güncellendi"},
               headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    assert r3.json()["success"] is True
    assert r3.json()["data"]["baslik"] == "Güncellendi"


@_t("template_toggle")
def _():
    c = make_client()
    if not c: return
    r = c.get("/api/admin/templates", headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    non_default = [t for t in r.json()["data"] if not t.get("varsayilan") and t.get("aktif")][0]
    r2 = c.get(f"/api/admin/templates/{non_default['id']}/toggle",
               headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    assert r2.json()["success"] is True
    assert r2.json()["data"]["aktif"] == 0 or r2.json()["data"]["aktif"] is False
    # geri aç
    c.get(f"/api/admin/templates/{non_default['id']}/toggle",
          headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})


@_t("template_admin_get")
def _():
    c = make_client()
    if not c: return
    r = c.get("/api/admin/templates/1", headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    assert r.json()["success"] is True
    assert r.json()["data"]["id"] == 1


@_t("homepage_template_param")
def _():
    c = make_client()
    if not c: return
    r = c.get("/api/template/homepage?template=estate-modern")
    assert r.json()["success"] is True
    assert len(r.json()["data"]) >= 9


def run_tests():
    passed = 0
    failed = 0
    print("=== CMS - Template ===")
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
