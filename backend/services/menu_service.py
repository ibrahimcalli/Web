"""Menu Service — iş kuralları katmanı (SOLID: tek sorumluluk).

Repository'leri DI ile alır; router'a service seviyesinde API sunar.
Hiyerarşik menü ağacı oluşturma burada yapılır (repo düz liste döner).
"""
from __future__ import annotations

from typing import List, Optional

from backend.core.errors import AppError, NotFoundError
from backend.repositories.menu_repository import (
    MenuRepository, MenuItemRepository,
)


class MenuService:
    """Menü yönetimi iş kuralları."""

    def __init__(
        self,
        menuler: Optional[MenuRepository] = None,
        ogeler: Optional[MenuItemRepository] = None,
    ):
        self.menuler = menuler or MenuRepository()
        self.ogeler = ogeler or MenuItemRepository()

    # ─── Menü CRUD ──────────────────────────────────────────────────────────
    def listele_menuler(self, aktif_only: bool = False) -> List[dict]:
        return self.menuler.get_all(aktif_only=aktif_only)

    def getir_menu(self, menu_id: int) -> dict:
        m = self.menuler.get_by_id(menu_id)
        if not m:
            raise NotFoundError("Menü bulunamadı")
        return m

    def olustur_menu(self, data: dict) -> dict:
        slug = (data.get("slug") or "").strip().lower()
        if not slug:
            raise AppError("slug gerekli", 400)
        if self.menuler.slug_exists(slug):
            raise AppError("Bu slug zaten kullanımda", 409)
        mid = self.menuler.create({
            "slug": slug,
            "ad": (data.get("ad") or "").strip(),
            "lokasyon": data.get("lokasyon", "header"),
            "aktif": data.get("aktif", True),
        })
        return {"id": mid, **{k: data.get(k, v) for k, v in {
            "slug": slug, "ad": "", "lokasyon": "header", "aktif": True
        }.items()}}

    def guncelle_menu(self, menu_id: int, data: dict) -> dict:
        if not self.menuler.exists(menu_id):
            raise NotFoundError("Menü bulunamadı")
        if "slug" in data:
            slug = data["slug"].strip().lower()
            if not slug:
                raise AppError("slug boş olamaz", 400)
            if self.menuler.slug_exists(slug, exclude_id=menu_id):
                raise AppError("Bu slug zaten kullanımda", 409)
            data["slug"] = slug
        self.menuler.update(menu_id, data)
        return self.menuler.get_by_id(menu_id)

    def sil_menu(self, menu_id: int) -> dict:
        if not self.menuler.exists(menu_id):
            raise NotFoundError("Menü bulunamadı")
        # cascade delete: menu_items tablosunda FK ON DELETE CASCADE
        self.menuler.delete(menu_id)
        return {"id": menu_id, "silindi": True}

    # ─── Menu Items ──────────────────────────────────────────────────────────
    def listele_ogeler(self, menu_id: int, aktif_only: bool = False) -> List[dict]:
        if not self.menuler.exists(menu_id):
            raise NotFoundError("Menü bulunamadı")
        return self.ogeler.get_by_menu(menu_id, aktif_only=aktif_only)

    def getir_oge(self, item_id: int) -> dict:
        it = self.ogeler.get_by_id(item_id)
        if not it:
            raise NotFoundError("Menü öğesi bulunamadı")
        return it

    def olustur_oge(self, data: dict) -> dict:
        menu_id = data.get("menu_id")
        if not menu_id or not self.menuler.exists(int(menu_id)):
            raise NotFoundError("Menü bulunamadı")
        if not (data.get("baslik") or "").strip():
            raise AppError("baslik gerekli", 400)
        # parent_id doğrula
        parent_id = data.get("parent_id")
        if parent_id:
            parent = self.ogeler.get_by_id(int(parent_id))
            if not parent:
                raise AppError("parent_id geçersiz", 400)
            if int(parent_id) == int(data.get("id", 0) or 0):
                raise AppError("Öğe kendi atası olamaz", 400)
        iid = self.ogeler.create(data)
        return self.ogeler.get_by_id(iid)

    def guncelle_oge(self, item_id: int, data: dict) -> dict:
        if not self.ogeler.exists(item_id):
            raise NotFoundError("Menü öğesi bulunamadı")
        if "baslik" in data and not (data["baslik"] or "").strip():
            raise AppError("baslik boş olamaz", 400)
        parent_id = data.get("parent_id")
        if parent_id:
            if int(parent_id) == item_id:
                raise AppError("Öğe kendi atası olamaz", 400)
            if not self.ogeler.get_by_id(int(parent_id)):
                raise AppError("parent_id geçersiz", 400)
        self.ogeler.update(item_id, data)
        return self.ogeler.get_by_id(item_id)

    def sil_oge(self, item_id: int) -> dict:
        if not self.ogeler.exists(item_id):
            raise NotFoundError("Menü öğesi bulunamadı")
        # cascade: alt öğeler FK CASCADE ile silinir
        self.ogeler.delete(item_id)
        return {"id": item_id, "silindi": True}

    def yeniden_sirala(self, items: List[dict]) -> dict:
        """Sürükle-bırak sonrası toplu yeniden sıralama.
        items: [{id, parent_id, sira}].
        """
        if not items:
            return {"guncellenen": 0}
        for it in items:
            if not self.ogeler.exists(int(it["id"])):
                raise NotFoundError(f"Öğe {it['id']} bulunamadı")
        n = self.ogeler.reorder(items)
        return {"guncellenen": n}

    # ─── Public (frontend) ────────────────────────────────────────────────────
    def halka_acik_menu(self, slug: str, kullanici_rol: str = "") -> List[dict]:
        """Frontend için filtrelenmiş hiyerarşik menü.
        - Aktif menü ve aktif öğeler
        - izin_rol boş veya kullanıcı rolünü içeriyorsa
        """
        m = self.menuler.get_by_slug(slug)
        if not m or not m.get("aktif"):
            return []
        items = self.ogeler.get_by_menu(m["id"], aktif_only=True)
        rol = kullanici_rol or ""
        # Yetki filtrele: izin_rol boşsa herkes; 'admin' ise sadece admin, vb.
        filtered = [
            it for it in items
            if not it.get("izin_rol")
            or (it["izin_rol"] == "admin" and rol == "admin")
            or it["izin_rol"] == rol
        ]
        return self._agac_yap(filtered, parent_id=None)

    def _agac_yap(self, items: List[dict], parent_id) -> List[dict]:
        """Düz listeyi hiyerarşik ağaca çevir."""
        result = []
        for it in items:
            if it.get("parent_id") == parent_id:
                cocuklar = self._agac_yap(items, it["id"])
                node = {**it, "alt_ogeler": cocuklar}
                result.append(node)
        return result
