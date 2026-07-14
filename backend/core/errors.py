"""Hata yönetimi ve middleware."""
from __future__ import annotations

from typing import Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


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
    """Hata handler middleware."""
    
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
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": "Sunucu hatası",
                    "data": None
                }
            )