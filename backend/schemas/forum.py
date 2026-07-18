"""Forum yönetimi Pydantic modelleri."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


# ─── Kategoriler ───────────────────────────────────────────────────────────
class ForumCategoryCreate(BaseModel):
    slug: str = Field(..., min_length=1, max_length=50)
    ad: str = Field(..., min_length=1, max_length=100)
    aciklama: str = ""
    sira: int = 0
    aktif: bool = True


class ForumCategoryUpdate(BaseModel):
    ad: Optional[str] = Field(None, min_length=1, max_length=100)
    aciklama: Optional[str] = None
    sira: Optional[int] = None
    aktif: Optional[bool] = None


class ForumCategoryOut(BaseModel):
    id: int
    slug: str
    ad: str
    aciklama: str
    sira: int
    aktif: bool
    olusturma: str


# ─── Konular ───────────────────────────────────────────────────────────────
class ForumTopicCreate(BaseModel):
    category_id: int
    baslik: str = Field(..., min_length=1, max_length=200)
    icerik: str = ""
    kullanici_id: Optional[int] = None
    kullanici_ad: str = ""
    sabit: bool = False
    kapali: bool = False
    durum: str = "yayin"


class ForumTopicUpdate(BaseModel):
    baslik: Optional[str] = None
    icerik: Optional[str] = None
    sabit: Optional[bool] = None
    kapali: Optional[bool] = None
    durum: Optional[str] = None


class ForumTopicOut(BaseModel):
    id: int
    category_id: int
    baslik: str
    slug: str
    icerik: str
    kullanici_id: Optional[int]
    kullanici_ad: str
    goruntuleme: int
    sabit: bool
    kapali: bool
    durum: str
    olusturma: str
    guncelleme: str


# ─── Yanıtlar ──────────────────────────────────────────────────────────────
class ForumPostCreate(BaseModel):
    topic_id: int
    parent_id: Optional[int] = None
    icerik: str = Field(..., min_length=1)
    kullanici_id: Optional[int] = None
    kullanici_ad: str = ""
    ip: str = ""


class ForumPostUpdate(BaseModel):
    icerik: Optional[str] = None
    durum: Optional[str] = None


class ForumPostOut(BaseModel):
    id: int
    topic_id: int
    parent_id: Optional[int]
    icerik: str
    kullanici_id: Optional[int]
    kullanici_ad: str
    ip: str
    durum: str
    olusturma: str


# ─── Ayarlar ───────────────────────────────────────────────────────────────
class ForumSettingUpdate(BaseModel):
    anahtar: str
    deger: str
