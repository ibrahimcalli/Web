"""Tenant Service — Multi-tenant domain yönetimi."""
from __future__ import annotations

from typing import Optional

from backend.db.database import Database, db


class TenantService:
    def __init__(self, database: Optional[Database] = None):
        self.db = database or db

    def domain_bul(self, domain: str) -> Optional[dict]:
        conn = self.db.connect()
        row = conn.execute(
            "SELECT mt.*, l.paket, l.aktif as lisans_aktif FROM multi_tenant_domains mt "
            "LEFT JOIN licenses l ON mt.license_id = l.id "
            "WHERE mt.domain=? AND mt.aktif=1", (domain,)
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    def listele(self) -> list:
        conn = self.db.connect()
        rows = conn.execute(
            "SELECT mt.*, l.paket, l.firma_adi as lisans_firma FROM multi_tenant_domains mt "
            "LEFT JOIN licenses l ON mt.license_id = l.id ORDER BY mt.id"
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def ekle(self, data: dict) -> int:
        conn = self.db.connect()
        c = conn.cursor()
        c.execute(
            "INSERT INTO multi_tenant_domains (domain, firma_adi, license_id) VALUES (?,?,?)",
            (data["domain"], data["firma_adi"], data.get("license_id")),
        )
        conn.commit()
        lid = c.lastrowid
        conn.close()
        return lid

    def guncelle(self, tid: int, data: dict) -> bool:
        sets = ", ".join(f"{k}=?" for k in data)
        vals = list(data.values()) + [tid]
        conn = self.db.connect()
        c = conn.cursor()
        c.execute(f"UPDATE multi_tenant_domains SET {sets} WHERE id=?", vals)
        conn.commit()
        affected = c.rowcount
        conn.close()
        return affected > 0

    def sil(self, tid: int) -> bool:
        conn = self.db.connect()
        c = conn.cursor()
        c.execute("DELETE FROM multi_tenant_domains WHERE id=?", (tid,))
        conn.commit()
        affected = c.rowcount
        conn.close()
        return affected > 0
