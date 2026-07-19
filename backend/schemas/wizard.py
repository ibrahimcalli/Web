"""Site Wizard Pydantic şemaları."""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel


class WizardBaslatOut(BaseModel):
    wizard_id: int
    adim: int
    sektorler: list


class WizardAdimKaydet(BaseModel):
    adim: int
    veri: dict[str, Any]


class SektorSec(BaseModel):
    sector: str


class TemplateSec(BaseModel):
    template: str


class RenkSec(BaseModel):
    palette: dict[str, Any]


class MenuOlustur(BaseModel):
    auto: bool = True


class SayfaOlustur(BaseModel):
    auto: bool = True


class WidgetAyarla(BaseModel):
    widget_list: list[str]


class ForumAyarla(BaseModel):
    aktif: bool = False


class SeoAyarla(BaseModel):
    seo: dict[str, str]


class DemoSec(BaseModel):
    demo: dict[str, bool]


class SiteOlustur(BaseModel):
    pass


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
