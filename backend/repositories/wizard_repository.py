"""Site Wizard Repository — wizard_state CRUD."""
from __future__ import annotations

from typing import Any, Optional

from backend.db.database import Database


class WizardRepository:
    def __init__(self, database: Database) -> None:
        self.db = database

    def getir(self) -> Optional[dict]:
        conn = self.db.connect()
        row = conn.execute("SELECT * FROM wizard_states ORDER BY id DESC LIMIT 1").fetchone()
        conn.close()
        if row:
            d = dict(row)
            if isinstance(d.get("veri"), str):
                import json
                d["veri"] = json.loads(d["veri"])
            return d
        return None

    def baslat(self) -> int:
        conn = self.db.connect()
        c = conn.cursor()
        c.execute("INSERT INTO wizard_states (adim, tamamlandi, veri) VALUES (1, 0, '{}')")
        conn.commit()
        wid = c.lastrowid
        conn.close()
        return wid

    def kaydet(self, wizard_id: int, adim: int, veri: dict) -> None:
        import json
        conn = self.db.connect()
        c = conn.cursor()
        existing = c.execute("SELECT veri FROM wizard_states WHERE id=?", (wizard_id,)).fetchone()
        current = json.loads(existing["veri"]) if existing and isinstance(existing["veri"], str) else {}
        current.update(veri)
        c.execute(
            "UPDATE wizard_states SET adim=?, veri=?, guncelleme=datetime('now') WHERE id=?",
            (adim, json.dumps(current, ensure_ascii=False), wizard_id),
        )
        conn.commit()
        conn.close()

    def tamamla(self, wizard_id: int) -> None:
        conn = self.db.connect()
        conn.execute("UPDATE wizard_states SET tamamlandi=1, guncelleme=datetime('now') WHERE id=?", (wizard_id,))
        conn.commit()
        conn.close()

    def sil(self, wizard_id: int) -> None:
        conn = self.db.connect()
        conn.execute("DELETE FROM wizard_states WHERE id=?", (wizard_id,))
        conn.commit()
        conn.close()


class LicenseRepository:
    def __init__(self, database: Database) -> None:
        self.db = database

    def listele(self) -> list:
        conn = self.db.connect()
        rows = conn.execute("SELECT * FROM licenses ORDER BY id").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def getir(self, lid: int) -> Optional[dict]:
        conn = self.db.connect()
        row = conn.execute("SELECT * FROM licenses WHERE id=?", (lid,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def olustur(self, data: dict) -> int:
        conn = self.db.connect()
        c = conn.cursor()
        c.execute(
            "INSERT INTO licenses (firma_adi, domain, paket, aktif) VALUES (?,?,?,1)",
            (data["firma_adi"], data["domain"], data.get("paket", "free")),
        )
        conn.commit()
        lid = c.lastrowid
        conn.close()
        return lid

    def guncelle(self, lid: int, data: dict) -> None:
        import json
        sets = ", ".join(f"{k}=?" for k in data)
        vals = list(data.values()) + [lid]
        conn = self.db.connect()
        conn.execute(f"UPDATE licenses SET {sets} WHERE id=?", vals)
        conn.commit()
        conn.close()

    def domain_bul(self, domain: str) -> Optional[dict]:
        conn = self.db.connect()
        row = conn.execute("SELECT * FROM multi_tenant_domains WHERE domain=? AND aktif=1", (domain,)).fetchone()
        conn.close()
        return dict(row) if row else None


class PluginRepository:
    def __init__(self, database: Database) -> None:
        self.db = database

    def listele(self) -> list:
        conn = self.db.connect()
        rows = conn.execute("SELECT * FROM plugins ORDER BY id").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def getir(self, pid: int) -> Optional[dict]:
        conn = self.db.connect()
        row = conn.execute("SELECT * FROM plugins WHERE id=?", (pid,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def anahtar_ile_getir(self, anahtar: str) -> Optional[dict]:
        conn = self.db.connect()
        row = conn.execute("SELECT * FROM plugins WHERE anahtar=?", (anahtar,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def aktif_degistir(self, pid: int) -> bool:
        conn = self.db.connect()
        row = conn.execute("SELECT aktif FROM plugins WHERE id=?", (pid,)).fetchone()
        if not row:
            conn.close()
            return False
        yeni = 0 if row["aktif"] else 1
        conn.execute("UPDATE plugins SET aktif=? WHERE id=?", (yeni, pid))
        conn.commit()
        conn.close()
        return bool(yeni)

    def ayarlar_guncelle(self, pid: int, ayarlar: dict) -> None:
        import json
        conn = self.db.connect()
        conn.execute("UPDATE plugins SET ayarlar=? WHERE id=?", (json.dumps(ayarlar), pid))
        conn.commit()
        conn.close()
