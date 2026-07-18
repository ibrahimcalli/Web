"""Tema ayarları Pydantic modelleri."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ThemeSettingSet(BaseModel):
    anahtar: str = Field(..., min_length=1, max_length=100)
    deger: str


class ThemeSettingOut(BaseModel):
    anahtar: str
    deger: str
