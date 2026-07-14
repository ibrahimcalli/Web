"""Fiyat analizi iş kuralları (SQL yok — repository üzerinden)."""
from __future__ import annotations

import re
from typing import Optional

from backend.core.errors import NotFoundError
from backend.repositories.misc_repository import AyarRepository
from backend.repositories.portfoy_repository import PortfoyRepository


def _m2_cikar(alanlar: dict) -> float:
    try:
        return float(alanlar.get("net_m2") or alanlar.get("alan_m2") or 0)
    except (ValueError, TypeError):
        return 0.0


def _fiyat_sayi(fiyat_str: str) -> float:
    try:
        temiz = re.sub(r"[^\d.,]", "", fiyat_str or "")
        temiz = temiz.replace(".", "").replace(",", ".")
        return float(temiz) if temiz else 0.0
    except (ValueError, TypeError):
        return 0.0


class FiyatAnalizService:
    def __init__(
        self,
        portfoyler: Optional[PortfoyRepository] = None,
        ayarlar: Optional[AyarRepository] = None,
    ):
        self.portfoyler = portfoyler or PortfoyRepository()
        self.ayarlar = ayarlar or AyarRepository()

    def portfoy_analizi(self, pid: int) -> dict:
        hedef = self.portfoyler.get(pid)
        if not hedef:
            raise NotFoundError("Portföy bulunamadı")
        hedef_m2 = _m2_cikar(hedef.get("alanlar") or {})
        hedef_fiyat = _fiyat_sayi(hedef.get("fiyat") or "")
        if hedef_m2 <= 0 or hedef_fiyat <= 0:
            return {
                "yeterli_veri": False,
                "mesaj": "Bu ilanda m² veya fiyat bilgisi eksik, analiz yapılamıyor.",
            }

        benzerler = [
            p
            for p in self.portfoyler.list(is_admin=True, durum="Aktif")
            if p["id"] != pid
            and p.get("ana_kategori") == hedef.get("ana_kategori")
            and p.get("alt_kategori") == hedef.get("alt_kategori")
        ]
        karsilastirma = []
        for b in benzerler:
            b_m2 = _m2_cikar(b.get("alanlar") or {})
            b_fiyat = _fiyat_sayi(b.get("fiyat") or "")
            if b_m2 > 0 and b_fiyat > 0:
                karsilastirma.append(
                    {
                        "id": b["id"],
                        "baslik": b["baslik"],
                        "mahalle": b.get("mahalle"),
                        "m2": b_m2,
                        "fiyat": b_fiyat,
                        "m2_fiyat": round(b_fiyat / b_m2, 2),
                    }
                )
        if len(karsilastirma) < 3:
            return {
                "yeterli_veri": False,
                "mesaj": f"Karşılaştırma için yeterli veri yok ({len(karsilastirma)} benzer ilan bulundu, minimum 3 gerekli).",
                "benzer_sayisi": len(karsilastirma),
            }

        m2_fiyatlari = sorted(k["m2_fiyat"] for k in karsilastirma)
        ortalama = sum(m2_fiyatlari) / len(m2_fiyatlari)
        medyan = m2_fiyatlari[len(m2_fiyatlari) // 2]
        hedef_m2_fiyat = round(hedef_fiyat / hedef_m2, 2)
        fark = round(((hedef_m2_fiyat - ortalama) / ortalama) * 100, 1)
        if fark > 15:
            durum, metin = "yuksek", "Piyasa Ortalamasının Üzerinde"
        elif fark < -15:
            durum, metin = "dusuk", "Piyasa Ortalamasının Altında"
        else:
            durum, metin = "uygun", "Piyasa Ortalamasına Yakın"

        return {
            "yeterli_veri": True,
            "hedef_m2_fiyat": hedef_m2_fiyat,
            "ortalama_m2_fiyat": round(ortalama, 2),
            "medyan_m2_fiyat": round(medyan, 2),
            "fark_yuzde": fark,
            "durum": durum,
            "durum_metin": metin,
            "benzer_sayisi": len(karsilastirma),
            "en_yakin_3": sorted(karsilastirma, key=lambda x: abs(x["m2_fiyat"] - hedef_m2_fiyat))[:3],
            "ai_yorum": None,
            "baslik": hedef.get("baslik"),
            "tahmin": hedef.get("fiyat"),
        }

    def genel(self) -> dict:
        liste = self.portfoyler.list_for_fiyat()
        gruplar = {}
        for p in liste:
            kat = p.get("ana_kategori") or "?"
            m2 = _m2_cikar(p.get("alanlar") or {})
            fiyat = _fiyat_sayi(p.get("fiyat") or "")
            if m2 <= 0 or fiyat <= 0:
                continue
            gruplar.setdefault(kat, []).append(fiyat / m2)
        veri = []
        for kat, vals in gruplar.items():
            veri.append(
                {
                    "kategori": kat,
                    "ilan_sayisi": len(vals),
                    "min_m2_fiyat": round(min(vals), 2),
                    "ortalama_m2_fiyat": round(sum(vals) / len(vals), 2),
                    "max_m2_fiyat": round(max(vals), 2),
                }
            )
        return {"ozet": "Genel m² fiyat analizi", "veri": veri, "mesaj": "OK"}
