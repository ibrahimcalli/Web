"""Widget Service — widget yönetimi iş kuralları."""
from __future__ import annotations

from typing import List, Optional

from backend.core.errors import AppError, NotFoundError
from backend.repositories.widget_repository import WidgetRepository


class WidgetService:
    def __init__(self, widgets: Optional[WidgetRepository] = None):
        self.widgets = widgets or WidgetRepository()

    def listele(self, aktif_only: bool = False) -> List[dict]:
        return self.widgets.get_all(aktif_only=aktif_only)

    def getir(self, wid: int) -> dict:
        w = self.widgets.get_by_id(wid)
        if not w:
            raise NotFoundError("Widget bulunamadı")
        return w

    def olustur(self, data: dict) -> dict:
        anahtar = (data.get("anahtar") or "").strip().lower()
        if not anahtar:
            raise AppError("anahtar gerekli", 400)
        if self.widgets.anahtar_exists(anahtar):
            raise AppError("Bu anahtar zaten kullanımda", 409)
        if not (data.get("ad") or "").strip():
            raise AppError("ad gerekli", 400)
        wid = self.widgets.create({**data, "anahtar": anahtar})
        return self.widgets.get_by_id(wid)

    def guncelle(self, wid: int, data: dict) -> dict:
        if not self.widgets.exists(wid):
            raise NotFoundError("Widget bulunamadı")
        if "ad" in data and not (data["ad"] or "").strip():
            raise AppError("ad boş olamaz", 400)
        self.widgets.update(wid, data)
        return self.widgets.get_by_id(wid)

    def konum_ile_getir(self, konum: str) -> List[dict]:
        return self.widgets.get_by_konum(konum, aktif_only=True)

    def sil(self, wid: int) -> dict:
        if not self.widgets.exists(wid):
            raise NotFoundError("Widget bulunamadı")
        self.widgets.delete(wid)
        return {"id": wid, "silindi": True}

    def toggle_aktif(self, wid: int) -> dict:
        if not self.widgets.exists(wid):
            raise NotFoundError("Widget bulunamadı")
        aktif = self.widgets.toggle_active(wid)
        return {"id": wid, "aktif": aktif}
