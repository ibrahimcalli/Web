"""Sistem paneli testleri."""
from __future__ import annotations

import os
import tempfile

os.environ.setdefault("LOG_DIR", tempfile.mkdtemp())

from backend.services.system_service import (
    KOMUTLAR,
    cache_temizle,
    log_goruntule,
    log_temizle,
    servis_durumu,
)


def test_system_commands_list():
    assert len(KOMUTLAR) >= 4


def test_system_guide():
    info = servis_durumu()
    assert "sistem" in info
    assert "servis" in info


def test_system_maintenance_catalog():
    out = cache_temizle()
    assert out["success"] is True
    out = log_temizle()
    assert out["success"] is True


def test_system_log_view_empty_or_text():
    text = log_goruntule("app", satir=5)
    assert isinstance(text, str)
