"""Widget Repository — widgets tablosu veri erişim katmanı."""
from __future__ import annotations

from typing import List, Optional

from backend.db.database import Database, db, row_to_dict, rows_to_dicts
from backend.repositories.base import BaseRepository


class WidgetRepository(BaseRepository):
    def __init__(self, database: Optional[Database] = None):
        super().__init__(database)

    def get_by_id(self, wid: int) -> Optional[dict]:
        return row_to_dict(
            self._fetchone("SELECT * FROM widgets WHERE id=?", (wid,))
        )

    def get_by_anahtar(self, anahtar: str) -> Optional[dict]:
        return row_to_dict(
            self._fetchone("SELECT * FROM widgets WHERE anahtar=?", (anahtar,))
        )

    def get_all(self, aktif_only: bool = False) -> List[dict]:
        sql = "SELECT * FROM widgets"
        if aktif_only:
            sql += " WHERE aktif=1"
        sql += " ORDER BY sira, id"
        return rows_to_dicts(self._fetchall(sql))

    def create(self, data: dict) -> int:
        return self._execute(
            "INSERT INTO widgets (anahtar,ad,aciklama,tip,aktif,ayarlar,konum,sira) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (
                data["anahtar"], data["ad"], data.get("aciklama", ""),
                data.get("tip", "embed"), int(bool(data.get("aktif", False))),
                data.get("ayarlar", "{}"), data.get("konum", ""),
                int(data.get("sira", 0)),
            ),
        )

    def update(self, wid: int, data: dict) -> bool:
        existing = self.get_by_id(wid)
        if not existing:
            return False
        merged = {**existing, **data, "id": wid}
        self._execute(
            "UPDATE widgets SET ad=?,aciklama=?,tip=?,aktif=?,ayarlar=?,"
            "konum=?,sira=?,guncelleme=datetime('now') WHERE id=?",
            (
                merged["ad"], merged.get("aciklama", ""),
                merged.get("tip", "embed"), int(bool(merged.get("aktif", False))),
                merged.get("ayarlar", "{}"), merged.get("konum", ""),
                int(merged.get("sira", 0)), wid,
            ),
        )
        return True

    def delete(self, wid: int) -> bool:
        return self._execute("DELETE FROM widgets WHERE id=?", (wid,)) > 0

    def exists(self, wid: int) -> bool:
        return self._fetchone("SELECT 1 FROM widgets WHERE id=?", (wid,)) is not None

    def anahtar_exists(self, anahtar: str, exclude_id: Optional[int] = None) -> bool:
        if exclude_id is None:
            return self._fetchone("SELECT 1 FROM widgets WHERE anahtar=?", (anahtar,)) is not None
        return self._fetchone(
            "SELECT 1 FROM widgets WHERE anahtar=? AND id<>?", (anahtar, exclude_id)
        ) is not None
