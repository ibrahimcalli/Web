"""Content Router - Kategori, alan, belge parse, fiyat analizi, PDF."""
from __future__ import annotations

from fastapi import APIRouter, Depends, UploadFile, File, Request

from backend.core.dependencies import get_current_user, require_auth
from backend.domain.catalog import (
    get_kategoriler, get_ilan_tipleri, get_alan_sablonlari
)
from backend.schemas.response import ok

router = APIRouter()


@router.get("/kategoriler")
async def kategoriler():
    """Ana kategori listesi."""
    return ok({
        "kategoriler": get_kategoriler(),
        "ilan_tipleri": get_ilan_tipleri(),
    })


@router.get("/alanlar")
async def alanlar():
    """Form alan şablonları."""
    return ok(get_alan_sablonlari())