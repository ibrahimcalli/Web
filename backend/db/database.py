"""Veritabanı soyutlaması — SQLite bugün, PostgreSQL yarın (yalnızca bu katman değişir)."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Any, Iterator, List, Optional, Protocol, Sequence

from backend.core.config import DB_PATH


class CursorLike(Protocol):
    lastrowid: int

    def execute(self, sql: str, params: Sequence[Any] = ()) -> Any: ...
    def fetchone(self) -> Any: ...
    def fetchall(self) -> list: ...


class ConnectionLike(Protocol):
    def execute(self, sql: str, params: Sequence[Any] = ()) -> CursorLike: ...
    def cursor(self) -> CursorLike: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
    def close(self) -> None: ...
    def executescript(self, script: str) -> Any: ...


class Database:
    """
    Bağlantı fabrikası.

    PostgreSQL geçişinde yalnızca `connect()` ve belki SQL diyalekti değişir;
    repository imzaları aynı kalır.
    """

    def __init__(self, path: Optional[str] = None):
        self.path = str(path or DB_PATH)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    @contextmanager
    def session(self) -> Iterator[sqlite3.Connection]:
        conn = self.connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


# Uygulama geneli varsayılan DB örneği (testlerde override edilir)
db = Database()


def row_to_dict(row: Any) -> Optional[dict]:
    if row is None:
        return None
    return dict(row)


def rows_to_dicts(rows: Sequence[Any]) -> List[dict]:
    return [dict(r) for r in rows]
