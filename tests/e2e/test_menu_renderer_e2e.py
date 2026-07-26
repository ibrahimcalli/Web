"""
menu-renderer.js — sayfaGit link'leri E2E testi.

onclick="event.preventDefault();sayfaGit(...)" attribute'undan
data-sayfa-git / data-sayfa-params + delegated addEventListener'a
geçişin (CSP uyumu için) gerçek tarayıcıda hâlâ doğru çalıştığını kanıtlar:
  1. <a> tıklanınca sayfa yönlendirmesi (hash navigasyonu) ENGELLENIYOR (preventDefault)
  2. sayfaGit doğru parametrelerle çağrılıyor (string slug VE sayısal id)
  3. <span> (href'siz) elemanlarda da çalışıyor
"""
from pathlib import Path

import pytest

playwright_sync_api = pytest.importorskip("playwright.sync_api")
sync_playwright = playwright_sync_api.sync_playwright

FIXTURE_URL_PATH = "/static/_e2e_fixtures/menu_links.html"
FIXTURE_SRC = Path(__file__).parent / "fixtures" / "menu_links.html"
FIXTURE_DEST_DIR = Path(__file__).resolve().parent.parent.parent / "static" / "_e2e_fixtures"


@pytest.fixture(scope="module", autouse=True)
def _fixture_dosyasini_yerlestir():
    FIXTURE_DEST_DIR.mkdir(parents=True, exist_ok=True)
    dest = FIXTURE_DEST_DIR / "menu_links.html"
    dest.write_text(FIXTURE_SRC.read_text(encoding="utf-8"), encoding="utf-8")
    yield
    dest.unlink(missing_ok=True)
    try:
        FIXTURE_DEST_DIR.rmdir()
    except OSError:
        pass


def test_sayfa_link_preventDefault_ve_dogru_parametre(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        hatalar = []
        page.on("pageerror", lambda exc: hatalar.append(str(exc)))

        page.goto(f"{live_server}{FIXTURE_URL_PATH}")
        page.wait_for_selector('[data-sayfa-git="sayfa"]', timeout=5000)

        url_once = page.url

        page.click('[data-sayfa-git="sayfa"]')
        page.wait_for_timeout(200)

        # preventDefault çalıştı mı? (URL hash'e gitmemeli)
        assert page.url == url_once, "Link tıklanınca sayfa yönlendi (preventDefault çalışmadı)"

        cagrilar = page.evaluate("window.__sayfaGitCagrilari")
        assert cagrilar == [{"sayfa": "sayfa", "params": {"slug": "hakkimizda"}}], \
            f"sayfaGit yanlış çağrıldı: {cagrilar}"

        assert not hatalar, f"Sayfada JS hatası oluştu: {hatalar}"
        browser.close()


def test_anasayfa_span_calisir(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(f"{live_server}{FIXTURE_URL_PATH}")
        page.wait_for_selector('[data-sayfa-git="anasayfa"]', timeout=5000)

        page.click('[data-sayfa-git="anasayfa"]')
        page.wait_for_timeout(200)

        cagrilar = page.evaluate("window.__sayfaGitCagrilari")
        anasayfa_cagri = next((c for c in cagrilar if c["sayfa"] == "anasayfa"), None)
        assert anasayfa_cagri is not None, f"anasayfa çağrısı bulunamadı: {cagrilar}"
        # params gönderilmemeli (tek argümanlı sayfaGit('anasayfa') çağrısı) —
        # Playwright JS'teki undefined'ı None olarak taşır, bu doğru davranış
        assert anasayfa_cagri["params"] is None, \
            f"anasayfa çağrısında params olmamalıydı: {anasayfa_cagri}"

        browser.close()


def test_sayisal_id_parametresi_dogru_tipte_gelir(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(f"{live_server}{FIXTURE_URL_PATH}")
        page.wait_for_selector('[data-sayfa-git="detay"]', timeout=5000)

        page.click('[data-sayfa-git="detay"]')
        page.wait_for_timeout(200)

        cagrilar = page.evaluate("window.__sayfaGitCagrilari")
        detay_cagri = next((c for c in cagrilar if c["sayfa"] == "detay"), None)
        assert detay_cagri is not None, f"detay çağrısı bulunamadı: {cagrilar}"
        assert detay_cagri["params"]["id"] == 42, \
            f"id sayısal (42) olmalıydı, geldi: {detay_cagri['params']['id']!r}"

        browser.close()
