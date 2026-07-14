"""Portföy Service - Portföy iş kuralları."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from backend.core.config import BASE_DIR
from backend.core.errors import AppError, ForbiddenError, NotFoundError
from backend.repositories.kullanici_repository import KullaniciRepository
from backend.repositories.misc_repository import AyarRepository, IstekRepository
from backend.repositories.portfoy_repository import PortfoyRepository
from backend.schemas.portfoy import PortfoyCreate, PortfoyUpdate


class PortfoyService:
    """Portföy yönetimi iş kuralları."""
    
    def __init__(
        self,
        portfoyler: Optional[PortfoyRepository] = None,
        kullanicilar: Optional[KullaniciRepository] = None,
        ayarlar: Optional[AyarRepository] = None,
        istekler: Optional[IstekRepository] = None,
    ):
        """
        Portföy Service başlatma.
        
        Args:
            portfoyler: PortfoyRepository
            kullanicilar: KullaniciRepository
            ayarlar: AyarRepository
            istekler: IstekRepository
        """
        self.portfoyler = portfoyler or PortfoyRepository()
        self.kullanicilar = kullanicilar or KullaniciRepository()
        self.ayarlar = ayarlar or AyarRepository()
        self.istekler = istekler or IstekRepository()
    
    def listele(self, payload: Optional[dict], kategori: str = "", 
                alt_kat: str = "", durum: str = "Aktif", arama: str = "") -> list:
        """
        Portföy listesi.
        
        Args:
            payload: JWT payload
            kategori: Kategori filtresi
            alt_kat: Alt kategori filtresi
            durum: Durum filtresi
            arama: Arama metni
            
        Returns:
            Portföy listesi
        """
        is_admin = bool(payload and payload.get("rol") == "admin")
        
        return self.portfoyler.list(
            is_admin=is_admin,
            durum=durum,
            kategori=kategori,
            alt_kat=alt_kat,
            arama=arama,
        )
    
    def detay(self, pid: int, payload: Optional[dict]) -> dict:
        """
        Portföy detay.
        
        Args:
            pid: Portföy ID
            payload: JWT payload
            
        Returns:
            Portföy detay
            
        Raises:
            NotFoundError: Portföy bulunamadı
            ForbiddenError: Yayında değil
        """
        row = self.portfoyler.get(pid)
        
        if not row:
            raise NotFoundError("Portföy bulunamadı")
        
        is_admin = bool(payload and payload.get("rol") == "admin")
        is_onaylanmis = False
        
        if payload and payload.get("rol") != "admin":
            k = self.kullanicilar.get_onay_aktif(payload["sub"])
            is_onaylanmis = bool(k and k.get("onay"))
        
        if not is_admin and row["durum"] != "Aktif":
            raise ForbiddenError("Bu portföy henüz yayında değil")
        
        d = dict(row)
        yetkili = is_admin or is_onaylanmis
        
        # Müşteri bilgilerini gizle
        if not yetkili or (not is_admin and not d.get("sahip_goster")):
            d["musteri_ad"] = "" if not yetkili else d.get("musteri_ad", "")
            d["musteri_tel"] = "" if not yetkili else d.get("musteri_tel", "")
            d["musteri_mail"] = "" if not yetkili else d.get("musteri_mail", "")
        
        if not is_admin:
            d["saha_notu"] = ""
        
        return d
    
    def ekle(self, p: PortfoyCreate) -> dict:
        """
        Portföy ekle.
        
        Args:
            p: PortfoyCreate objesi
            
        Returns:
            Oluşturulan portföy ID ve mesaj
        """
        pid = self.portfoyler.create(p)
        return {"id": pid, "mesaj": "Portföy oluşturuldu"}
    
    def guncelle(self, pid: int, p: PortfoyUpdate) -> dict:
        """
        Portföy güncelle.
        
        Args:
            pid: Portföy ID
            p: PortfoyUpdate objesi
            
        Returns:
            Sonuç mesajı
            
        Raises:
            NotFoundError: Portföy bulunamadı
        """
        if not self.portfoyler.get(pid):
            raise NotFoundError("Portföy bulunamadı")
        
        self.portfoyler.update(pid, p)
        return {"mesaj": "Portföy güncellendi"}
    
    def durum_degistir(self, pid: int, durum: str) -> dict:
        """
        Portföy durum değiştir.
        
        Args:
            pid: Portföy ID
            durum: Yeni durum
            
        Returns:
            Sonuç mesajı
            
        Raises:
            AppError: Geçersiz durum
        """
        if durum not in ("Aktif", "Taslak", "Pasif", "Satıldı", "Kiralandı"):
            raise AppError("Geçersiz durum", 400)
        
        self.portfoyler.set_durum(pid, durum)
        return {"mesaj": f"Durum → {durum}"}
    
    def sil(self, pid: int) -> dict:
        """
        Portföy sil.
        
        Args:
            pid: Portföy ID
            
        Returns:
            Sonuç mesajı
        """
        p = self.portfoyler.get(pid)
        
        if p:
            for url in p.get("resimler") or []:
                dosya = BASE_DIR / str(url).lstrip("/")
                if dosya.exists():
                    try:
                        dosya.unlink()
                    except OSError:
                        pass
        
        self.portfoyler.delete(pid)
        return {"mesaj": "Portföy silindi"}
    
    def resim_ekle(self, pid: int, url: str) -> dict:
        """
        Resim ekle.
        
        Args:
            pid: Portföy ID
            url: Resim URL
            
        Returns:
            Sonuç ve resim listesi
            
        Raises:
            NotFoundError: Portföy bulunamadı
        """
        p = self.portfoyler.get(pid)
        
        if not p:
            raise NotFoundError("Portföy bulunamadı")
        
        resimler = list(p.get("resimler") or [])
        resimler.append(url)
        self.portfoyler.set_resimler(pid, resimler)
        
        return {"mesaj": "Yüklendi", "url": url, "resimler": resimler}
    
    def resim_sil(self, pid: int, url: str) -> dict:
        """
        Resim sil.
        
        Args:
            pid: Portföy ID
            url: Resim URL
            
        Returns:
            Sonuç ve güncel resim listesi
            
        Raises:
            NotFoundError: Portföy bulunamadı
        """
        p = self.portfoyler.get(pid)
        
        if not p:
            raise NotFoundError("Portföy bulunamadı")
        
        resimler = [u for u in (p.get("resimler") or []) if u != url]
        self.portfoyler.set_resimler(pid, resimler)
        
        dosya = BASE_DIR / url.lstrip("/")
        if dosya.exists():
            try:
                dosya.unlink()
            except OSError:
                pass
        
        return {"mesaj": "Resim silindi", "resimler": resimler}
    
    def resim_sirala(self, pid: int, resimler: list) -> dict:
        """
        Resim sırala.
        
        Args:
            pid: Portföy ID
            resimler: Resim URL listesi
            
        Returns:
            Sonuç mesajı
            
        Raises:
            NotFoundError: Portföy bulunamadı
        """
        if not self.portfoyler.get(pid):
            raise NotFoundError("Portföy bulunamadı")
        
        self.portfoyler.set_resimler(pid, resimler)
        return {"mesaj": "Sıra kaydedildi"}
    
    def kapak_guncelle(self, pid: int, url: str) -> dict:
        """
        Kapak resmi güncelle.
        
        Args:
            pid: Portföy ID
            url: Yeni kapak URL
            
        Returns:
            Sonuç ve resim listesi
            
        Raises:
            NotFoundError: Portföy bulunamadı
        """
        p = self.portfoyler.get(pid)
        
        if not p:
            raise NotFoundError("Portföy bulunamadı")
        
        imgs = list(p.get("resimler") or [])
        
        if url in imgs:
            imgs.remove(url)
            imgs.insert(0, url)
            self.portfoyler.set_resimler(pid, imgs)
        
        return {"mesaj": "Kapak güncellendi", "resimler": imgs}
    
    def istatistik(self, payload: Optional[dict]) -> dict:
        """
        İstatistikler.
        
        Args:
            payload: JWT payload
            
        Returns:
            İstatistikler
        """
        counts = self.portfoyler.counts()
        
        sonuc = {
            "toplam": counts["aktif"],
            "aktif": counts["aktif"],
            "taslak": 0,
            "yeni_istekler": 0,
            "kategori_dagilimi": self.portfoyler.kategori_dagilimi(),
        }
        
        if payload and payload.get("rol") == "admin":
            sonuc.update({
                "toplam": counts["toplam"],
                "taslak": counts["taslak"],
                "yeni_istekler": self.istekler.count_yeni(),
            })
        
        return sonuc
    
    def sahip_profil(self, pid: int) -> dict:
        """
        Sahip profil bilgileri.
        
        Args:
            pid: Portföy ID
            
        Returns:
            Sahip profil
            
        Raises:
            NotFoundError: Portföy bulunamadı
        """
        p = self.portfoyler.get(pid)
        
        if not p:
            raise NotFoundError("Portföy bulunamadı")
        
        admin = self.kullanicilar.get_first_admin_profil()
        ay = self.ayarlar.get_all()
        
        return {
            "ad_soyad": (admin or {}).get("ad_soyad") or ay.get("site_adi", ""),
            "profil_resmi": (admin or {}).get("profil_resmi", ""),
            "telefon": p.get("musteri_tel") or ay.get("telefon", ""),
        }
    
    def danismanlar(self, pid: int) -> dict:
        """
        Danışman bilgileri.
        
        Args:
            pid: Portföy ID
            
        Returns:
            Danışman bilgileri
            
        Raises:
            NotFoundError: Portföy bulunamadı
        """
        p = self.portfoyler.get(pid)
        
        if not p:
            raise NotFoundError("Portföy bulunamadı")
        
        return {
            "musteri_ad": p.get("musteri_ad") or "",
            "musteri_tel": p.get("musteri_tel") or "",
            "musteri_mail": p.get("musteri_mail") or "",
        }