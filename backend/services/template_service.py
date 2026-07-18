"""Template ve Homepage Service — iş kuralları katmanı."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from backend.core.errors import AppError, NotFoundError
from backend.repositories.template_repository import (
    HomepageSectionRepository, TemplateRepository,
)


class TemplateService:
    def __init__(
        self,
        templates: Optional[TemplateRepository] = None,
        sections: Optional[HomepageSectionRepository] = None,
    ):
        self.templates = templates or TemplateRepository()
        self.sections = sections or HomepageSectionRepository()

    def listele(self, aktif_only: bool = False) -> List[dict]:
        return self.templates.get_all(aktif_only=aktif_only)

    def getir(self, tid: int) -> dict:
        t = self.templates.get_by_id(tid)
        if not t:
            raise NotFoundError("Template bulunamadı")
        return t

    def olustur(self, data: dict) -> dict:
        slug = (data.get("slug") or "").strip().lower()
        if not slug:
            raise AppError("slug gerekli", 400)
        if self.templates.slug_exists(slug):
            raise AppError("Bu slug zaten kullanımda", 409)
        if not (data.get("ad") or "").strip():
            raise AppError("ad gerekli", 400)
        tid = self.templates.create({**data, "slug": slug})
        return self.templates.get_by_id(tid)

    def guncelle(self, tid: int, data: dict) -> dict:
        if not self.templates.exists(tid):
            raise NotFoundError("Template bulunamadı")
        if "slug" in data:
            slug = data["slug"].strip().lower()
            if self.templates.slug_exists(slug, exclude_id=tid):
                raise AppError("Bu slug zaten kullanımda", 409)
            data["slug"] = slug
        if "varsayilan" in data and data["varsayilan"]:
            self.templates.set_default(tid)
            data.pop("varsayilan")
        self.templates.update(tid, data)
        return self.templates.get_by_id(tid)

    def sil(self, tid: int) -> dict:
        if not self.templates.exists(tid):
            raise NotFoundError("Template bulunamadı")
        self.templates.delete(tid)
        return {"id": tid, "silindi": True}

    def aktif_degistir(self, tid: int) -> dict:
        t = self.getir(tid)
        yeni = not t.get("aktif")
        self.templates.update(tid, {"aktif": yeni})
        return self.templates.get_by_id(tid)


class HomepageService:
    def __init__(
        self,
        templates: Optional[TemplateRepository] = None,
        sections: Optional[HomepageSectionRepository] = None,
    ):
        self.templates = templates or TemplateRepository()
        self.sections = sections or HomepageSectionRepository()

    # ─── Public ────────────────────────────────────────────────────────────
    def aktif_homepage(self, template_slug: Optional[str] = None) -> List[dict]:
        """Aktif template'in aktif bölümlerini getir (frontend için)."""
        if template_slug:
            t = self.templates.get_by_slug(template_slug)
        else:
            t = self.templates.get_default()
        if not t or not t.get("aktif"):
            return []
        bolumler = self.sections.get_by_template(t["id"], aktif_only=True)
        result = []
        for b in bolumler:
            ayarlar = self._parse_ayarlar(b.get("ayarlar", "{}"))
            result.append({
                "id": b["id"],
                "section_key": b["section_key"],
                "baslik": b["baslik"],
                "sira": b["sira"],
                "ayarlar": ayarlar,
            })
        return result

    def _parse_ayarlar(self, raw: str) -> dict:
        try:
            return json.loads(raw) if isinstance(raw, str) else (raw or {})
        except (json.JSONDecodeError, TypeError):
            return {}

    # ─── Admin ─────────────────────────────────────────────────────────────
    def template_bolumleri(self, template_id: int) -> List[dict]:
        if not self.templates.exists(template_id):
            raise NotFoundError("Template bulunamadı")
        return self.sections.get_by_template(template_id)

    def bolum_getir(self, section_id: int) -> dict:
        s = self.sections.get_by_id(section_id)
        if not s:
            raise NotFoundError("Bölüm bulunamadı")
        return s

    def bolum_guncelle(self, section_id: int, data: dict) -> dict:
        if not self.sections.exists(section_id):
            raise NotFoundError("Bölüm bulunamadı")
        self.sections.update(section_id, data)
        return self.sections.get_by_id(section_id)

    def bolum_sirala(self, items: List[dict]) -> dict:
        if not items:
            return {"guncellenen": 0}
        n = self.sections.reorder(items)
        return {"guncellenen": n}
