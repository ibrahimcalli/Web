"""Template Engine Pydantic modelleri."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TemplateCreate(BaseModel):
    slug: str = Field(..., min_length=1, max_length=50)
    ad: str = Field(..., min_length=1, max_length=100)
    aciklama: str = ""
    klasor: str = ""
    aktif: bool = True
    varsayilan: bool = False


class TemplateUpdate(BaseModel):
    slug: Optional[str] = Field(None, min_length=1, max_length=50)
    ad: Optional[str] = Field(None, min_length=1, max_length=100)
    aciklama: Optional[str] = None
    klasor: Optional[str] = None
    aktif: Optional[bool] = None
    varsayilan: Optional[bool] = None
    modules: Optional[str] = None


class TemplateOut(BaseModel):
    id: int
    slug: str
    ad: str
    aciklama: str
    klasor: str
    aktif: bool
    varsayilan: bool
    modules: str = '{}'
    olusturma: str


class HomepageSectionUpdate(BaseModel):
    baslik: Optional[str] = None
    aktif: Optional[bool] = None
    sira: Optional[int] = None
    ayarlar: Optional[str] = None


class HomepageSectionReorder(BaseModel):
    items: List[Dict[str, Any]]


class HomepageSectionOut(BaseModel):
    id: int
    template_id: int
    section_key: str
    baslik: str
    aktif: bool
    sira: int
    ayarlar: str
    olusturma: str


class HomepageSectionPublic(BaseModel):
    id: int
    section_key: str
    baslik: str
    sira: int
    ayarlar: Dict[str, Any]
