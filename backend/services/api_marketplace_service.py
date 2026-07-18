"""API Marketplace Service — Üçüncü parti API entegrasyonları."""
from __future__ import annotations

import json
from typing import Any, Optional

from backend.db.database import Database, db


class ApiMarketplaceService:
    SAGLAYICILAR = {
        "openai": {"ad": "OpenAI", "varsayilan_url": "https://api.openai.com/v1"},
        "gemini": {"ad": "Google Gemini", "varsayilan_url": "https://generativelanguage.googleapis.com/v1"},
        "claude": {"ad": "Anthropic Claude", "varsayilan_url": "https://api.anthropic.com/v1"},
        "google_maps": {"ad": "Google Maps", "varsayilan_url": "https://maps.googleapis.com/maps/api"},
        "whatsapp": {"ad": "WhatsApp Business API", "varsayilan_url": "https://graph.facebook.com/v18.0"},
        "sms": {"ad": "SMS Servisi", "varsayilan_url": ""},
        "mail": {"ad": "E-Posta Servisi", "varsayilan_url": ""},
        "muhasebe": {"ad": "Muhasebe Entegrasyonu", "varsayilan_url": ""},
        "e-imza": {"ad": "E-İmza", "varsayilan_url": ""},
    }

    def __init__(self, database: Optional[Database] = None):
        self.db = database or db

    def saglayici_listesi(self) -> list:
        return [{"key": k, **v} for k, v in self.SAGLAYICILAR.items()]

    def listele(self) -> list:
        conn = self.db.connect()
        rows = conn.execute("SELECT * FROM api_integrations ORDER BY id").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def getir(self, aid: int) -> Optional[dict]:
        conn = self.db.connect()
        row = conn.execute("SELECT * FROM api_integrations WHERE id=?", (aid,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def saglayici_ile_getir(self, saglayici: str) -> Optional[dict]:
        conn = self.db.connect()
        row = conn.execute("SELECT * FROM api_integrations WHERE saglayici=?", (saglayici,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def seed(self) -> int:
        eklenen = 0
        conn = self.db.connect()
        c = conn.cursor()
        for key, meta in self.SAGLAYICILAR.items():
            exists = c.execute("SELECT 1 FROM api_integrations WHERE saglayici=?", (key,)).fetchone()
            if not exists:
                c.execute(
                    "INSERT INTO api_integrations (saglayici, ad, api_url, aktif) VALUES (?,?,?,0)",
                    (key, meta["ad"], meta.get("varsayilan_url", "")),
                )
                eklenen += 1
        conn.commit()
        conn.close()
        return eklenen

    def kaydet(self, saglayici: str, data: dict) -> dict:
        conn = self.db.connect()
        c = conn.cursor()
        existing = c.execute("SELECT id FROM api_integrations WHERE saglayici=?", (saglayici,)).fetchone()
        if existing:
            sets = []
            vals = []
            for k in ("api_key", "api_url", "aktif"):
                if k in data:
                    sets.append(f"{k}=?")
                    vals.append(data[k])
            if "ayarlar" in data:
                sets.append("ayarlar=?")
                vals.append(json.dumps(data["ayarlar"]))
            if sets:
                sets.append("guncelleme=datetime('now')")
                vals.append(existing["id"])
                c.execute(f"UPDATE api_integrations SET {', '.join(sets)} WHERE id=?", vals)
            sonuc = {"id": existing["id"], "saglayici": saglayici, "guncellendi": True}
        else:
            meta = self.SAGLAYICILAR.get(saglayici, {"ad": saglayici})
            c.execute(
                "INSERT INTO api_integrations (saglayici, ad, api_key, api_url, aktif, ayarlar) VALUES (?,?,?,?,?,?)",
                (saglayici, meta["ad"], data.get("api_key", ""), data.get("api_url", meta.get("varsayilan_url", "")),
                 int(bool(data.get("aktif", False))), json.dumps(data.get("ayarlar", {}))),
            )
            sonuc = {"id": c.lastrowid, "saglayici": saglayici, "olusturuldu": True}
        conn.commit()
        conn.close()
        return sonuc

    def toggle(self, saglayici: str) -> Optional[bool]:
        mevcut = self.saglayici_ile_getir(saglayici)
        if not mevcut:
            self.kaydet(saglayici, {"aktif": True})
            return True
        yeni = 0 if mevcut["aktif"] else 1
        conn = self.db.connect()
        conn.execute("UPDATE api_integrations SET aktif=?, guncelleme=datetime('now') WHERE saglayici=?", (yeni, saglayici))
        conn.commit()
        conn.close()
        return bool(yeni)

    def test_et(self, saglayici: str) -> dict:
        ent = self.saglayici_ile_getir(saglayici)
        if not ent or not ent["aktif"] or not ent["api_key"]:
            return {"success": False, "message": "API aktif değil veya anahtar eksik"}
        return {"success": True, "message": f"{ent['ad']} bağlantısı başarılı"}
