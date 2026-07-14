"""İstek, ayar, banner, blog Pydantic modelleri."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ─── İstek Modelleri ──────────────────────────────────────────────────────────
class IstekCreate(BaseModel):
    """Kullanıcı isteği oluşturma."""
    ad_soyad: str = Field(..., min_length=3, max_length=100)
    telefon: Optional[str] = ""
    email: Optional[str] = ""
    mesaj: Optional[str] = ""
    portfoy_id: Optional[int] = None


class IstekDurumGuncelle(BaseModel):
    """İstek durum güncelleme."""
    durum: str = Field(..., pattern="^(Yeni|İşleniyor|Tamamlandı|Reddedildi)$")


class IstekListeItem(BaseModel):
    """İstek liste öğesi."""
    id: int
    ad_soyad: str
    telefon: Optional[str]
    email: Optional[str]
    mesaj: Optional[str]
    portfoy_id: Optional[int]
    durum: str
    olusturma: str
    portfoy_baslik: Optional[str]


# ─── Ayar Modelleri ───────────────────────────────────────────────────────────
class AyarSet(BaseModel):
    """Ayarlar güncelleme."""
    ayarlar: Dict[str, Any]


class AyarListe(BaseModel):
    """Ayarlar yanıtı."""
    site_adi: str
    site_slogan: str
    telefon: str
    email: str
    adres: str
    web_sitesi: str
    renk_tema: Optional[str]
    logo_url: Optional[str]
    sosyal_ig: Optional[str]
    sosyal_fb: Optional[str]
    sosyal_wa: Optional[str]


# ─── Banner Modelleri ─────────────────────────────────────────────────────────
class BannerCreate(BaseModel):
    """Banner oluşturma."""
    tip: Optional[str] = "slider"
    baslik: Optional[str] = ""
    alt_metin: Optional[str] = ""
    aciklama: Optional[str] = ""
    link_url: Optional[str] = ""
    link_metin: Optional[str] = ""
    link_hedef: Optional[str] = "_self"
    konum: Optional[str] = "anasayfa_hero_alti"
    boyut: Optional[str] = "genis"
    sira: Optional[int] = 0
    aktif: Optional[int] = 1


class BannerUpdate(BaseModel):
    """Banner güncelleme."""
    tip: Optional[str] = None
    baslik: Optional[str] = None
    alt_metin: Optional[str] = None
    aciklama: Optional[str] = None
    link_url: Optional[str] = None
    link_metin: Optional[str] = None
    link_hedef: Optional[str] = None
    konum: Optional[str] = None
    boyut: Optional[str] = None
    sira: Optional[int] = None
    aktif: Optional[int] = None


class BannerAktifGuncelle(BaseModel):
    """Banner aktif/pasif güncelleme."""
    aktif: int = Field(..., ge=0, le=1)


class BannerSiraGuncelle(BaseModel):
    """Banner sıralama güncelleme."""
    siralar: List[int]


class BannerResimEkle(BaseModel):
    """Banner resim ekleme."""
    url: str


class BannerListeItem(BaseModel):
    """Banner liste öğesi."""
    id: int
    tip: str
    baslik: str
    alt_metin: str
    aciklama: str
    resim_url: Optional[str]
    link_url: str
    link_metin: str
    link_hedef: str
    konum: str
    boyut: str
    renk_arka: Optional[str]
    renk_metin: str
    sira: int
    aktif: int
    olusturma: str


# ─── Blog Modelleri ───────────────────────────────────────────────────────────
class BlogCreate(BaseModel):
    """Blog yazısı oluşturma."""
    baslik: str = Field(..., min_length=5, max_length=200)
    icerik: Optional[str] = ""
    ozet: Optional[str] = ""
    etiketler: Optional[List[str]] = Field(default_factory=list)
    kapak_resim: Optional[str] = ""
    durum: Optional[str] = "Taslak"


class BlogUpdate(BaseModel):
    """Blog yazısı güncelleme."""
    baslik: Optional[str] = None
    icerik: Optional[str] = None
    ozet: Optional[str] = None
    etiketler: Optional[List[str]] = None
    kapak_resim: Optional[str] = None
    durum: Optional[str] = None


class BlogKapakEkle(BaseModel):
    """Blog kapak resmi ekleme."""
    url: str


class BlogListeItem(BaseModel):
    """Blog liste öğesi."""
    id: int
    baslik: str
    slug: str
    icerik: str
    ozet: str
    etiketler: List[str]
    kapak_resim: Optional[str]
    durum: str
    yazar_id: Optional[int]
    yazar_adi: Optional[str]
    olusturma: str
    guncelleme: str


class BlogDetay(BaseModel):
    """Blog detay yanıtı."""
    id: int
    baslik: str
    slug: str
    icerik: str
    ozet: str
    etiketler: List[str]
    kapak_resim: Optional[str]
    durum: str
    yazar_id: Optional[int]
    yazar_adi: Optional[str]
    olusturma: str
    guncelleme: str


# ─── Fiyat Analizi Modelleri ──────────────────────────────────────────────────
class FiyatAnalizi(BaseModel):
    """Fiyat analizi yanıtı."""
    portfoy_id: int
    ortalama_fiyat: Optional[float]
    min_fiyat: Optional[float]
    max_fiyat: Optional[float]
    benzer_ilan_sayisi: int
    fiyat_karsilastirma: str
    onerilen_fiyat_araligi: Optional[str]


class FiyatAnaliziGenel(BaseModel):
    """Genel fiyat analizi yanıtı."""
    toplam_ilan: int
    ortalama_fiyat: Optional[float]
    orta_aralik: Optional[str]
    en_cok_ilan_olan_kategori: Optional[str]