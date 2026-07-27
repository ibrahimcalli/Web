"""
app.js — saas / sayfa / sablon / editorEkle gruplarının data-action E2E testi.

Bu gruplardaki onclick="fnAdi(...)" attribute'ları daAttr() ile
data-action/data-action-args'a çevrildi. Dispatch mekanizması zaten
test_app_daattr_e2e.py'de kapsanıyor — burada özellikle bu gruplara özgü
argüman şekillerini (çok satırlı string, tek tırnak içeren HTML, null id,
iki elementli sıralama argümanları) doğru taşındığını kanıtlıyoruz.
"""
import pytest

playwright_sync_api = pytest.importorskip("playwright.sync_api")
sync_playwright = playwright_sync_api.sync_playwright

STUB_JS = """
() => {
  window.__cagrilar = [];
  window.saasTenantSil = (...args) => window.__cagrilar.push({ fn: 'saasTenantSil', args });
  window.sayfaKaydet = (...args) => window.__cagrilar.push({ fn: 'sayfaKaydet', args });
  window.sablonBolumTasi = (...args) => window.__cagrilar.push({ fn: 'sablonBolumTasi', args });
  window.editorEkle = (...args) => window.__cagrilar.push({ fn: 'editorEkle', args });
  window.sayfaEditorEkle = (...args) => window.__cagrilar.push({ fn: 'sayfaEditorEkle', args });
}
"""

INJECT_BUTTONS_JS = r"""
() => {
  const div = document.createElement('div');
  div.id = 'test-yeni-daattr-butonlari';
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


def test_saas_tenant_sil_confirm_kabul(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _sayfa_ac(browser, live_server)
        page.on("dialog", lambda d: d.accept())

        page.click('[data-action="saasTenantSil"]')
        page.wait_for_timeout(150)
        cagrilar = page.evaluate("window.__cagrilar")
        assert cagrilar == [{"fn": "saasTenantSil", "args": [5]}], f"Beklenmedik: {cagrilar}"
        assert not hatalar, f"JS hatası: {hatalar}"
        context.close()
        browser.close()


def test_sayfa_kaydet_null_id(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _sayfa_ac(browser, live_server)

        page.click('[data-action="sayfaKaydet"]')
        page.wait_for_timeout(150)
        cagrilar = page.evaluate("window.__cagrilar")
        assert cagrilar == [{"fn": "sayfaKaydet", "args": [None]}], f"Beklenmedik: {cagrilar}"
        assert not hatalar, f"JS hatası: {hatalar}"
        context.close()
        browser.close()


def test_sablon_bolum_tasi_iki_id(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _sayfa_ac(browser, live_server)

        page.click('[data-action="sablonBolumTasi"]')
        page.wait_for_timeout(150)
        cagrilar = page.evaluate("window.__cagrilar")
        assert cagrilar == [{"fn": "sablonBolumTasi", "args": [3, 7]}], f"Beklenmedik: {cagrilar}"
        assert not hatalar, f"JS hatası: {hatalar}"
        context.close()
        browser.close()


def test_editor_ekle_cok_satirli_string(live_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _sayfa_ac(browser, live_server)

        page.click('[data-action="editorEkle"]')
        page.wait_for_timeout(150)
        cagrilar = page.evaluate("window.__cagrilar")
        assert cagrilar == [{"fn": "editorEkle", "args": ["\n## ", ""]}], f"Beklenmedik: {cagrilar}"
        assert not hatalar, f"JS hatası: {hatalar}"
        context.close()
        browser.close()


def test_sayfa_editor_ekle_tek_tirnakli_html(live_server):
    """Tek tırnak İÇEREN bir HTML string (<a href='' ...>) doğru taşınmalı — bu, orijinal
    kodda kırılgan manuel escape'e ihtiyaç duyan tam senaryo."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context, page, hatalar = _sayfa_ac(browser, live_server)

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
