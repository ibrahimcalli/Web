"""
admin-sistem.js — data-action / data-copy delegated click handler E2E testi.

onclick="fnAdi(...)" ve onclick="navigator.clipboard.writeText(...)" gibi
attribute'lardan data-action / data-copy-text / data-copy-target + tek bir
delegated addEventListener'a geçişin (CSP uyumu için) gerçek tarayıcıda
doğru çalıştığını kanıtlar. İş mantığı fonksiyonları (sistemLogYukle vb.)
zaten backend testlerinde (tests/test_cms_system.py) kapsanıyor — burada
sadece YENİ delegation mekanizmasının kendisi test ediliyor.
"""
from pathlib import Path

import pytest

playwright_sync_api = pytest.importorskip("playwright.sync_api")
sync_playwright = playwright_sync_api.sync_playwright

FIXTURE_URL_PATH = "/static/_e2e_fixtures/admin_sistem_actions.html"
FIXTURE_SRC = Path(__file__).parent / "fixtures" / "admin_sistem_actions.html"
FIXTURE_DEST_DIR = Path(__file__).resolve().parent.parent.parent / "static" / "_e2e_fixtures"


@pytest.fixture(scope="module", autouse=True)
def _fixture_dosyasini_yerlestir():
    FIXTURE_DEST_DIR.mkdir(parents=True, exist_ok=True)
    dest = FIXTURE_DEST_DIR / "admin_sistem_actions.html"
    dest.write_text(FIXTURE_SRC.read_text(encoding="utf-8"), encoding="utf-8")
    yield
    dest.unlink(missing_ok=True)
    try:
        FIXTURE_DEST_DIR.rmdir()
    except OSError:
        pass


def _sayfa_ac(browser, live_server):
    context = browser.new_context()
    context.grant_permissions(["clipboard-read", "clipboard-write"])
    page = context.new_page()
    hatalar = []
    page.on("pageerror", lambda exc: hatalar.append(str(exc)))
    page.goto(f"{live_server}{FIXTURE_URL_PATH}")
    page.wait_for_selector('[data-action="sistemLogYukle"]', timeout=5000)
    return context, page, hatalar


def test_data_action_argumanli_cagri(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _sayfa_ac(browser, live_server)

        page.click('[data-action="sistemLogYukle"]')
        page.wait_for_timeout(200)

        cagrilar = page.evaluate("window.__cagrilar")
        assert cagrilar == [{"fn": "sistemLogYukle", "args": ["error"]}], \
            f"Yanlış çağrı: {cagrilar}"
        assert not hatalar, f"JS hatası: {hatalar}"
        context.close()
        browser.close()


def test_data_action_argumansiz_cagri(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _sayfa_ac(browser, live_server)

        page.click('[data-action="sistemAiTanilamaIndir"]')
        page.wait_for_timeout(200)

        cagrilar = page.evaluate("window.__cagrilar")
        assert cagrilar == [{"fn": "sistemAiTanilamaIndir", "args": []}], \
            f"Yanlış çağrı: {cagrilar}"
        assert not hatalar, f"JS hatası: {hatalar}"
        context.close()
        browser.close()


def test_data_copy_text_statik_metin_kopyalar(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _sayfa_ac(browser, live_server)

        btn = page.locator('[data-copy-text]')
        assert btn.text_content() == "📋"

        btn.click()
        page.wait_for_timeout(100)
        assert btn.text_content() == "✓", "Tıklama sonrası geri bildirim metni görünmedi"

        panoya_kopyalanan = page.evaluate("navigator.clipboard.readText()")
        assert panoya_kopyalanan == "git pull && echo test", \
            f"Panoya yanlış metin kopyalandı: {panoya_kopyalanan!r}"

        page.wait_for_timeout(400)  # data-copy-delay=300 sonrası eski metne dönmeli
        assert btn.text_content() == "📋", "Geri bildirim süresi sonunda eski metne dönmedi"

        assert not hatalar, f"JS hatası: {hatalar}"
        context.close()
        browser.close()


def test_data_copy_target_element_icerigini_kopyalar(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _sayfa_ac(browser, live_server)

        page.click('[data-copy-target="ai-json"]')
        page.wait_for_timeout(100)

        panoya_kopyalanan = page.evaluate("navigator.clipboard.readText()")
        assert panoya_kopyalanan == '{"ornek": "veri"}', \
            f"Panoya yanlış içerik kopyalandı: {panoya_kopyalanan!r}"

        assert not hatalar, f"JS hatası: {hatalar}"
        context.close()
        browser.close()
