"""Portföy Pydantic modelleri."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PortfoyCreate(BaseModel):
    """Portföy oluşturma isteği."""
    baslik: str = Field(..., min_length=3, max_length=200)
    ana_kategori: str
    alt_kategori: str
    ilan_tipi: Optional[str] = ""
    il: Optional[str] = "Muğla"
    ilce: Optional[str] = "Fethiye"
    mahalle: Optional[str] = ""
    fiyat: Optional[str] = ""
    para_birimi: Optional[str] = "TL"
    aciklama: Optional[str] = ""
    saha_notu: Optional[str] = ""
    gps: Optional[str] = ""
    durum: Optional[str] = "Taslak"
    alanlar: Optional[Dict[str, Any]] = Field(default_factory=dict)
    musteri_ad: Optional[str] = ""
    musteri_tel: Optional[str] = ""
    musteri_mail: Optional[str] = ""
    musteri_adres: Optional[str] = ""
    musteri_tc: Optional[str] = ""
    musteri_not: Optional[str] = ""
    sahip_goster: Optional[int] = 0


class PortfoyUpdate(BaseModel):
    """Portföy güncelleme isteği."""
    baslik: Optional[str] = None
    ana_kategori: Optional[str] = None
    alt_kategori: Optional[str] = None
    ilan_tipi: Optional[str] = None
    il: Optional[str] = None
    ilce: Optional[str] = None
    mahalle: Optional[str] = None
    fiyat: Optional[str] = None
    para_birimi: Optional[str] = None
    aciklama: Optional[str] = None
    saha_notu: Optional[str] = None
    gps: Optional[str] = None
    durum: Optional[str] = None
    alanlar: Optional[Dict[str, Any]] = None
    musteri_ad: Optional[str] = None
    musteri_tel: Optional[str] = None
    musteri_mail: Optional[str] = None
    musteri_adres: Optional[str] = None
    musteri_tc: Optional[str] = None
    musteri_not: Optional[str] = None
    sahip_goster: Optional[int] = None


class PortfoyDurumGuncelle(BaseModel):
    """Portföy durum güncelleme."""
    durum: str = Field(..., pattern="^(Aktif|Taslak|Pasif|Satıldı|Kiralandı)$")


class PortfoyResimEkle(BaseModel):
    """Portföy resim ekleme."""
    url: str


class PortfoyResimSirala(BaseModel):
    """Portföy resim sıralama."""
    resimler: List[str] = Field(..., description="Resim URL listesi")


class PortfoyKapakGuncelle(BaseModel):
    """Portföy kapak resmi güncelleme."""
    url: str


class PortfoyDetay(BaseModel):
    """Portföy detay yanıtı."""
    id: int
    baslik: str
    ana_kategori: str
    alt_kategori: str
    ilan_tipi: Optional[str]
    il: Optional[str]
    ilce: Optional[str]
    mahalle: Optional[str]
    fiyat: Optional[str]
    para_birimi: Optional[str]
    aciklama: Optional[str]
    saha_notu: Optional[str]
    gps: Optional[str]
    durum: str
    alanlar: Dict[str, Any]
    resimler: List[str]
    musteri_ad: Optional[str]
    musteri_tel: Optional[str]
    musteri_mail: Optional[str]
    musteri_adres: Optional[str]
    musteri_tc: Optional[str]
    musteri_not: Optional[str]
    sahip_goster: int
    kaynak: str
    olusturma: str
    guncelleme: str


class PortfoyListeItem(BaseModel):
    """Portföy liste öğesi."""
    id: int
    baslik: str
    ana_kategori: str
    alt_kategori: str
    il: Optional[str]
    ilce: Optional[str]
    fiyat: Optional[str]
    durum: str
    resimler: List[str]
    guncelleme: str


class PortfoyCounts(BaseModel):
    """Portföy sayıları."""
    aktif: int
    toplam: int
    taslak: int


class PortfoyKategoriDagilim(BaseModel):
    """Kategori dağılımı."""
    ana_kategori: str
    sayi: int