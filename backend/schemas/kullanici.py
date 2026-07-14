"""Kullanıcı Pydantic modelleri."""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field

class KullaniciKayit(BaseModel):
    ad_soyad: str = Field(..., min_length=3, max_length=100)
    email: str
    sifre: str = Field(..., min_length=6, max_length=128)
    rol: Optional[str] = "kullanici"


class KullaniciCreate(BaseModel):
    ad_soyad: str = Field(..., min_length=3, max_length=100)
    email: str
    sifre: str = Field(..., min_length=8, max_length=128)
    rol: Optional[str] = "kullanici"


class KullaniciUpdate(BaseModel):
    ad_soyad: Optional[str] = None
    email: Optional[str] = None
    profil_resmi: Optional[str] = None


class SifreDegistir(BaseModel):
    mevcut_sifre: str = Field(..., min_length=6)
    yeni_sifre: str = Field(..., min_length=8, max_length=128)


class SifreSifirlamaBaslat(BaseModel):
    email: str


class SifreSifirlamaTamamla(BaseModel):
    token: str = Field(..., min_length=10)
    yeni_sifre: str = Field(..., min_length=8, max_length=128)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    rol: str
    ad: str


class KullaniciOnay(BaseModel):
    id: int
    ad_soyad: str
    email: str
    rol: str
    aktif: int
    onay: int
    profil_resmi: Optional[str]
    olusturma: str


class KullaniciBen(BaseModel):
    id: int
    ad_soyad: str
    email: str
    rol: str
    aktif: int
    onay: int
    profil_resmi: Optional[str]


class KullaniciListeItem(BaseModel):
    id: int
    ad_soyad: str
    email: str
    rol: str
    aktif: int
    onay: int
    profil_resmi: Optional[str]
    olusturma: str


class KullaniciProfilResim(BaseModel):
    url: str
    eski: Optional[str]