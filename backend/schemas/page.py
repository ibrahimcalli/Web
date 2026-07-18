"""Sayfa yönetimi Pydantic modelleri."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class PageCreate(BaseModel):
    baslik: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=1, max_length=100)
    icerik: str = ""
    ozet: str = ""
    seo_baslik: str = ""
    seo_aciklama: str = ""
    seo_anahtar_kelimeler: str = ""
    kapak_resim: str = ""
    durum: str = "Taslak"
    sablon: str = "default"
    yazar_id: Optional[int] = None


class PageUpdate(BaseModel):
    baslik: Optional[str] = Field(None, min_length=1, max_length=200)
    slug: Optional[str] = Field(None, min_length=1, max_length=100)
    icerik: Optional[str] = None
    ozet: Optional[str] = None
    seo_baslik: Optional[str] = None
    seo_aciklama: Optional[str] = None
    seo_anahtar_kelimeler: Optional[str] = None
    kapak_resim: Optional[str] = None
    durum: Optional[str] = None
    sablon: Optional[str] = None
    yazar_id: Optional[int] = None


class PageOut(BaseModel):
    id: int
    baslik: str
    slug: str
    icerik: str
    ozet: str
    seo_baslik: str
    seo_aciklama: str
    seo_anahtar_kelimeler: str
    kapak_resim: str
    durum: str
    sablon: str
    yazar_id: Optional[int]
    olusturma: str
    guncelleme: str
