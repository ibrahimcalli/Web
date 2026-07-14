"""Kullanıcı Repository - PostgreSQL uyumlu implementasyon."""
from __future__ import annotations

from typing import List, Optional

from backend.repositories.base import BaseRepository
from backend.db.database import row_to_dict, rows_to_dicts


class KullaniciRepository(BaseRepository):
    """
    Kullanıcı CRUD operasyonları.
    
    PostgreSQL geçişinde bu sınıfın SQL sorguları değişir,
    interface ve service katmanı aynı kalır.
    """
    
    def get_by_email(self, email: str, *, aktif_only: bool = False) -> Optional[dict]:
        """
        Email ile kullanıcı getir.
        
        Args:
            email: E-posta adresi
            aktif_only: Sadece aktif kullanıcılar
            
        Returns:
            Kullanıcı dict veya None
        """
        if aktif_only:
            row = self._fetchone(
                "SELECT * FROM kullanicilar WHERE email=? AND aktif=1",
                (email.lower().strip(),),
            )
        else:
            row = self._fetchone(
                "SELECT * FROM kullanicilar WHERE email=?",
                (email.lower().strip(),),
            )
        return row_to_dict(row) if row else None
    
    def get_by_id(self, kid: int) -> Optional[dict]:
        """
        ID ile kullanıcı getir.
        
        Args:
            kid: Kullanıcı ID
            
        Returns:
            Kullanıcı dict veya None
        """
        row = self._fetchone("SELECT * FROM kullanicilar WHERE id=?", (kid,))
        return row_to_dict(row) if row else None
    
    def get_public_by_email(self, email: str) -> Optional[dict]:
        """
        Public kullanıcı bilgileri (email ile).
        
        Args:
            email: E-posta adresi
            
        Returns:
            Public kullanıcı dict veya None
        """
        row = self._fetchone(
            "SELECT id,ad_soyad,email,rol,COALESCE(onay,1) as onay,profil_resmi FROM kullanicilar WHERE email=?",
            (email,),
        )
        return row_to_dict(row) if row else None
    
    def get_me(self, email: str) -> Optional[dict]:
        """
        Kullanıcı kendi bilgileri.
        
        Args:
            email: E-posta adresi
            
        Returns:
            Kullanıcı dict veya None
        """
        row = self._fetchone(
            "SELECT id,ad_soyad,email,rol,aktif,onay,profil_resmi FROM kullanicilar WHERE email=?",
            (email,),
        )
        return row_to_dict(row) if row else None
    
    def list_all(self) -> List[dict]:
        """
        Tüm kullanıcıları getir.
        
        Returns:
            Kullanıcı listesi
        """
        rows = self._fetchall(
            "SELECT id,ad_soyad,email,rol,aktif,COALESCE(onay,1) as onay,"
            "COALESCE(onay,1) as onayli,profil_resmi,olusturma FROM kullanicilar ORDER BY id"
        )
        return rows_to_dicts(rows)
    
    def create(self, ad_soyad: str, email: str, sifre_hash: str, rol: str, onay: int) -> int:
        """
        Kullanıcı oluştur.
        
        Args:
            ad_soyad: Ad soyad
            email: E-posta
            sifre_hash: Şifre hash
            rol: Rol
            onay: Onay durumu
            
        Returns:
            Oluşturulan kullanıcı ID
        """
        return self._execute(
            "INSERT INTO kullanicilar (ad_soyad,email,sifre,rol,onay) VALUES (?,?,?,?,?)",
            (ad_soyad, email.lower().strip(), sifre_hash, rol, onay),
        )
    
    def set_onay(self, kid: int, onay: int) -> None:
        """
        Kullanıcı onay durumu güncelle.
        
        Args:
            kid: Kullanıcı ID
            onay: Onay durumu (0/1)
        """
        self._execute("UPDATE kullanicilar SET onay=? WHERE id=?", (onay, kid))
    
    def delete(self, kid: int) -> None:
        """
        Kullanıcı sil.
        
        Args:
            kid: Kullanıcı ID
        """
        self._execute("DELETE FROM kullanicilar WHERE id=?", (kid,))
    
    def update_sifre(self, email: str, sifre_hash: str) -> None:
        """
        Kullanıcı şifresini güncelle.
        
        Args:
            email: E-posta
            sifre_hash: Yeni şifre hash
        """
        self._execute("UPDATE kullanicilar SET sifre=? WHERE email=?", (sifre_hash, email))
    
    def update_profil(self, old_email: str, ad_soyad: str, email: str) -> None:
        """
        Kullanıcı profilini güncelle.
        
        Args:
            old_email: Eski e-posta
            ad_soyad: Yeni ad soyad
            email: Yeni e-posta
        """
        self._execute(
            "UPDATE kullanicilar SET ad_soyad=?, email=? WHERE email=?",
            (ad_soyad, email.lower().strip(), old_email),
        )
    
    def set_profil_resmi(self, email: str, url: str) -> None:
        """
        Kullanıcı profil resmi güncelle.
        
        Args:
            email: E-posta
            url: Profil resmi URL
        """
        self._execute("UPDATE kullanicilar SET profil_resmi=? WHERE email=?", (url, email))
    
    def get_onay_aktif(self, email: str) -> Optional[dict]:
        """
        Kullanıcı onay ve aktif durumu.
        
        Args:
            email: E-posta
            
        Returns:
            Onay/aktif durumu dict
        """
        row = self._fetchone(
            "SELECT onay, aktif FROM kullanicilar WHERE email=?",
            (email,),
        )
        return row_to_dict(row) if row else None
    
    def get_first_admin_profil(self) -> Optional[dict]:
        """
        İlk admin profil bilgileri.
        
        Returns:
            Admin profil dict
        """
        row = self._fetchone(
            "SELECT ad_soyad, profil_resmi, email FROM kullanicilar WHERE rol='admin' ORDER BY id LIMIT 1"
        )
        return row_to_dict(row) if row else None
    
    def exists(self, kid: int) -> bool:
        """
        Kullanıcı var mı kontrol et.
        
        Args:
            kid: Kullanıcı ID
            
        Returns:
            True varsa
        """
        row = self._fetchone("SELECT 1 FROM kullanicilar WHERE id=?", (kid,))
        return row is not None
    
    def email_exists(self, email: str, exclude_id: Optional[int] = None) -> bool:
        """
        E-posta zaten kayıtlı mı kontrol et.
        
        Args:
            email: E-posta
            exclude_id: Hariç tutulacak ID (güncelleme için)
            
        Returns:
            True zaten kayıtlı
        """
        if exclude_id:
            row = self._fetchone(
                "SELECT 1 FROM kullanicilar WHERE email=? AND id!=?",
                (email.lower().strip(), exclude_id),
            )
        else:
            row = self._fetchone(
                "SELECT 1 FROM kullanicilar WHERE email=?",
                (email.lower().strip(),),
            )
        return row is not None