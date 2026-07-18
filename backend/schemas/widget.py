"""Widget yönetimi Pydantic modelleri."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class WidgetCreate(BaseModel):
    anahtar: str = Field(..., min_length=1, max_length=50)
    ad: str = Field(..., min_length=1, max_length=100)
    aciklama: str = ""
    tip: str = "embed"
    aktif: bool = False
    ayarlar: str = "{}"
    konum: str = ""
    sira: int = 0


class WidgetUpdate(BaseModel):
    ad: Optional[str] = Field(None, min_length=1, max_length=100)
    aciklama: Optional[str] = None
    tip: Optional[str] = None
    aktif: Optional[bool] = None
    ayarlar: Optional[str] = None
    konum: Optional[str] = None
    sira: Optional[int] = None


class WidgetOut(BaseModel):
    id: int
    anahtar: str
    ad: str
    aciklama: str
    tip: str
    aktif: bool
    ayarlar: str
    konum: str
    sira: int
    olusturma: str
    guncelleme: str
