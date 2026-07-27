"""
app.js — daAttr() / delegated data-action mekanizması E2E testi (genel).

onclick="fnAdi(...)" attribute'larından daAttr() ile üretilen
data-action / data-action-args / data-confirm + tek bir delegated
addEventListener'a geçişin (CSP uyumu için) gerçek tarayıcıda doğru
çalıştığını kanıtlar. Bu, wizard/tema/widget gruplarının hepsinin
kullandığı ORTAK mekanizmayı test eder (iş mantığı fonksiyonlarının
kendisi değil — onlar backend testlerinde kapsanıyor).

GERÇEK index.html yüklenir (test_app_banner_e2e.py ile aynı yöntem),
üzerine test butonları enjekte edilir — app.js kendi doğal ortamında
hatasız çalışır.

Kapsanan senaryolar:
  1. Argümansız çağrı (wizardAdim1)
  2. String argümanlı çağrı (wizardAdim2)
  3. '__EL__' sentinel — tıklanan elementin kendisini argüman olarak geçirme (temaUygula)
  4. data-confirm reddedilirse fonksiyon ÇAĞRILMAMALI
  5. data-confirm kabul edilirse fonksiyon çağrılmalı
  6. null argüman doğru taşınmalı (widgetKaydet(id||null) deseni)
  7. Regresyon: app.js'in listener'ı SADECE BİR KEZ tetiklenmeli (admin-sistem.js
     ile çakışma hatası burada yakalandı ve düzeltildi)
"""
import pytest

playwright_sync_api = pytest.importorskip("playwright.sync_api")
sync_playwright = playwright_sync_api.sync_playwright

STUB_JS = """
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

INJECT_BUTTONS_JS = """
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


def _sayfa_ac(browser, live_server):
    context = browser.new_context()
    page = context.new_page()
    page.add_init_script("""
        Object.defineProperty(navigator, 'serviceWorker', {
            value: { register: () => Promise.resolve({ addEventListener(){}, update: () => Promise.resolve() }),
                     addEventListener(){}, getRegistrations: () => Promise.resolve([]) },
            configurable: true
        });
    """)
    hatalar = []
    page.on("pageerror", lambda exc: hatalar.append(str(exc)))
    page.goto(f"{live_server}/static/index.html")
    page.wait_for_load_state("networkidle")
    page.evaluate(STUB_JS)
    page.evaluate(INJECT_BUTTONS_JS)
    return context, page, hatalar


def test_argumansiz_cagri(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _sayfa_ac(browser, live_server)

        page.click('[data-action="wizardAdim1"]')
        page.wait_for_timeout(150)
        cagrilar = page.evaluate("window.__cagrilar")
        assert cagrilar == [{"fn": "wizardAdim1", "args": []}], f"Beklenmedik: {cagrilar}"
        assert not hatalar, f"JS hatası: {hatalar}"
        context.close()
        browser.close()


def test_string_argumanli_cagri(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _sayfa_ac(browser, live_server)

        page.click('[data-action="wizardAdim2"]')
        page.wait_for_timeout(150)
        cagrilar = page.evaluate("window.__cagrilar")
        assert cagrilar == [{"fn": "wizardAdim2", "args": ["emlak"]}], f"Beklenmedik: {cagrilar}"
        assert not hatalar, f"JS hatası: {hatalar}"
        context.close()
        browser.close()


def test_el_sentinel_tiklanan_elementi_gecirir(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _sayfa_ac(browser, live_server)

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


def test_confirm_reddedilirse_fonksiyon_cagrilmaz(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _sayfa_ac(browser, live_server)
        page.on("dialog", lambda d: d.dismiss())

        onceki = page.evaluate("window.__cagrilar.length")
        page.click('[data-action="bannerSilTest"]')
        page.wait_for_timeout(150)
        sonraki = page.evaluate("window.__cagrilar.length")

        assert sonraki == onceki, "confirm() reddedildiği halde fonksiyon çağrıldı!"
        assert not hatalar, f"JS hatası: {hatalar}"
        context.close()
        browser.close()


def test_confirm_kabul_edilirse_fonksiyon_cagrilir(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _sayfa_ac(browser, live_server)
        page.on("dialog", lambda d: d.accept())

        page.click('[data-action="bannerSilTest"]')
        page.wait_for_timeout(150)
        cagrilar = page.evaluate("window.__cagrilar")
        assert cagrilar == [{"fn": "bannerSilTest", "args": []}], \
            f"confirm() kabul edildiği halde beklenmedik çağrı listesi: {cagrilar}"
        assert not hatalar, f"JS hatası: {hatalar}"
        context.close()
        browser.close()


def test_null_argumani_dogru_tasinir(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _sayfa_ac(browser, live_server)

        page.click('[data-action="widgetKaydetTest"]')
        page.wait_for_timeout(150)
        cagri = page.evaluate("window.__cagrilar[window.__cagrilar.length-1]")
        assert cagri == {"fn": "widgetKaydetTest", "args": [None]}, f"Beklenmedik: {cagri}"
        assert not hatalar, f"JS hatası: {hatalar}"
        context.close()
        browser.close()


def test_listener_tek_sefer_tetiklenir(live_server):
    """
    Regresyon: admin-sistem.js'in KENDİ data-action listener'ı app.js'inkiyle
    çakışıp aynı tıklamada fonksiyonu 2 KEZ çağırıyordu. Bu hata yakalanıp
    admin-sistem.js'ten çakışan listener kaldırıldı. Bu test bunu kalıcı
    olarak korur.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _sayfa_ac(browser, live_server)

        page.click('[data-action="wizardAdim1"]')
        page.wait_for_timeout(150)
        cagrilar = page.evaluate("window.__cagrilar")
        assert len(cagrilar) == 1, \
            f"wizardAdim1 tam olarak 1 kez çağrılmalıydı, {len(cagrilar)} kez çağrıldı: {cagrilar}"
        assert not hatalar, f"JS hatası: {hatalar}"
        context.close()
        browser.close()
