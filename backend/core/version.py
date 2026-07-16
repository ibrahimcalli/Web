"""
Sürüm bilgileri — tek yerden VERSION, BUILD_DATE, GIT_HASH.

- VERSION:	settings.API_VERSION ile senkron.
- BUILD_DATE:	paketin build edildiği tarih (env veya __file__ mtime).
- GIT_HASH:	ortam değişkeni BUILD_GIT_HASH (CI'dan) veya git rev-parse HEAD.
- GIT_BRANCH:	ortam değişkeni BUILD_GIT_BRANCH veya git rev-parse --abbrev-ref HEAD.

Kullanım:
    from backend.core.version import get_version_info
    get_version_info()  # {"version": "2.0.0", "build_date": "...", "git_hash": "...", ...}

Varsa:
    # CI ortamında
    export BUILD_GIT_HASH=$(git rev-parse HEAD)
    export BUILD_GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    export BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
"""
from __future__ import annotations

import datetime as _dt
import os
import subprocess
from pathlib import Path
from typing import Optional

from backend.core.settings import settings


def _git_hash() -> Optional[str]:
    """git HEAD hash'i (env > git CLI > None)."""
    raw = os.environ.get("BUILD_GIT_HASH", "").strip()
    if raw:
        return raw
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(settings.BASE_DIR),
            stderr=subprocess.DEVNULL,
            timeout=2,
        ).decode().strip()
        return out or None
    except (FileNotFoundError, subprocess.SubprocessError, OSError):
        return None


def _git_branch() -> Optional[str]:
    raw = os.environ.get("BUILD_GIT_BRANCH", "").strip()
    if raw:
        return raw
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(settings.BASE_DIR),
            stderr=subprocess.DEVNULL,
            timeout=2,
        ).decode().strip()
        return out or None
    except (FileNotFoundError, subprocess.SubprocessError, OSError):
        return None


def _build_date() -> str:
    """Build tarihi (env > VERSION dosyası mtime > now UTC ISO 8601)."""
    raw = os.environ.get("BUILD_DATE", "").strip()
    if raw:
        return raw
    # VERSION dosyasının mtime'ı build zamanına yaklaştırır
    try:
        mtime = Path(__file__).stat().st_mtime
        return _dt.datetime.utcfromtimestamp(mtime).strftime("%Y-%m-%dT%H:%M:%SZ")
    except OSError:
        pass
    return _dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def get_version_info() -> dict:
    """
    Sürüm bilgisi dict'i. /health endpoint'i bunu döndürür.
    """
    return {
        "version": settings.API_VERSION,
        "build_date": _build_date(),
        "git_hash": _git_hash(),
        "git_branch": _git_branch(),
        "domain": settings.DOMAIN,
    }


# Cache'lenmiş singleton — sıklıkla çağrılacak
_version_info = get_version_info()
