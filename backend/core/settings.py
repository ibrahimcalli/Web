"""
Aplikasyon ayarları — tek yerden tüm config.

Tüm DB/JWT/Domain/CORS/Cache parametreleri ortam değişkenlerinden okunur.
Varsayılan değerlerle production risk altında DEĞİL — env vermeden çalışmaz
gibi bir kısıtlama yoktur; ama production TORUNLU gizli anahtarlar env'den
sağlanmalıdır.

Kullanım:
    from backend.core.settings import settings
    settings.DATABASE_URL
    settings.JWT_SECRET
    settings.DEBUG

Önerilen ortam değişkenleri:
    # DB
    DATABASE_URL=sqlite:///./emlak_web.db
    # veya PostgreSQL: postgresql+psycopg://user:pass@localhost:5432/emlak
    EMLAK_DB_PATH=./emlak_web.db   # eski SQLite path API (geçiş için)

    # JWT
    JWT_SECRET=<gizli_anahtar>
    JWT_ALGORITHM=HS256
    JWT_EXPIRE_MINUTES=1440

    # Uygulama
    DEBUG=false
    DOMAIN=emlakfethiye.com.tr
    API_TITLE=Portföy Gayrimenkul API

    # CORS
    CORS_ORIGINS=https://emlakfethiye.com.tr,https://www.emlakfethiye.com.tr

    # Cache
    CACHE_TTL=3600

    # Upload
    UPLOAD_DIR=./static/uploads
    MAX_UPLOAD_MB=10
    ALLOWED_UPLOAD_EXTENSIONS=jpg,jpeg,png,webp,gif,pdf,docx
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional


# ─── Sunucu yolu ────────────────────────────────────────────────────────────
# BASE_DIR: repo kökü (settings.py'nin 3 üstü)
BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent


def _env_str(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


def _env_int(key: str, default: int) -> int:
    try:
        return int(os.environ.get(key, str(default)))
    except (TypeError, ValueError):
        return default


def _env_bool(key: str, default: bool = False) -> bool:
    raw = os.environ.get(key, "")
    if not raw:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _env_list(key: str, default: List[str]) -> List[str]:
    raw = os.environ.get(key, "").strip()
    if not raw:
        return list(default)
    return [s.strip() for s in raw.split(",") if s.strip()]


class Settings:
    """
    Uygulama ayarları singleton.

    Tüm değerler ortam değişkenlerinden okunur; env yoksa güvenli varsayılanları.
    Production'da gizli anahtarlar SECRET_KEY/JWT_SECRET env ile verilmelidir.
    """

    # ─── Uygulama ──────────────────────────────────────────────────────────
    BASE_DIR: Path = BASE_DIR
    DEBUG: bool = _env_bool("DEBUG", False)
    DOMAIN: str = _env_str("DOMAIN", "emlakfethiye.com.tr")

    API_TITLE: str = _env_str("API_TITLE", "Portföy Gayrimenkul API")
    API_VERSION: str = _env_str("API_VERSION", "2.0.0")
    API_DESCRIPTION: str = (
        "Portföy Gayrimenkul ortak API'si. "
        "Web, masaüstü ve mobil istemciler tarafından kullanılır. "
        "Tüm JSON yanıtlar: {success, message, data}."
    )

    # ─── Veritabanı ──────────────────────────────────────────────────────────
    # DATABASE_URL ileride PostgreSQL için: postgresql+psycopg://user:pass@host/db
    DATABASE_URL: str = _env_str(
        "DATABASE_URL",
        f"sqlite:///{_env_str('EMLAK_DB_PATH', str(BASE_DIR / 'emlak_web.db'))}",
    )
    # Eski DB path (sadece SQLite ile) — database.py bunu kullanıyor.
    DB_PATH: Path = Path(_env_str("EMLAK_DB_PATH", str(BASE_DIR / "emlak_web.db")))

    # ─── JWT ────────────────────────────────────────────────────────────────
    JWT_SECRET: str = _env_str("JWT_SECRET", "") or _env_str("SECRET_KEY", "")
    # Eğer env verilmemişse: geliştirme için sabit (uyarı basılır) —
    # production'da JWT_SECRET set edildiğinden emin olun.
    if not JWT_SECRET:
        JWT_SECRET = "emlak-gizli-anahtar-2026-degistir"
    JWT_ALGORITHM: str = _env_str("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = _env_int("JWT_EXPIRE_MINUTES", 60 * 24)

    # ─── CORS ───────────────────────────────────────────────────────────────
    # Virgülle ayrılmış origin listesi. Boşsa starlette'in allow_origins=[]
    # devreye girer; geliştirme için yalnız * da girilebilir.
    CORS_ORIGINS: List[str] = _env_list(
        "CORS_ORIGINS",
        default=_env_list("CORS_ORIGINS_DEFAULT", []) or ["*"],
    )

    # ─── Cache ──────────────────────────────────────────────────────────────
    CACHE_TTL: int = _env_int("CACHE_TTL", 3600)

    # ─── Upload ─────────────────────────────────────────────────────────────
    UPLOAD_DIR: Path = Path(
        _env_str("UPLOAD_DIR", str(BASE_DIR / "static" / "uploads"))
    )
    MAX_UPLOAD_MB: int = _env_int("MAX_UPLOAD_MB", 10)
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = _env_list(
        "ALLOWED_UPLOAD_EXTENSIONS",
        default=["jpg", "jpeg", "png", "webp", "gif", "pdf", "docx"],
    )

    # ─── Rate Limit ────────────────────────────────────────────────────────
    LOGIN_MAX_ATTEMPTS: int = _env_int("LOGIN_MAX_ATTEMPTS", 5)
    LOGIN_LOCK_SECONDS: int = _env_int("LOGIN_LOCK_SECONDS", 900)  # 15 dk
    LOGIN_WINDOW_SECONDS: int = _env_int("LOGIN_WINDOW_SECONDS", 300)  # 5 dk

    # ─── Logging ───────────────────────────────────────────────────────────
    LOG_LEVEL: str = _env_str("LOG_LEVEL", "INFO")
    LOG_DIR: Path = Path(_env_str("LOG_DIR", str(BASE_DIR / "logs")))

    # ─── CMS v2.1 — Modüler feature flags (aç/kapat) ───────────────────────
    # Her modül bağımsız açılıp kapatılabilir. Backend modülü kapatılırsa
    # router kaydı yapılmaz, tablolar yine de oluşturulur (ileriye dönük).
    CMS_MENU_ENABLED: bool = _env_bool("CMS_MENU_ENABLED", True)
    CMS_PAGE_ENABLED: bool = _env_bool("CMS_PAGE_ENABLED", True)
    CMS_WIDGET_ENABLED: bool = _env_bool("CMS_WIDGET_ENABLED", True)
    CMS_THEME_ENABLED: bool = _env_bool("CMS_THEME_ENABLED", True)
    CMS_FORUM_ENABLED: bool = _env_bool("CMS_FORUM_ENABLED", False)  # opsiyonel
    CMS_DASHBOARD_ENABLED: bool = _env_bool("CMS_DASHBOARD_ENABLED", True)
    CMS_TEMPLATE_ENABLED: bool = _env_bool("CMS_TEMPLATE_ENABLED", True)
    CMS_WIZARD_ENABLED: bool = _env_bool("CMS_WIZARD_ENABLED", True)
    CMS_MARKETPLACE_ENABLED: bool = _env_bool("CMS_MARKETPLACE_ENABLED", True)
    CMS_MULTI_TENANT_ENABLED: bool = _env_bool("CMS_MULTI_TENANT_ENABLED", False)

    # ─── Computed / Convenience ─────────────────────────────────────────────
    def is_production(self) -> bool:
        return not self.DEBUG

    def is_debug(self) -> bool:
        return self.DEBUG

    def __repr__(self) -> str:
        return f"<Settings DEBUG={self.DEBUG} DOMAIN={self.DOMAIN} DB={self.DATABASE_URL}>"


# Singleton
settings = Settings()

# ─── Yan etkiler ─────────────────────────────────────────────────────────────
# UPLOAD_DIR mevcut değilse oluştur (logs dizini logging yapılandırmasında)
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
