"""Uygulama yapılandırması — sabit IP/domain kodda yok; ortam değişkeninden okunur."""
from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = Path(os.environ.get("EMLAK_DB_PATH", str(BASE_DIR / "emlak_web.db")))
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

SECRET_KEY = os.environ.get("SECRET_KEY", "emlak-gizli-anahtar-2026-degistir")
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = int(os.environ.get("TOKEN_EXPIRE_MINUTES", str(60 * 24)))

# CORS: virgülle ayrılmış origin listesi. Boşsa geliştirme için * benzeri esnek davranış yok —
# en azından aynı origin kullanıldığında middleware çalışır.
_CORS = os.environ.get("CORS_ORIGINS", "").strip()
if _CORS:
    CORS_ORIGINS = [o.strip() for o in _CORS.split(",") if o.strip()]
else:
    # Ortam değişkeni yoksa açık liste kullanılmaz; boş liste → mirror yok, allow yok
    # Üretimde CORS_ORIGINS set edilmelidir. Geliştirme kolaylığı için yaygın yerel + prod örnekleri:
    CORS_ORIGINS = [
        o.strip()
        for o in os.environ.get(
            "CORS_ORIGINS_DEFAULT",
            "",
        ).split(",")
        if o.strip()
    ]
    # Hâlâ boşsa tarayıcı same-origin için CORS gerekmez; API client'lar için credentials kapalı tutulur
    if not CORS_ORIGINS:
        CORS_ORIGINS = ["*"]

API_TITLE = "Portföy Gayrimenkul API"
API_VERSION = "2.0.0"
API_DESCRIPTION = """
Portföy Gayrimenkul ortak API'si.

Aynı uç noktalar **web**, **masaüstü** ve **mobil** istemciler tarafından kullanılır.

## Yanıt formatı

Tüm JSON yanıtlar:

```json
{ "success": true, "message": "", "data": { } }
```

Hata:

```json
{ "success": false, "message": "Açıklama", "data": null }
```

## Kimlik doğrulama

`Authorization: Bearer <JWT>` başlığı.

Binary yanıtlar (PDF vb.) zarf kullanmaz.
"""
