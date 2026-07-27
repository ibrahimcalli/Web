"""
admin-sistem.js — data-action / data-copy delegated click handler E2E testi.

onclick="fnAdi(...)" ve onclick="navigator.clipboard.writeText(...)" gibi
attribute'lardan data-action / data-copy-text / data-copy-target + tek bir
delegated addEventListener'a geçişin (CSP uyumu için) gerçek tarayıcıda
doğru çalıştığını kanıtlar. İş mantığı fonksiyonları (sistemLogYukle vb.)
zaten backend testlerinde (tests/test_cms_system.py) kapsanıyor — burada
sadece delegation mekanizması test ediliyor.

NOT: app.js baslat() gerçek SPA DOM'unu bekliyor. Bare-bones bir fixture
yerine GERÇEK index.html'i yüklüyoruz (test_app_banner_e2e.py ile aynı
yöntem) — böylece app.js kendi doğal ortamında hatasız çalışırken sadece
bizim test butonlarımızı test ediyoruz.
"""
import pytest

playwright_sync_api = pytest.importorskip("playwright.sync_api")
sync_playwright = playwright_sync_api.sync_playwright

STUB_JS = """
() => {
  window.__cagrilar = [];
  window.sistemLogYukle = (...args) => window.__cagrilar.push({ fn: 'sistemLogYukle', args });
  window.sistemAiTanilamaIndir = (...args) => window.__cagrilar.push({ fn: 'sistemAiTanilamaIndir', args });
}
"""

INJECT_BUTTONS_JS = """
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


def _sayfa_ac(browser, live_server):
    context = browser.new_context()
    context.grant_permissions(["clipboard-read", "clipboard-write"])
    page = context.new_page()
    # Service worker'ı devre dışı bırak — aktifse sayfa yeniden yükleyip
    # app.js'i 2. kez çalıştırabiliyor (test izolasyonu için).
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


def test_data_action_argumanli_cagri(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _sayfa_ac(browser, live_server)

        page.click('[data-action="sistemLogYukle"]')
        page.wait_for_timeout(200)

        cagrilar = page.evaluate("window.__cagrilar")
        assert cagrilar == [{"fn": "sistemLogYukle", "args": ["error"]}], f"Yanlış çağrı: {cagrilar}"
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
        assert cagrilar == [{"fn": "sistemAiTanilamaIndir", "args": []}], f"Yanlış çağrı: {cagrilar}"
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

        page.wait_for_timeout(400)
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
