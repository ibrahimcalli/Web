"""İçerik Service - İstek, Ayar, Banner, Blog iş kuralları."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend.core.errors import NotFoundError
from backend.repositories.misc_repository import (
    IstekRepository, AyarRepository, BannerRepository, BlogRepository
)
from backend.repositories.portfoy_repository import PortfoyRepository


class IstekService:
    """Kullanıcı istekleri iş kuralları."""
    
    def __init__(
        self,
        istekler: Optional[IstekRepository] = None,
        portfoyler: Optional[PortfoyRepository] = None,
    ):
        self.istekler = istekler or IstekRepository()
        self.portfoyler = portfoyler or PortfoyRepository()
    
    def olustur(self, ad_soyad: str, telefon: str, email: str, 
                mesaj: str, portfoy_id: Optional[int] = None) -> dict:
        """
        İstek oluştur.
        
        Args:
            ad_soyad: Ad soyad
            telefon: Telefon
            email: E-posta
            mesaj: Mesaj
            portfoy_id: Portföy ID
            
        Returns:
            Sonuç mesajı ve ID
        """
        iid = self.istekler.create(ad_soyad, telefon, email, mesaj, portfoy_id)
        return {"id": iid, "mesaj": "İsteğiniz alındı"}
    
    def listele(self) -> List[dict]:
        """
        Tüm istekleri listele.
        
        Returns:
            İstek listesi
        """
        return self.istekler.list_with_portfoy()
    
    def durum_degistir(self, iid: int, durum: str) -> dict:
        """
        İstek durum değiştir.
        
        Args:
            iid: İstek ID
            durum: Yeni durum
            
        Returns:
            Sonuç mesajı
        """
        self.istekler.set_durum(iid, durum)
        return {"mesaj": f"Durum → {durum}"}


class AyarService:
    """Site ayarları iş kuralları."""
    
    def __init__(self, ayarlar: Optional[AyarRepository] = None):
        self.ayarlar = ayarlar or AyarRepository()
    
    def get_all(self) -> Dict[str, str]:
        """
        Tüm ayarları getir.
        
        Returns:
            Ayarlar sözlüğü
        """
        return self.ayarlar.get_all()
    
    def set_all(self, ayarlar: Dict[str, Any]) -> dict:
        """
        Tüm ayarları güncelle.
        
        Args:
            ayarlar: Yeni ayarlar
            
        Returns:
            Sonuç mesajı
        """
        self.ayarlar.set_many(ayarlar)
        return {"mesaj": "Ayarlar güncellendi"}
    
    def get(self, anahtar: str, default: str = "") -> str:
        """
        Tek ayar getir.
        
        Args:
            anahtar: Ayar anahtarı
            default: Varsayılan değer
            
        Returns:
            Ayar değeri
        """
        return self.ayarlar.get(anahtar, default)


class BannerService:
    """Banner iş kuralları."""
    
    def __init__(
        self,
        bannerlar: Optional[BannerRepository] = None,
        upload_service=None,
    ):
        self.bannerlar = bannerlar or BannerRepository()
    
    def listele(self, konum: str = "", sadece_aktif: bool = False) -> List[dict]:
        """
        Banner listesi.
        
        Args:
            konum: Konum filtresi
            sadece_aktif: Sadece aktif
            
        Returns:
            Banner listesi
        """
        return self.bannerlar.list(konum, sadece_aktif)
    
    def get(self, bid: int) -> Optional[dict]:
        """
        Banner getir.
        
        Args:
            bid: Banner ID
            
        Returns:
            Banner dict
        """
        return self.bannerlar.get(bid)
    
    def olustur(self, data: dict) -> dict:
        """
        Banner oluştur.
        
        Args:
            data: Banner verisi
            
        Returns:
            Sonuç mesajı ve ID
        """
        bid = self.bannerlar.create(data)
        return {"id": bid, "mesaj": "Banner oluşturuldu"}
    
    def guncelle(self, bid: int, data: dict) -> dict:
        """
        Banner güncelle.
        
        Args:
            bid: Banner ID
            data: Yeni veriler
            
        Returns:
            Sonuç mesajı
            
        Raises:
            NotFoundError: Banner bulunamadı
        """
        if not self.bannerlar.get(bid):
            raise NotFoundError("Banner bulunamadı")
        
        self.bannerlar.update(bid, data)
        return {"mesaj": "Banner güncellendi"}
    
    def aktif_degistir(self, bid: int, aktif: int) -> dict:
        """
        Banner aktif/pasif yap.
        
        Args:
            bid: Banner ID
            aktif: Aktif durumu
            
        Returns:
            Sonuç mesajı
        """
        self.bannerlar.set_aktif(bid, aktif)
        return {"mesaj": f"Banner {'aktif' if aktif else 'pasif'}"}
    
    def sirala(self, siralar: List[int]) -> dict:
        """
        Banner sırala.
        
        Args:
            siralar: Banner ID sıralaması
            
        Returns:
            Sonuç mesajı
        """
        self.bannerlar.reorder(siralar)
        return {"mesaj": "Sıra kaydedildi"}
    
    def sil(self, bid: int) -> dict:
        """
        Banner sil.
        
        Args:
            bid: Banner ID
            
        Returns:
            Sonuç mesajı
        """
        self.bannerlar.delete(bid)
        return {"mesaj": "Banner silindi"}
    
    def resim_ekle(self, bid: int, url: str) -> dict:
        """
        Banner resim ekle.
        
        Args:
            bid: Banner ID
            url: Resim URL
            
        Returns:
            Sonuç mesajı
        """
        self.bannerlar.set_resim(bid, url)
        return {"mesaj": "Resim güncellendi", "url": url}


class BlogService:
    """Blog iş kuralları."""
    
    def __init__(
        self,
        bloglar: Optional[BlogRepository] = None,
        portfoyler: Optional[PortfoyRepository] = None,
    ):
        self.bloglar = bloglar or BlogRepository()
    
    def listele(self, is_admin: bool, durum: str = "") -> List[dict]:
        """
        Blog yazıları listesi.
        
        Args:
            is_admin: Admin mi?
            durum: Durum filtresi
            
        Returns:
            Blog listesi
        """
        return self.bloglar.list(is_admin=is_admin, durum=durum)
    
    def get(self, slug_or_id: str) -> Optional[dict]:
        """
        Blog yazısı getir.
        
        Args:
            slug_or_id: Slug veya ID
            
        Returns:
            Blog yazısı dict
        """
        return self.bloglar.get_by_slug_or_id(slug_or_id)
    
    def olustur(self, data: dict, yazar_id: Optional[int]) -> dict:
        """
        Blog yazısı oluştur.
        
        Args:
            data: Blog verisi
            yazar_id: Yazar ID
            
        Returns:
            Sonuç mesajı ve ID
        """
        bid = self.bloglar.create(data, yazar_id)
        return {"id": bid, "mesaj": "Blog yazısı oluşturuldu"}
    
    def guncelle(self, bid: int, data: dict) -> dict:
        """
        Blog yazısı güncelle.
        
        Args:
            bid: Blog ID
            data: Yeni veriler
            
        Returns:
            Sonuç mesajı
            
        Raises:
            NotFoundError: Blog bulunamadı
        """
        if not self.bloglar.get_by_slug_or_id(str(bid)):
            raise NotFoundError("Blog yazısı bulunamadı")
        
        self.bloglar.update(bid, data)
        return {"mesaj": "Blog yazısı güncellendi"}
    
    def sil(self, bid: int) -> dict:
        """
        Blog yazısı sil.
        
        Args:
            bid: Blog ID
            
        Returns:
            Sonuç mesajı
        """
        self.bloglar.delete(bid)
        return {"mesaj": "Blog yazısı silindi"}
    
    def kapak_ekle(self, bid: int, url: str) -> dict:
        """
        Blog kapak resmi ekle.
        
        Args:
            bid: Blog ID
            url: Kapak resmi URL
            
        Returns:
            Sonuç mesajı
        """
        self.bloglar.set_kapak(bid, url)
        return {"mesaj": "Kapak resmi güncellendi", "url": url}
    
    def icerik_resim_ekle(self, url: str, boyut: str, konum: str) -> dict:
        """
        Blog içeriğe resim ekle.
        
        Args:
            url: Resim URL
            boyut: Resim boyutu (kare, dikdortgen, genis, orijinal)
            konum: Resim konumu (basta, ortali, sonda)
            
        Returns:
            Sonuç mesajı ve HTML snippet
        """
        # HTML snippet oluştur
        boyut_class = f"boyut-{boyut}"
        konum_class = f"konum-{konum}"
        html = f'<div class="blog-icerik-resim {boyut_class} {konum_class}"><img src="{url}" loading="lazy" alt=""></div>'
        
        return {
            "mesaj": "Resim yüklendi",
            "url": url,
            "boyut": boyut,
            "konum": konum,
            "html": html
        }