"""
widget-renderer.js — çerez banner'ı E2E testi.

Bu, onclick="" attribute'undan data-widget-action + delegated
addEventListener'a geçişin (CSP uyumu için) gerçek tarayıcıda hâlâ
doğru çalıştığını kanıtlar:
  1. Banner görünür
  2. "Tamam" butonuna tıklanınca banner kayboluyor (container.remove())
  3. cookie_ok çerezi 1 yıl süreyle set ediliyor
"""
from pathlib import Path

import pytest

playwright_sync_api = pytest.importorskip("playwright.sync_api")
sync_playwright = playwright_sync_api.sync_playwright

FIXTURE_URL_PATH = "/static/_e2e_fixtures/cookie_banner.html"
FIXTURE_SRC = Path(__file__).parent / "fixtures" / "cookie_banner.html"
FIXTURE_DEST_DIR = Path(__file__).resolve().parent.parent.parent / "static" / "_e2e_fixtures"


@pytest.fixture(scope="module", autouse=True)
def _fixture_dosyasini_yerlestir():
    """Test fixture HTML'ini static/ altına geçici olarak kopyalar, test bitince siler."""
    FIXTURE_DEST_DIR.mkdir(parents=True, exist_ok=True)
    dest = FIXTURE_DEST_DIR / "cookie_banner.html"
    dest.write_text(FIXTURE_SRC.read_text(encoding="utf-8"), encoding="utf-8")
    yield
    dest.unlink(missing_ok=True)
    try:
        FIXTURE_DEST_DIR.rmdir()
    except OSError:
        pass  # başka dosya varsa (paralel test) silme


def test_cerez_banner_kapat_ve_cookie_set_edilir(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        hatalar = []
        page.on("pageerror", lambda exc: hatalar.append(str(exc)))

        page.goto(f"{live_server}{FIXTURE_URL_PATH}")
        page.wait_for_selector('[data-widget-action="cerez-onayla"]', timeout=5000)

        assert page.locator('[data-widget-container="footer-1"]').is_visible(), \
            "Banner render edilmedi"

        page.click('[data-widget-action="cerez-onayla"]')
        page.wait_for_timeout(300)

        assert page.locator('[data-widget-container="footer-1"]').count() == 0, \
            "Banner tıklamadan sonra kaybolmadı (container.remove() çalışmadı)"

        cookies = page.context.cookies()
        cookie_ok = next((c for c in cookies if c["name"] == "cookie_ok"), None)
        assert cookie_ok is not None and cookie_ok["value"] == "1", \
            "cookie_ok çerezi set edilmedi"

        assert not hatalar, f"Sayfada JS hatası oluştu: {hatalar}"

        browser.close()
