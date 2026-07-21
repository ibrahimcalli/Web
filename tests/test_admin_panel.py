"""Yönetim paneli DOM/test entegrasyon testleri."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
INDEX_HTML = ROOT / "static" / "index.html"
APP_JS = ROOT / "src" / "ui" / "app.js"


def test_admin_sidebar_contains_new_modules():
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert "adminSayfa('wizard')" in html
    assert "adminSayfa('marketplace')" in html
    assert "adminSayfa('saas')" in html
    assert "adminSayfa('sistem-test')" in html
    assert "Site Sihirbazı" in html
    assert "Marketplace" in html
    assert "SaaS" in html


def test_admin_js_exports_new_functions():
    js = APP_JS.read_text(encoding="utf-8")
    assert "window.adminWizard" in js
    assert "window.adminMarketplace" in js
    assert "window.adminSaaS" in js
    assert "window.adminMenuler" in js
    assert "window.adminSayfalar" in js
    assert "window.adminWidgetler" in js
    assert "window.adminTema" in js
    assert "window.adminSablonlar" in js
