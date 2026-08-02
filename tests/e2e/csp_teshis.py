"""
CSP ihlalinin TAM KAYNAĞINI (dosya + satır) bulmak için bağımsız teşhis scripti.
pytest'in özet çıktısı mesajı kısaltıyor, bu script tam detayı basar.

Çalıştırma:
    cd emlak_web
    python3 tests/e2e/csp_teshis.py
"""
import os
import socket
import sys
import tempfile
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import uvicorn
from playwright.sync_api import sync_playwright

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


def _test_db_hazirla():
    import sqlite3
    fd, path = tempfile.mkstemp(suffix=".db", prefix="csp_teshis_")
    os.close(fd)
    os.environ["EMLAK_DB_PATH"] = path
    os.environ.setdefault("JWT_SECRET", "csp-teshis-secret")

    from backend.db.schema import SCHEMA_SQL
    from backend.core.password import hash_sifre

    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA_SQL)
    try:
        conn.execute("ALTER TABLE kullanicilar ADD COLUMN onay INTEGER DEFAULT 1")
    except sqlite3.OperationalError:
        pass
    conn.execute(
        "INSERT INTO kullanicilar (ad_soyad,email,sifre,rol,aktif,onay_durumu,onay) VALUES (?,?,?,?,?,?,?)",
        ("Test Admin", "admin@test.com", hash_sifre("admin123"), "admin", 1, "onaylandi", 1),
    )
    conn.commit()
    conn.close()
    return path


def _bos_port_bul():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main():
    print("Test veritabanı hazırlanıyor...")
    _test_db_hazirla()

    from app import app as fastapi_app

    port = _bos_port_bul()
    config = uvicorn.Config(fastapi_app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    for _ in range(100):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                break
        except OSError:
            time.sleep(0.1)
    else:
        print("HATA: sunucu ayağa kalkmadı")
        sys.exit(1)

    base_url = f"http://127.0.0.1:{port}"
    print(f"Sunucu hazır: {base_url}")
    print("Tarayıcı açılıyor, gerçek CSP header'ı ile index.html yükleniyor...\n")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # Service worker devre dışı
        page.add_init_script("""
            Object.defineProperty(navigator, 'serviceWorker', {
                value: { register: () => Promise.resolve({ addEventListener(){}, update: () => Promise.resolve() }),
                         addEventListener(){}, getRegistrations: () => Promise.resolve([]) },
                configurable: true
            });
        """)

        def handle_route(route):
            response = route.fetch()
            headers = dict(response.headers)
            headers["content-security-policy"] = PROD_CSP
            route.fulfill(response=response, headers=headers)
        page.route("**/*", handle_route)

        tum_konsol = []

        def on_console(msg):
            loc = msg.location
            konum_str = f"{loc.get('url', '?')}:{loc.get('lineNumber', '?')}:{loc.get('columnNumber', '?')}" if loc else "konum yok"
            satir = f"[{msg.type}] {msg.text}\n    KONUM: {konum_str}"
            tum_konsol.append(satir)
            if "Content Security Policy" in msg.text or "Refused" in msg.text or "inline" in msg.text.lower():
                print("=" * 70)
                print("CSP İHLALİ BULUNDU:")
                print(satir)
                print("=" * 70)

        page.on("console", on_console)

        page.goto(f"{base_url}/static/index.html")
        page.wait_for_timeout(4000)

        print(f"\nToplam konsol mesajı: {len(tum_konsol)}")
        ihlaller = [m for m in tum_konsol if "Content Security Policy" in m or "Refused" in m]
        print(f"Toplam CSP ihlali: {len(ihlaller)}")

        if not ihlaller:
            print("\n✅ Bu çalıştırmada hiç CSP ihlali YAKALANMADI.")
            print("(Sorun aralıklı/durum bağımlı olabilir — birkaç kez daha çalıştırmayı deneyin)")
        else:
            print("\n--- TÜM İHLALLER (tam detay) ---")
            for v in ihlaller:
                print(v)
                print()

        browser.close()

    server.should_exit = True
    thread.join(timeout=5)


if __name__ == "__main__":
    main()
