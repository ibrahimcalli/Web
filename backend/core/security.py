"""Kimlik doğrulama yardımcıları (JWT, şifre, rate limit)."""
from __future__ import annotations

import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.core.config import ALGORITHM, SECRET_KEY, TOKEN_EXPIRE_MINUTES
from backend.core.password import hash_sifre, sifre_dogrula
from backend.db.database import db, row_to_dict

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2 = OAuth2PasswordBearer(tokenUrl="/api/auth/giris", auto_error=False)

_giris_denemeleri: Dict[str, list] = defaultdict(list)
_engellenen_ipler: Dict[str, float] = {}
MAX_DENEME = 5
ENGEL_SURESI = 900
PENCERE_SURESI = 300

# Şifre sıfırlama token deposu (bellek)
_sifre_sifirlama_tokenlar: Dict[str, dict] = {}


def hash_sifre(sifre: str) -> str:
    return pwd_ctx.hash(sifre)


def sifre_dogrula(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)


def token_olustur(data: dict, dakika: int = TOKEN_EXPIRE_MINUTES) -> str:
    exp = datetime.utcnow() + timedelta(minutes=dakika)
    return jwt.encode({**data, "exp": exp}, SECRET_KEY, algorithm=ALGORITHM)


def client_ip(request: Optional[Request]) -> str:
    if not request:
        return "bilinmiyor"
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return getattr(request.client, "host", None) or "bilinmiyor"


def rate_limit_kontrol(ip: str) -> None:
    simdi = time.time()
    if ip in _engellenen_ipler:
        if simdi < _engellenen_ipler[ip]:
            kalan = int(_engellenen_ipler[ip] - simdi)
            raise HTTPException(
                status_code=429,
                detail=f"Çok fazla başarısız deneme. {kalan} saniye bekleyin.",
                headers={"Retry-After": str(kalan)},
            )
        del _engellenen_ipler[ip]
        _giris_denemeleri[ip] = []
    bas = simdi - PENCERE_SURESI
    _giris_denemeleri[ip] = [t for t in _giris_denemeleri[ip] if t > bas]


def rate_limit_basarisiz(ip: str) -> None:
    simdi = time.time()
    _giris_denemeleri[ip].append(simdi)
    if len(_giris_denemeleri[ip]) >= MAX_DENEME:
        _engellenen_ipler[ip] = simdi + ENGEL_SURESI
        raise HTTPException(status_code=429, detail="Çok fazla başarısız deneme. 15 dakika bekleyin.")


def rate_limit_basarili(ip: str) -> None:
    _giris_denemeleri.pop(ip, None)
    _engellenen_ipler.pop(ip, None)


def decode_token(token: Optional[str] = None) -> Optional[dict]:
    if not token:
        return None
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


def token_coz(token: Optional[str] = Depends(oauth2)) -> Optional[dict]:
    if not token:
        return None
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


def admin_gerek(payload: Optional[dict] = Depends(token_coz)) -> dict:
    if not payload or payload.get("rol") != "admin":
        raise HTTPException(status_code=401, detail="Yetkisiz erişim")
    return payload


def kullanici_gerek(payload: Optional[dict] = Depends(token_coz)) -> dict:
    if not payload:
        raise HTTPException(status_code=401, detail="Giriş yapmanız gerekiyor")
    if payload.get("rol") != "admin":
        conn = db.connect()
        try:
            k = conn.execute(
                "SELECT onay, aktif FROM kullanicilar WHERE email=?",
                (payload["sub"],),
            ).fetchone()
        finally:
            conn.close()
        if not k or not k["aktif"]:
            raise HTTPException(status_code=403, detail="Hesabınız devre dışı")
        if not k["onay"]:
            raise HTTPException(
                status_code=403,
                detail="Hesabınız henüz onaylanmadı. Lütfen yönetici onayını bekleyin.",
            )
    return payload


def get_sifre_token_store() -> Dict[str, dict]:
    return _sifre_sifirlama_tokenlar
