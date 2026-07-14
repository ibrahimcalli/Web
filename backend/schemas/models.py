"""Pydantic istek/yanıt modelleri — OpenAPI şeması için eksiksiz."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PortfoyGiren(BaseModel):
    baslik: str
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


class IstekGiren(BaseModel):
    ad_soyad: str
    telefon: Optional[str] = ""
    email: Optional[str] = ""
    mesaj: Optional[str] = ""
    portfoy_id: Optional[int] = None


class KullaniciGiren(BaseModel):
    ad_soyad: str
    email: str
    sifre: str
    rol: Optional[str] = "kullanici"


class AyarGiren(BaseModel):
    ayarlar: Dict[str, Any]


class BlogGiren(BaseModel):
    baslik: str
    icerik: Optional[str] = ""
    ozet: Optional[str] = ""
    etiketler: Optional[List[Any]] = Field(default_factory=list)
    kapak_resim: Optional[str] = ""
    durum: Optional[str] = "Taslak"


class ResimSirala(BaseModel):
    resimler: List[str]


class SifreDegistir(BaseModel):
    mevcut_sifre: str
    yeni_sifre: str


class ProfilGuncelle(BaseModel):
    ad_soyad: str
    email: str
    profil_resmi: Optional[str] = None


class AIAyarGiren(BaseModel):
    ai_api_key: str = ""
    ai_saglayici: str = "deepseek"


class SifreSifirlamaBaslat(BaseModel):
    email: str


class SifreSifirlamaTamamla(BaseModel):
    token: str
    yeni_sifre: str


class BannerGiren(BaseModel):
    tip: Optional[str] = "slider"
    baslik: Optional[str] = ""
    alt_metin: Optional[str] = ""
    aciklama: Optional[str] = ""
    link_url: Optional[str] = ""
    link_metin: Optional[str] = ""
    link_hedef: Optional[str] = "_self"
    konum: Optional[str] = "anasayfa_hero_alti"
    boyut: Optional[str] = "genis"
    renk_arka: Optional[str] = ""
    renk_metin: Optional[str] = "#ffffff"
    sira: Optional[int] = 0
    aktif: Optional[int] = 1


class BannerSiraGiren(BaseModel):
    siralar: List[int]


class LoginData(BaseModel):
    access_token: str
    token_type: str = "bearer"
    rol: str
    ad: str


class IdMesaj(BaseModel):
    id: Optional[int] = None
    mesaj: str = ""
