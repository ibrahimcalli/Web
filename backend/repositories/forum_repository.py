"""Forum Repository — forum kategorileri, konular, yanıtlar ve ayarlar."""
from __future__ import annotations

from typing import List, Optional

from backend.db.database import Database, db, row_to_dict, rows_to_dicts
from backend.repositories.base import BaseRepository


class ForumCategoryRepository(BaseRepository):
    def __init__(self, database: Optional[Database] = None):
        super().__init__(database)

    def get_by_id(self, cat_id: int) -> Optional[dict]:
        return row_to_dict(
            self._fetchone("SELECT * FROM forum_categories WHERE id=?", (cat_id,))
        )

    def get_by_slug(self, slug: str) -> Optional[dict]:
        return row_to_dict(
            self._fetchone("SELECT * FROM forum_categories WHERE slug=?", (slug,))
        )

    def get_all(self, aktif_only: bool = False) -> List[dict]:
        sql = "SELECT * FROM forum_categories"
        if aktif_only:
            sql += " WHERE aktif=1"
        sql += " ORDER BY sira, id"
        return rows_to_dicts(self._fetchall(sql))

    def create(self, data: dict) -> int:
        return self._execute(
            "INSERT INTO forum_categories (slug,ad,aciklama,sira,aktif) VALUES (?,?,?,?,?)",
            (
                data["slug"], data["ad"], data.get("aciklama", ""),
                int(data.get("sira", 0)), int(bool(data.get("aktif", True))),
            ),
        )

    def update(self, cat_id: int, data: dict) -> bool:
        existing = self.get_by_id(cat_id)
        if not existing:
            return False
        merged = {**existing, **data, "id": cat_id}
        self._execute(
            "UPDATE forum_categories SET ad=?,aciklama=?,sira=?,aktif=? WHERE id=?",
            (
                merged["ad"], merged.get("aciklama", ""),
                int(merged.get("sira", 0)), int(bool(merged.get("aktif", True))),
                cat_id,
            ),
        )
        return True

    def delete(self, cat_id: int) -> bool:
        return self._execute("DELETE FROM forum_categories WHERE id=?", (cat_id,)) > 0

    def exists(self, cat_id: int) -> bool:
        return self._fetchone("SELECT 1 FROM forum_categories WHERE id=?", (cat_id,)) is not None

    def slug_exists(self, slug: str, exclude_id: Optional[int] = None) -> bool:
        if exclude_id is None:
            return self._fetchone("SELECT 1 FROM forum_categories WHERE slug=?", (slug,)) is not None
        return self._fetchone(
            "SELECT 1 FROM forum_categories WHERE slug=? AND id<>?", (slug, exclude_id)
        ) is not None


class ForumTopicRepository(BaseRepository):
    def __init__(self, database: Optional[Database] = None):
        super().__init__(database)

    def get_by_id(self, topic_id: int) -> Optional[dict]:
        return row_to_dict(
            self._fetchone("SELECT * FROM forum_topics WHERE id=?", (topic_id,))
        )

    def get_by_slug(self, slug: str) -> Optional[dict]:
        return row_to_dict(
            self._fetchone("SELECT * FROM forum_topics WHERE slug=?", (slug,))
        )

    def get_by_category(self, cat_id: int) -> List[dict]:
        sql = "SELECT * FROM forum_topics WHERE category_id=? ORDER BY sabit DESC, olusturma DESC"
        return rows_to_dicts(self._fetchall(sql, (cat_id,)))

    def get_all(self) -> List[dict]:
        return rows_to_dicts(self._fetchall(
            "SELECT * FROM forum_topics ORDER BY sabit DESC, olusturma DESC"
        ))

    def create(self, data: dict) -> int:
        slug = data.get("slug") or data.get("baslik", "").lower().replace(" ", "-")
        return self._execute(
            "INSERT INTO forum_topics (category_id,baslik,slug,icerik,"
            "kullanici_id,kullanici_ad,sabit,kapali,durum) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (
                data["category_id"], data["baslik"], slug,
                data.get("icerik", ""), data.get("kullanici_id"),
                data.get("kullanici_ad", ""),
                int(bool(data.get("sabit", False))),
                int(bool(data.get("kapali", False))),
                data.get("durum", "yayin"),
            ),
        )

    def update(self, topic_id: int, data: dict) -> bool:
        existing = self.get_by_id(topic_id)
        if not existing:
            return False
        merged = {**existing, **data, "id": topic_id}
        self._execute(
            "UPDATE forum_topics SET baslik=?,icerik=?,"
            "sabit=?,kapali=?,durum=?,guncelleme=datetime('now') WHERE id=?",
            (
                merged["baslik"], merged.get("icerik", ""),
                int(bool(merged.get("sabit", False))),
                int(bool(merged.get("kapali", False))),
                merged.get("durum", "yayin"), topic_id,
            ),
        )
        return True

    def increment_goruntuleme(self, topic_id: int) -> bool:
        return self._execute(
            "UPDATE forum_topics SET goruntuleme=goruntuleme+1 WHERE id=?",
            (topic_id,),
        ) > 0

    def delete(self, topic_id: int) -> bool:
        return self._execute("DELETE FROM forum_topics WHERE id=?", (topic_id,)) > 0

    def exists(self, topic_id: int) -> bool:
        return self._fetchone("SELECT 1 FROM forum_topics WHERE id=?", (topic_id,)) is not None


class ForumPostRepository(BaseRepository):
    def __init__(self, database: Optional[Database] = None):
        super().__init__(database)

    def get_by_id(self, post_id: int) -> Optional[dict]:
        return row_to_dict(
            self._fetchone("SELECT * FROM forum_posts WHERE id=?", (post_id,))
        )

    def get_by_topic(self, topic_id: int) -> List[dict]:
        return rows_to_dicts(self._fetchall(
            "SELECT * FROM forum_posts WHERE topic_id=? AND durum!='silindi' "
            "ORDER BY olusturma", (topic_id,)
        ))

    def create(self, data: dict) -> int:
        return self._execute(
            "INSERT INTO forum_posts (topic_id,parent_id,icerik,"
            "kullanici_id,kullanici_ad,ip,durum) VALUES (?,?,?,?,?,?,?)",
            (
                data["topic_id"], data.get("parent_id"),
                data["icerik"], data.get("kullanici_id"),
                data.get("kullanici_ad", ""), data.get("ip", ""),
                data.get("durum", "yayin"),
            ),
        )

    def update(self, post_id: int, data: dict) -> bool:
        existing = self.get_by_id(post_id)
        if not existing:
            return False
        merged = {**existing, **data, "id": post_id}
        self._execute(
            "UPDATE forum_posts SET icerik=?,durum=? WHERE id=?",
            (merged["icerik"], merged.get("durum", "yayin"), post_id),
        )
        return True

    def delete(self, post_id: int) -> bool:
        return self._execute("DELETE FROM forum_posts WHERE id=?", (post_id,)) > 0

    def exists(self, post_id: int) -> bool:
        return self._fetchone("SELECT 1 FROM forum_posts WHERE id=?", (post_id,)) is not None


class ForumSettingRepository(BaseRepository):
    def __init__(self, database: Optional[Database] = None):
        super().__init__(database)

    def get(self, anahtar: str) -> Optional[dict]:
        return row_to_dict(
            self._fetchone("SELECT * FROM forum_settings WHERE anahtar=?", (anahtar,))
        )

    def get_all(self) -> dict:
        rows = self._fetchall("SELECT anahtar, deger FROM forum_settings")
        return {r["anahtar"]: r["deger"] for r in rows}

    def set(self, anahtar: str, deger: str) -> bool:
        self._execute(
            "INSERT OR REPLACE INTO forum_settings (anahtar, deger) VALUES (?,?)",
            (anahtar, deger),
        )
        return True
