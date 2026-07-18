"""Wizard Service — 10 adımlı site oluşturma sihirbazı."""
from __future__ import annotations

import json
from typing import Any, Optional

from backend.db.database import Database
from backend.repositories.menu_repository import MenuRepository, MenuItemRepository
from backend.repositories.misc_repository import AyarRepository
from backend.repositories.page_repository import PageRepository
from backend.repositories.widget_repository import WidgetRepository
from backend.repositories.wizard_repository import WizardRepository
from backend.repositories.template_repository import TemplateRepository, HomepageSectionRepository
from backend.services.demo_service import DemoService
from backend.services.preset_service import PresetService
from backend.core.settings import settings


class WizardService:
    def __init__(self, database: Database) -> None:
        self.db = database
        self.wizard_repo = WizardRepository(database)
        self.preset_service = PresetService()
        self.demo_service = DemoService(database)
        self.ayar_repo = AyarRepository(database)
        self.page_repo = PageRepository(database)
        self.menu_repo = MenuRepository(database)
        self.menu_item_repo = MenuItemRepository(database)
        self.widget_repo = WidgetRepository(database)
        self.template_repo = TemplateRepository(database)
        self.section_repo = HomepageSectionRepository(database)

    def baslat(self) -> dict:
        wid = self.wizard_repo.baslat()
        sektorler = self.preset_service.sektor_listesi()
        return {"wizard_id": wid, "adim": 1, "sektorler": sektorler}

    def durum(self, wizard_id: int) -> Optional[dict]:
        state = self.wizard_repo.getir()
        if not state or state["id"] != wizard_id:
            return None
        return state

    def adim_kaydet(self, wizard_id: int, adim: int, veri: dict) -> dict:
        self.wizard_repo.kaydet(wizard_id, adim, veri)
        state = self.wizard_repo.getir()
        return {"wizard_id": wizard_id, "adim": adim, "veri": state["veri"] if state else veri}

    def sektor_sec(self, wizard_id: int, sector: str) -> dict:
        self.wizard_repo.kaydet(wizard_id, 2, {"sector": sector})
        preset = self.preset_service.sektor_getir(sector)
        if not preset:
            return {"error": "Sektör bulunamadı"}
        return {
            "wizard_id": wizard_id,
            "adim": 2,
            "sector": sector,
            "templates": preset.get("templates", []),
            "color_palettes": preset.get("color_palettes", []),
        }

    def template_sec(self, wizard_id: int, template_slug: str) -> dict:
        self.wizard_repo.kaydet(wizard_id, 3, {"template": template_slug})
        return {"wizard_id": wizard_id, "adim": 3, "template": template_slug}

    def renk_sec(self, wizard_id: int, palette: dict) -> dict:
        self.wizard_repo.kaydet(wizard_id, 4, {"renk_paleti": palette})
        return {"wizard_id": wizard_id, "adim": 4}

    def menu_olustur(self, wizard_id: int, menu_conf: dict) -> dict:
        preset = self._preset_oku(wizard_id)
        if not preset:
            return {"error": "Önce sektör seçilmeli"}
        menus = preset.get("menus", {})
        if menu_conf.get("auto", True):
            for slug, m_data in menus.items():
                mevcut = self.menu_repo.get_by_slug(slug)
                if not mevcut:
                    mid = self.menu_repo.create({
                        "slug": slug,
                        "ad": m_data.get("ad", slug),
                        "lokasyon": m_data.get("lokasyon", "header"),
                    })
                    for oge in m_data.get("ogeler", []):
                        self.menu_item_repo.create({
                            "menu_id": mid,
                            "baslik": oge["baslik"],
                            "hedef_url": oge.get("hedef_url", ""),
                            "hedef_tip": oge.get("hedef_tip", "dahili"),
                            "sira": oge.get("sira", 0),
                        })
        self.wizard_repo.kaydet(wizard_id, 5, {"menus": "auto" if menu_conf.get("auto") else "manual"})
        return {"wizard_id": wizard_id, "adim": 5, "menus_olusturuldu": True}

    def sayfa_olustur(self, wizard_id: int, sayfa_conf: dict) -> dict:
        preset = self._preset_oku(wizard_id)
        if not preset:
            return {"error": "Önce sektör seçilmeli"}
        sayfalar = preset.get("pages", [])
        if sayfa_conf.get("auto", True):
            for p_data in sayfalar:
                try:
                    self.page_repo.create({
                        "baslik": p_data["baslik"],
                        "slug": p_data["slug"],
                        "icerik": p_data.get("icerik", ""),
                        "durum": p_data.get("durum", "Yayınla"),
                    })
                except Exception:
                    pass
        self.wizard_repo.kaydet(wizard_id, 6, {"pages": "auto" if sayfa_conf.get("auto") else "manual"})
        return {"wizard_id": wizard_id, "adim": 6, "sayfalar_olusturuldu": True}

    def widget_ayarla(self, wizard_id: int, widget_secim: list[str]) -> dict:
        preset = self._preset_oku(wizard_id)
        if not preset:
            return {"error": "Önce sektör seçilmeli"}
        for w in preset.get("widgets", []):
            if w["anahtar"] in widget_secim:
                mevcut = self.widget_repo.get_by_anahtar(w["anahtar"])
                if mevcut:
                    self.widget_repo.toggle_active(mevcut["id"])
        self.wizard_repo.kaydet(wizard_id, 7, {"widgets": widget_secim})
        return {"wizard_id": wizard_id, "adim": 7}

    def forum_ayarla(self, wizard_id: int, forum_aktif: bool) -> dict:
        self.wizard_repo.kaydet(wizard_id, 8, {"forum_aktif": forum_aktif})
        if forum_aktif:
            import os
            os.environ["CMS_FORUM_ENABLED"] = "1"
        return {"wizard_id": wizard_id, "adim": 8, "forum_aktif": forum_aktif}

    def seo_ayarla(self, wizard_id: int, seo_data: dict) -> dict:
        preset = self._preset_oku(wizard_id)
        if not preset:
            return {"error": "Önce sektör seçilmeli"}
        defaults = preset.get("seo", {})
        for k, v in {**defaults, **seo_data}.items():
            if k in ("site_adi", "site_slogan") or k.startswith("seo_"):
                self.ayar_repo.set(k, v)
        self.wizard_repo.kaydet(wizard_id, 9, {"seo": seo_data})
        return {"wizard_id": wizard_id, "adim": 9}

    def demo_olustur(self, wizard_id: int, demo_secim: dict) -> dict:
        preset = self._preset_oku(wizard_id)
        if not preset:
            return {"error": "Önce sektör seçilmeli"}
        sonuc = self.demo_service.hepsi(demo_secim, preset)
        self.wizard_repo.kaydet(wizard_id, 10, {"demo": demo_secim})
        return {"wizard_id": wizard_id, "adim": 10, "demo_sonuc": sonuc}

    def siteyi_olustur(self, wizard_id: int) -> dict:
        state = self.wizard_repo.getir()
        if not state or state["id"] != wizard_id:
            return {"error": "Wizard bulunamadı"}
        veri = state.get("veri", {})
        sector = veri.get("sector", "corporate")
        preset = self.preset_service.sektor_getir(sector)

        # Firma bilgilerini kaydet
        if veri.get("firma_adi"):
            self.ayar_repo.set("site_adi", veri["firma_adi"])
        if veri.get("firma_email"):
            self.ayar_repo.set("email", veri["firma_email"])
        if veri.get("firma_tel"):
            self.ayar_repo.set("telefon", veri["firma_tel"])

        # Renk paletini tema ayarlarına yaz
        palette = veri.get("renk_paleti", {})
        if palette.get("colors"):
            for k, v in palette["colors"].items():
                self.ayar_repo.set(f"renk_{k}" if not k.startswith("renk_") else k, v)

        # Template aktifleştir
        template_slug = veri.get("template", preset.get("default_template", "corporate"))
        template = self.template_repo.get_by_slug(template_slug)
        if template:
            self.template_repo.set_default(template["id"])

        self.wizard_repo.tamamla(wizard_id)
        return {
            "success": True,
            "message": "Site başarıyla oluşturuldu!",
            "wizard_id": wizard_id,
            "sector": sector,
            "template": template_slug,
        }

    def _preset_oku(self, wizard_id: int) -> Optional[dict]:
        state = self.wizard_repo.getir()
        if not state or state["id"] != wizard_id:
            return None
        sector = state["veri"].get("sector", "")
        if not sector:
            return None
        return self.preset_service.sektor_getir(sector)
