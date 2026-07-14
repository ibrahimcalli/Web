"""Şifre hash ve doğrulama — Döngüsel import önleme için ayrı modül."""
from __future__ import annotations

from passlib.context import CryptContext

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_sifre(sifre: str) -> str:
    """Şifre hash'le."""
    return pwd_ctx.hash(sifre)


def sifre_dogrula(plain: str, hashed: str) -> bool:
    """Şifre doğrula."""
    return pwd_ctx.verify(plain, hashed)