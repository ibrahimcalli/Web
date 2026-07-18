"""Site Wizard Pydantic şemaları."""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel


class WizardBaslatOut(BaseModel):
    wizard_id: int
    adim: int
    sektorler: list


class WizardAdimKaydet(BaseModel):
    wizard_id: int
    adim: int
    veri: dict[str, Any]


class SektorSec(BaseModel):
    wizard_id: int
    sector: str


class TemplateSec(BaseModel):
    wizard_id: int
    template: str


class RenkSec(BaseModel):
    wizard_id: int
    palette: dict[str, Any]


class MenuOlustur(BaseModel):
    wizard_id: int
    auto: bool = True


class SayfaOlustur(BaseModel):
    wizard_id: int
    auto: bool = True


class WidgetAyarla(BaseModel):
    wizard_id: int
    widget_list: list[str]


class ForumAyarla(BaseModel):
    wizard_id: int
    aktif: bool = False


class SeoAyarla(BaseModel):
    wizard_id: int
    seo: dict[str, str]


class DemoSec(BaseModel):
    wizard_id: int
    demo: dict[str, bool]


class SiteOlustur(BaseModel):
    wizard_id: int


class LicenseCreate(BaseModel):
    firma_adi: str
    domain: str
    paket: str = "free"


class LicenseUpdate(BaseModel):
    paket: Optional[str] = None
    aktif: Optional[int] = None
    bitis: Optional[str] = None


class PluginToggle(BaseModel):
    id: int
