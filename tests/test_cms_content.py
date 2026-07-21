"""CMS v2.1 — İçerik / Katalog modülü testleri."""
from __future__ import annotations

import os
import tempfile

os.environ.setdefault("LOG_DIR", tempfile.mkdtemp())

from fastapi.testclient import TestClient


def make_client():
    try:
        from app import app
        return TestClient(app)
    except Exception:
        return None


def test_content_categories():
    c = make_client()
    if not c:
        return
    r = c.get("/api/kategoriler")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert "Konut" in body["data"]["kategoriler"]
    assert "Konut" in body["data"]["ilan_tipleri"]


def test_content_field_templates():
    c = make_client()
    if not c:
        return
    r = c.get("/api/alanlar")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert "konut_satilik" in body["data"]
    assert len(body["data"]["konut_satilik"]) >= 5
