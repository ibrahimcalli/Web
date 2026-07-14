"""Auth Router - Kimlik doğrulama endpoint'leri."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.security import HTTPBearer

from backend.core.dependencies import get_auth_service, get_current_user, require_auth
from backend.schemas.kullanici import (
    SifreSifirlamaBaslat, SifreSifirlamaTamamla, LoginResponse
)
from backend.schemas.response import ok, fail
from backend.services.auth_service import AuthService

router = APIRouter()
security = HTTPBearer(auto_error=False)


@router.post("/auth/giris", tags=["Auth"])
async def giris(
    request: Request,
    email: str,
    sifre: str,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Kullanıcı girişi.
    
    - **email**: Kullanıcı e-posta adresi
    - **sifre**: Kullanıcı şifresi
    """
    try:
        result = auth_service.login(email, sifre, client.host)
        return ok(result, "Giriş başarılı")
    except Exception as e:
        return fail(str(e))


@router.get("/auth/ben", tags=["Auth"])
async def ben(
    user: dict = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Mevcut kullanıcı bilgileri.
    """
    result = auth_service.ben(user)
    if not result.get("giris"):
        return fail("Oturum açılmamış")
    return ok(result)


@router.post("/auth/sifre-sifirlama-baslat", tags=["Auth"])
async def sifre_sifirlama_baslat(
    data: SifreSifirlamaBaslat,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Şifre sıfırlama başlatma.
    
    Token terminal çıktısında gösterilir.
    """
    try:
        result = auth_service.sifre_sifirlama_baslat(data.email)
        return ok(result)
    except Exception as e:
        return fail(str(e))


@router.post("/auth/sifre-sifirlama-tamamla", tags=["Auth"])
async def sifre_sifirlama_tamamla(
    data: SifreSifirlamaTamamla,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Şifre sıfırlama tamamlama.
    """
    try:
        result = auth_service.sifre_sifirlama_tamamla(data.token, data.yeni_sifre)
        return ok(result)
    except Exception as e:
        return fail(str(e))