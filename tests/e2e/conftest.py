"""
E2E testleri için gerçek (canlı) FastAPI sunucusu fixture'ı.

Bu testler gerçek bir headless tarayıcı (Playwright/Chromium) açar,
gerçek DOM üzerinde tıklama yapar ve sonucu doğrular. Amaç: onclick=""
attribute'larından addEventListener'a geçişte davranışın BOZULMADIĞINI
gerçek tarayıcı ortamında kanıtlamak (statik kod analizi yetmez).

Çalıştırmak için (bir kereye mahsus):
    pip install playwright --break-system-packages
    python3 -m playwright install chromium

Testleri çalıştırmak için:
    python3 -m pytest tests/e2e/ -v
"""
import os
import socket
import sqlite3
import sys
import tempfile
import threading
import time
from pathlib import Path

import pytest
import uvicorn

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))


def _bos_port_bul() -> int:
    """İşletim sisteminden boş bir TCP portu ister (çakışma riski olmadan)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _test_db_hazirla() -> str:
    """
    Gerçek (production) emlak_web.db'ye HİÇ dokunmadan, izole bir test
    veritabanı oluşturur ve admin@test.com / admin123 kullanıcısını ekler.
    tests/test_api.py'deki setup_test_db ile aynı prensip.

    ÖNEMLİ: dönen path, backend.* importlarından ÖNCE os.environ'a yazılmalı —
    aksi halde backend.core.settings modülü (import zamanında okunan) yanlış
    (varsayılan/production) DB yoluna sabitlenir.
    """
    fd, path = tempfile.mkstemp(suffix=".db", prefix="e2e_test_")
    os.close(fd)
    return path


def _test_db_doldur(path: str) -> None:
    """DB dosyasına şema + admin kullanıcısını yazar (env var set edildikten SONRA çağrılmalı)."""
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


@pytest.fixture(scope="session")
def live_server():
    """Gerçek uygulamayı (app.py'deki app nesnesi), izole bir test DB'siyle arka planda başlatır."""
    # ÖNEMLİ: app import edilmeden ÖNCE env var set edilmeli (settings.py import
    # zamanında okur). Böylece gerçek emlak_web.db'ye asla dokunulmaz.
    _db_path = _test_db_hazirla()
    os.environ["EMLAK_DB_PATH"] = _db_path
    os.environ.setdefault("JWT_SECRET", "e2e-test-only-secret")
    _test_db_doldur(_db_path)

    from app import app as fastapi_app

    port = _bos_port_bul()
    config = uvicorn.Config(fastapi_app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    # Sunucu hazır olana kadar bekle (max 10sn)
    base_url = f"http://127.0.0.1:{port}"
    for _ in range(100):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                break
        except OSError:
            time.sleep(0.1)
    else:
        raise RuntimeError("Test sunucusu 10sn içinde ayağa kalkmadı")

    yield base_url

    server.should_exit = True
    thread.join(timeout=5)


@pytest.fixture(scope="session")
def admin_token(live_server):
    """admin@test.com ile giriş yapar, JWT döner (admin paneli testleri için)."""
    import httpx
    r = httpx.post(
        f"{live_server}/api/auth/giris",
        json={"email": "admin@test.com", "sifre": "admin123"},
    )
    r.raise_for_status()
    body = r.json()
    assert body.get("success"), f"Login başarısız: {body}"
    token = body["data"]["access_token"]
    assert token, f"Login'den token alınamadı: {body}"
    return token


@pytest.fixture(scope="session")
def browser():
    """
    TÜM test oturumu boyunca TEK bir Chromium tarayıcı süreci paylaşılır.

    ÖNEMLİ (2026-07 hata düzeltmesi): eskiden her test kendi
    `with sync_playwright() as p: browser = p.chromium.launch()` bloğunu
    açıyordu. Bir test assertion hatasıyla düşünce (exception), o testin
    `browser.close()` satırına HİÇ ulaşılmıyordu — tarayıcı süreci "zombi"
    olarak açık kalıyordu. 50+ test arka arkaya çalışınca, her başarısız
    testin arkasında bir zombi Chromium süreci birikiyor, sistem kaynakları
    tükeniyor ve SONRAKİ testler sayfa bile açamadan (Page.goto timeout)
    başarısız oluyordu (gerçek bir kullanıcıda 24+ dakika süren, art arda
    18 testin patladığı bir çöküş zinciri olarak gözlemlendi).

    Çözüm: tek bir paylaşılan tarayıcı + her testte YENİ bir context/page
    (izolasyon için) + her testte try/finally ile context.close() garantisi.
    Bir context/page'in kapanmaması çok küçük bir sızıntıdır (tüm tarayıcı
    süreci değil), zincirleme çöküşe yol açmaz.
    """
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()
