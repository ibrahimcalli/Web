"""
Logging yapılandırması — production için ayrı log dosyaları.

Log dosyaları:
    logs/access.log  → HTTP istekleri (middleware tarafından)
    logs/error.log   → ERROR ve üstü seviye ( uygulama hataları)
    logs/app.log     → Genel uygulama logları (INFO+)

Rotasyon:
    - Her log 10 MB'a ulaşınca rotate edilir
    - En fazla 5 yedek tutulur (50 MB/log x 3 = 150 MB max)

Kullanım:
    from backend.core.logging import get_logger
    log = get_logger(__name__)
    log.info("mesaj", extra={"request_id": "..."})

    # Veya: initialize() bir kez başlangıçta çağrılır (backend/app.py'de).
"""
from __future__ import annotations

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

from backend.core.settings import settings

# Log format — structured (machine-parseable + human-readable)
_LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)
_LOG_FORMAT_DEBUG = (
    "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
)

# Kullanılan log levels:
LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

_INITIALIZED = False


def _build_formatter() -> logging.Formatter:
    """Settings.DEBUG'a göre format döndürür."""
    fmt = _LOG_FORMAT_DEBUG if settings.DEBUG else _LOG_FORMAT
    return logging.Formatter(
        fmt=fmt,
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _ensure_log_dir() -> Path:
    """Log dizinini oluştur."""
    log_dir = settings.LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def initialize() -> None:
    """
    Logging sistemini yapılandır. Uygulama başlangıcında BİR KEZ çağrılmalı.
    
    Üç dosya handler + bir konsol handler (DEBUG mode'da) ekler:
        - access.log → INFO, access logger only
        - error.log  → ERROR ve üstü
        - app.log    → INFO ve üstü (root logger)
    
    Rotasyon: 10 MB başına, 5 backup.
    """
    global _INITIALIZED
    if _INITIALIZED:
        return
    
    log_dir = _ensure_log_dir()
    formatter = _build_formatter()
    level = LEVELS.get(settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Root logger
    root = logging.getLogger()
    root.setLevel(level)
    # Mevcut handler'ları temizle (tekrar eklenmesin)
    for h in list(root.handlers):
        root.removeHandler(h)
    
    # ─── app.log (INFO+ tüm loglar) ──────────────────────────────────────
    app_handler = logging.handlers.RotatingFileHandler(
        filename=str(log_dir / "app.log"),
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(formatter)
    app_handler.addFilter(lambda r: r.name != "access")
    root.addHandler(app_handler)
    
    # ─── error.log (ERROR+ sadece) ───────────────────────────────────────
    err_handler = logging.handlers.RotatingFileHandler(
        filename=str(log_dir / "error.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    err_handler.setLevel(logging.ERROR)
    err_handler.setFormatter(formatter)
    root.addHandler(err_handler)
    
    # ─── access.log (HTTP istekleri) ─────────────────────────────────────
    access_logger = logging.getLogger("access")
    access_logger.setLevel(logging.INFO)
    access_logger.propagate = False  # app.log'a da yazılmasın (sadece access.log)
    access_handler = logging.handlers.RotatingFileHandler(
        filename=str(log_dir / "access.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    access_handler.setLevel(logging.INFO)
    access_handler.setFormatter(logging.Formatter(
        fmt="%(asctime)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    access_logger.addHandler(access_handler)
    
    # ─── Konsol (DEBUG mode) ─────────────────────────────────────────────
    if settings.DEBUG:
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(logging.DEBUG)
        console.setFormatter(formatter)
        root.addHandler(console)
    
    # uvicorn'un kendi logger'ını da yakala
    for name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        lg = logging.getLogger(name)
        lg.handlers = []  # uvicorn default handler'ı kapalı
        lg.propagate = True  # root'a değil, bizim app.log'a yazsın
    
    _INITIALIZED = True


def get_logger(name: str = __name__) -> logging.Logger:
    """
    Logger döndür. Otomatik initialize() çağrısı yapar.
    
    Args:
        name: genelde __name__ — modül adı
    
    Returns:
        logging.Logger
    """
    if not _INITIALIZED:
        initialize()
    return logging.getLogger(name)


def get_access_logger() -> logging.Logger:
    """HTTP access logger (logs/access.log'a yazar)."""
    if not _INITIALIZED:
        initialize()
    return logging.getLogger("access")
