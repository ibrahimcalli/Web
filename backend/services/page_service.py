"""Page Service — sayfa yönetimi iş kuralları."""
from __future__ import annotations

from typing import List, Optional

from backend.core.errors import AppError, NotFoundError
from backend.repositories.page_repository import PageRepository


class PageService:
    def __init__(self, pages: Optional[PageRepository] = None):
        self.pages = pages or PageRepository()

    def listele(self, durum: Optional[str] = None) -> List[dict]:
        return self.pages.get_all(durum=durum)

    def getir(self, page_id: int) -> dict:
        p = self.pages.get_by_id(page_id)
        if not p:
            raise NotFoundError("Sayfa bulunamadı")
        return p

    def slug_ile_getir(self, slug: str) -> dict:
        p = self.pages.get_by_slug(slug)
        if not p:
            raise NotFoundError("Sayfa bulunamadı")
        if p.get("durum") != "Yayınla":
            raise NotFoundError("Sayfa bulunamadı")
        return p

    def olustur(self, data: dict) -> dict:
        slug = (data.get("slug") or "").strip().lower()
        if not slug:
            raise AppError("slug gerekli", 400)
        if self.pages.slug_exists(slug):
            raise AppError("Bu slug zaten kullanımda", 409)
        if not (data.get("baslik") or "").strip():
            raise AppError("baslik gerekli", 400)
        pid = self.pages.create({**data, "slug": slug})
        return self.pages.get_by_id(pid)

    def guncelle(self, page_id: int, data: dict) -> dict:
        if not self.pages.exists(page_id):
            raise NotFoundError("Sayfa bulunamadı")
        if "slug" in data:
            slug = data["slug"].strip().lower()
            if self.pages.slug_exists(slug, exclude_id=page_id):
                raise AppError("Bu slug zaten kullanımda", 409)
            data["slug"] = slug
        if "baslik" in data and not (data["baslik"] or "").strip():
            raise AppError("baslik boş olamaz", 400)
        self.pages.update(page_id, data)
        return self.pages.get_by_id(page_id)

    def sil(self, page_id: int) -> dict:
        if not self.pages.exists(page_id):
            raise NotFoundError("Sayfa bulunamadı")
        self.pages.delete(page_id)
        return {"id": page_id, "silindi": True}
