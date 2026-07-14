"""Kullanıcı Service - Kullanıcı iş kuralları."""
from __future__ import annotations

from typing import Optional

from backend.core.errors import AppError, NotFoundError
from backend.core.security import hash_sifre, sifre_dogrula
from backend.repositories.kullanici_repository import KullaniciRepository
from backend.schemas.kullanici import KullaniciCreate, KullaniciUpdate


class KullaniciService:
    """Kullanıcı yönetimi iş kuralları."""
    
    def __init__(self, kullanicilar: Optional[KullaniciRepository] = None):
        """
        Kullanıcı Service başlatma.
        
        Args:
            kullanicilar: KullaniciRepository instance
        """
        self.kullanicilar = kullanicilar or KullaniciRepository()
    
    def listele(self) -> list:
        """
        Tüm kullanıcıları listele.
        
        Returns:
            Kullanıcı listesi
        """
        return self.kullanicilar.list_all()
    
    def kayit(self, data: object) -> dict:
        """
        Yeni kullanıcı kaydı (public).
        
        Args:
            data: KullaniciKayit objesi
            
        Returns:
            Sonuç mesajı
            
        Raises:
            AppError: Geçersiz veri veya duplicate email
        """
        if not data.email or not data.sifre or len(data.sifre) < 6:
            raise AppError("Geçerli email ve en az 6 karakterli şifre gerekli", 400)
        
        try:
            self.kullanicilar.create(
                data.ad_soyad, data.email, hash_sifre(data.sifre), "kullanici", 0
            )
        except Exception as e:
            if "UNIQUE" in str(e).upper() or "unique" in str(e).lower():
                raise AppError("Bu e-posta adresi zaten kayıtlı", 400)
            raise
        
        return {"mesaj": "Kayıt alındı. Admin onayından sonra giriş yapabilirsiniz."}
    
    def ekle(self, data: KullaniciCreate) -> dict:
        """
        Kullanıcı oluştur (admin).
        
        Args:
            data: KullaniciCreate objesi
            
        Returns:
            Sonuç mesajı
            
        Raises:
            AppError: Duplicate email
        """
        try:
            self.kullanicilar.create(
                data.ad_soyad, data.email, hash_sifre(data.sifre), data.rol or "kullanici", 1
            )
        except Exception as e:
            if "UNIQUE" in str(e).upper() or "unique" in str(e).lower():
                raise AppError("Bu email zaten kayıtlı", 400)
            raise
        
        return {"mesaj": "Kullanıcı oluşturuldu"}
    
    def onayla(self, kid: int) -> dict:
        """
        Kullanıcıyı onayla.
        
        Args:
            kid: Kullanıcı ID
            
        Returns:
            Sonuç mesajı
            
        Raises:
            NotFoundError: Kullanıcı bulunamadı
        """
        if not self.kullanicilar.get_by_id(kid):
            raise NotFoundError("Kullanıcı bulunamadı")
        
        self.kullanicilar.set_onay(kid, 1)
        return {"mesaj": "Onaylı", "onay": 1}
    
    def onay_kaldir(self, kid: int) -> dict:
        """
        Kullanıcı onayını kaldır.
        
        Args:
            kid: Kullanıcı ID
            
        Returns:
            Sonuç mesajı
            
        Raises:
            NotFoundError: Kullanıcı bulunamadı
        """
        if not self.kullanicilar.get_by_id(kid):
            raise NotFoundError("Kullanıcı bulunamadı")
        
        self.kullanicilar.set_onay(kid, 0)
        return {"mesaj": "Onay kaldırıldı", "onay": 0}
    
    def sil(self, kid: int) -> dict:
        """
        Kullanıcı sil.
        
        Args:
            kid: Kullanıcı ID
            
        Returns:
            Sonuç mesajı
            
        Raises:
            AppError: Varsayılan admin silinemez
        """
        if kid == 1:
            raise AppError("Varsayılan admin silinemez", 400)
        
        self.kullanicilar.delete(kid)
        return {"mesaj": "Kullanıcı silindi"}
    
    def sifre_degistir(self, email: str, mevcut: str, yeni: str) -> dict:
        """
        Şifre değiştirme.
        
        Args:
            email: E-posta
            mevcut: Mevcut şifre
            yeni: Yeni şifre
            
        Returns:
            Sonuç mesajı
            
        Raises:
            AppError: Yanlış şifre veya kısa yeni şifre
        """
        k = self.kullanicilar.get_by_email(email)
        
        if not k or not sifre_dogrula(mevcut, k["sifre"]):
            raise AppError("Mevcut şifre hatalı", 400)
        
        if len(yeni) < 8:
            raise AppError("Yeni şifre en az 8 karakter olmalı", 400)
        
        self.kullanicilar.update_sifre(email, hash_sifre(yeni))
        return {"mesaj": "Şifre güncellendi"}
    
    def profil_guncelle(self, old_email: str, data: KullaniciUpdate) -> dict:
        """
        Profil güncelleme.
        
        Args:
            old_email: Eski e-posta
            data: KullaniciUpdate objesi
            
        Returns:
            Sonuç mesajı
        """
        self.kullanicilar.update_profil(old_email, data.ad_soyad, data.email)
        
        if data.profil_resmi is not None:
            self.kullanicilar.set_profil_resmi(data.email.lower().strip(), data.profil_resmi)
        
        return {"mesaj": "Profil güncellendi"}
    
    def ben(self, email: str) -> dict:
        """
        Kullanıcı kendi bilgileri.
        
        Args:
            email: E-posta
            
        Returns:
            Kullanıcı bilgileri
            
        Raises:
            NotFoundError: Kullanıcı bulunamadı
        """
        k = self.kullanicilar.get_me(email)
        
        if not k:
            raise NotFoundError("Kullanıcı bulunamadı")
        
        return k
    
    def set_profil_resmi(self, email: str, url: str) -> dict:
        """
        Profil resmi güncelleme.
        
        Args:
            email: E-posta
            url: Profil resmi URL
            
        Returns:
            Yeni ve eski URL
        """
        eski = self.kullanicilar.get_by_email(email)
        self.kullanicilar.set_profil_resmi(email, url)
        
        return {"url": url, "eski": (eski or {}).get("profil_resmi", "")}