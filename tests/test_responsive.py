"""
Responsive cross-device test — tüm cihazlarda görünürlük ve overflow analizi.

Çalıştırma:
    python3 tests/test_responsive.py
"""
import asyncio
import json
import time

try:
    import pytest
except Exception:  # pragma: no cover - pytest dışı kullanım
    pytest = None

try:
    from playwright.async_api import async_playwright
except ModuleNotFoundError:  # pragma: no cover - ortamda opsiyonel bağımlılık
    async_playwright = None

if pytest is not None and __name__ != "__main__":  # pragma: no cover - pytest'te standalone test
    pytestmark = pytest.mark.skip(reason="Standalone responsive script; pytest altında çalıştırılmıyor")

# Test edilecek cihazlar
DEVICES = [
    # (isim,                       width, height, user_agent)
    ("iPhone SE",                    375,  667, "iPhone SE"),
    ("iPhone 13",                   390,  844, "iPhone 13"),
    ("iPhone 15 Pro Max",           430,  932, "iPhone 15 Pro Max"),
    ("Galaxy S22",                  360,  800, "Galaxy S22"),
    ("Galaxy S24 Ultra",            412,  915, "Galaxy S24 Ultra"),
    ("iPad",                        768, 1024, "iPad"),
    ("iPad Pro",                   1024, 1366, "iPad Pro"),
    ("Surface Pro",                1366,  768, "Surface Pro"),
    ("Laptop 1366x768",            1366,  768, "Laptop"),
    ("Desktop 1920x1080",          1920, 1080, "Desktop"),
]

# Test edilecek sayfalar (bölüm seçiciler)
PAGES = [
    ("Anasayfa", "#sayfa-anasayfa"),
    ("İlanlar", "#sayfa-ilanlar"),
    ("Blog", "#sayfa-blog"),
    ("Admin", "#sayfa-admin"),
    ("Giriş", "#sayfa-giris"),
    ("Detay", "#sayfa-detay"),
]

URL = "http://127.0.0.1:8201/"


async def test_device(playwright, name, width, height, ua):
    """Tek cihaz için tüm sayfaları test et."""
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context(
        viewport={"width": width, "height": height},
        user_agent=ua,
        device_scale_factor=2 if "iPhone" in name or "Galaxy" in name else 1,
        is_mobile="iPhone" in name or "Galaxy" in name or "iPad" in name,
        has_touch="iPhone" in name or "Galaxy" in name or "iPad" in name,
    )
    page = await context.new_page()
    
    results = []
    
    for page_name, selector in PAGES:
        try:
            await page.goto(URL, wait_until="domcontentloaded", timeout=12000)
            await page.wait_for_timeout(400)
            
            # Sayfayı aktif et (sayfaGit fonksiyonu varsa)
            if selector != "#sayfa-anasayfa":
                page_arg = selector.replace("#sayfa-", "")
                await page.evaluate(f"if (typeof sayfaGit === 'function') sayfaGit('{page_arg}');")
                await page.wait_for_timeout(500)
            
            # Overflow kontrolü
            overflow_x = await page.evaluate("""
                () => {
                    const b = document.body;
                    return {
                        scrollWidth: b.scrollWidth,
                        clientWidth: b.clientWidth,
                        hasHorizontalScroll: b.scrollWidth > b.clientWidth,
                        overflowAmount: Math.max(0, b.scrollWidth - b.clientWidth),
                    };
                }
            """)
            
            # Navbar kontrolü
            navbar = {
                "hamburger_present": await page.evaluate(
                    "() => !!document.querySelector('.nav-hamburger')"
                ),
                "mobil_panel_present": await page.evaluate(
                    "() => !!document.querySelector('.nav-mobil-panel')"
                ),
                "hamburger_visible": await page.evaluate(
                    """() => {
                        const el = document.querySelector('.nav-hamburger');
                        const st = getComputedStyle(el);
                        return st.display !== 'none' && st.visibility !== 'hidden';
                    }"""
                ),
                "desktop_links_visible": await page.evaluate(
                    """() => {
                        const el = document.querySelector('.nav-links');
                        const st = getComputedStyle(el);
                        return st.display !== 'none';
                    }"""
                ),
            }
            
            # Buton yüksekliği (min 44px)
            btn_height = await page.evaluate("""
                () => {
                    const btns = document.querySelectorAll('.btn, .nav-giris-btn, .nav-cikis-btn, .nav-admin-btn');
                    let minH = 999, count = btns.length;
                    btns.forEach(b => {
                        const h = b.getBoundingClientRect().height;
                        if (h < minH && h > 0) minH = h;
                    });
                    return { min_btn_height: Math.round(minH), btn_count: count };
                }
            """)
            
            # Input genişliği kontrolü
            input_width = await page.evaluate("""
                () => {
                    const inp = document.querySelectorAll('.form-girdi, .hero-arama-input, .filtre-input');
                    let widths = [];
                    inp.forEach(i => {
                        const r = i.getBoundingClientRect();
                        if (r.height > 0) widths.push(Math.round(r.width));
                    });
                    return {
                        count: inp.length,
                        max_width: widths.length ? Math.max(...widths) : 0,
                        min_width: widths.length ? Math.min(...widths) : 0,
                        sample_viewport_width: window.innerWidth,
                    };
                }
            """)
            
            # Font okunabilirlik
            font_check = await page.evaluate("""
                () => {
                    const body = getComputedStyle(document.body);
                    return {
                        body_font_size: parseFloat(body.fontSize),
                        hero_baslik_fs: parseFloat(getComputedStyle(
                            document.querySelector('.hero-baslik') || document.body
                        ).fontSize),
                    };
                }
            """)
            
            # Kart/grid sütun sayısı
            grid_cols = await page.evaluate("""
                () => {
                    const grids = ['.ilan-grid', '.blog-grid', '.stat-grid'];
                    const result = {};
                    grids.forEach(sel => {
                        const g = document.querySelector(sel);
                        if (g) {
                            const st = getComputedStyle(g);
                            const tpl = st.gridTemplateColumns;
                            result[sel] = tpl.split(' ').length;
                        }
                    });
                    return result;
                }
            """)
            
            # Modal geniş kontrolü (varsayılan modal yoksa skip)
            modal = await page.evaluate("""
                () => {
                    const m = document.querySelector('.modal');
                    if (!m) return { present: false };
                    const r = m.getBoundingClientRect();
                    const st = getComputedStyle(m);
                    return {
                        present: true,
                        width_pct: Math.round((r.width / window.innerWidth) * 100),
                        max_width_px: parseInt(st.maxWidth, 10),
                    };
                }
            """)
            
            # Tablo kart dönüşümü
            table_check = await page.evaluate("""
                () => {
                    const t = document.querySelector('table.tablo');
                    if (!t) return { present: false };
                    const thead = t.querySelector('thead');
                    const st = getComputedStyle(thead);
                    return {
                        present: true,
                        thead_hidden: st.display === 'none',
                        has_data_labels: t.querySelectorAll('td[data-label]').length,
                    };
                }
            """)
            
            # Scroll pozisyonu sıfırla
            await page.evaluate("window.scrollTo(0, 0)")
            
            results.append({
                "sayfa": page_name,
                "overflow": {
                    "has_hor_scroll": overflow_x["hasHorizontalScroll"],
                    "overflow_px": overflow_x["overflowAmount"],
                    "scroll_w": overflow_x["scrollWidth"],
                    "client_w": overflow_x["clientWidth"],
                },
                "navbar": navbar,
                "buton": btn_height,
                "input": input_width,
                "font": font_check,
                "grid": grid_cols,
                "modal": modal,
                "tablo": table_check,
                "status": "OK" if not overflow_x["hasHorizontalScroll"] else "TAŞMA",
            })
        except Exception as e:
            results.append({
                "sayfa": page_name,
                "status": f"HATA: {str(e)[:80]}",
            })
    
    await context.close()
    await browser.close()
    return {"cihaz": name, "viewport": f"{width}x{height}", "sayfalar": results}


async def main():
    if async_playwright is None:
        print("playwright kurulu değil; responsive testi atlandı.")
        return []

    print("=" * 78)
    print("RESPONSIVE CROSS-DEVICE TEST RAPORU")
    print("=" * 78)
    print(f"Sunucu: {URL}")
    print(f"Cihaz sayısı: {len(DEVICES)}")
    print(f"Sayfa sayısı: {len(PAGES)}")
    print()
    
    async with async_playwright() as playwright:
        all_results = []
        for name, w, h, ua in DEVICES:
            print(f"  [{name}] {w}x{h} test ediliyor...")
            r = await test_device(playwright, name, w, h, ua)
            all_results.append(r)
    
    # Rapor
    print("\n" + "=" * 78)
    print("RAPOR")
    print("=" * 78)
    for r in all_results:
        print(f"\n{'─' * 78}")
        print(f"📱 {r['cihaz']}  ({r['viewport']})")
        print(f"{'─' * 78}")
        
        for s in r["sayfalar"]:
            page = s.get("sayfa", "")
            status = s.get("status", "")
            
            if "TAŞMA" in status:
                mark = "❌"
            elif "HATA" in status:
                mark = "⚠️"
            else:
                mark = "✅"
            
            print(f"\n  {mark} {page}: {status}")
            
            if "overflow" in s:
                ov = s["overflow"]
                if ov["has_hor_scroll"]:
                    tasma = f"{ov['overflow_px']}px"
                else:
                    tasma = "YOK"
                print(f"     Taşma: {tasma} (scrollW={ov['scroll_w']}, clientW={ov['client_w']})")
            
            if "navbar" in s:
                nb = s["navbar"]
                # Mobil'de hamburger görünür, desktop'ta linkler görünür
                is_mobile = r["viewport"].split("x")[0]
                is_mobile = int(is_mobile) < 768
                if is_mobile:
                    nav_ok = nb["hamburger_visible"] and not nb["desktop_links_visible"]
                    print(f"     Menü: {'✅ hamburger açık, linkler gizli' if nav_ok else '⚠️ ' + json.dumps(nb)}")
                else:
                    nav_ok = nb["desktop_links_visible"] and not nb["hamburger_visible"]
                    print(f"     Menü: {'✅ desktop linkler açık, hamburger gizli' if nav_ok else '⚠️ ' + json.dumps(nb)}")
            
            if "buton" in s:
                b = s["buton"]
                ok = b["min_btn_height"] >= 44 or b["btn_count"] == 0
                print(f"     Buton: {'✅' if ok else '⚠️'} min={b['min_btn_height']}px (44px standart), adet={b['btn_count']}")
            
            if "input" in s and s["input"]["count"] > 0:
                i = s["input"]
                # Mobilde input ~ viewport genişliği (tam genişlik beklenir)
                ratio = (i["max_width"] / i["sample_viewport_width"]) if i["sample_viewport_width"] else 0
                ok_mob = not is_mobile or ratio >= 0.8
                print(f"     Input: {'✅' if ok_mob else '⚠️'} max={i['max_width']}px, vw={i['sample_viewport_width']}px (oran={ratio:.2f})")
            
            if "font" in s:
                f = s["font"]
                ok = f["body_font_size"] >= 14
                print(f"     Font: {'✅' if ok else '⚠️'} body={f['body_font_size']}px, hero={f['hero_baslik_fs']}px")
            
            if "grid" in s and s["grid"]:
                print(f"     Grid: {s['grid']}")
            
            if "modal" in s and s["modal"]["present"]:
                m = s["modal"]
                # Mobilde %95 genişlik beklenebilir
                ok = m["width_pct"] <= 100
                print(f"     Modal: {'✅' if ok else '⚠️'} width={m['width_pct']}% viewport, max_w={m['max_width_px']}px")
    
    # Özet tablo
    print("\n" + "=" * 78)
    print("ÖZET")
    print("=" * 78)
    print(f"{'Cihaz':<25} {'Görüş alanı':<15} {'Taşma':<10} {'Sonuç':<10}")
    print("─" * 78)
    
    total_ok = 0
    total_fail = 0
    for r in all_results:
        cihaz = r["cihaz"]
        vw = r["viewport"]
        any_fail = False
        for s in r["sayfalar"]:
            st = s.get("status", "")
            if "TAŞMA" in st or "HATA" in st:
                any_fail = True
                print(f"{cihaz:<25} {vw:<15} {s['sayfa']:<10} ❌ {st}")
        if any_fail:
            total_fail += 1
            print(f"{cihaz:<25} {vw:<15} {'—':<10} ❌ HATA var")
        else:
            total_ok += 1
            print(f"{cihaz:<25} {vw:<15} {'YOK':<10} ✅ OK")
    
    print("─" * 78)
    print(f"Toplam: {total_ok} OK, {total_fail} HATA")
    print(f"Başarı: {total_ok}/{len(all_results)} = {total_ok*100//len(all_results)}%")
    
    return all_results


if __name__ == "__main__":
    asyncio.run(main())
