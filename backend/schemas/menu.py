"""Menü yönetimi Pydantic modelleri."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ─── Menü ──────────────────────────────────────────────────────────────────
class MenuCreate(BaseModel):
    slug: str = Field(..., min_length=1, max_length=50, description="Benzersiz menü anahtarı (ana-menu, footer-menu)")
    ad: str = Field("", max_length=100, description="Menü görünen adı")
    lokasyon: str = Field("header", description="header / footer / sidebar")
    aktif: bool = Field(True)


class MenuUpdate(BaseModel):
    slug: Optional[str] = Field(None, min_length=1, max_length=50)
    ad: Optional[str] = Field(None, max_length=100)
    lokasyon: Optional[str] = None
    aktif: Optional[bool] = None


class MenuOut(BaseModel):
    id: int
    slug: str
    ad: str
    lokasyon: str
    aktif: bool
    olusturma: str


# ─── Menü Öğeleri ──────────────────────────────────────────────────────────
class MenuItemCreate(BaseModel):
    menu_id: int
    parent_id: Optional[int] = None
    baslik: str = Field(..., min_length=1, max_length=100)
    ikon: str = ""
    hedef_tip: str = Field("dahili", description="dahili / harici")
    hedef_url: str = ""
    hedef_page_id: Optional[int] = None
    gosterim: str = "_self"
    izin_rol: str = ""
    sira: int = 0
    aktif: bool = True
    dil: str = ""


class MenuItemUpdate(BaseModel):
    parent_id: Optional[int] = None
    baslik: Optional[str] = Field(None, min_length=1, max_length=100)
    ikon: Optional[str] = None
    hedef_tip: Optional[str] = None
    hedef_url: Optional[str] = None
    hedef_page_id: Optional[int] = None
    gosterim: Optional[str] = None
    izin_rol: Optional[str] = None
    sira: Optional[int] = None
    aktif: Optional[bool] = None
    dil: Optional[str] = None


class MenuItemReorder(BaseModel):
    items: List[Dict[str, Any]] = Field(..., description="[{id, parent_id, sira}, ...]")


class MenuItemOut(BaseModel):
    id: int
    menu_id: int
    parent_id: Optional[int]
    baslik: str
    ikon: str
    hedef_tip: str
    hedef_url: str
    hedef_page_id: Optional[int]
    gosterim: str
    izin_rol: str
    sira: int
    aktif: bool
    dil: str
    olusturma: str
    page_slug: Optional[str] = None
    alt_ogeler: List[MenuItemOut] = []
