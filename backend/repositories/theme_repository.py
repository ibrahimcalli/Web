"""Theme Repository — theme_settings tablosu veri erişim katmanı (key-value)."""
from __future__ import annotations

from typing import Dict, List, Optional

from backend.db.database import Database, db, row_to_dict, rows_to_dicts
from backend.repositories.base import BaseRepository


class ThemeRepository(BaseRepository):
    def __init__(self, database: Optional[Database] = None):
        super().__init__(database)

    def get(self, anahtar: str) -> Optional[dict]:
        return row_to_dict(
            self._fetchone("SELECT * FROM theme_settings WHERE anahtar=?", (anahtar,))
        )

    def get_all(self) -> Dict[str, str]:
        rows = self._fetchall("SELECT anahtar, deger FROM theme_settings")
        return {r["anahtar"]: r["deger"] for r in rows}

    def set(self, anahtar: str, deger: str) -> bool:
        self._execute(
            "INSERT OR REPLACE INTO theme_settings (anahtar, deger) VALUES (?,?)",
            (anahtar, deger),
        )
        return True

    def set_many(self, settings: Dict[str, str]) -> int:
        if not settings:
            return 0
        rows = [(k, v) for k, v in settings.items()]
        return self._execute_many(
            "INSERT OR REPLACE INTO theme_settings (anahtar, deger) VALUES (?,?)",
            rows,
        )

    def delete(self, anahtar: str) -> bool:
        return self._execute("DELETE FROM theme_settings WHERE anahtar=?", (anahtar,)) > 0

    def exists(self, anahtar: str) -> bool:
        return self._fetchone("SELECT 1 FROM theme_settings WHERE anahtar=?", (anahtar,)) is not None
