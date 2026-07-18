"""Template Repository — templates ve homepage_sections tabloları."""
from __future__ import annotations

from typing import List, Optional

from backend.db.database import Database, db, row_to_dict, rows_to_dicts
from backend.repositories.base import BaseRepository


class TemplateRepository(BaseRepository):
    def __init__(self, database: Optional[Database] = None):
        super().__init__(database)

    def get_by_id(self, tid: int) -> Optional[dict]:
        return row_to_dict(self._fetchone("SELECT * FROM templates WHERE id=?", (tid,)))

    def get_by_slug(self, slug: str) -> Optional[dict]:
        return row_to_dict(self._fetchone("SELECT * FROM templates WHERE slug=?", (slug,)))

    def get_default(self) -> Optional[dict]:
        return row_to_dict(self._fetchone("SELECT * FROM templates WHERE varsayilan=1 AND aktif=1 LIMIT 1"))

    def get_all(self, aktif_only: bool = False) -> List[dict]:
        sql = "SELECT * FROM templates"
        if aktif_only:
            sql += " WHERE aktif=1"
        sql += " ORDER BY ad"
        return rows_to_dicts(self._fetchall(sql))

    def create(self, data: dict) -> int:
        return self._execute(
            "INSERT INTO templates (slug,ad,aciklama,klasor,aktif,varsayilan) VALUES (?,?,?,?,?,?)",
            (data["slug"], data["ad"], data.get("aciklama", ""), data.get("klasor", data["slug"]),
             int(bool(data.get("aktif", True))), int(bool(data.get("varsayilan", False)))),
        )

    def update(self, tid: int, data: dict) -> bool:
        existing = self.get_by_id(tid)
        if not existing:
            return False
        merged = {**existing, **data, "id": tid}
        self._execute(
            "UPDATE templates SET slug=?,ad=?,aciklama=?,klasor=?,aktif=?,varsayilan=? WHERE id=?",
            (merged["slug"], merged["ad"], merged.get("aciklama", ""), merged.get("klasor", merged["slug"]),
             int(bool(merged.get("aktif", True))), int(bool(merged.get("varsayilan", False))), tid),
        )
        return True

    def delete(self, tid: int) -> bool:
        return self._execute("DELETE FROM templates WHERE id=?", (tid,)) > 0

    def exists(self, tid: int) -> bool:
        return self._fetchone("SELECT 1 FROM templates WHERE id=?", (tid,)) is not None

    def slug_exists(self, slug: str, exclude_id: Optional[int] = None) -> bool:
        if exclude_id is None:
            return self._fetchone("SELECT 1 FROM templates WHERE slug=?", (slug,)) is not None
        return self._fetchone("SELECT 1 FROM templates WHERE slug=? AND id<>?", (slug, exclude_id)) is not None

    def set_default(self, tid: int) -> None:
        self._execute("UPDATE templates SET varsayilan=0 WHERE varsayilan=1")
        self._execute("UPDATE templates SET varsayilan=1 WHERE id=?", (tid,))


class HomepageSectionRepository(BaseRepository):
    def __init__(self, database: Optional[Database] = None):
        super().__init__(database)

    def get_by_id(self, sid: int) -> Optional[dict]:
        return row_to_dict(self._fetchone("SELECT * FROM homepage_sections WHERE id=?", (sid,)))

    def get_by_template(self, template_id: int, aktif_only: bool = False) -> List[dict]:
        sql = "SELECT * FROM homepage_sections WHERE template_id=?"
        if aktif_only:
            sql += " AND aktif=1"
        sql += " ORDER BY sira, id"
        return rows_to_dicts(self._fetchall(sql, (template_id,)))

    def get_by_template_and_key(self, template_id: int, section_key: str) -> Optional[dict]:
        return row_to_dict(self._fetchone(
            "SELECT * FROM homepage_sections WHERE template_id=? AND section_key=?", (template_id, section_key)
        ))

    def create(self, data: dict) -> int:
        return self._execute(
            "INSERT INTO homepage_sections (template_id,section_key,baslik,aktif,sira,ayarlar) VALUES (?,?,?,?,?,?)",
            (data["template_id"], data["section_key"], data.get("baslik", ""),
             int(bool(data.get("aktif", True))), int(data.get("sira", 0)), data.get("ayarlar", "{}")),
        )

    def update(self, sid: int, data: dict) -> bool:
        existing = self.get_by_id(sid)
        if not existing:
            return False
        merged = {**existing, **data, "id": sid}
        self._execute(
            "UPDATE homepage_sections SET baslik=?,aktif=?,sira=?,ayarlar=? WHERE id=?",
            (merged["baslik"], int(bool(merged.get("aktif", True))),
             int(merged.get("sira", 0)), merged.get("ayarlar", "{}"), sid),
        )
        return True

    def delete(self, sid: int) -> bool:
        return self._execute("DELETE FROM homepage_sections WHERE id=?", (sid,)) > 0

    def exists(self, sid: int) -> bool:
        return self._fetchone("SELECT 1 FROM homepage_sections WHERE id=?", (sid,)) is not None

    def reorder(self, items: List[dict]) -> int:
        return self._execute_many(
            "UPDATE homepage_sections SET sira=? WHERE id=?",
            [(int(it.get("sira", 0)), it["id"]) for it in items],
        )
