"""
Modüler responsive test - sunucuyu kendi başlatır, ölçer, kapatır.
"""
import asyncio
import json
import os
import signal
import subprocess
import sys
import time

PORT = 8283
HOST = "127.0.0.1"
URL = f"http://{HOST}:{PORT}/"

DEVICES = [
    ("iPhone SE",                    375,  667, 2, True),
    ("iPhone 13",                   390,  844, 3, True),
    ("iPhone 15 Pro Max",           430,  932, 3, True),
    ("Galaxy S22",                  360,  800, 3, True),
    ("Galaxy S24 Ultra",            412,  915, 3, True),
    ("iPad",                        768, 1024, 2, True),
    ("iPad Pro",                   1024, 1366, 2, True),
    ("Surface Pro",                1366,  768, 1, False),
    ("Laptop 1366x768",            1366,  768, 1, False),
    ("Desktop 1920x1080",          1920, 1080, 1, False),
]

PAGES = [
    ("Anasayfa", "#sayfa-anasayfa"),
    ("İlanlar", "#sayfa-ilanlar"),
    ("Blog", "#sayfa-blog"),
    ("Admin", "#sayfa-admin"),
    ("Giriş", "#sayfa-giris"),
    ("Detay", "#sayfa-detay"),
]


async def measure_one(playwright, name, w, h, dsf, is_mob):
    from playwright.async_api import async_playwright
    browser = await playwright.chromium.launch(headless=True)
    ctx = await browser.new_context(
        viewport={"width": w, "height": h},
        device_scale_factor=dsf,
        is_mobile=is_mob,
        has_touch=is_mob,
    )
    page = await ctx.new_page()
    out = []
    
    for pn, sel in PAGES:
        try:
            await page.goto(URL, wait_until="domcontentloaded", timeout=10000)
            await page.wait_for_timeout(300)
            
            if sel != "#sayfa-anasayfa":
                arg = sel.replace("#sayfa-", "")
                try:
                    await page.evaluate(f"if (typeof sayfaGit==='function') sayfaGit('{arg}');")
                    await page.wait_for_timeout(300)
                except Exception:
                    pass
            
            ov = await page.evaluate("""() => {
                const b = document.body;
                return {
                    h: b.scrollWidth > b.clientWidth,
                    px: Math.max(0, b.scrollWidth - b.clientWidth),
                    sw: b.scrollWidth,
                    cw: b.clientWidth,
                };
            }""")
            
            nb = await page.evaluate("""() => {
                const h = document.querySelector('.nav-hamburger');
                const l = document.querySelector('.nav-links');
                return {
                    hamb: h ? getComputedStyle(h).display !== 'none' : false,
                    links: l ? getComputedStyle(l).display !== 'none' : false,
                };
            }""")
            
            btn = await page.evaluate("""() => {
                const b = document.querySelectorAll('.btn, .nav-giris-btn, .nav-cikis-btn, .nav-admin-btn');
                let mn = 9999, n = 0;
                b.forEach(x => {
                    const r = x.getBoundingClientRect().height;
                    if (r > 0 && r < mn) mn = r;
                    n++;
                });
                return { mn: Math.round(mn), n };
            }""")
            
            inp = await page.evaluate("""() => {
                const i = document.querySelectorAll('.form-girdi, .hero-arama-input, .filtre-input, .filtre-select');
                let mx = 0, n = 0;
                i.forEach(x => {
                    const r = x.getBoundingClientRect();
                    if (r.height > 0 && r.width > mx) mx = r.width;
                    n++;
                });
                return { mx: Math.round(mx), n, vw: window.innerWidth };
            }""")
            
            fnt = await page.evaluate("""() => {
                return {
                    body: parseFloat(getComputedStyle(document.body).fontSize),
                };
            }""")
            
            grid = await page.evaluate("""() => {
                const sels = ['.ilan-grid', '.blog-grid', '.stat-grid'];
                const r = {};
                sels.forEach(s => {
                    const g = document.querySelector(s);
                    if (g) {
                        const st = getComputedStyle(g);
                        const tpl = st.gridTemplateColumns || '';
                        r[s] = tpl.split(' ').filter(Boolean).length;
                    }
                });
                return r;
            }""")
            
            tab = await page.evaluate("""() => {
                const t = document.querySelector('table.tablo');
                if (!t) return { p: false };
                const thead = t.querySelector('thead');
                return {
                    p: true,
                    th_hidden: thead ? getComputedStyle(thead).display === 'none' : false,
                    dl_count: t.querySelectorAll('td[data-label]').length,
                };
            }""")
            
            mod = await page.evaluate("""() => {
                const m = document.querySelector('.modal');
                if (!m) return { p: false };
                const r = m.getBoundingClientRect();
                return { p: true, w_pct: Math.round(r.width / window.innerWidth * 100) };
            }""")
            
            await page.evaluate("window.scrollTo(0, 0)")
            
            durum = "OK"
            if ov["h"]:
                durum = "TAŞMA"
            
            out.append({
                "sayfa": pn,
                "durum": durum,
                "ov": ov,
                "nb": nb,
                "btn": btn,
                "inp": inp,
                "fnt": fnt,
                "grid": grid,
                "tab": tab,
                "mod": mod,
            })
        except Exception as e:
            out.append({"sayfa": pn, "durum": "HATA", "err": str(e)[:60]})
    
    await ctx.close()
    await browser.close()
    return {"cihaz": name, "vp": f"{w}x{h}", "mob": is_mob, "sayfalar": out}


async def main():
    from playwright.async_api import async_playwright
    
    # Sunucuyu başlat
    print(f"Sunucu başlatılıyor... ({URL})")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app:app",
         "--host", HOST, "--port", str(PORT), "--log-level", "critical"],
        cwd=os.getcwd(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        preexec_fn=os.setsid,
    )
    try:
        # Hazır olmasını bekle
        import urllib.request
        for _ in range(20):
            try:
                urllib.request.urlopen(URL + "health", timeout=2)
                print("Sunucu hazır!")
                break
            except Exception:
                time.sleep(0.5)
        else:
            print("Sunucu başlamadı!")
            return
        
        print("Test başlıyor...\n")
        
        results = []
        async with async_playwright() as p:
            for nm, w, h, dsf, mob in DEVICES:
                print(f"  [{nm}] {w}x{h} ...", end=" ", flush=True)
                try:
                    r = await measure_one(p, nm, w, h, dsf, mob)
                    results.append(r)
                    print("OK")
                except Exception as e:
                    print(f"HATA: {e}")
                    results.append({"cihaz": nm, "vp": f"{w}x{h}", "sayfalar": [], "err": str(e)[:80]})
        
        # Rapor
        print("\n" + "=" * 78)
        print("RESPONSIVE TEST RAPORU")
        print("=" * 78)
        
        for r in results:
            print(f"\n{'─' * 78}")
            print(f"📱 {r['cihaz']}  ({r['vp']})  {'mobil' if r.get('mob') else 'desktop'}")
            print(f"{'─' * 78}")
            is_mob = r.get("mob", False)
            for s in r.get("sayfalar", []):
                pn = s.get("sayfa", "")
                du = s.get("durum", "")
                if "TAŞMA" in du:
                    mk = "❌"
                elif "HATA" in du:
                    mk = "⚠️"
                else:
                    mk = "✅"
                print(f"\n  {mk} {pn}: {du}")
                
                if "ov" in s:
                    o = s["ov"]
                    t = f"{o['px']}px" if o["h"] else "YOK"
                    print(f"     Taşma: {t} (scroll={o['sw']}, client={o['cw']})")
                
                if "nb" in s:
                    n = s["nb"]
                    # Hamburger sadece <768px viewport'ta beklenir
                    vw_px = int(r["vp"].split("x")[0])
                    if vw_px < 768:
                        nav_ok = n["hamb"] and not n["links"]
                        print(f"     Menü: {'✅ hamburger' if nav_ok else '⚠️ '+json.dumps(n)}")
                    else:
                        nav_ok = n["links"] and not n["hamb"]
                        print(f"     Menü: {'✅ linkler (geniş ekran)' if nav_ok else '⚠️ '+json.dumps(n)}")
                
                if "btn" in s and s["btn"]["n"] > 0:
                    b = s["btn"]
                    ok = b["mn"] >= 44 if b["mn"] < 9000 else False
                    print(f"     Buton: {'✅' if ok else '⚠️'} min={b['mn']}px, adet={b['n']}")
                
                if "inp" in s and s["inp"]["n"] > 0:
                    i = s["inp"]
                    rat = round(i["mx"] / i["vw"], 2) if i["vw"] else 0
                    ok = (not is_mob) or rat >= 0.8
                    print(f"     Input: {'✅' if ok else '⚠️'} max={i['mx']}px (vw={i['vw']}, oran={rat})")
                
                if "fnt" in s:
                    f = s["fnt"]
                    ok = f["body"] >= 14
                    print(f"     Font: {'✅' if ok else '⚠️'} body={f['body']}px")
                
                if "grid" in s and s["grid"]:
                    print(f"     Grid: {s['grid']}")
                
                if "tab" in s and s["tab"].get("p"):
                    t = s["tab"]
                    ok = (not is_mob) or t["th_hidden"]
                    print(f"     Tablo: {'✅ kart' if ok else '⚠️'} thead_hidden={t['th_hidden']}, data-labels={t['dl_count']}")
                
                if "mod" in s and s["mod"].get("p"):
                    m = s["mod"]
                    print(f"     Modal: {m['w_pct']}% vw")
        
        # Özet
        print("\n" + "=" * 78)
        print("ÖZET")
        print("=" * 78)
        print(f"{'Cihaz':<25} {'VP':<12} {'Menü':<12} {'Taşma':<12} {'Sonuç':<8}")
        print("─" * 78)
        ok_count = 0
        for r in results:
            nm = r["cihaz"]
            vp = r["vp"]
            vw_px = int(vp.split("x")[0])
            any_tasma = False
            menu_ok = True
            for s in r.get("sayfalar", []):
                if "TAŞMA" in s.get("durum", ""):
                    any_tasma = True
                if "nb" in s:
                    n = s["nb"]
                    if vw_px < 768:
                        if not n["hamb"]:
                            menu_ok = False
                    else:
                        if not n["links"]:
                            menu_ok = False
            status = "✅" if (not any_tasma and menu_ok) else "❌"
            print(f"{nm:<25} {vp:<12} {'✅' if menu_ok else '❌':<12} {'YOK' if not any_tasma else 'VAR':<12} {status:<8}")
            if not any_tasma and menu_ok:
                ok_count += 1
        
        print("─" * 78)
        print(f"Başarı: {ok_count}/{len(results)} ({ok_count*100//max(1,len(results))}%)")
        
        return results
    finally:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())
