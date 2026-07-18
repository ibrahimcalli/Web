"""Backup Service — Veritabanı yedekleme."""
from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from backend.core.settings import BASE_DIR
from backend.db.database import Database, db


class BackupService:
    def __init__(self, database: Optional[Database] = None):
        self.db = database or db
        self.backup_dir = BASE_DIR / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def listele(self) -> list:
        conn = self.db.connect()
        rows = conn.execute("SELECT * FROM backups ORDER BY id DESC").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def olustur(self, tur: str = "manuel", hedef: str = "local") -> dict:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        dosya_adi = f"emlak_yedek_{ts}.db"
        dosya_yolu = self.backup_dir / dosya_adi

        db_path = self.db.path
        try:
            import shutil
            shutil.copy2(db_path, dosya_yolu)
            boyut = dosya_yolu.stat().st_size

            conn = self.db.connect()
            c = conn.cursor()
            c.execute(
                "INSERT INTO backups (dosya_adi, boyut, tur, hedef, durum) VALUES (?,?,?,?,?)",
                (dosya_adi, boyut, tur, hedef, "tamam"),
            )
            conn.commit()
            conn.close()

            return {"success": True, "dosya_adi": dosya_adi, "boyut": boyut, "tarih": ts}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def geri_yukle(self, backup_id: int) -> dict:
        conn = self.db.connect()
        row = conn.execute("SELECT * FROM backups WHERE id=?", (backup_id,)).fetchone()
        conn.close()
        if not row:
            return {"success": False, "error": "Yedek bulunamadı"}
        dosya_yolu = self.backup_dir / row["dosya_adi"]
        if not dosya_yolu.exists():
            return {"success": False, "error": "Yedek dosyası bulunamadı"}
        try:
            shutil.copy2(dosya_yolu, self.db.path)
            return {"success": True, "message": "Yedek geri yüklendi"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def sil(self, backup_id: int) -> bool:
        conn = self.db.connect()
        row = conn.execute("SELECT dosya_adi FROM backups WHERE id=?", (backup_id,)).fetchone()
        if row:
            dosya = self.backup_dir / row["dosya_adi"]
            if dosya.exists():
                dosya.unlink()
            conn.execute("DELETE FROM backups WHERE id=?", (backup_id,))
            conn.commit()
            conn.close()
            return True
        conn.close()
        return False

    def otomatik_yedekle(self) -> dict:
        return self.olustur(tur="otomatik", hedef="local")
