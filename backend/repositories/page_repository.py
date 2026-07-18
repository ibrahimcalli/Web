"""Page Repository — pages tablosu veri erişim katmanı."""
from __future__ import annotations

from typing import List, Optional

from backend.db.database import Database, db, row_to_dict, rows_to_dicts
from backend.repositories.base import BaseRepository


class PageRepository(BaseRepository):
    def __init__(self, database: Optional[Database] = None):
        super().__init__(database)

    def get_by_id(self, page_id: int) -> Optional[dict]:
        return row_to_dict(
            self._fetchone("SELECT * FROM pages WHERE id=?", (page_id,))
        )

    def get_by_slug(self, slug: str) -> Optional[dict]:
        return row_to_dict(
            self._fetchone("SELECT * FROM pages WHERE slug=?", (slug,))
        )

    def get_all(self, durum: Optional[str] = None) -> List[dict]:
        sql = "SELECT * FROM pages"
        params = []
        if durum:
            sql += " WHERE durum=?"
            params.append(durum)
        sql += " ORDER BY guncelleme DESC"
        return rows_to_dicts(self._fetchall(sql, params))

    def create(self, data: dict) -> int:
        return self._execute(
            "INSERT INTO pages (baslik,slug,icerik,ozet,seo_baslik,seo_aciklama,"
            "seo_anahtar_kelimeler,kapak_resim,durum,sablon,yazar_id) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                data["baslik"], data["slug"], data.get("icerik", ""),
                data.get("ozet", ""), data.get("seo_baslik", ""),
                data.get("seo_aciklama", ""), data.get("seo_anahtar_kelimeler", ""),
                data.get("kapak_resim", ""), data.get("durum", "Taslak"),
                data.get("sablon", "default"), data.get("yazar_id"),
            ),
        )

    def update(self, page_id: int, data: dict) -> bool:
        existing = self.get_by_id(page_id)
        if not existing:
            return False
        merged = {**existing, **data, "id": page_id}
        self._execute(
            "UPDATE pages SET baslik=?,slug=?,icerik=?,ozet=?,"
            "seo_baslik=?,seo_aciklama=?,seo_anahtar_kelimeler=?,"
            "kapak_resim=?,durum=?,sablon=?,yazar_id=?,"
            "guncelleme=datetime('now') WHERE id=?",
            (
                merged["baslik"], merged["slug"], merged.get("icerik", ""),
                merged.get("ozet", ""), merged.get("seo_baslik", ""),
                merged.get("seo_aciklama", ""), merged.get("seo_anahtar_kelimeler", ""),
                merged.get("kapak_resim", ""), merged.get("durum", "Taslak"),
                merged.get("sablon", "default"), merged.get("yazar_id"),
                page_id,
            ),
        )
        return True

    def delete(self, page_id: int) -> bool:
        return self._execute("DELETE FROM pages WHERE id=?", (page_id,)) > 0

    def exists(self, page_id: int) -> bool:
        return self._fetchone("SELECT 1 FROM pages WHERE id=?", (page_id,)) is not None

    def slug_exists(self, slug: str, exclude_id: Optional[int] = None) -> bool:
        if exclude_id is None:
            return self._fetchone("SELECT 1 FROM pages WHERE slug=?", (slug,)) is not None
        return self._fetchone(
            "SELECT 1 FROM pages WHERE slug=? AND id<>?", (slug, exclude_id)
        ) is not None
