"""Preset Service — Sektör preset'lerini yükler ve uygular."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from backend.core.settings import BASE_DIR


class PresetService:
    PRESETS_DIR = BASE_DIR / "presets"

    def sektor_listesi(self) -> list[dict]:
        presetler = []
        if not self.PRESETS_DIR.exists():
            return presetler
        for f in sorted(self.PRESETS_DIR.glob("*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                presetler.append({
                    "sector": data.get("sector", f.stem),
                    "label": data.get("label", f.stem.title()),
                    "templates": data.get("templates", []),
                    "default_template": data.get("default_template", ""),
                    "color_palettes": data.get("color_palettes", []),
                    "has_forum": len(data.get("forum_categories", [])) > 0,
                })
            except Exception:
                pass
        return presetler

    def sektor_getir(self, sector: str) -> Optional[dict]:
        path = self.PRESETS_DIR / f"{sector}.json"
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def palette_getir(self, sector: str) -> list:
        data = self.sektor_getir(sector)
        if not data:
            return []
        return data.get("color_palettes", [])

    def template_getir(self, sector: str) -> list:
        data = self.sektor_getir(sector)
        if not data:
            return []
        return data.get("templates", [])

    def uygula(self, sector: str, secim: dict) -> dict:
        preset = self.sektor_getir(sector)
        if not preset:
            return {}
        return {
            "templates": preset.get("templates", []),
            "selected_template": secim.get("template") or preset.get("default_template", ""),
            "menus": preset.get("menus", {}),
            "pages": preset.get("pages", []),
            "widgets": preset.get("widgets", []),
            "forum_categories": preset.get("forum_categories", []),
            "seo": preset.get("seo", {}),
            "demo": preset.get("demo", {}),
        }

    def demo_ayarlari(self, sector: str) -> dict:
        preset = self.sektor_getir(sector)
        if not preset:
            return {}
        return preset.get("demo", {})
