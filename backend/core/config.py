"""
DEPRECATED — backend/core/settings.py kullanın.

Bu modül geriye dönük uyumluluk için vardır. Eski importlar (örn:
`from backend.core.config import BASE_DIR`) çalışmaya devam eder, ama
new code `from backend.core.settings import settings` kullanmalıdır.

Migration:
    from backend.core.config import BASE_DIR, SECRET_KEY
    →
    from backend.core.settings import settings
    settings.BASE_DIR, settings.JWT_SECRET
"""
from __future__ import annotations

# Settings singleton — ortam değişkenlerinden yüklenmiş
from backend.core.settings import settings

# Eski isimleri expose et (geriye dönük uyumluluk)
BASE_DIR = settings.BASE_DIR
DB_PATH = settings.DB_PATH
UPLOAD_DIR = settings.UPLOAD_DIR

SECRET_KEY = settings.JWT_SECRET  # geriye dönük uyum
ALGORITHM = settings.JWT_ALGORITHM
TOKEN_EXPIRE_MINUTES = settings.JWT_EXPIRE_MINUTES

CORS_ORIGINS = settings.CORS_ORIGINS

API_TITLE = settings.API_TITLE
API_VERSION = settings.API_VERSION
API_DESCRIPTION = settings.API_DESCRIPTION
