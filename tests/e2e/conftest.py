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
import socket
import threading
import time

import pytest
import uvicorn

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))


def _bos_port_bul() -> int:
    """İşletim sisteminden boş bir TCP portu ister (çakışma riski olmadan)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def live_server():
    """Gerçek uygulamayı (app.py'deki app nesnesi) arka planda başlatır."""
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
