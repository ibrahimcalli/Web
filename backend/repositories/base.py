"""
Repository Pattern - Interface ve Base Class.

PostgreSQL geçişinde yalnızca Database katmanı değişir.
Repository imzaları ve Service katmanı aynı kalır.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic
from backend.db.database import Database, db

T = TypeVar("T")


class IRepository(ABC, Generic[T]):
    """
    Repository interface - CRUD operasyonlarının sözleşmesi.
    
    Bu interface, tüm repository'ler için standart bir sözleşme sağlar.
    PostgreSQL geçişinde implementasyon değişir, interface aynı kalır.
    """
    
    @abstractmethod
    def get_by_id(self, id: int) -> Optional[T]:
        """ID ile kayıt getir."""
        pass
    
    @abstractmethod
    def get_all(self) -> List[T]:
        """Tüm kayıtları getir."""
        pass
    
    @abstractmethod
    def create(self, data: Dict[str, Any]) -> int:
        """Yeni kayıt oluştur ve ID döndür."""
        pass
    
    @abstractmethod
    def update(self, id: int, data: Dict[str, Any]) -> bool:
        """Kaydı güncelle."""
        pass
    
    @abstractmethod
    def delete(self, id: int) -> bool:
        """Kaydı sil."""
        pass
    
    @abstractmethod
    def exists(self, id: int) -> bool:
        """Kayıt var mı kontrol et."""
        pass


class BaseRepository:
    """
    Temel repository sınıfı - ortak bağlantı yönetimi.
    
    PostgreSQL geçişinde yalnızca Database sınıfı değişir.
    """
    
    def __init__(self, database: Optional[Database] = None):
        """
        Repository başlatma.
        
        Args:
            database: Database instance (testlerde override edilebilir)
        """
        self.database = database or db
    
    def _connect(self):
        """Veritabanı bağlantısı kur."""
        return self.database.connect()
    
    def _fetchone(self, sql: str, params: tuple = ()):
        """
        Tek satır getir.
        
        Args:
            sql: SQL sorgusu
            params: Parametreler
            
        Returns:
            sqlite3.Row veya None
        """
        conn = self._connect()
        try:
            return conn.execute(sql, params).fetchone()
        finally:
            conn.close()
    
    def _fetchall(self, sql: str, params: tuple = ()):
        """
        Tüm satırları getir.
        
        Args:
            sql: SQL sorgusu
            params: Parametreler
            
        Returns:
            sqlite3.Row listesi
        """
        conn = self._connect()
        try:
            return conn.execute(sql, params).fetchall()
        finally:
            conn.close()
    
    def _execute(self, sql: str, params: tuple = ()) -> int:
        """
        INSERT/UPDATE/DELETE çalıştır ve son ID döndür.
        
        Args:
            sql: SQL sorgusu
            params: Parametreler
            
        Returns:
            Son satırın ID'si (INSERT için) veya 0
        """
        conn = self._connect()
        try:
            cur = conn.execute(sql, params)
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()
    
    def _execute_many(self, sql: str, params_list: List[tuple]) -> int:
        """
        Toplu INSERT/DELETE çalıştır.
        
        Args:
            sql: SQL sorgusu
            params_list: Parametre listesi
            
        Returns:
            Etkilenen satır sayısı
        """
        conn = self._connect()
        try:
            cur = conn.executemany(sql, params_list)
            conn.commit()
            return cur.rowcount
        finally:
            conn.close()