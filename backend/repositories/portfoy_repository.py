"""Portföy Repository - PostgreSQL uyumlu implementasyon."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from backend.repositories.base import BaseRepository
from backend.db.database import row_to_dict, rows_to_dicts


def _decode_portfoy(row) -> Optional[dict]:
    """Portföy satırını decode et (JSON alanları)."""
    if row is None:
        return None
    d = dict(row)
    d["alanlar"] = json.loads(d.get("alanlar") or "{}")
    d["resimler"] = json.loads(d.get("resimler") or "[]")
    return d


class PortfoyRepository(BaseRepository):
    """
    Portföy CRUD operasyonları.
    
    PostgreSQL geçişinde bu sınıfın SQL sorguları değişir,
    interface ve service katmanı aynı kalır.
    """
    
    def list(
        self,
        *,
        is_admin: bool = False,
        durum: str = "Aktif",
        kategori: str = "",
        alt_kat: str = "",
        arama: str = "",
    ) -> List[dict]:
        """
        Portföy listesi getir.
        
        Args:
            is_admin: Admin mi?
            durum: Durum filtresi
            kategori: Ana kategori filtresi
            alt_kat: Alt kategori filtresi
            arama: Arama metni
            
        Returns:
            Portföy listesi
        """
        q = "SELECT * FROM portfoyler WHERE 1=1"
        args: list = []
        
        if not is_admin:
            q += " AND durum='Aktif'"
        elif durum:
            q += " AND durum=?"
            args.append(durum)
            
        if kategori:
            q += " AND ana_kategori=?"
            args.append(kategori)
            
        if alt_kat:
            q += " AND alt_kategori=?"
            args.append(alt_kat)
            
        if arama:
            q += " AND (baslik LIKE ? OR mahalle LIKE ? OR ilce LIKE ?)"
            args += [f"%{arama}%"] * 3
            
        q += " ORDER BY guncelleme DESC"
        
        return [_decode_portfoy(r) for r in self._fetchall(q, args)]
    
    def get(self, pid: int) -> Optional[dict]:
        """
        Portföy getir.
        
        Args:
            pid: Portföy ID
            
        Returns:
            Portföy dict veya None
        """
        return _decode_portfoy(
            self._fetchone("SELECT * FROM portfoyler WHERE id=?", (pid,))
        )
    
    def create(self, p: Any) -> int:
        """
        Portföy oluştur.
        
        Args:
            p: PortföyCreate/PortfoyUpdate objesi
            
        Returns:
            Oluşturulan portföy ID
        """
        sql = """
            INSERT INTO portfoyler
            (baslik,ana_kategori,alt_kategori,ilan_tipi,il,ilce,mahalle,
             fiyat,para_birimi,aciklama,saha_notu,gps,durum,alanlar,
             musteri_ad,musteri_tel,musteri_mail,musteri_not,sahip_goster,kaynak)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'web')
        """
        return self._execute(
            sql,
            (
                p.baslik, p.ana_kategori, p.alt_kategori, p.ilan_tipi,
                p.il, p.ilce, p.mahalle, p.fiyat, p.para_birimi,
                p.aciklama, p.saha_notu, p.gps, p.durum,
                json.dumps(p.alanlar or {}, ensure_ascii=False),
                p.musteri_ad, p.musteri_tel, p.musteri_mail,
                p.musteri_not, p.sahip_goster,
            ),
        )
    
    def update(self, pid: int, p: Any) -> None:
        """
        Portföy güncelle.
        
        Args:
            pid: Portföy ID
            p: PortföyUpdate objesi
        """
        self._execute(
            """
            UPDATE portfoyler SET
            baslik=?,ana_kategori=?,alt_kategori=?,ilan_tipi=?,
            il=?,ilce=?,mahalle=?,fiyat=?,para_birimi=?,
            aciklama=?,saha_notu=?,gps=?,durum=?,alanlar=?,
            musteri_ad=?,musteri_tel=?,musteri_mail=?,musteri_not=?,sahip_goster=?,
            guncelleme=datetime('now')
            WHERE id=?
            """,
            (
                p.baslik, p.ana_kategori, p.alt_kategori, p.ilan_tipi,
                p.il, p.ilce, p.mahalle, p.fiyat, p.para_birimi,
                p.aciklama, p.saha_notu, p.gps, p.durum,
                json.dumps(p.alanlar or {}, ensure_ascii=False),
                p.musteri_ad, p.musteri_tel, p.musteri_mail,
                p.musteri_not, p.sahip_goster, pid,
            ),
        )
    
    def set_durum(self, pid: int, durum: str) -> None:
        """
        Portföy durum güncelle.
        
        Args:
            pid: Portföy ID
            durum: Yeni durum
        """
        self._execute(
            "UPDATE portfoyler SET durum=?,guncelleme=datetime('now') WHERE id=?",
            (durum, pid),
        )
    
    def delete(self, pid: int) -> None:
        """
        Portföy sil.
        
        Args:
            pid: Portföy ID
        """
        self._execute("DELETE FROM portfoyler WHERE id=?", (pid,))
    
    def set_resimler(self, pid: int, resimler: list) -> None:
        """
        Portföy resimlerini güncelle.
        
        Args:
            pid: Portföy ID
            resimler: Resim URL listesi
        """
        self._execute(
            "UPDATE portfoyler SET resimler=?, guncelleme=datetime('now') WHERE id=?",
            (json.dumps(resimler, ensure_ascii=False), pid),
        )
    
    def exists(self, pid: int) -> bool:
        """
        Portföy var mı kontrol et.
        
        Args:
            pid: Portföy ID
            
        Returns:
            True varsa
        """
        row = self._fetchone("SELECT 1 FROM portfoyler WHERE id=?", (pid,))
        return row is not None
    
    def counts(self) -> Dict[str, int]:
        """
        Portföy sayıları.
        
        Returns:
            aktif, toplam, taslak sayıları
        """
        aktif = self._fetchone("SELECT COUNT(*) AS c FROM portfoyler WHERE durum='Aktif'")["c"]
        toplam = self._fetchone("SELECT COUNT(*) AS c FROM portfoyler")["c"]
        taslak = self._fetchone("SELECT COUNT(*) AS c FROM portfoyler WHERE durum='Taslak'")["c"]
        return {"aktif": aktif, "toplam": toplam, "taslak": taslak}
    
    def kategori_dagilimi(self) -> List[dict]:
        """
        Kategori dağılımı.
        
        Returns:
            Kategori bazlı sayılar
        """
        rows = self._fetchall(
            """
            SELECT ana_kategori, COUNT(*) as sayi
            FROM portfoyler WHERE durum='Aktif'
            GROUP BY ana_kategori
            """
        )
        return rows_to_dicts(rows)
    
    def list_aktif_sitemap(self) -> List[dict]:
        """
        Aktif portföyler (sitemap için).
        
        Returns:
            ID ve güncelleme tarihi
        """
        rows = self._fetchall(
            "SELECT id, guncelleme FROM portfoyler WHERE durum='Aktif' ORDER BY guncelleme DESC"
        )
        return rows_to_dicts(rows)
    
    def list_for_fiyat(self) -> List[dict]:
        """
        Fiyat analizi için aktif portföyler.
        
        Returns:
            Aktif portföy listesi
        """
        return [_decode_portfoy(r) for r in self._fetchall("SELECT * FROM portfoyler WHERE durum='Aktif'")]