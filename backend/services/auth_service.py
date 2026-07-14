"""Auth Service - İş kuralları ve kimlik doğrulama."""
from __future__ import annotations

import secrets
import time
from typing import Optional

from backend.core.errors import AppError, ForbiddenError, NotFoundError
from backend.core.security import (
    get_sifre_token_store,
    hash_sifre,
    rate_limit_basarili,
    rate_limit_basarisiz,
    rate_limit_kontrol,
    sifre_dogrula,
    token_olustur,
)
from backend.repositories.kullanici_repository import KullaniciRepository
from backend.schemas.kullanici import LoginResponse


class AuthService:
    """Kimlik doğrulama ve yetkilendirme iş kuralları."""
    
    def __init__(self, kullanicilar: Optional[KullaniciRepository] = None):
        """
        Auth Service başlatma.
        
        Args:
            kullanicilar: KullaniciRepository instance (testlerde override edilebilir)
        """
        self.kullanicilar = kullanicilar or KullaniciRepository()
    
    def login(self, email: str, sifre: str, ip: str) -> LoginResponse:
        """
        Kullanıcı girişi.
        
        Args:
            email: E-posta
            sifre: Şifre
            ip: IP adresi
            
        Returns:
            LoginResponse
            
        Raises:
            AppError: Geçersiz email/şifre
            ForbiddenError: Hesap onay bekliyor
        """
        rate_limit_kontrol(ip)
        
        if not email or len(email) > 120:
            raise AppError("Geçersiz istek", 400)
        
        kullanici = self.kullanicilar.get_by_email(email, aktif_only=True)
        
        if not kullanici or not sifre_dogrula(sifre, kullanici["sifre"]):
            rate_limit_basarisiz(ip)
            raise AppError("Email veya şifre hatalı", 400)
        
        onay = kullanici.get("onay", 1)
        if not onay:
            raise ForbiddenError(
                "Hesabınız henüz admin onayı bekliyor. Onaylandıktan sonra giriş yapabilirsiniz."
            )
        
        rate_limit_basarili(ip)
        
        token = token_olustur(
            {"sub": kullanici["email"], "rol": kullanici["rol"], "ad": kullanici["ad_soyad"]}
        )
        
        return LoginResponse(
            access_token=token,
            token_type="bearer",
            rol=kullanici["rol"],
            ad=kullanici["ad_soyad"],
        )
    
    def ben(self, payload: Optional[dict]) -> dict:
        """
        Mevcut kullanıcı bilgileri.
        
        Args:
            payload: JWT payload
            
        Returns:
            Kullanıcı bilgileri
        """
        if not payload:
            return {"giris": False}
        
        k = self.kullanicilar.get_public_by_email(payload["sub"])
        if not k:
            return {"giris": False}
        
        return {"giris": True, **k}
    
    def sifre_sifirlama_baslat(self, email: str) -> dict:
        """
        Şifre sıfırlama başlatma.
        
        Args:
            email: E-posta
            
        Returns:
            Sonuç mesajı
        """
        email = (email or "").lower().strip()
        
        # Enumerasyonu önlemek için varlık kontrolü sessiz
        _ = self.kullanicilar.get_by_email(email, aktif_only=True)
        
        token = secrets.token_urlsafe(32)
        get_sifre_token_store()[token] = {"email": email, "exp": time.time() + 900}
        
        print(f"\n{'='*60}\nŞİFRE SIFIRLAMA TOKENI\nE-posta : {email}\nToken   : {token}\nGeçerlilik: 15 dakika\n{'='*60}\n")
        
        return {"mesaj": "Sıfırlama talebi alındı. Sunucu terminalini kontrol edin."}
    
    def sifre_sifirlama_tamamla(self, token: str, yeni_sifre: str) -> dict:
        """
        Şifre sıfırlama tamamlama.
        
        Args:
            token: Sıfırlama token
            yeni_sifre: Yeni şifre
            
        Returns:
            Sonuç mesajı
            
        Raises:
            AppError: Geçersiz token veya kısa şifre
        """
        if not token or not yeni_sifre:
            raise AppError("Token ve yeni şifre gerekli", 400)
        
        if len(yeni_sifre) < 8:
            raise AppError("Şifre en az 8 karakter olmalı", 400)
        
        info = get_sifre_token_store().get(token)
        
        if not info or time.time() > info["exp"]:
            get_sifre_token_store().pop(token, None)
            raise AppError("Geçersiz veya süresi dolmuş token", 400)
        
        self.kullanicilar.update_sifre(info["email"], hash_sifre(yeni_sifre))
        get_sifre_token_store().pop(token, None)
        
        return {"mesaj": "Şifre güncellendi"}