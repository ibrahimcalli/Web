"""Hata yönetimi ve middleware."""
from __future__ import annotations

import time
import uuid
from typing import Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from backend.core.logging import get_access_logger, get_logger


class AppError(Exception):
    """Uygulama hatası."""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundError(AppError):
    """Kayıt bulunamadı."""
    def __init__(self, message: str = "Kayıt bulunamadı"):
        super().__init__(message, 404)


class UnauthorizedError(AppError):
    """Yetkisiz erişim."""
    def __init__(self, message: str = "Yetkisiz erişim"):
        super().__init__(message, 401)


class ForbiddenError(AppError):
    """Yasak."""
    def __init__(self, message: str = "Bu işlem için yetkiniz yok"):
        super().__init__(message, 403)


class ErrorHandler(BaseHTTPMiddleware):
    """Hata handler middleware — AppError yakalar ve standardize yanıtı döner."""
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except AppError as e:
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "success": False,
                    "message": str(e),
                    "data": None
                }
            )
        except Exception as e:
            # Structured logging — error.log'a yazılır (ERROR level)
            log = get_logger(__name__)
            log.exception("Unhandled error: %s | path=%s", e, request.url.path)
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": "Sunucu hatası",
                    "data": None
                }
            )


class AccessLogMiddleware(BaseHTTPMiddleware):
    """
    Access logging middleware — her isteği logs/access.log'a yazar.
    
    Format: {ip} {method} {path} {status} {duration_ms}ms {user_agent} {request_id}
    
    request_id: her isteğe UUID — korrelation troubleshooting için.
    """
    
    async def dispatch(self, request: Request, call_next):
        # İstek başlangıcı
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
        # Header'a koy ki downstream handler'lar görebilsin
        # Not: Starlette'de request.headers immutable; response header'da döneriz.
        start = time.perf_counter()
        
        # Hatayı da yakalayacak şekilde next'i çağır
        try:
            response = await call_next(request)
        except Exception:
            # access log yine de yazılsın
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            self._log(request, 500, elapsed_ms, request_id)
            raise
        
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        # Yanıt header'larına request_id ekle
        response.headers["X-Request-ID"] = request_id
        self._log(request, response.status_code, elapsed_ms, request_id)
        return response
    
    @staticmethod
    def _log(request: Request, status: int, elapsed_ms: int, request_id: str) -> None:
        ip = request.client.host if request.client else "?"
        # X-Forwarded-For varsa onu kullan
        xff = request.headers.get("X-Forwarded-For")
        if xff:
            ip = xff.split(",")[0].strip()
        method = request.method
        path = request.url.path
        ua = request.headers.get("User-Agent", "?")[:80]
        acc = get_access_logger()
        acc.info(
            "%s | %s %s | %d | %dms | %s | rid=%s",
            ip, method, path, status, elapsed_ms, ua, request_id,
        )


class CsrfProtectMiddleware(BaseHTTPMiddleware):
    """
    JSON-based CSRF koruması — state-changing HTTP metodlarında (POST, PUT, PATCH,
    DELETE) Content-Type kontrolü yapar.
    
    SPA ve JWT tabanlı auth kullanırız, yani CSRF büyük risk değil; ama yine de
    yan koruma olarak:
        - Yalnızca application/json kabul edilir (form-encoded CSRF vector).
        - multipart/form-data yalnızca upload endpoint'leri (route /api/upload/*).
        -XHR/fetch zaten application/json gönderir; basit istekler (cross-site form)
         application/json GÖNDEREMEZ → CSRF engellenir.
    
    Lib davranışı:
        - GET, HEAD, OPTIONS → atla.
        - /api/* yolunda olmayan → atlaSPA fallback index.html döner.
        - multipart ve path /api/upload/* → izin ver (upload endpoint'leri için).
    """
    SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}
    
    async def dispatch(self, request: Request, call_next):
        method = request.method
        if method in self.SAFE_METHODS:
            return await call_next(request)
        
        path = request.url.path
        # Yalnızca API path'leri korunur
        if not path.startswith("/api/"):
            return await call_next(request)
        
        ct = (request.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        # application/json → güvenli (cross-site form basit istek olamaz)
        if ct == "application/json":
            return await call_next(request)
        # multipart/form-data → yalnızca upload endpoint'leri için
        if ct == "multipart/form-data" and ("/upload" in path or "/resim" in path):
            return await call_next(request)
        
        return JSONResponse(
            status_code=415,
            content={
                "success": False,
                "message": "Desteklenmeyen Content-Type. application/json gerekli.",
                "data": None,
            },
        )