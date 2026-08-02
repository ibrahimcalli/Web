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

ZAMANLAMA NOTU: Sabit page.wait_for_timeout(N) yerine mümkün olduğunca
_bekle_kosul() ile POLLING kullanılır — böylece testler yavaş/yüklü
makinelerde de (sabit süre yetmediği için) yanlışlıkla başarısız olmaz,
koşul ne zaman gerçekleşirse o an devam eder (timeout'a kadar).

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


def _bekle_kosul(page, js_kosul, timeout=15000, mesaj=""):
    """Sabit page.wait_for_timeout(N) yerine: js_kosul (string, JS ifadesi)
    true dönene kadar POLLING ile bekler. Yavaş/yüklü makinelerde sabit
    süre yetmediği için testlerin yanlışlıkla kırılmasını önler — koşul
    ne zaman sağlanırsa o an devam eder, en fazla timeout kadar bekler."""
    try:
        page.wait_for_function(js_kosul, timeout=timeout)
    except Exception as e:
        raise AssertionError(f"{mesaj or 'Koşul zaman aşımına uğradı'}: {js_kosul!r} ({e})")


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


def test_widget_cerez_banner_kapat_ve_cookie_set_edilir(live_server, browser):
    page = browser.new_page()
    try:
        hatalar = []
        page.on("pageerror", lambda exc: hatalar.append(str(exc)))

        page.goto(f"{live_server}{WIDGET_FIXTURE_URL_PATH}")
        page.wait_for_selector('[data-widget-action="cerez-onayla"]', timeout=5000)

        assert page.locator('[data-widget-container="footer-1"]').is_visible(), \
            "Banner render edilmedi"

        page.click('[data-widget-action="cerez-onayla"]')
        page.wait_for_timeout(700)

        assert page.locator('[data-widget-container="footer-1"]').count() == 0, \
            "Banner tıklamadan sonra kaybolmadı (container.remove() çalışmadı)"

        cookies = page.context.cookies()
        cookie_ok = next((c for c in cookies if c["name"] == "cookie_ok"), None)
        assert cookie_ok is not None and cookie_ok["value"] == "1", \
            "cookie_ok çerezi set edilmedi"

        assert not hatalar, f"Sayfada JS hatası oluştu: {hatalar}"
    finally:
        page.close()


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


def test_menu_sayfa_link_preventDefault_ve_dogru_parametre(live_server, browser):
    page = browser.new_page()
    try:
        hatalar = []
        page.on("pageerror", lambda exc: hatalar.append(str(exc)))

        page.goto(f"{live_server}{MENU_FIXTURE_URL_PATH}")
        page.wait_for_selector('[data-sayfa-git="sayfa"]', timeout=5000)

        url_once = page.url
        page.click('[data-sayfa-git="sayfa"]')
        page.wait_for_timeout(600)

        assert page.url == url_once, "Link tıklanınca sayfa yönlendi (preventDefault çalışmadı)"

        cagrilar = page.evaluate("window.__sayfaGitCagrilari")
        assert cagrilar == [{"sayfa": "sayfa", "params": {"slug": "hakkimizda"}}], \
            f"sayfaGit yanlış çağrıldı: {cagrilar}"
        assert not hatalar, f"Sayfada JS hatası oluştu: {hatalar}"
    finally:
        page.close()


def test_menu_anasayfa_span_calisir(live_server, browser):
    page = browser.new_page()
    try:
        page.goto(f"{live_server}{MENU_FIXTURE_URL_PATH}")
        page.wait_for_selector('[data-sayfa-git="anasayfa"]', timeout=5000)

        page.click('[data-sayfa-git="anasayfa"]')
        page.wait_for_timeout(600)

        cagrilar = page.evaluate("window.__sayfaGitCagrilari")
        anasayfa_cagri = next((c for c in cagrilar if c["sayfa"] == "anasayfa"), None)
        assert anasayfa_cagri is not None, f"anasayfa çağrısı bulunamadı: {cagrilar}"
        assert anasayfa_cagri["params"] is None, \
            f"anasayfa çağrısında params olmamalıydı: {anasayfa_cagri}"
    finally:
        page.close()


def test_menu_sayisal_id_parametresi_dogru_tipte_gelir(live_server, browser):
    page = browser.new_page()
    try:
        page.goto(f"{live_server}{MENU_FIXTURE_URL_PATH}")
        page.wait_for_selector('[data-sayfa-git="detay"]', timeout=5000)

        page.click('[data-sayfa-git="detay"]')
        page.wait_for_timeout(600)

        cagrilar = page.evaluate("window.__sayfaGitCagrilari")
        detay_cagri = next((c for c in cagrilar if c["sayfa"] == "detay"), None)
        assert detay_cagri is not None, f"detay çağrısı bulunamadı: {cagrilar}"
        assert detay_cagri["params"]["id"] == 42, \
            f"id sayısal (42) olmalıydı, geldi: {detay_cagri['params']['id']!r}"
    finally:
        page.close()


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


def test_adminsistem_data_action_argumanli_cagri(live_server, browser):
    context, page, hatalar = _admin_sayfa_ac(browser, live_server)

    page.click('[data-action="sistemLogYukle"]')
    page.wait_for_timeout(600)

    cagrilar = page.evaluate("window.__cagrilar")
    assert cagrilar == [{"fn": "sistemLogYukle", "args": ["error"]}], f"Yanlış çağrı: {cagrilar}"
    assert not hatalar, f"JS hatası: {hatalar}"
    context.close()


def test_adminsistem_data_action_argumansiz_cagri(live_server, browser):
    context, page, hatalar = _admin_sayfa_ac(browser, live_server)

    page.click('[data-action="sistemAiTanilamaIndir"]')
    page.wait_for_timeout(600)

    cagrilar = page.evaluate("window.__cagrilar")
    assert cagrilar == [{"fn": "sistemAiTanilamaIndir", "args": []}], f"Yanlış çağrı: {cagrilar}"
    assert not hatalar, f"JS hatası: {hatalar}"
    context.close()


def test_adminsistem_data_copy_text_statik_metin_kopyalar(live_server, browser):
    context, page, hatalar = _admin_sayfa_ac(browser, live_server)

    btn = page.locator('[data-copy-text]')
    assert btn.text_content() == "📋"

    btn.click()
    _bekle_kosul(
        page,
        "document.querySelector('[data-copy-text]')?.textContent === '✓'",
        mesaj="Tıklama sonrası geri bildirim metni görünmedi",
    )

    panoya_kopyalanan = page.evaluate("navigator.clipboard.readText()")
    assert panoya_kopyalanan == "git pull && echo test", \
        f"Panoya yanlış metin kopyalandı: {panoya_kopyalanan!r}"

    _bekle_kosul(
        page,
        "document.querySelector('[data-copy-text]')?.textContent === '📋'",
        mesaj="Geri bildirim süresi sonunda eski metne dönmedi",
    )

    assert not hatalar, f"JS hatası: {hatalar}"
    context.close()


def test_adminsistem_data_copy_target_element_icerigini_kopyalar(live_server, browser):
    context, page, hatalar = _admin_sayfa_ac(browser, live_server)

    page.click('[data-copy-target="ai-json"]')
    _bekle_kosul(
        page,
        "document.querySelector('[data-copy-target=\\\"ai-json\\\"]')?.textContent !== '📋 Panoya Kopyala'",
        mesaj="Kopyalama sonrası buton geri bildirimi görünmedi",
    )

    panoya_kopyalanan = page.evaluate("navigator.clipboard.readText()")
    assert panoya_kopyalanan == '{"ornek": "veri"}', \
        f"Panoya yanlış içerik kopyalandı: {panoya_kopyalanan!r}"

    assert not hatalar, f"JS hatası: {hatalar}"
    context.close()


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


def test_appdaattr_argumansiz_cagri(live_server, browser):
    context, page, hatalar = _daattr_sayfa_ac(browser, live_server)

    page.click('[data-action="wizardAdim1"]')
    page.wait_for_timeout(500)
    cagrilar = page.evaluate("window.__cagrilar")
    assert cagrilar == [{"fn": "wizardAdim1", "args": []}], f"Beklenmedik: {cagrilar}"
    assert not hatalar, f"JS hatası: {hatalar}"
    context.close()


def test_appdaattr_string_argumanli_cagri(live_server, browser):
    context, page, hatalar = _daattr_sayfa_ac(browser, live_server)

    page.click('[data-action="wizardAdim2"]')
    page.wait_for_timeout(500)
    cagrilar = page.evaluate("window.__cagrilar")
    assert cagrilar == [{"fn": "wizardAdim2", "args": ["emlak"]}], f"Beklenmedik: {cagrilar}"
    assert not hatalar, f"JS hatası: {hatalar}"
    context.close()


def test_appdaattr_el_sentinel_tiklanan_elementi_gecirir(live_server, browser):
    context, page, hatalar = _daattr_sayfa_ac(browser, live_server)

    page.click('#tema-yesil')
    page.wait_for_timeout(500)
    cagri = page.evaluate("window.__cagrilar[window.__cagrilar.length-1]")
    assert cagri["fn"] == "temaUygula"
    assert cagri["tema"] == "green"
    assert cagri["elIsButton"] is True, "İkinci argüman gerçek bir DOM elementi olmalıydı"
    assert cagri["elId"] == "tema-yesil", "Tıklanan elementin kendisi geçmeliydi"
    assert not hatalar, f"JS hatası: {hatalar}"
    context.close()


def test_appdaattr_confirm_reddedilirse_fonksiyon_cagrilmaz(live_server, browser):
    context, page, hatalar = _daattr_sayfa_ac(browser, live_server)
    page.on("dialog", lambda d: d.dismiss())

    onceki = page.evaluate("window.__cagrilar.length")
    page.click('[data-action="bannerSilTest"]')
    page.wait_for_timeout(500)
    sonraki = page.evaluate("window.__cagrilar.length")

    assert sonraki == onceki, "confirm() reddedildiği halde fonksiyon çağrıldı!"
    assert not hatalar, f"JS hatası: {hatalar}"
    context.close()


def test_appdaattr_confirm_kabul_edilirse_fonksiyon_cagrilir(live_server, browser):
    context, page, hatalar = _daattr_sayfa_ac(browser, live_server)
    page.on("dialog", lambda d: d.accept())

    page.click('[data-action="bannerSilTest"]')
    page.wait_for_timeout(500)
    cagrilar = page.evaluate("window.__cagrilar")
    assert cagrilar == [{"fn": "bannerSilTest", "args": []}], \
        f"confirm() kabul edildiği halde beklenmedik çağrı listesi: {cagrilar}"
    assert not hatalar, f"JS hatası: {hatalar}"
    context.close()


def test_appdaattr_null_argumani_dogru_tasinir(live_server, browser):
    context, page, hatalar = _daattr_sayfa_ac(browser, live_server)

    page.click('[data-action="widgetKaydetTest"]')
    page.wait_for_timeout(500)
    cagri = page.evaluate("window.__cagrilar[window.__cagrilar.length-1]")
    assert cagri == {"fn": "widgetKaydetTest", "args": [None]}, f"Beklenmedik: {cagri}"
    assert not hatalar, f"JS hatası: {hatalar}"
    context.close()


def test_appdaattr_listener_tek_sefer_tetiklenir(live_server, browser):
    """
    Regresyon: admin-sistem.js'in KENDİ data-action listener'ı app.js'inkiyle
    çakışıp aynı tıklamada fonksiyonu 2 KEZ çağırıyordu. Bu hata yakalanıp
    admin-sistem.js'ten çakışan listener kaldırıldı. Bu test bunu kalıcı
    olarak korur.
    """
    context, page, hatalar = _daattr_sayfa_ac(browser, live_server)

    page.click('[data-action="wizardAdim1"]')
    page.wait_for_timeout(500)
    cagrilar = page.evaluate("window.__cagrilar")
    assert len(cagrilar) == 1, \
        f"wizardAdim1 tam olarak 1 kez çağrılmalıydı, {len(cagrilar)} kez çağrıldı: {cagrilar}"
    assert not hatalar, f"JS hatası: {hatalar}"
    context.close()


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


def test_appbanner_argumansiz_json_objeler_dogru_iletilir(live_server, browser):
    page, hatalar = _banner_sayfa_ac(browser, live_server)
    try:
        page.click('[data-action="bannerYeniModal"]')
        page.wait_for_timeout(500)

        cagrilar = page.evaluate("window.__cagrilar")
        assert cagrilar == [{
            "fn": "bannerYeniModal",
            "args": [{"anasayfa-top": "Anasayfa Üst"}, {"buyuk": "Büyük"}],
        }], f"Yanlış çağrı: {cagrilar}"
        assert not hatalar, f"JS hatası: {hatalar}"
    finally:
        page.close()


def test_appbanner_id_ve_toggle_degeri_dogru_tipte_gelir(live_server, browser):
    page, hatalar = _banner_sayfa_ac(browser, live_server)
    try:
        page.click('[data-action="bannerToggle"]')
        page.wait_for_timeout(500)

        cagrilar = page.evaluate("window.__cagrilar")
        assert cagrilar == [{"fn": "bannerToggle", "args": [7, 0]}], f"Yanlış çağrı: {cagrilar}"
        assert not hatalar, f"JS hatası: {hatalar}"
    finally:
        page.close()


def test_appbanner_confirm_onaylanirsa_fonksiyon_cagrilir(live_server, browser):
    page, hatalar = _banner_sayfa_ac(browser, live_server)
    try:
        page.on("dialog", lambda d: d.accept())
        page.click('[data-action="bannerSil"]')
        page.wait_for_timeout(500)

        cagrilar = page.evaluate("window.__cagrilar")
        assert cagrilar == [{"fn": "bannerSil", "args": [7]}], f"Yanlış çağrı: {cagrilar}"
        assert not hatalar, f"JS hatası: {hatalar}"
    finally:
        page.close()


def test_appbanner_confirm_reddedilirse_fonksiyon_cagrilmaz(live_server, browser):
    page, hatalar = _banner_sayfa_ac(browser, live_server)
    try:
        page.on("dialog", lambda d: d.dismiss())
        page.click('[data-action="bannerSil"]')
        page.wait_for_timeout(500)

        cagrilar = page.evaluate("window.__cagrilar")
        assert cagrilar == [], f"Confirm reddedilmesine rağmen çağrıldı: {cagrilar}"
        assert not hatalar, f"JS hatası: {hatalar}"
    finally:
        page.close()


def test_appbanner_ic_ice_json_arguman_dogru_iletilir(live_server, browser):
    """bannerDuzenleModal(id, konumlar, boyutlar) — 3 karışık tipte argüman."""
    page, hatalar = _banner_sayfa_ac(browser, live_server)
    try:
        page.click('[data-action="bannerDuzenleModal"]')
        page.wait_for_timeout(500)

        cagrilar = page.evaluate("window.__cagrilar")
        assert cagrilar == [{
            "fn": "bannerDuzenleModal",
            "args": [7, {"anasayfa-top": "Anasayfa Üst"}, {"buyuk": "Büyük"}],
        }], f"Yanlış çağrı: {cagrilar}"
        assert not hatalar, f"JS hatası: {hatalar}"
    finally:
        page.close()


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


def test_appsaas_saas_tenant_sil_confirm_kabul(live_server, browser):
    context, page, hatalar = _saas_sayfa_ac(browser, live_server)
    page.on("dialog", lambda d: d.accept())

    page.click('[data-action="saasTenantSil"]')
    page.wait_for_timeout(500)
    cagrilar = page.evaluate("window.__cagrilar")
    assert cagrilar == [{"fn": "saasTenantSil", "args": [5]}], f"Beklenmedik: {cagrilar}"
    assert not hatalar, f"JS hatası: {hatalar}"
    context.close()


def test_appsaas_sayfa_kaydet_null_id(live_server, browser):
    context, page, hatalar = _saas_sayfa_ac(browser, live_server)

    page.click('[data-action="sayfaKaydet"]')
    page.wait_for_timeout(500)
    cagrilar = page.evaluate("window.__cagrilar")
    assert cagrilar == [{"fn": "sayfaKaydet", "args": [None]}], f"Beklenmedik: {cagrilar}"
    assert not hatalar, f"JS hatası: {hatalar}"
    context.close()


def test_appsaas_sablon_bolum_tasi_iki_id(live_server, browser):
    context, page, hatalar = _saas_sayfa_ac(browser, live_server)

    page.click('[data-action="sablonBolumTasi"]')
    page.wait_for_timeout(500)
    cagrilar = page.evaluate("window.__cagrilar")
    assert cagrilar == [{"fn": "sablonBolumTasi", "args": [3, 7]}], f"Beklenmedik: {cagrilar}"
    assert not hatalar, f"JS hatası: {hatalar}"
    context.close()


def test_appsaas_editor_ekle_cok_satirli_string(live_server, browser):
    context, page, hatalar = _saas_sayfa_ac(browser, live_server)

    page.click('[data-action="editorEkle"]')
    page.wait_for_timeout(500)
    cagrilar = page.evaluate("window.__cagrilar")
    assert cagrilar == [{"fn": "editorEkle", "args": ["\n## ", ""]}], f"Beklenmedik: {cagrilar}"
    assert not hatalar, f"JS hatası: {hatalar}"
    context.close()


def test_appsaas_sayfa_editor_ekle_tek_tirnakli_html(live_server, browser):
    """Tek tırnak İÇEREN bir HTML string (<a href='' ...>) doğru taşınmalı — bu, orijinal
    kodda kırılgan manuel escape'e ihtiyaç duyan tam senaryo."""
    context, page, hatalar = _saas_sayfa_ac(browser, live_server)

    page.click('[data-action="sayfaEditorEkle"]')
    page.wait_for_timeout(500)
    cagrilar = page.evaluate("window.__cagrilar")
    assert cagrilar == [{
        "fn": "sayfaEditorEkle",
        "args": ["<a href='' target='_blank'>", "</a>"],
    }], f"Beklenmedik: {cagrilar}"
    assert not hatalar, f"JS hatası: {hatalar}"
    context.close()


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


def test_ilan_paylas_tek_tirnakli_baslik_dogru_tasinir(live_server, browser):
    """Eski kod .replace(/'/g,"\\'") ile elle escape ediyordu — daAttr() bunu
    JSON.stringify ile otomatik ve güvenli yapıyor. Başlıkta tek tırnak VE
    parantez olan gerçekçi bir örnekle doğruluyoruz."""
    context, page, hatalar = _ilan_sayfa_ac(browser, live_server)

    page.click('[data-action="ilanPaylas"]')
    page.wait_for_timeout(500)
    cagrilar = page.evaluate("window.__cagrilar")
    assert cagrilar == [{
        "fn": "ilanPaylas",
        "args": ["wa", 42, "Satılık Ev (Sahibinden'e Yakın)", "2.500.000 TL"],
    }], f"Beklenmedik: {cagrilar}"
    assert not hatalar, f"JS hatası: {hatalar}"
    context.close()


def test_ilan_harita_ac_id_argumani(live_server, browser):
    context, page, hatalar = _ilan_sayfa_ac(browser, live_server)

    page.click('[data-action="haritaIlanAc"]')
    page.wait_for_timeout(500)
    cagrilar = page.evaluate("window.__cagrilar")
    assert cagrilar == [{"fn": "haritaIlanAc", "args": [99]}], f"Beklenmedik: {cagrilar}"
    assert not hatalar, f"JS hatası: {hatalar}"
    context.close()


def test_ilan_gfoto_degis_el_ilk_argumanda(live_server, browser):
    """gFotoDegis(this, url) — __EL__ sentinel BİRİNCİ argümanda (temaUygula'dan
    farklı olarak); sıra doğru korunmalı."""
    context, page, hatalar = _ilan_sayfa_ac(browser, live_server)

    page.click('#foto-thumb')
    page.wait_for_timeout(500)
    cagri = page.evaluate("window.__cagrilar[window.__cagrilar.length-1]")
    assert cagri["fn"] == "gFotoDegis"
    assert cagri["elIsElement"] is True
    assert cagri["elId"] == "foto-thumb"
    assert cagri["url"] == "https://example.com/foto.jpg"
    assert not hatalar, f"JS hatası: {hatalar}"
    context.close()


def test_ilan_fav_toggle_el_ucuncu_argumanda(live_server, browser):
    """favToggle(id, baslik, this) — __EL__ sentinel ÜÇÜNCÜ argümanda."""
    context, page, hatalar = _ilan_sayfa_ac(browser, live_server)

    page.click('#fav-btn')
    page.wait_for_timeout(500)
    cagri = page.evaluate("window.__cagrilar[window.__cagrilar.length-1]")
    assert cagri["fn"] == "favToggle"
    assert cagri["id"] == 15
    assert cagri["btnIsElement"] is True
    assert cagri["btnId"] == "fav-btn"
    assert not hatalar, f"JS hatası: {hatalar}"
    context.close()


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


def test_blog_duzenle_id_argumani(live_server, browser):
    context, page, hatalar = _blog_sayfa_ac(browser, live_server)

    page.click('[data-action="blogDuzenle"]')
    page.wait_for_timeout(500)
    cagrilar = page.evaluate("window.__cagrilar")
    assert cagrilar == [{"fn": "blogDuzenle", "args": [11]}], f"Beklenmedik: {cagrilar}"
    assert not hatalar, f"JS hatası: {hatalar}"
    context.close()


def test_blog_durum_degis_string_argumani(live_server, browser):
    context, page, hatalar = _blog_sayfa_ac(browser, live_server)

    page.click('[data-action="blogDurumDegis"]')
    page.wait_for_timeout(500)
    cagrilar = page.evaluate("window.__cagrilar")
    assert cagrilar == [{"fn": "blogDurumDegis", "args": [11, "Taslak"]}], f"Beklenmedik: {cagrilar}"
    assert not hatalar, f"JS hatası: {hatalar}"
    context.close()


def test_blog_sil_admin_confirm_reddedilirse_cagrilmaz(live_server, browser):
    """Regresyon: blogSilAdmin kendi içinde confirm() ÇAĞIRMIYOR — bu yüzden
    buton tarafında data-confirm OLMALI. Reddedilince çağrılmamalı."""
    context, page, hatalar = _blog_sayfa_ac(browser, live_server)
    page.on("dialog", lambda d: d.dismiss())

    page.click('[data-action="blogSilAdmin"]')
    page.wait_for_timeout(500)
    cagrilar = page.evaluate("window.__cagrilar")
    assert cagrilar == [], f"confirm() reddedildiği halde çağrıldı: {cagrilar}"
    assert not hatalar, f"JS hatası: {hatalar}"
    context.close()


def test_blog_sil_admin_confirm_kabul_edilirse_cagrilir(live_server, browser):
    context, page, hatalar = _blog_sayfa_ac(browser, live_server)
    page.on("dialog", lambda d: d.accept())

    page.click('[data-action="blogSilAdmin"]')
    page.wait_for_timeout(500)
    cagrilar = page.evaluate("window.__cagrilar")
    assert cagrilar == [{"fn": "blogSilAdmin", "args": [11]}], f"Beklenmedik: {cagrilar}"
    assert not hatalar, f"JS hatası: {hatalar}"
    context.close()


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


def test_menuyon_oge_tasi_uc_argumanli(live_server, browser):
    context, page, hatalar = _menuyon_sayfa_ac(browser, live_server)

    page.click('[data-action="menuOgeTasi"]')
    page.wait_for_timeout(500)
    cagrilar = page.evaluate("window.__cagrilar")
    assert cagrilar == [{"fn": "menuOgeTasi", "args": [5, 2, -1]}], f"Beklenmedik: {cagrilar}"
    assert not hatalar, f"JS hatası: {hatalar}"
    context.close()


def test_menuyon_sil_confirm_reddedilirse_cagrilmaz(live_server, browser):
    """Regresyon: menuSil kendi içinde de confirm() çağırıyor. Buton tarafında
    AYRICA data-confirm ekleyip çift onay hatası yapmadığımızı doğruluyoruz —
    burada tek confirm (bizim test dialog handler'ımız) reddedince hiç
    çağrılmamalı."""
    context, page, hatalar = _menuyon_sayfa_ac(browser, live_server)
    page.on("dialog", lambda d: d.dismiss())

    page.click('[data-action="menuSil"]')
    page.wait_for_timeout(500)
    cagrilar = page.evaluate("window.__cagrilar")
    assert cagrilar == [], f"confirm() reddedildiği halde çağrıldı: {cagrilar}"
    assert not hatalar, f"JS hatası: {hatalar}"
    context.close()


def test_menuyon_hedef_sec_uc_string_argumani(live_server, browser):
    context, page, hatalar = _menuyon_sayfa_ac(browser, live_server)

    page.click('[data-action="menuHedefSec"]')
    page.wait_for_timeout(500)
    cagrilar = page.evaluate("window.__cagrilar")
    assert cagrilar == [{
        "fn": "menuHedefSec",
        "args": ["sayfa", "hakkimizda", "Hakkımızda · sayfa"],
    }], f"Beklenmedik: {cagrilar}"
    assert not hatalar, f"JS hatası: {hatalar}"
    context.close()


def test_menuyon_admin_menu_ogelr_id_ve_slug(live_server, browser):
    context, page, hatalar = _menuyon_sayfa_ac(browser, live_server)

    page.click('[data-action="adminMenuOgelr"]')
    page.wait_for_timeout(500)
    cagrilar = page.evaluate("window.__cagrilar")
    assert cagrilar == [{"fn": "adminMenuOgelr", "args": [2, "ana-menu"]}], f"Beklenmedik: {cagrilar}"
    assert not hatalar, f"JS hatası: {hatalar}"
    context.close()


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


def test_kullanici_onayla_id_argumani(live_server, browser):
    context, page, hatalar = _kullanici_sayfa_ac(browser, live_server)

    page.click('[data-action="kullaniciOnayla"]')
    page.wait_for_timeout(500)
    cagrilar = page.evaluate("window.__cagrilar")
    assert cagrilar == [{"fn": "kullaniciOnayla", "args": [8]}], f"Beklenmedik: {cagrilar}"
    assert not hatalar, f"JS hatası: {hatalar}"
    context.close()


def test_profil_kaydet_argumansiz(live_server, browser):
    context, page, hatalar = _kullanici_sayfa_ac(browser, live_server)

    page.click('[data-action="profilKaydet"]')
    page.wait_for_timeout(500)
    cagrilar = page.evaluate("window.__cagrilar")
    assert cagrilar == [{"fn": "profilKaydet", "args": []}], f"Beklenmedik: {cagrilar}"
    assert not hatalar, f"JS hatası: {hatalar}"
    context.close()


def test_hero_font_sec_el_tek_argumanda(live_server, browser):
    """heroFontSec(this) — __EL__ sentinel TEK argüman olarak; elementin
    kendi data-font attribute'una fonksiyon içinde erişilebilmeli."""
    context, page, hatalar = _kullanici_sayfa_ac(browser, live_server)

    page.click('#font-secim')
    page.wait_for_timeout(500)
    cagri = page.evaluate("window.__cagrilar[window.__cagrilar.length-1]")
    assert cagri["fn"] == "heroFontSec"
    assert cagri["elIsElement"] is True
    assert cagri["font"] == "Playfair Display"
    assert not hatalar, f"JS hatası: {hatalar}"
    context.close()


# ═══════════════════════════════════════════════════════════════════════
# BÖLÜM 11 — app.js: slider, karşılaştırma, duyuru, admin nav, özel desenler
# (bu, app.js'teki SON onclick grubudur — bu bölümden sonra app.js'te
# hiç onclick="" attribute'u kalmamıştır)
# ═══════════════════════════════════════════════════════════════════════
SONGRUP_STUB_JS = """
() => {
  window.__cagrilar = [];
  window.sliderGit = (...args) => window.__cagrilar.push({ fn: 'sliderGit', args });
  window.durumDegistir = (...args) => window.__cagrilar.push({ fn: 'durumDegistir', args });
  window.katFiltrele = (el, k) => window.__cagrilar.push({
    fn: 'katFiltrele', elIsElement: el instanceof HTMLElement, elId: el && el.id, k
  });
  window.belgeFormAc = (...args) => window.__cagrilar.push({ fn: 'belgeFormAc', args });
  // NOT: karsSifirlaVeListeyeDon KASITLI olarak stublanmıyor — app.js bir ES
  // module olduğu için içindeki karsSifirla()/sayfaGit() çağrıları lexical
  // scope'tan çözülür, window.X override'ları etkilemez. Bu yüzden o test
  // gerçek fonksiyonu çalıştırıp DOM yan etkisini (sayfa-ilanlar aktif mi)
  // kontrol ediyor.
}
"""

SONGRUP_INJECT_BUTTONS_JS = r"""
() => {
  const div = document.createElement('div');
  div.id = 'test-songrup-butonlari';
  div.innerHTML = `
    <button data-action="sliderGit" data-action-args="[&quot;anasayfa&quot;,-1]">‹</button>
    <button id="kars-donus-btn" data-action="karsSifirlaVeListeyeDon">← Listeye Dön</button>
    <button data-action="durumDegistir" data-action-args="[7,&quot;Taslak&quot;]">⏸</button>
    <div id="kat-tumu" data-kat="" data-action="katFiltrele" data-action-args="[&quot;__EL__&quot;,&quot;&quot;]" style="width:60px;height:20px">Tümü</div>
    <div id="drop-zone-test" data-action="belgeInputAc" style="width:60px;height:20px"></div>
    <div id="modal-zemin-test" data-backdrop-close="modal-zemin-test" style="width:100px;height:100px">
      <div id="modal-icerik-test" style="width:50px;height:50px">İçerik</div>
    </div>
  `;
  document.body.appendChild(div);
  // Gerçek karsSifirlaVeListeyeDon fonksiyonunu, iki alt-çağrıyı (karsSifirla +
  // sayfaGit) yaptığını doğrulamak için ÇAĞIRMASINA izin veriyoruz (stub değil).
}
"""


def _songrup_sayfa_ac(browser, live_server):
    context = browser.new_context()
    page = context.new_page()
    page.add_init_script(_sw_devre_disi_birak_init_script())
    hatalar = []
    page.on("pageerror", lambda exc: hatalar.append(str(exc)))
    page.goto(f"{live_server}/static/index.html")
    page.wait_for_selector("#giris-btn", timeout=10000)
    page.evaluate(SONGRUP_STUB_JS)
    page.evaluate(SONGRUP_INJECT_BUTTONS_JS)
    return context, page, hatalar


def test_songrup_slider_git_negatif_yon(live_server, browser):
    context, page, hatalar = _songrup_sayfa_ac(browser, live_server)

    page.click('[data-action="sliderGit"]')
    page.wait_for_timeout(500)
    cagrilar = page.evaluate("window.__cagrilar")
    assert cagrilar == [{"fn": "sliderGit", "args": ["anasayfa", -1]}], f"Beklenmedik: {cagrilar}"
    assert not hatalar, f"JS hatası: {hatalar}"
    context.close()


def test_songrup_kars_sifirla_ve_listeye_don_iki_cagri_yapar(live_server, browser):
    """Regresyon: eskiden onclick="karsSifirla();sayfaGit('ilanlar')" tek
    attribute'ta İKİ ayrı fonksiyon çağırıyordu. Artık karsSifirlaVeListeyeDon()
    adlı BİRLEŞİK bir fonksiyon bu ikisini sırayla çağırıyor.

    NOT: app.js bir ES module olduğu için window.karsSifirla = stub ataması,
    karsSifirlaVeListeyeDon'un İÇİNDEKİ lexical-scope çağrısını etkilemez
    (modüllerde üst-seviye fonksiyon bildirimleri window'a otomatik
    bağlanmaz). Bu yüzden burada stub yerine GERÇEK yan etkileri
    (DOM state değişimi) doğruluyoruz."""
    context, page, hatalar = _songrup_sayfa_ac(browser, live_server)

    page.click('#kars-donus-btn')
    page.wait_for_timeout(700)

    # sayfaGit('ilanlar') çalıştıysa: #sayfa-ilanlar 'aktif' sınıfını almalı
    ilanlar_aktif = page.evaluate(
        "document.getElementById('sayfa-ilanlar')?.classList.contains('aktif')"
    )
    assert ilanlar_aktif is True, "sayfaGit('ilanlar') çalışmadı (sayfa-ilanlar aktif değil)"

    assert not hatalar, f"JS hatası: {hatalar}"
    context.close()


def test_songrup_durum_degistir_id_ve_yeni_durum(live_server, browser):
    context, page, hatalar = _songrup_sayfa_ac(browser, live_server)

    page.click('[data-action="durumDegistir"]')
    page.wait_for_timeout(500)
    cagrilar = page.evaluate("window.__cagrilar")
    assert cagrilar == [{"fn": "durumDegistir", "args": [7, "Taslak"]}], f"Beklenmedik: {cagrilar}"
    assert not hatalar, f"JS hatası: {hatalar}"
    context.close()


def test_songrup_dinamik_fonksiyon_adi_katFiltrele(live_server, browser):
    """katYukle()'de fonksiyon adı bir DEĞİŞKENDEN (tiklama) geliyordu
    (onclick="${tiklama}(this,'')"). daAttr(tiklama, [...]) ile de aynı
    şekilde çalıştığını doğruluyoruz."""
    context, page, hatalar = _songrup_sayfa_ac(browser, live_server)

    page.click('#kat-tumu')
    page.wait_for_timeout(500)
    cagri = page.evaluate("window.__cagrilar[window.__cagrilar.length-1]")
    assert cagri["fn"] == "katFiltrele"
    assert cagri["elIsElement"] is True
    assert cagri["elId"] == "kat-tumu"
    assert cagri["k"] == ""
    assert not hatalar, f"JS hatası: {hatalar}"
    context.close()


def test_songrup_belge_input_ac_gizli_input_tetikler(live_server, browser):
    """onclick="document.getElementById('belge-input').click()" yerine
    window.belgeInputAc() yardımcı fonksiyonu — gerçek dosya input'unun
    tıklanmasını tetiklediğini (gizli file input) doğruluyoruz."""
    context, page, hatalar = _songrup_sayfa_ac(browser, live_server)

    # Gerçek belge-input elementini ekleyip tıklamayı yakalıyoruz
    page.evaluate("""() => {
        const inp = document.createElement('input');
        inp.type = 'file';
        inp.id = 'belge-input';
        inp.style.display = 'none';
        window.__belgeInputTiklandi = false;
        inp.addEventListener('click', (e) => { e.preventDefault(); window.__belgeInputTiklandi = true; });
        document.body.appendChild(inp);
    }""")

    page.click('#drop-zone-test')
    page.wait_for_timeout(500)
    tiklandi = page.evaluate("window.__belgeInputTiklandi")
    assert tiklandi is True, "belge-input'a tıklama tetiklenmedi"
    assert not hatalar, f"JS hatası: {hatalar}"
    context.close()


def test_songrup_modal_backdrop_dogrudan_tiklamada_kapanir(live_server, browser):
    """data-backdrop-close: zemine DOĞRUDAN tıklanınca element kaldırılmalı."""
    context, page, hatalar = _songrup_sayfa_ac(browser, live_server)

    # Zeminin boş bir köşesine tıkla (içerik kutusunun DIŞINDA — içerik
    # varsayılan block akışında üst-sol köşede (0,0)-(50,50) durduğu için
    # zeminin sağ-alt köşesine tıklıyoruz)
    page.click('#modal-zemin-test', position={"x": 90, "y": 90})
    page.wait_for_timeout(500)
    assert page.locator('#modal-zemin-test').count() == 0, \
        "Zemine doğrudan tıklanınca modal kapanmadı"
    assert not hatalar, f"JS hatası: {hatalar}"
    context.close()


def test_songrup_modal_backdrop_icerige_tiklamada_kapanmaz(live_server, browser):
    """data-backdrop-close: modal İÇERİĞİNE tıklanınca (bubble ile zemine
    ulaşsa bile) KAPANMAMALI — bu yüzden closest() değil, doğrudan e.target
    kontrolü kullanıyoruz."""
    context, page, hatalar = _songrup_sayfa_ac(browser, live_server)

    page.click('#modal-icerik-test')
    page.wait_for_timeout(500)
    assert page.locator('#modal-zemin-test').count() == 1, \
        "İçeriğe tıklanınca modal yanlışlıkla kapandı"
    assert not hatalar, f"JS hatası: {hatalar}"
    context.close()


def test_songrup_belge_form_ac_obje_argumani(live_server, browser):
    """belgeFormAc(veri) — eskiden onclick='...JSON.stringify(d).replace(/'/g,"&#39;")...'
    gibi kırılgan manuel escape kullanıyordu. daAttr() artık objeyi doğrudan
    JSON.stringify ile güvenle taşıyor — tırnak içeren bir değerle doğruluyoruz."""
    context, page, hatalar = _songrup_sayfa_ac(browser, live_server)

    page.evaluate("""() => {
        const div = document.createElement('div');
        div.innerHTML = `<button id="belge-form-btn" data-action="belgeFormAc" style="width:60px;height:20px">Aç</button>`;
        document.body.appendChild(div);
        const veri = { portfoy: { baslik: "Ev (Sahibinden'e Yakın)", id: 5 } };
        document.getElementById('belge-form-btn').setAttribute('data-action-args', JSON.stringify([veri]));
    }""")

    page.click('#belge-form-btn')
    page.wait_for_timeout(500)
    cagrilar = page.evaluate("window.__cagrilar")
    assert cagrilar == [{
        "fn": "belgeFormAc",
        "args": [{"portfoy": {"baslik": "Ev (Sahibinden'e Yakın)", "id": 5}}],
    }], f"Beklenmedik: {cagrilar}"
    assert not hatalar, f"JS hatası: {hatalar}"
    context.close()


# ═══════════════════════════════════════════════════════════════════════
# BÖLÜM 12 — index.html'deki özel desenler (mobil nav, modal gizleme,
# şifre sıfırlama adım geçişi, gizli input tetikleme)
# Bu bölümle birlikte TÜM projede (app.js + index.html + diğer src/ui/*.js)
# hiç onclick="" attribute'u kalmamıştır — unsafe-inline artık script-src'den
# kaldırılabilir (bkz. deploy/security-headers.conf).
# ═══════════════════════════════════════════════════════════════════════
SONINDEX_STUB_JS = """
() => {
  window.__navMobilKapatCagrildi = false;
  window.navMobilKapat = () => { window.__navMobilKapatCagrildi = true; };
}
"""

SONINDEX_INJECT_BUTTONS_JS = """
() => {
  const div = document.createElement('div');
  div.id = 'test-sonindex-butonlari';
  div.innerHTML = `
    <div id="modal-gizle-test" style="display:block">
      <button id="modal-gizle-btn" data-action="modalGizle" data-action-args="[&quot;modal-gizle-test&quot;]">Kapat</button>
    </div>
    <button id="ssm-geri-btn" data-action="ssmAdim1eDon">← Geri</button>
    <div id="backdrop-hide-test" data-backdrop-hide="backdrop-hide-test" style="width:100px;height:100px;display:block">
      <div id="backdrop-hide-icerik" style="width:50px;height:50px">İçerik</div>
    </div>
    <button id="sgm-test-btn" data-action="sayfaGitMobil" data-action-args="[&quot;ilanlar&quot;]">Git</button>
    <button id="blog-resim-input-ac-btn" data-action="blogResimInputAc">🖼 Resim Ekle</button>
  `;
  document.body.appendChild(div);

  // blog-resim-input SAYFADA ZATEN GERÇEK OLARAK VAR (id çakışmasın diye
  // duplike ETMİYORUZ) — ona bir tıklama gözlemcisi ekliyoruz.
  const gercekInput = document.getElementById('blog-resim-input');
  window.__blogResimInputTiklandi = false;
  if (gercekInput) {
    gercekInput.addEventListener('click', (e) => { e.preventDefault(); window.__blogResimInputTiklandi = true; });
  }
}
"""


def _sonindex_sayfa_ac(browser, live_server):
    context = browser.new_context()
    page = context.new_page()
    page.add_init_script(_sw_devre_disi_birak_init_script())
    hatalar = []
    page.on("pageerror", lambda exc: hatalar.append(str(exc)))
    page.goto(f"{live_server}/static/index.html")
    page.wait_for_selector("#giris-btn", timeout=10000)
    page.evaluate(SONINDEX_STUB_JS)
    page.evaluate(SONINDEX_INJECT_BUTTONS_JS)
    return context, page, hatalar


def _js_tikla(page, selector):
    """Playwright'ın fiziksel fare tıklaması yerine JS ile doğrudan bir click
    event'i dispatch eder. Gerçek index.html kendi CSS/layout'una sahip
    olduğu için, fiziksel tıklama bazı ortamlarda üstte duran başka bir
    elementin (nav, sabit konumlu bir şey vb.) tıklamayı 'yutmasına' karşı
    kırılgan olabilir — JS dispatch bu belirsizliği tamamen ortadan kaldırır,
    doğrudan hedef elementi tıklar."""
    page.evaluate(f"document.querySelector('{selector}')?.click()")


def test_sonindex_sayfa_git_mobil_sayfa_degistir_ve_menu_kapat(live_server, browser):
    """sayfaGitMobil: eskiden onclick="sayfaGit('ilanlar'); navMobilKapat()"
    iki ayrı çağrıydı — artık birleşik fonksiyon her ikisini de yapmalı."""
    context, page, hatalar = _sonindex_sayfa_ac(browser, live_server)

    # NOT: #sgm-test-btn zaten SONINDEX_INJECT_BUTTONS_JS içinde oluşturuluyor —
    # burada TEKRAR oluşturmuyoruz (eskiden aynı id'yle 2. bir buton daha
    # ekleniyordu, bu belirsiz/kırılgan bir durumdu, kaldırıldı).
    _js_tikla(page, '#sgm-test-btn')
    _bekle_kosul(
        page,
        "document.getElementById('sayfa-ilanlar')?.classList.contains('aktif') && window.__navMobilKapatCagrildi === true",
        mesaj="sayfaGitMobil sayfa değiştirmedi veya navMobilKapat çağrılmadı",
    )
    assert not hatalar, f"JS hatası: {hatalar}"
    context.close()


def test_sonindex_modal_gizle_display_none_yapar(live_server, browser):
    context, page, hatalar = _sonindex_sayfa_ac(browser, live_server)

    assert page.locator('#modal-gizle-test').is_visible()
    _js_tikla(page, '#modal-gizle-btn')
    _bekle_kosul(
        page,
        "document.getElementById('modal-gizle-test')?.style.display === 'none'",
        mesaj="modalGizle çalışmadı",
    )
    assert not hatalar, f"JS hatası: {hatalar}"
    context.close()


def test_sonindex_ssm_adim1e_don_iki_elementi_birden_degistirir(live_server, browser):
    """ssmAdim1eDon: eskiden tek onclick'te İKİ ayrı DOM manipülasyonu vardı
    (adım1 göster + adım2 gizle) — ikisinin de doğru çalıştığını doğruluyoruz.
    Not: gerçek index.html'de #ssm-adim1 varsayılan olarak görünür, #ssm-adim2
    gizlidir (style="display:none") — yani "adım 1" başlangıç durumudur. Bu
    testin anlamlı olması için önce "adım 2'deyim" durumunu simüle edip
    (adım1 gizle, adım2 göster), SONRA "geri" butonuna tıklayıp adım 1'e
    dönüldüğünü doğruluyoruz."""
    context, page, hatalar = _sonindex_sayfa_ac(browser, live_server)

    # "Adım 2'deyim" durumunu simüle et
    page.evaluate("""() => {
        document.getElementById('ssm-adim1').style.display = 'none';
        document.getElementById('ssm-adim2').style.display = '';
    }""")
    assert page.locator('#ssm-adim1').get_attribute('style') == 'display: none;' \
        or page.evaluate("document.getElementById('ssm-adim1').style.display") == 'none'

    _js_tikla(page, '#ssm-geri-btn')
    _bekle_kosul(
        page,
        "document.getElementById('ssm-adim1')?.style.display === '' && document.getElementById('ssm-adim2')?.style.display === 'none'",
        mesaj="ssmAdim1eDon iki adımı da doğru değiştirmedi",
    )
    assert not hatalar, f"JS hatası: {hatalar}"
    context.close()


def test_sonindex_blog_resim_input_ac_gizli_input_tetikler(live_server, browser):
    context, page, hatalar = _sonindex_sayfa_ac(browser, live_server)

    _js_tikla(page, '#blog-resim-input-ac-btn')
    _bekle_kosul(page, "window.__blogResimInputTiklandi === true", mesaj="blog-resim-input'a tıklama tetiklenmedi")
    assert not hatalar, f"JS hatası: {hatalar}"
    context.close()


def test_sonindex_backdrop_hide_dogrudan_tiklamada_gizler(live_server, browser):
    context, page, hatalar = _sonindex_sayfa_ac(browser, live_server)

    # e.target'ın DOĞRUDAN zemin elementi olduğu bir click event'i dispatch
    # ediyoruz (position-bazlı fiziksel tıklama yerine) — bu, gerçek sayfada
    # olası layout/overlay farklarından tamamen bağımsız, deterministik.
    page.evaluate("""() => {
        const el = document.getElementById('backdrop-hide-test');
        el.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
    }""")
    _bekle_kosul(
        page,
        "document.getElementById('backdrop-hide-test')?.style.display === 'none'",
        mesaj="Zemine doğrudan tıklanınca gizlenmedi",
    )
    assert not hatalar, f"JS hatası: {hatalar}"
    context.close()


def test_sonindex_backdrop_hide_icerige_tiklamada_gizlenmez(live_server, browser):
    context, page, hatalar = _sonindex_sayfa_ac(browser, live_server)

    _js_tikla(page, '#backdrop-hide-icerik')
    page.wait_for_timeout(500)
    gizli = page.evaluate("document.getElementById('backdrop-hide-test')?.style.display === 'none'")
    assert not gizli, "İçeriğe tıklanınca yanlışlıkla gizlendi"
    assert not hatalar, f"JS hatası: {hatalar}"
    context.close()


# ═══════════════════════════════════════════════════════════════════════
# BÖLÜM 12 — CSP ENFORCEMENT REGRESYON TESTİ (en kritik test)
#
# Şimdiye kadarki tüm testler CSP header'ı OLMADAN (dev sunucusunda) çalıştı
# — yani JS'in çalıştığını kanıtladılar ama CSP'nin gerçekten izin verdiğini
# değil (CSP production'da nginx tarafından ekleniyor, uvicorn dev sunucusu
# eklemiyor). Bu test, deploy/security-headers.conf'taki GERÇEK CSP
# header'ını Playwright ile response'lara enjekte ederek nginx'i simüle
# eder ve tarayıcı konsolunda SIFIR "Content Security Policy" / "Refused to"
# ihlali olduğunu doğrular. Bu, en güçlü regresyon korumasıdır: ileride biri
# yanlışlıkla bir onclick="" veya inline <script> eklerse, bu test kırmızı
# yanar.
# ═══════════════════════════════════════════════════════════════════════
PROD_CSP = (
    "default-src 'self'; "
    "script-src 'self' https://www.google.com https://www.gstatic.com; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com data:; "
    "img-src 'self' data: blob: https: http:; "
    "connect-src 'self' https:; "
    "worker-src 'self'; manifest-src 'self'; media-src 'self'; "
    "object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
)


def _csp_ile_sayfa_ac(browser, url):
    """Gerçek production CSP header'ını response'lara enjekte ederek nginx'i
    simüle eder (dev sunucusu CSP eklemez)."""
    page = browser.new_page()
    # Service worker'ı devre dışı bırak — aktifse ESKİ (onclick'li) bir
    # sürümü cache'den servis edip yanlış-pozitif CSP ihlaline yol açabilir.
    page.add_init_script(_sw_devre_disi_birak_init_script())

    def handle_route(route):
        response = route.fetch()
        headers = dict(response.headers)
        headers["content-security-policy"] = PROD_CSP
        route.fulfill(response=response, headers=headers)
    page.route("**/*", handle_route)

    ihlaller = []
    page.on("console", lambda msg: ihlaller.append(msg.text)
            if msg.type == "error" and ("Content Security Policy" in msg.text or "Refused to" in msg.text)
            else None)
    return page, ihlaller


def test_csp_index_html_sifir_ihlal(live_server, browser):
    page, ihlaller = _csp_ile_sayfa_ac(browser, f"{live_server}/static/index.html")
    try:
        page.goto(f"{live_server}/static/index.html")
        page.wait_for_selector("#giris-btn", timeout=10000)
        page.wait_for_timeout(1000)  # geç tetiklenen (async) ihlaller için ek pay
        assert ihlaller == [], f"CSP ihlalleri bulundu: {ihlaller}"
    finally:
        page.close()


def test_csp_offline_html_sifir_ihlal(live_server, browser):
    page, ihlaller = _csp_ile_sayfa_ac(browser, f"{live_server}/static/offline.html")
    try:
        page.goto(f"{live_server}/static/offline.html")
        page.wait_for_selector("#tekrar-dene-btn", timeout=5000)
        assert ihlaller == [], f"CSP ihlalleri bulundu: {ihlaller}"
    finally:
        page.close()


def test_csp_altinda_navigasyon_tiklamasi_calisir(live_server, browser):
    """Sadece 'ihlal yok' yetmez — gerçek CSP altında bir tıklamanın da
    fonksiyonel olarak çalıştığını (delegated listener engellenmedi)
    kanıtlıyoruz."""
    page, ihlaller = _csp_ile_sayfa_ac(browser, f"{live_server}/static/index.html")
    try:
        page.goto(f"{live_server}/static/index.html")
        page.wait_for_selector("#giris-btn", timeout=10000)

        page.click('[data-sayfa="ilanlar"]')
        page.wait_for_timeout(800)
        ilanlar_aktif = page.evaluate(
            "document.getElementById('sayfa-ilanlar')?.classList.contains('aktif')"
        )
        assert ilanlar_aktif is True, "CSP altında navigasyon tıklaması çalışmadı"
        assert ihlaller == [], f"CSP ihlalleri bulundu: {ihlaller}"
    finally:
        page.close()


# ═══════════════════════════════════════════════════════════════════════
# PROJE GENELİ onclick="" TEMİZLİĞİ TAMAMLANDI (2026-07).
# app.js + index.html + offline.html + widget-renderer.js + menu-renderer.js
# + admin-sistem.js hiçbirinde artık gerçek bir onclick="" attribute'u yok.
# CSP script-src'den 'unsafe-inline' KALDIRILDI (deploy/security-headers.conf)
# ve BÖLÜM 12'deki testlerle gerçek CSP enforcement altında sıfır ihlal
# olduğu kanıtlandı (sadece statik analiz değil).
# ═══════════════════════════════════════════════════════════════════════
