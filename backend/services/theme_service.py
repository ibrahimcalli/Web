"""Theme Service — tema ayarları iş kuralları (key-value)."""
from __future__ import annotations

from typing import Dict, Optional

from backend.repositories.theme_repository import ThemeRepository


class ThemeService:
    def __init__(self, theme: Optional[ThemeRepository] = None):
        self.theme = theme or ThemeRepository()

    def get_all(self) -> Dict[str, str]:
        return self.theme.get_all()

    def set(self, anahtar: str, deger: str) -> dict:
        self.theme.set(anahtar, deger)
        return {"anahtar": anahtar, "deger": deger}

    def delete(self, anahtar: str) -> dict:
        self.theme.delete(anahtar)
        return {"anahtar": anahtar, "silindi": True}
