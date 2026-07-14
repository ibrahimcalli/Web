"""Ortak response modelleri ve yardımcı fonksiyonlar."""
from __future__ import annotations

from typing import Any, Generic, Optional, TypeVar, Dict
from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """
    Tek tip API yanıt zarfı.
    
    Tüm JSON endpoint'leri bu şemayı kullanır:
    - Başarılı: { "success": true, "message": "", "data": {...} }
    - Başarısız: { "success": false, "message": "Hata mesajı", "data": null }
    
    Masaüstü, mobil ve web uygulamaları için ortak sözleşme.
    """
    success: bool = Field(..., description="İşlem başarılı mı")
    message: str = Field("", description="Kullanıcıya gösterilebilir mesaj")
    data: Optional[T] = Field(None, description="İşlem sonucu verisi")
    
    class Config:
        json_schema_extra = {
            "examples": [
                {"success": True, "message": "", "data": {"id": 1}},
                {"success": False, "message": "Kayıt bulunamadı", "data": None},
            ]
        }


class EmptyData(BaseModel):
    """Boş veri yanıtı için."""
    pass


class IdResponse(BaseModel):
    """ID dönen yanıt."""
    id: int


class MesajResponse(BaseModel):
    """Sadece mesaj dönen yanıt."""
    mesaj: str


class SuccessResponse(BaseModel):
    """Başarılı işlem yanıtı."""
    success: bool = True
    message: str
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Hata yanıtı."""
    success: bool = False
    message: str
    data: Optional[Any] = None


# ─── Yardımcı Fonksiyonlar ────────────────────────────────────────────────────
def ok(data: Optional[T] = None, message: str = "") -> Dict[str, Any]:
    """
    Başarılı yanıt oluşturur.
    
    Args:
        data: Döndürülecek veri
        message: Opsiyonel mesaj
        
    Returns:
        API response sözlüğü
    """
    return {
        "success": True,
        "message": message or "",
        "data": data
    }


def fail(message: str, data: Optional[Any] = None) -> Dict[str, Any]:
    """
    Başarısız yanıt oluşturur.
    
    Args:
        message: Hata mesajı
        data: Opsiyonel veri
        
    Returns:
        API response sözlüğü
    """
    return {
        "success": False,
        "message": message or "İşlem başarısız",
        "data": data
    }


def paginated(data: list, page: int, page_size: int, total: int) -> Dict[str, Any]:
    """
    Sayfalı yanıt oluşturur.
    
    Args:
        data: Veri listesi
        page: Mevcut sayfa
        page_size: Sayfa başına öğe sayısı
        total: Toplam öğe sayısı
        
    Returns:
        Sayfalı API response
    """
    return {
        "success": True,
        "message": "",
        "data": {
            "items": data,
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size
        }
    }