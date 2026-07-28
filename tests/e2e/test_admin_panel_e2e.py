"""
Admin Panel — CSP uyumu için onclick="" → data-action/data-* delegated
click listener geçişinin E2E (gerçek tarayıcı) test paketi.

TÜM yeni E2E testler BUNDAN SONRA BU DOSYAYA eklenir (ayrı dosya açılmaz),
Zeki'nin tercihiyle: tek dosyada tüm sonuçları bir arada görüp, sorun
çıkarsa ilgili bölümü doğrudan işaret edebilmek için.

Yapı: Her bölüm dönüştürülen JS dosyasına/gruba karşılık gelir. Her
bölümün kendi STUB_JS / INJECT_BUTTONS_JS / yardımcı fonksiyonları vardır
(isim çakışmasını önlemek için bölüm öneki taşırlar). Test fonksiyon
adları da bölüm önekiyle başlar (örn. test_appbanner_..., test_menu_...).

Çalıştırma:
    python3 -m pytest tests/e2e/test_admin_panel_e2e.py -v
"""
from pathlib import Path

import pytest

playwright_sync_api = pytest.importorskip("playwright.sync_api")
sync_playwright = playwright_sync_api.sync_playwright


def _sw_devre_disi_birak_init_script():
    """Service worker'ı devre dışı bırakır — aktifse sayfa PWA güncellemesiyle
    yeniden yükleyip app.js'i 2. kez çalıştırabiliyor (sadece test izolasyonu
    için; üretimde/normal kullanıcıda bu durum oluşmaz)."""
    return """
        Object.defineProperty(navigator, 'serviceWorker', {
            value: { register: () => Promise.resolve({ addEventListener(){}, update: () => Promise.resolve() }),
                     addEventListener(){}, getRegistrations: () => Promise.resolve([]) },
            configurable: true
        });
    """


# ═══════════════════════════════════════════════════════════════════════
# BÖLÜM 1 — widget-renderer.js (çerez banner'ı)
# ═══════════════════════════════════════════════════════════════════════
WIDGET_FIXTURE_URL_PATH = "/static/_e2e_fixtures/cookie_banner.html"
WIDGET_FIXTURE_SRC = Path(__file__).parent / "fixtures" / "cookie_banner.html"
WIDGET_FIXTURE_DEST_DIR = Path(__file__).resolve().parent.parent.parent / "static" / "_e2e_fixtures"


@pytest.fixture(scope="module", autouse=True)
def _widget_fixture_yerlestir():
    """cookie_banner.html'i static/ altına geçici kopyalar, modül bitince siler."""
    WIDGET_FIXTURE_DEST_DIR.mkdir(parents=True, exist_ok=True)
    dest = WIDGET_FIXTURE_DEST_DIR / "cookie_banner.html"
    dest.write_text(WIDGET_FIXTURE_SRC.read_text(encoding="utf-8"), encoding="utf-8")
    yield
    dest.unlink(missing_ok=True)
    try:
        WIDGET_FIXTURE_DEST_DIR.rmdir()
    except OSError:
        pass


def test_widget_cerez_banner_kapat_ve_cookie_set_edilir(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        hatalar = []
        page.on("pageerror", lambda exc: hatalar.append(str(exc)))

        page.goto(f"{live_server}{WIDGET_FIXTURE_URL_PATH}")
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


# ═══════════════════════════════════════════════════════════════════════
# BÖLÜM 2 — menu-renderer.js (sayfaGit link'leri)
# ═══════════════════════════════════════════════════════════════════════
MENU_FIXTURE_URL_PATH = "/static/_e2e_fixtures/menu_links.html"
MENU_FIXTURE_SRC = Path(__file__).parent / "fixtures" / "menu_links.html"
MENU_FIXTURE_DEST_DIR = Path(__file__).resolve().parent.parent.parent / "static" / "_e2e_fixtures"


@pytest.fixture(scope="module", autouse=True)
def _menu_fixture_yerlestir():
    MENU_FIXTURE_DEST_DIR.mkdir(parents=True, exist_ok=True)
    dest = MENU_FIXTURE_DEST_DIR / "menu_links.html"
    dest.write_text(MENU_FIXTURE_SRC.read_text(encoding="utf-8"), encoding="utf-8")
    yield
    dest.unlink(missing_ok=True)
    try:
        MENU_FIXTURE_DEST_DIR.rmdir()
    except OSError:
        pass


def test_menu_sayfa_link_preventDefault_ve_dogru_parametre(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        hatalar = []
        page.on("pageerror", lambda exc: hatalar.append(str(exc)))

        page.goto(f"{live_server}{MENU_FIXTURE_URL_PATH}")
        page.wait_for_selector('[data-sayfa-git="sayfa"]', timeout=5000)

        url_once = page.url
        page.click('[data-sayfa-git="sayfa"]')
        page.wait_for_timeout(200)

        assert page.url == url_once, "Link tıklanınca sayfa yönlendi (preventDefault çalışmadı)"

        cagrilar = page.evaluate("window.__sayfaGitCagrilari")
        assert cagrilar == [{"sayfa": "sayfa", "params": {"slug": "hakkimizda"}}], \
            f"sayfaGit yanlış çağrıldı: {cagrilar}"
        assert not hatalar, f"Sayfada JS hatası oluştu: {hatalar}"
        browser.close()


def test_menu_anasayfa_span_calisir(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(f"{live_server}{MENU_FIXTURE_URL_PATH}")
        page.wait_for_selector('[data-sayfa-git="anasayfa"]', timeout=5000)

        page.click('[data-sayfa-git="anasayfa"]')
        page.wait_for_timeout(200)

        cagrilar = page.evaluate("window.__sayfaGitCagrilari")
        anasayfa_cagri = next((c for c in cagrilar if c["sayfa"] == "anasayfa"), None)
        assert anasayfa_cagri is not None, f"anasayfa çağrısı bulunamadı: {cagrilar}"
        assert anasayfa_cagri["params"] is None, \
            f"anasayfa çağrısında params olmamalıydı: {anasayfa_cagri}"
        browser.close()


def test_menu_sayisal_id_parametresi_dogru_tipte_gelir(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(f"{live_server}{MENU_FIXTURE_URL_PATH}")
        page.wait_for_selector('[data-sayfa-git="detay"]', timeout=5000)

        page.click('[data-sayfa-git="detay"]')
        page.wait_for_timeout(200)

        cagrilar = page.evaluate("window.__sayfaGitCagrilari")
        detay_cagri = next((c for c in cagrilar if c["sayfa"] == "detay"), None)
        assert detay_cagri is not None, f"detay çağrısı bulunamadı: {cagrilar}"
        assert detay_cagri["params"]["id"] == 42, \
            f"id sayısal (42) olmalıydı, geldi: {detay_cagri['params']['id']!r}"
        browser.close()


# ═══════════════════════════════════════════════════════════════════════
# BÖLÜM 3 — admin-sistem.js (data-action / data-copy)
# ═══════════════════════════════════════════════════════════════════════
ADMIN_STUB_JS = """
() => {
  window.__cagrilar = [];
  window.sistemLogYukle = (...args) => window.__cagrilar.push({ fn: 'sistemLogYukle', args });
  window.sistemAiTanilamaIndir = (...args) => window.__cagrilar.push({ fn: 'sistemAiTanilamaIndir', args });
}
"""

ADMIN_INJECT_BUTTONS_JS = """
() => {
  const div = document.createElement('div');
  div.id = 'test-admin-sistem-butonlari';
  div.innerHTML = `
    <button data-action="sistemLogYukle" data-action-args="[&quot;error&quot;]">error.log</button>
    <button data-action="sistemAiTanilamaIndir">İndir</button>
    <button data-copy-text="git pull &amp;&amp; echo test" data-copy-feedback="✓" data-copy-delay="300">📋</button>
    <pre id="ai-json">{"ornek": "veri"}</pre>
    <button data-copy-target="ai-json" data-copy-feedback="✅ Kopyalandı" data-copy-delay="300">📋 Panoya Kopyala</button>
  `;
  document.body.appendChild(div);
}
"""


def _admin_sayfa_ac(browser, live_server):
    context = browser.new_context()
    context.grant_permissions(["clipboard-read", "clipboard-write"])
    page = context.new_page()
    page.add_init_script(_sw_devre_disi_birak_init_script())
    hatalar = []
    page.on("pageerror", lambda exc: hatalar.append(str(exc)))
    page.goto(f"{live_server}/static/index.html")
    page.wait_for_selector("#giris-btn", timeout=10000)
    page.evaluate(ADMIN_STUB_JS)
    page.evaluate(ADMIN_INJECT_BUTTONS_JS)
    return context, page, hatalar


def test_adminsistem_data_action_argumanli_cagri(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _admin_sayfa_ac(browser, live_server)

        page.click('[data-action="sistemLogYukle"]')
        page.wait_for_timeout(200)

        cagrilar = page.evaluate("window.__cagrilar")
        assert cagrilar == [{"fn": "sistemLogYukle", "args": ["error"]}], f"Yanlış çağrı: {cagrilar}"
        assert not hatalar, f"JS hatası: {hatalar}"
        context.close()
        browser.close()


def test_adminsistem_data_action_argumansiz_cagri(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _admin_sayfa_ac(browser, live_server)

        page.click('[data-action="sistemAiTanilamaIndir"]')
        page.wait_for_timeout(200)

        cagrilar = page.evaluate("window.__cagrilar")
        assert cagrilar == [{"fn": "sistemAiTanilamaIndir", "args": []}], f"Yanlış çağrı: {cagrilar}"
        assert not hatalar, f"JS hatası: {hatalar}"
        context.close()
        browser.close()


def test_adminsistem_data_copy_text_statik_metin_kopyalar(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _admin_sayfa_ac(browser, live_server)

        btn = page.locator('[data-copy-text]')
        assert btn.text_content() == "📋"

        btn.click()
        page.wait_for_timeout(100)
        assert btn.text_content() == "✓", "Tıklama sonrası geri bildirim metni görünmedi"

        panoya_kopyalanan = page.evaluate("navigator.clipboard.readText()")
        assert panoya_kopyalanan == "git pull && echo test", \
            f"Panoya yanlış metin kopyalandı: {panoya_kopyalanan!r}"

        page.wait_for_timeout(400)
        assert btn.text_content() == "📋", "Geri bildirim süresi sonunda eski metne dönmedi"

        assert not hatalar, f"JS hatası: {hatalar}"
        context.close()
        browser.close()


def test_adminsistem_data_copy_target_element_icerigini_kopyalar(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _admin_sayfa_ac(browser, live_server)

        page.click('[data-copy-target="ai-json"]')
        page.wait_for_timeout(100)

        panoya_kopyalanan = page.evaluate("navigator.clipboard.readText()")
        assert panoya_kopyalanan == '{"ornek": "veri"}', \
            f"Panoya yanlış içerik kopyalandı: {panoya_kopyalanan!r}"

        assert not hatalar, f"JS hatası: {hatalar}"
        context.close()
        browser.close()


# ═══════════════════════════════════════════════════════════════════════
# BÖLÜM 4 — app.js: genel daAttr() / data-action mekanizması
# (wizard, tema, widget gruplarının hepsinin kullandığı ORTAK altyapı)
# ═══════════════════════════════════════════════════════════════════════
DAATTR_STUB_JS = """
() => {
  window.__cagrilar = [];
  window.wizardAdim1 = (...args) => window.__cagrilar.push({ fn: 'wizardAdim1', args });
  window.wizardAdim2 = (...args) => window.__cagrilar.push({ fn: 'wizardAdim2', args });
  window.temaUygula = (tema, el) => window.__cagrilar.push({
    fn: 'temaUygula', tema, elIsButton: el instanceof HTMLElement, elId: el && el.id
  });
  window.bannerSilTest = (...args) => window.__cagrilar.push({ fn: 'bannerSilTest', args });
  window.widgetKaydetTest = (...args) => window.__cagrilar.push({ fn: 'widgetKaydetTest', args });
}
"""

DAATTR_INJECT_BUTTONS_JS = """
() => {
  const div = document.createElement('div');
  div.id = 'test-daattr-butonlari';
  div.innerHTML = `
    <button data-action="wizardAdim1">Devam</button>
    <button data-action="wizardAdim2" data-action-args="[&quot;emlak&quot;]">Emlak</button>
    <div id="tema-yesil" data-action="temaUygula" data-action-args="[&quot;green&quot;,&quot;__EL__&quot;]">
      <div class="tema-renk-ic">renk</div>
    </div>
    <button data-action="bannerSilTest" data-confirm="Silinsin mi?">Sil</button>
    <button data-action="widgetKaydetTest" data-action-args="[null]">Kaydet</button>
  `;
  document.body.appendChild(div);
}
"""


def _daattr_sayfa_ac(browser, live_server):
    context = browser.new_context()
    page = context.new_page()
    page.add_init_script(_sw_devre_disi_birak_init_script())
    hatalar = []
    page.on("pageerror", lambda exc: hatalar.append(str(exc)))
    page.goto(f"{live_server}/static/index.html")
    page.wait_for_selector("#giris-btn", timeout=10000)
    page.evaluate(DAATTR_STUB_JS)
    page.evaluate(DAATTR_INJECT_BUTTONS_JS)
    return context, page, hatalar


def test_appdaattr_argumansiz_cagri(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _daattr_sayfa_ac(browser, live_server)

        page.click('[data-action="wizardAdim1"]')
        page.wait_for_timeout(150)
        cagrilar = page.evaluate("window.__cagrilar")
        assert cagrilar == [{"fn": "wizardAdim1", "args": []}], f"Beklenmedik: {cagrilar}"
        assert not hatalar, f"JS hatası: {hatalar}"
        context.close()
        browser.close()


def test_appdaattr_string_argumanli_cagri(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _daattr_sayfa_ac(browser, live_server)

        page.click('[data-action="wizardAdim2"]')
        page.wait_for_timeout(150)
        cagrilar = page.evaluate("window.__cagrilar")
        assert cagrilar == [{"fn": "wizardAdim2", "args": ["emlak"]}], f"Beklenmedik: {cagrilar}"
        assert not hatalar, f"JS hatası: {hatalar}"
        context.close()
        browser.close()


def test_appdaattr_el_sentinel_tiklanan_elementi_gecirir(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _daattr_sayfa_ac(browser, live_server)

        page.click('#tema-yesil')
        page.wait_for_timeout(150)
        cagri = page.evaluate("window.__cagrilar[window.__cagrilar.length-1]")
        assert cagri["fn"] == "temaUygula"
        assert cagri["tema"] == "green"
        assert cagri["elIsButton"] is True, "İkinci argüman gerçek bir DOM elementi olmalıydı"
        assert cagri["elId"] == "tema-yesil", "Tıklanan elementin kendisi geçmeliydi"
        assert not hatalar, f"JS hatası: {hatalar}"
        context.close()
        browser.close()


def test_appdaattr_confirm_reddedilirse_fonksiyon_cagrilmaz(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _daattr_sayfa_ac(browser, live_server)
        page.on("dialog", lambda d: d.dismiss())

        onceki = page.evaluate("window.__cagrilar.length")
        page.click('[data-action="bannerSilTest"]')
        page.wait_for_timeout(150)
        sonraki = page.evaluate("window.__cagrilar.length")

        assert sonraki == onceki, "confirm() reddedildiği halde fonksiyon çağrıldı!"
        assert not hatalar, f"JS hatası: {hatalar}"
        context.close()
        browser.close()


def test_appdaattr_confirm_kabul_edilirse_fonksiyon_cagrilir(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _daattr_sayfa_ac(browser, live_server)
        page.on("dialog", lambda d: d.accept())

        page.click('[data-action="bannerSilTest"]')
        page.wait_for_timeout(150)
        cagrilar = page.evaluate("window.__cagrilar")
        assert cagrilar == [{"fn": "bannerSilTest", "args": []}], \
            f"confirm() kabul edildiği halde beklenmedik çağrı listesi: {cagrilar}"
        assert not hatalar, f"JS hatası: {hatalar}"
        context.close()
        browser.close()


def test_appdaattr_null_argumani_dogru_tasinir(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _daattr_sayfa_ac(browser, live_server)

        page.click('[data-action="widgetKaydetTest"]')
        page.wait_for_timeout(150)
        cagri = page.evaluate("window.__cagrilar[window.__cagrilar.length-1]")
        assert cagri == {"fn": "widgetKaydetTest", "args": [None]}, f"Beklenmedik: {cagri}"
        assert not hatalar, f"JS hatası: {hatalar}"
        context.close()
        browser.close()


def test_appdaattr_listener_tek_sefer_tetiklenir(live_server):
    """
    Regresyon: admin-sistem.js'in KENDİ data-action listener'ı app.js'inkiyle
    çakışıp aynı tıklamada fonksiyonu 2 KEZ çağırıyordu. Bu hata yakalanıp
    admin-sistem.js'ten çakışan listener kaldırıldı. Bu test bunu kalıcı
    olarak korur.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _daattr_sayfa_ac(browser, live_server)

        page.click('[data-action="wizardAdim1"]')
        page.wait_for_timeout(150)
        cagrilar = page.evaluate("window.__cagrilar")
        assert len(cagrilar) == 1, \
            f"wizardAdim1 tam olarak 1 kez çağrılmalıydı, {len(cagrilar)} kez çağrıldı: {cagrilar}"
        assert not hatalar, f"JS hatası: {hatalar}"
        context.close()
        browser.close()


# ═══════════════════════════════════════════════════════════════════════
# BÖLÜM 5 — app.js: Banner yönetimi
# ═══════════════════════════════════════════════════════════════════════
BANNER_STUB_JS = """
() => {
  window.__cagrilar = [];
  window.bannerYeniModal = (...args) => window.__cagrilar.push({ fn: 'bannerYeniModal', args });
  window.bannerResimModal = (...args) => window.__cagrilar.push({ fn: 'bannerResimModal', args });
  window.bannerDuzenleModal = (...args) => window.__cagrilar.push({ fn: 'bannerDuzenleModal', args });
  window.bannerToggle = (...args) => window.__cagrilar.push({ fn: 'bannerToggle', args });
  window.bannerSil = (...args) => window.__cagrilar.push({ fn: 'bannerSil', args });
}
"""

BANNER_INJECT_BUTTONS_JS = """
() => {
  const div = document.createElement('div');
  div.id = 'test-banner-butonlari';
  div.innerHTML = `
    <button class="btn btn-kirm" data-action="bannerYeniModal" data-action-args='[{"anasayfa-top":"Anasayfa Üst"},{"buyuk":"Büyük"}]'>+ Yeni Banner</button>
    <button class="btn btn-ntr btn-sm" data-action="bannerResimModal" data-action-args="[7]">📷</button>
    <button class="btn btn-ntr btn-sm" data-action="bannerDuzenleModal" data-action-args='[7,{"anasayfa-top":"Anasayfa Üst"},{"buyuk":"Büyük"}]'>✏</button>
    <button class="btn btn-sm" data-action="bannerToggle" data-action-args="[7,0]">⏸ Pasif</button>
    <button class="btn btn-hat btn-sm" data-action="bannerSil" data-action-args="[7]" data-confirm="Silinsin mi?">🗑</button>
  `;
  document.body.appendChild(div);
}
"""


def _banner_sayfa_ac(browser, live_server):
    page = browser.new_page()
    page.add_init_script(_sw_devre_disi_birak_init_script())
    hatalar = []
    page.on("pageerror", lambda exc: hatalar.append(str(exc)))
    page.goto(f"{live_server}/static/index.html")
    page.wait_for_selector("#giris-btn", timeout=10000)
    page.evaluate(BANNER_STUB_JS)
    page.evaluate(BANNER_INJECT_BUTTONS_JS)
    return page, hatalar


def test_appbanner_argumansiz_json_objeler_dogru_iletilir(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page, hatalar = _banner_sayfa_ac(browser, live_server)

        page.click('[data-action="bannerYeniModal"]')
        page.wait_for_timeout(150)

        cagrilar = page.evaluate("window.__cagrilar")
        assert cagrilar == [{
            "fn": "bannerYeniModal",
            "args": [{"anasayfa-top": "Anasayfa Üst"}, {"buyuk": "Büyük"}],
        }], f"Yanlış çağrı: {cagrilar}"
        assert not hatalar, f"JS hatası: {hatalar}"
        browser.close()


def test_appbanner_id_ve_toggle_degeri_dogru_tipte_gelir(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page, hatalar = _banner_sayfa_ac(browser, live_server)

        page.click('[data-action="bannerToggle"]')
        page.wait_for_timeout(150)

        cagrilar = page.evaluate("window.__cagrilar")
        assert cagrilar == [{"fn": "bannerToggle", "args": [7, 0]}], f"Yanlış çağrı: {cagrilar}"
        assert not hatalar, f"JS hatası: {hatalar}"
        browser.close()


def test_appbanner_confirm_onaylanirsa_fonksiyon_cagrilir(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page, hatalar = _banner_sayfa_ac(browser, live_server)

        page.on("dialog", lambda d: d.accept())
        page.click('[data-action="bannerSil"]')
        page.wait_for_timeout(150)

        cagrilar = page.evaluate("window.__cagrilar")
        assert cagrilar == [{"fn": "bannerSil", "args": [7]}], f"Yanlış çağrı: {cagrilar}"
        assert not hatalar, f"JS hatası: {hatalar}"
        browser.close()


def test_appbanner_confirm_reddedilirse_fonksiyon_cagrilmaz(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page, hatalar = _banner_sayfa_ac(browser, live_server)

        page.on("dialog", lambda d: d.dismiss())
        page.click('[data-action="bannerSil"]')
        page.wait_for_timeout(150)

        cagrilar = page.evaluate("window.__cagrilar")
        assert cagrilar == [], f"Confirm reddedilmesine rağmen çağrıldı: {cagrilar}"
        assert not hatalar, f"JS hatası: {hatalar}"
        browser.close()


def test_appbanner_ic_ice_json_arguman_dogru_iletilir(live_server):
    """bannerDuzenleModal(id, konumlar, boyutlar) — 3 karışık tipte argüman."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page, hatalar = _banner_sayfa_ac(browser, live_server)

        page.click('[data-action="bannerDuzenleModal"]')
        page.wait_for_timeout(150)

        cagrilar = page.evaluate("window.__cagrilar")
        assert cagrilar == [{
            "fn": "bannerDuzenleModal",
            "args": [7, {"anasayfa-top": "Anasayfa Üst"}, {"buyuk": "Büyük"}],
        }], f"Yanlış çağrı: {cagrilar}"
        assert not hatalar, f"JS hatası: {hatalar}"
        browser.close()


# ═══════════════════════════════════════════════════════════════════════
# BÖLÜM 6 — app.js: saas / sayfa / sablon / editorEkle grupları
# ═══════════════════════════════════════════════════════════════════════
SAAS_STUB_JS = """
() => {
  window.__cagrilar = [];
  window.saasTenantSil = (...args) => window.__cagrilar.push({ fn: 'saasTenantSil', args });
  window.sayfaKaydet = (...args) => window.__cagrilar.push({ fn: 'sayfaKaydet', args });
  window.sablonBolumTasi = (...args) => window.__cagrilar.push({ fn: 'sablonBolumTasi', args });
  window.editorEkle = (...args) => window.__cagrilar.push({ fn: 'editorEkle', args });
  window.sayfaEditorEkle = (...args) => window.__cagrilar.push({ fn: 'sayfaEditorEkle', args });
}
"""

SAAS_INJECT_BUTTONS_JS = r"""
() => {
  const div = document.createElement('div');
  div.id = 'test-saas-sayfa-editor-butonlari';
  div.innerHTML = `
    <button data-action="saasTenantSil" data-action-args="[5]" data-confirm="Emin misiniz?">Sil</button>
    <button data-action="sayfaKaydet" data-action-args="[null]">Kaydet</button>
    <button data-action="sablonBolumTasi" data-action-args="[3,7]">Taşı</button>
    <button data-action="editorEkle" id="btn-editor-ekle">H2</button>
    <button data-action="sayfaEditorEkle" data-action-args="[&quot;&lt;a href='' target='_blank'&gt;&quot;,&quot;&lt;/a&gt;&quot;]">Link</button>
  `;
  document.body.appendChild(div);
  // '\n## ' gibi kontrol karakteri içeren argümanları, gerçek daAttr()'ın
  // yaptığı gibi JSON.stringify ile üretiyoruz (elle yazılmış HTML'de
  // literal newline JSON'u bozar; bu sadece test kurulumunun kendi hatası).
  const btn = document.getElementById('btn-editor-ekle');
  btn.setAttribute('data-action-args', JSON.stringify(['\n## ', '']));
}
"""


def _saas_sayfa_ac(browser, live_server):
    context = browser.new_context()
    page = context.new_page()
    page.add_init_script(_sw_devre_disi_birak_init_script())
    hatalar = []
    page.on("pageerror", lambda exc: hatalar.append(str(exc)))
    page.goto(f"{live_server}/static/index.html")
    page.wait_for_selector("#giris-btn", timeout=10000)
    page.evaluate(SAAS_STUB_JS)
    page.evaluate(SAAS_INJECT_BUTTONS_JS)
    return context, page, hatalar


def test_appsaas_saas_tenant_sil_confirm_kabul(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _saas_sayfa_ac(browser, live_server)
        page.on("dialog", lambda d: d.accept())

        page.click('[data-action="saasTenantSil"]')
        page.wait_for_timeout(150)
        cagrilar = page.evaluate("window.__cagrilar")
        assert cagrilar == [{"fn": "saasTenantSil", "args": [5]}], f"Beklenmedik: {cagrilar}"
        assert not hatalar, f"JS hatası: {hatalar}"
        context.close()
        browser.close()


def test_appsaas_sayfa_kaydet_null_id(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _saas_sayfa_ac(browser, live_server)

        page.click('[data-action="sayfaKaydet"]')
        page.wait_for_timeout(150)
        cagrilar = page.evaluate("window.__cagrilar")
        assert cagrilar == [{"fn": "sayfaKaydet", "args": [None]}], f"Beklenmedik: {cagrilar}"
        assert not hatalar, f"JS hatası: {hatalar}"
        context.close()
        browser.close()


def test_appsaas_sablon_bolum_tasi_iki_id(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _saas_sayfa_ac(browser, live_server)

        page.click('[data-action="sablonBolumTasi"]')
        page.wait_for_timeout(150)
        cagrilar = page.evaluate("window.__cagrilar")
        assert cagrilar == [{"fn": "sablonBolumTasi", "args": [3, 7]}], f"Beklenmedik: {cagrilar}"
        assert not hatalar, f"JS hatası: {hatalar}"
        context.close()
        browser.close()


def test_appsaas_editor_ekle_cok_satirli_string(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _saas_sayfa_ac(browser, live_server)

        page.click('[data-action="editorEkle"]')
        page.wait_for_timeout(150)
        cagrilar = page.evaluate("window.__cagrilar")
        assert cagrilar == [{"fn": "editorEkle", "args": ["\n## ", ""]}], f"Beklenmedik: {cagrilar}"
        assert not hatalar, f"JS hatası: {hatalar}"
        context.close()
        browser.close()


def test_appsaas_sayfa_editor_ekle_tek_tirnakli_html(live_server):
    """Tek tırnak İÇEREN bir HTML string (<a href='' ...>) doğru taşınmalı — bu, orijinal
    kodda kırılgan manuel escape'e ihtiyaç duyan tam senaryo."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _saas_sayfa_ac(browser, live_server)

        page.click('[data-action="sayfaEditorEkle"]')
        page.wait_for_timeout(150)
        cagrilar = page.evaluate("window.__cagrilar")
        assert cagrilar == [{
            "fn": "sayfaEditorEkle",
            "args": ["<a href='' target='_blank'>", "</a>"],
        }], f"Beklenmedik: {cagrilar}"
        assert not hatalar, f"JS hatası: {hatalar}"
        context.close()
        browser.close()


# ═══════════════════════════════════════════════════════════════════════
# BÖLÜM 7 — app.js: ilan/portföy grubu (paylaşım, düzenle, harita, favori)
# ═══════════════════════════════════════════════════════════════════════
ILAN_STUB_JS = """
() => {
  window.__cagrilar = [];
  window.ilanPaylas = (...args) => window.__cagrilar.push({ fn: 'ilanPaylas', args });
  window.haritaIlanAc = (...args) => window.__cagrilar.push({ fn: 'haritaIlanAc', args });
  window.gFotoDegis = (el, url) => window.__cagrilar.push({
    fn: 'gFotoDegis', elIsElement: el instanceof HTMLElement, elId: el && el.id, url
  });
  window.favToggle = (id, baslik, btn) => window.__cagrilar.push({
    fn: 'favToggle', id, baslik, btnIsElement: btn instanceof HTMLElement, btnId: btn && btn.id
  });
}
"""

ILAN_INJECT_BUTTONS_JS = r"""
() => {
  const div = document.createElement('div');
  div.id = 'test-ilan-butonlari';
  div.innerHTML = `
    <button data-action="ilanPaylas" id="btn-ilan-paylas">Paylaş</button>
    <button data-action="haritaIlanAc" data-action-args="[99]">Haritada Aç</button>
    <div id="foto-thumb" style="width:40px;height:40px;background:#ccc" data-action="gFotoDegis" data-action-args="[&quot;__EL__&quot;,&quot;https://example.com/foto.jpg&quot;]"></div>
    <button id="fav-btn" data-action="favToggle" data-action-args="[15,&quot;Deniz Manzaralı Villa (O'Hara Sk.)&quot;,&quot;__EL__&quot;]">♡</button>
  `;
  document.body.appendChild(div);
  // Başlıkta tek tırnak İÇEREN bir değeri, eski koddaki manuel .replace(/'/g,...)
  // yerine JSON.stringify ile güvenle taşıdığımızı kanıtlamak için gerçekçi bir
  // örnek kullanıyoruz (yukarıdaki O'Hara Sk. değeri).
  document.getElementById('btn-ilan-paylas').setAttribute(
    'data-action-args',
    JSON.stringify(['wa', 42, "Satılık Ev (Sahibinden'e Yakın)", '2.500.000 TL'])
  );
}
"""


def _ilan_sayfa_ac(browser, live_server):
    context = browser.new_context()
    page = context.new_page()
    page.add_init_script(_sw_devre_disi_birak_init_script())
    hatalar = []
    page.on("pageerror", lambda exc: hatalar.append(str(exc)))
    page.goto(f"{live_server}/static/index.html")
    page.wait_for_selector("#giris-btn", timeout=10000)
    page.evaluate(ILAN_STUB_JS)
    page.evaluate(ILAN_INJECT_BUTTONS_JS)
    return context, page, hatalar


def test_ilan_paylas_tek_tirnakli_baslik_dogru_tasinir(live_server):
    """Eski kod .replace(/'/g,"\\'") ile elle escape ediyordu — daAttr() bunu
    JSON.stringify ile otomatik ve güvenli yapıyor. Başlıkta tek tırnak VE
    parantez olan gerçekçi bir örnekle doğruluyoruz."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _ilan_sayfa_ac(browser, live_server)

        page.click('[data-action="ilanPaylas"]')
        page.wait_for_timeout(150)
        cagrilar = page.evaluate("window.__cagrilar")
        assert cagrilar == [{
            "fn": "ilanPaylas",
            "args": ["wa", 42, "Satılık Ev (Sahibinden'e Yakın)", "2.500.000 TL"],
        }], f"Beklenmedik: {cagrilar}"
        assert not hatalar, f"JS hatası: {hatalar}"
        context.close()
        browser.close()


def test_ilan_harita_ac_id_argumani(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _ilan_sayfa_ac(browser, live_server)

        page.click('[data-action="haritaIlanAc"]')
        page.wait_for_timeout(150)
        cagrilar = page.evaluate("window.__cagrilar")
        assert cagrilar == [{"fn": "haritaIlanAc", "args": [99]}], f"Beklenmedik: {cagrilar}"
        assert not hatalar, f"JS hatası: {hatalar}"
        context.close()
        browser.close()


def test_ilan_gfoto_degis_el_ilk_argumanda(live_server):
    """gFotoDegis(this, url) — __EL__ sentinel BİRİNCİ argümanda (temaUygula'dan
    farklı olarak); sıra doğru korunmalı."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _ilan_sayfa_ac(browser, live_server)

        page.click('#foto-thumb')
        page.wait_for_timeout(150)
        cagri = page.evaluate("window.__cagrilar[window.__cagrilar.length-1]")
        assert cagri["fn"] == "gFotoDegis"
        assert cagri["elIsElement"] is True
        assert cagri["elId"] == "foto-thumb"
        assert cagri["url"] == "https://example.com/foto.jpg"
        assert not hatalar, f"JS hatası: {hatalar}"
        context.close()
        browser.close()


def test_ilan_fav_toggle_el_ucuncu_argumanda(live_server):
    """favToggle(id, baslik, this) — __EL__ sentinel ÜÇÜNCÜ argümanda."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _ilan_sayfa_ac(browser, live_server)

        page.click('#fav-btn')
        page.wait_for_timeout(150)
        cagri = page.evaluate("window.__cagrilar[window.__cagrilar.length-1]")
        assert cagri["fn"] == "favToggle"
        assert cagri["id"] == 15
        assert cagri["btnIsElement"] is True
        assert cagri["btnId"] == "fav-btn"
        assert not hatalar, f"JS hatası: {hatalar}"
        context.close()
        browser.close()


# ═══════════════════════════════════════════════════════════════════════
# BÖLÜM 8 — app.js: blog yönetimi grubu
# ═══════════════════════════════════════════════════════════════════════
BLOG_STUB_JS = """
() => {
  window.__cagrilar = [];
  window.blogDuzenle = (...args) => window.__cagrilar.push({ fn: 'blogDuzenle', args });
  window.blogDurumDegis = (...args) => window.__cagrilar.push({ fn: 'blogDurumDegis', args });
  window.blogSilAdmin = (...args) => window.__cagrilar.push({ fn: 'blogSilAdmin', args });
}
"""

BLOG_INJECT_BUTTONS_JS = """
() => {
  const div = document.createElement('div');
  div.id = 'test-blog-butonlari';
  div.innerHTML = `
    <button data-action="blogDuzenle" data-action-args="[11]">✏</button>
    <button data-action="blogDurumDegis" data-action-args="[11,&quot;Taslak&quot;]">⏸</button>
    <button data-action="blogSilAdmin" data-action-args="[11]" data-confirm="Yazı silinsin mi?">🗑</button>
  `;
  document.body.appendChild(div);
}
"""


def _blog_sayfa_ac(browser, live_server):
    context = browser.new_context()
    page = context.new_page()
    page.add_init_script(_sw_devre_disi_birak_init_script())
    hatalar = []
    page.on("pageerror", lambda exc: hatalar.append(str(exc)))
    page.goto(f"{live_server}/static/index.html")
    page.wait_for_selector("#giris-btn", timeout=10000)
    page.evaluate(BLOG_STUB_JS)
    page.evaluate(BLOG_INJECT_BUTTONS_JS)
    return context, page, hatalar


def test_blog_duzenle_id_argumani(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _blog_sayfa_ac(browser, live_server)

        page.click('[data-action="blogDuzenle"]')
        page.wait_for_timeout(150)
        cagrilar = page.evaluate("window.__cagrilar")
        assert cagrilar == [{"fn": "blogDuzenle", "args": [11]}], f"Beklenmedik: {cagrilar}"
        assert not hatalar, f"JS hatası: {hatalar}"
        context.close()
        browser.close()


def test_blog_durum_degis_string_argumani(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _blog_sayfa_ac(browser, live_server)

        page.click('[data-action="blogDurumDegis"]')
        page.wait_for_timeout(150)
        cagrilar = page.evaluate("window.__cagrilar")
        assert cagrilar == [{"fn": "blogDurumDegis", "args": [11, "Taslak"]}], f"Beklenmedik: {cagrilar}"
        assert not hatalar, f"JS hatası: {hatalar}"
        context.close()
        browser.close()


def test_blog_sil_admin_confirm_reddedilirse_cagrilmaz(live_server):
    """Regresyon: blogSilAdmin kendi içinde confirm() ÇAĞIRMIYOR — bu yüzden
    buton tarafında data-confirm OLMALI. Reddedilince çağrılmamalı."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _blog_sayfa_ac(browser, live_server)
        page.on("dialog", lambda d: d.dismiss())

        page.click('[data-action="blogSilAdmin"]')
        page.wait_for_timeout(150)
        cagrilar = page.evaluate("window.__cagrilar")
        assert cagrilar == [], f"confirm() reddedildiği halde çağrıldı: {cagrilar}"
        assert not hatalar, f"JS hatası: {hatalar}"
        context.close()
        browser.close()


def test_blog_sil_admin_confirm_kabul_edilirse_cagrilir(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _blog_sayfa_ac(browser, live_server)
        page.on("dialog", lambda d: d.accept())

        page.click('[data-action="blogSilAdmin"]')
        page.wait_for_timeout(150)
        cagrilar = page.evaluate("window.__cagrilar")
        assert cagrilar == [{"fn": "blogSilAdmin", "args": [11]}], f"Beklenmedik: {cagrilar}"
        assert not hatalar, f"JS hatası: {hatalar}"
        context.close()
        browser.close()


# ═══════════════════════════════════════════════════════════════════════
# BÖLÜM 9 — app.js: admin menü yönetimi grubu
# ═══════════════════════════════════════════════════════════════════════
MENUYON_STUB_JS = """
() => {
  window.__cagrilar = [];
  window.menuOgeTasi = (...args) => window.__cagrilar.push({ fn: 'menuOgeTasi', args });
  window.menuSil = (...args) => window.__cagrilar.push({ fn: 'menuSil', args });
  window.menuHedefSec = (...args) => window.__cagrilar.push({ fn: 'menuHedefSec', args });
  window.adminMenuOgelr = (...args) => window.__cagrilar.push({ fn: 'adminMenuOgelr', args });
}
"""

MENUYON_INJECT_BUTTONS_JS = """
() => {
  const div = document.createElement('div');
  div.id = 'test-menuyon-butonlari';
  div.innerHTML = `
    <button data-action="menuOgeTasi" data-action-args="[5,2,-1]">↑</button>
    <button data-action="menuSil" data-action-args="[2]" data-confirm="Bu menü silinsin mi? (içindeki tüm öğeler de silinir)">🗑️</button>
    <button data-action="menuHedefSec" data-action-args="[&quot;sayfa&quot;,&quot;hakkimizda&quot;,&quot;Hakkımızda · sayfa&quot;]">Seç</button>
    <button data-action="adminMenuOgelr" data-action-args="[2,&quot;ana-menu&quot;]">📋 Öğeleri Düzenle</button>
  `;
  document.body.appendChild(div);
}
"""


def _menuyon_sayfa_ac(browser, live_server):
    context = browser.new_context()
    page = context.new_page()
    page.add_init_script(_sw_devre_disi_birak_init_script())
    hatalar = []
    page.on("pageerror", lambda exc: hatalar.append(str(exc)))
    page.goto(f"{live_server}/static/index.html")
    page.wait_for_selector("#giris-btn", timeout=10000)
    page.evaluate(MENUYON_STUB_JS)
    page.evaluate(MENUYON_INJECT_BUTTONS_JS)
    return context, page, hatalar


def test_menuyon_oge_tasi_uc_argumanli(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _menuyon_sayfa_ac(browser, live_server)

        page.click('[data-action="menuOgeTasi"]')
        page.wait_for_timeout(150)
        cagrilar = page.evaluate("window.__cagrilar")
        assert cagrilar == [{"fn": "menuOgeTasi", "args": [5, 2, -1]}], f"Beklenmedik: {cagrilar}"
        assert not hatalar, f"JS hatası: {hatalar}"
        context.close()
        browser.close()


def test_menuyon_sil_confirm_reddedilirse_cagrilmaz(live_server):
    """Regresyon: menuSil kendi içinde de confirm() çağırıyor. Buton tarafında
    AYRICA data-confirm ekleyip çift onay hatası yapmadığımızı doğruluyoruz —
    burada tek confirm (bizim test dialog handler'ımız) reddedince hiç
    çağrılmamalı."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _menuyon_sayfa_ac(browser, live_server)
        page.on("dialog", lambda d: d.dismiss())

        page.click('[data-action="menuSil"]')
        page.wait_for_timeout(150)
        cagrilar = page.evaluate("window.__cagrilar")
        assert cagrilar == [], f"confirm() reddedildiği halde çağrıldı: {cagrilar}"
        assert not hatalar, f"JS hatası: {hatalar}"
        context.close()
        browser.close()


def test_menuyon_hedef_sec_uc_string_argumani(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _menuyon_sayfa_ac(browser, live_server)

        page.click('[data-action="menuHedefSec"]')
        page.wait_for_timeout(150)
        cagrilar = page.evaluate("window.__cagrilar")
        assert cagrilar == [{
            "fn": "menuHedefSec",
            "args": ["sayfa", "hakkimizda", "Hakkımızda · sayfa"],
        }], f"Beklenmedik: {cagrilar}"
        assert not hatalar, f"JS hatası: {hatalar}"
        context.close()
        browser.close()


def test_menuyon_admin_menu_ogelr_id_ve_slug(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _menuyon_sayfa_ac(browser, live_server)

        page.click('[data-action="adminMenuOgelr"]')
        page.wait_for_timeout(150)
        cagrilar = page.evaluate("window.__cagrilar")
        assert cagrilar == [{"fn": "adminMenuOgelr", "args": [2, "ana-menu"]}], f"Beklenmedik: {cagrilar}"
        assert not hatalar, f"JS hatası: {hatalar}"
        context.close()
        browser.close()


# ═══════════════════════════════════════════════════════════════════════
# BÖLÜM 10 — app.js: kullanıcı yönetimi + profil/ayarlar grupları
# ═══════════════════════════════════════════════════════════════════════
KULLANICI_STUB_JS = """
() => {
  window.__cagrilar = [];
  window.kullaniciOnayla = (...args) => window.__cagrilar.push({ fn: 'kullaniciOnayla', args });
  window.profilKaydet = (...args) => window.__cagrilar.push({ fn: 'profilKaydet', args });
  window.heroFontSec = (el) => window.__cagrilar.push({
    fn: 'heroFontSec', elIsElement: el instanceof HTMLElement, font: el && el.dataset.font
  });
}
"""

KULLANICI_INJECT_BUTTONS_JS = """
() => {
  const div = document.createElement('div');
  div.id = 'test-kullanici-butonlari';
  div.innerHTML = `
    <button data-action="kullaniciOnayla" data-action-args="[8]">✓ Onayla</button>
    <button data-action="profilKaydet">💾 Profili Güncelle</button>
    <div id="font-secim" data-font="Playfair Display" data-action="heroFontSec" data-action-args="[&quot;__EL__&quot;]" style="width:80px;height:20px">Playfair</div>
  `;
  document.body.appendChild(div);
}
"""


def _kullanici_sayfa_ac(browser, live_server):
    context = browser.new_context()
    page = context.new_page()
    page.add_init_script(_sw_devre_disi_birak_init_script())
    hatalar = []
    page.on("pageerror", lambda exc: hatalar.append(str(exc)))
    page.goto(f"{live_server}/static/index.html")
    page.wait_for_selector("#giris-btn", timeout=10000)
    page.evaluate(KULLANICI_STUB_JS)
    page.evaluate(KULLANICI_INJECT_BUTTONS_JS)
    return context, page, hatalar


def test_kullanici_onayla_id_argumani(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _kullanici_sayfa_ac(browser, live_server)

        page.click('[data-action="kullaniciOnayla"]')
        page.wait_for_timeout(150)
        cagrilar = page.evaluate("window.__cagrilar")
        assert cagrilar == [{"fn": "kullaniciOnayla", "args": [8]}], f"Beklenmedik: {cagrilar}"
        assert not hatalar, f"JS hatası: {hatalar}"
        context.close()
        browser.close()


def test_profil_kaydet_argumansiz(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _kullanici_sayfa_ac(browser, live_server)

        page.click('[data-action="profilKaydet"]')
        page.wait_for_timeout(150)
        cagrilar = page.evaluate("window.__cagrilar")
        assert cagrilar == [{"fn": "profilKaydet", "args": []}], f"Beklenmedik: {cagrilar}"
        assert not hatalar, f"JS hatası: {hatalar}"
        context.close()
        browser.close()


def test_hero_font_sec_el_tek_argumanda(live_server):
    """heroFontSec(this) — __EL__ sentinel TEK argüman olarak; elementin
    kendi data-font attribute'una fonksiyon içinde erişilebilmeli."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _kullanici_sayfa_ac(browser, live_server)

        page.click('#font-secim')
        page.wait_for_timeout(150)
        cagri = page.evaluate("window.__cagrilar[window.__cagrilar.length-1]")
        assert cagri["fn"] == "heroFontSec"
        assert cagri["elIsElement"] is True
        assert cagri["font"] == "Playfair Display"
        assert not hatalar, f"JS hatası: {hatalar}"
        context.close()
        browser.close()


# ═══════════════════════════════════════════════════════════════════════
# BÖLÜM 11+ — YENİ TESTLER BURADAN SONRA EKLENİR
# (kalan grup: slider, karşılaştırma, duyuru, adminSayfa nav, geriGit vb.)
# ═══════════════════════════════════════════════════════════════════════
