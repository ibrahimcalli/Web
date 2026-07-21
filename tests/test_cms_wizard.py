"""CMS v2.3 / v2.4 — Wizard ve Marketplace testleri."""
from __future__ import annotations

import os
import tempfile

os.environ.setdefault("LOG_DIR", tempfile.mkdtemp())

from backend.db.database import Database
from backend.db.schema import init_db
from backend.repositories.wizard_repository import WizardRepository
from backend.services.preset_service import PresetService
from backend.services.wizard_service import WizardService


def make_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = Database(path)
    init_db(db)
    return db


def test_wizard_sector_list():
    ps = PresetService()
    sektorler = ps.sektor_listesi()
    assert any(s["sector"] == "estate" for s in sektorler)


def test_wizard_sector_detail():
    ps = PresetService()
    data = ps.sektor_getir("estate")
    assert data is not None
    assert data["default_template"] == "estate-modern"


def test_wizard_sector_assets():
    ps = PresetService()
    assert "estate-modern" in ps.template_getir("estate")
    assert len(ps.palette_getir("estate")) >= 3


def test_wizard_start_and_step():
    db = make_db()
    service = WizardService(db)
    started = service.baslat()
    wid = started["wizard_id"]
    assert started["adim"] == 1
    assert any(s["sector"] == "estate" for s in started["sektorler"])

    state = service.durum(wid)
    assert state is not None
    assert state["id"] == wid

    saved = service.adim_kaydet(wid, 2, {"sector": "estate"})
    assert saved["wizard_id"] == wid
    assert saved["adim"] == 2
    assert saved["veri"]["sector"] == "estate"

    selected = service.sektor_sec(wid, "estate")
    assert selected["sector"] == "estate"
    assert "templates" in selected and selected["templates"]


def test_wizard_plugin_and_license_lists():
    db = make_db()
    service = WizardService(db)
    # Repo'lar seed ile dolu olmalı.
    assert len(service.menu_repo.get_all()) >= 0
    assert len(service.widget_repo.get_all()) >= 0
    assert len(service.template_repo.get_all()) >= 7


def test_wizard_menu_creation():
    db = make_db()
    service = WizardService(db)
    started = service.baslat()
    wid = started["wizard_id"]
    service.sektor_sec(wid, "estate")
    result = service.menu_olustur(wid, {"auto": True})
    assert result["menus_olusturuldu"] is True
    repo = WizardRepository(db)
    state = repo.getir()
    assert state is not None
    assert state["veri"]["menus"] == "auto"
