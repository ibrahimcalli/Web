"""Menu Repository — Menu ve MenuItem tabloları için veri erişim katmanı.

PG geçişinde yalnızca Database katmanı değişir; imzalar aynı kalır.
"""
from __future__ import annotations

from typing import List, Optional

from backend.db.database import Database, db, row_to_dict, rows_to_dicts
from backend.repositories.base import BaseRepository


class MenuRepository(BaseRepository):
    """menus tablosu — üst düzey menü grupları."""

    def __init__(self, database: Optional[Database] = None):
        super().__init__(database)

    def get_by_id(self, menu_id: int) -> Optional[dict]:
        return row_to_dict(
            self._fetchone("SELECT * FROM menus WHERE id=?", (menu_id,))
        )

    def get_by_slug(self, slug: str) -> Optional[dict]:
        return row_to_dict(
            self._fetchone("SELECT * FROM menus WHERE slug=?", (slug,))
        )

    def get_all(self, aktif_only: bool = False) -> List[dict]:
        sql = "SELECT * FROM menus"
        if aktif_only:
            sql += " WHERE aktif=1"
        sql += " ORDER BY id"
        return rows_to_dicts(self._fetchall(sql))

    def create(self, data: dict) -> int:
        return self._execute(
            "INSERT INTO menus (slug, ad, lokasyon, aktif) VALUES (?,?,?,?)",
            (
                data["slug"],
                data.get("ad", ""),
                data.get("lokasyon", "header"),
                int(bool(data.get("aktif", True))),
            ),
        )

    def update(self, menu_id: int, data: dict) -> bool:
        existing = self.get_by_id(menu_id)
        if not existing:
            return False
        merged = {**existing, **data, "id": menu_id}
        self._execute(
            "UPDATE menus SET slug=?, ad=?, lokasyon=?, aktif=? WHERE id=?",
            (
                merged["slug"], merged["ad"], merged["lokasyon"],
                int(bool(merged.get("aktif", True))), menu_id,
            ),
        )
        return True

    def delete(self, menu_id: int) -> bool:
        return self._execute("DELETE FROM menus WHERE id=?", (menu_id,)) > 0

    def exists(self, menu_id: int) -> bool:
        return self._fetchone("SELECT 1 FROM menus WHERE id=?", (menu_id,)) is not None

    def slug_exists(self, slug: str, exclude_id: Optional[int] = None) -> bool:
        if exclude_id is None:
            return self._fetchone("SELECT 1 FROM menus WHERE slug=?", (slug,)) is not None
        return self._fetchone(
            "SELECT 1 FROM menus WHERE slug=? AND id<>?", (slug, exclude_id)
        ) is not None


class MenuItemRepository(BaseRepository):
    """menu_items tablosu — hiyerarşik menü öğeleri (alt menü destekli)."""

    def __init__(self, database: Optional[Database] = None):
        super().__init__(database)

    def get_by_id(self, item_id: int) -> Optional[dict]:
        return row_to_dict(
            self._fetchone(
                "SELECT * FROM menu_items WHERE id=?", (item_id,))
        )

    def get_by_menu(self, menu_id: int, aktif_only: bool = False) -> List[dict]:
        """Bir menüye ait tüm öğeleri (hiyerarşik olarak) getir."""
        if aktif_only:
            sql = (
                "SELECT mi.*, p.slug AS page_slug FROM menu_items mi "
                "LEFT JOIN pages p ON p.id=mi.hedef_page_id "
                "WHERE mi.menu_id=? AND mi.aktif=1 ORDER BY mi.parent_id, mi.sira"
            )
        else:
            sql = (
                "SELECT mi.*, p.slug AS page_slug FROM menu_items mi "
                "LEFT JOIN pages p ON p.id=mi.hedef_page_id "
                "WHERE mi.menu_id=? ORDER BY mi.parent_id, mi.sira"
            )
        return rows_to_dicts(self._fetchall(sql, (menu_id,)))

    def create(self, data: dict) -> int:
        return self._execute(
            (
                "INSERT INTO menu_items "
                "(menu_id, parent_id, baslik, ikon, hedef_tip, hedef_url, "
                "hedef_page_id, gosterim, izin_rol, sira, aktif, dil) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)"
            ),
            (
                data["menu_id"],
                data.get("parent_id"),
                data["baslik"],
                data.get("ikon", ""),
                data.get("hedef_tip", "dahili"),
                data.get("hedef_url", ""),
                data.get("hedef_page_id"),
                data.get("gosterim", "_self"),
                data.get("izin_rol", ""),
                int(data.get("sira", 0)),
                int(bool(data.get("aktif", True))),
                data.get("dil", ""),
            ),
        )

    def update(self, item_id: int, data: dict) -> bool:
        existing = self.get_by_id(item_id)
        if not existing:
            return False
        merged = {**existing, **data, "id": item_id}
        self._execute(
            (
                "UPDATE menu_items SET parent_id=?, baslik=?, ikon=?, "
                "hedef_tip=?, hedef_url=?, hedef_page_id=?, gosterim=?, "
                "izin_rol=?, sira=?, aktif=?, dil=? WHERE id=?"
            ),
            (
                merged.get("parent_id"),
                merged["baslik"],
                merged.get("ikon", ""),
                merged.get("hedef_tip", "dahili"),
                merged.get("hedef_url", ""),
                merged.get("hedef_page_id"),
                merged.get("gosterim", "_self"),
                merged.get("izin_rol", ""),
                int(merged.get("sira", 0)),
                int(bool(merged.get("aktif", True))),
                merged.get("dil", ""),
                item_id,
            ),
        )
        return True

    def delete(self, item_id: int) -> bool:
        return self._execute("DELETE FROM menu_items WHERE id=?", (item_id,)) > 0

    def reorder(self, items: List[dict]) -> int:
        """Toplu yeniden sıralama (sürükle-bırak). items: [{id, parent_id, sira}]."""
        return self._execute_many(
            "UPDATE menu_items SET parent_id=?, sira=? WHERE id=?",
            [(it.get("parent_id"), int(it.get("sira", 0)), it["id"]) for it in items],
        )

    def exists(self, item_id: int) -> bool:
        return self._fetchone("SELECT 1 FROM menu_items WHERE id=?", (item_id,)) is not None

    def count_by_menu(self, menu_id: int) -> int:
        r = self._fetchone("SELECT COUNT(*) AS n FROM menu_items WHERE menu_id=?", (menu_id,))
        return r["n"] if r else 0
