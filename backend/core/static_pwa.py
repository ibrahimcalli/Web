"""
Whitelist'li StaticFiles — yalnızca belirli dosyaları kök seviyeden servis eder.

Performance:
    - Starlette StaticFiles doğrudan ASGI seviyesinde çalışır.
    - FastAPI router overhead'i (Pydantic validation, dependency injection) YOK.
    - HEAD ve GET otomatik支持. Cache headers eklenebilir.

Güvenlik:
    - Sadece whitelist'teki dosyalar servis edilir.
    - Dizin gezinti (directory listing) kapalı.
    - Bilinmeyen dosya → 404 (HTML düşmez).

Content-Type Düzeltme:
    - Starlette Python'ın mimetypes modülünü kullanır; .js → text/javascript verir.
    - Biz PWA için application/javascript dönmesini istiyoruz (W3C service worker spec).
    - .json → application/json, ama manifest.json için application/manifest+json tercih.
      (manifest.json override kök app.py'de yapılır, burada genel .js override).
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Mapping, Optional

from starlette.responses import FileResponse, PlainTextResponse
from starlette.staticfiles import StaticFiles
from starlette.types import Scope

# PWA için doğru Content-Type'lar. Starlette varsayılanı bazı türleri
# yanlış veriyor (örn. .js → text/javascript). Burada override.
# MIME_MAP[extension] = media_type
MIME_OVERRIDES: Mapping[str, str] = {
    ".js": "application/javascript",
    ".mjs": "application/javascript",
    ".webmanifest": "application/manifest+json",
}


class WhitelistedStaticFiles(StaticFiles):
    """
    Sadece whitelist'teki dosyaları servis eden StaticFiles.
    
    Args:
        directory: Statik dosya kök dizini.
        allowed: İzin verilen dosya isimleri (relative path, küçük harf).
                 örn: {"manifest.json", "sw.js", "offline.html", "favicon.ico"}
        cache_max_age: Cache-Control max-age (saniye). 0 ise header eklenmez.
    """
    
    def __init__(
        self,
        directory: str | Path,
        allowed: Iterable[str],
        html: bool = False,
        cache_max_age: int = 3600,
    ) -> None:
        super().__init__(directory=str(directory), html=html)
        # Whitelist'i normalize et: küçük harf + başında / olmayan relative path
        self._allowed: frozenset[str] = frozenset(
            a.lstrip("/").lower() for a in allowed
        )
        self._cache_max_age = cache_max_age
        # Statik dosya kök dizini — FileResponse için
        self._directory = Path(directory)
    
    def _mime_for(self, filename: str) -> str:
        """
        Override edilebilir Content-Type bulucu.
        MIME_OVERRIDES'te yoksa mimetypes modülüne düşer.
        """
        import mimetypes
        ext = Path(filename).suffix.lower()
        if ext in MIME_OVERRIDES:
            return MIME_OVERRIDES[ext]
        # mimetypes'a bak; yoksa application/octet-stream
        mt, _ = mimetypes.guess_type(filename)
        return mt or "application/octet-stream"
    
    async def get_response(self, path: str, scope: Scope):
        """
        Sadece whitelist'teki path'ler için cevap döndürür.
        
        - Whitelisted dosya → FileResponse (override Content-Type ile)
        - HEAD desteği otomatik (Starlette FileResponse HEAD'i handle eder)
        - Bilinmeyen dosya → 404 (PlainTextResponse, HTML değil)
        - Cache-Control header eklenir (cache_max_age > 0 ise)
        """
        normalize = path.lstrip("/").lower()
        ilk_segment = normalize.split("/", 1)[0] if "/" in normalize else normalize
        if normalize not in self._allowed and ilk_segment not in self._allowed:
            return PlainTextResponse("Not found", status_code=404)
        
        # Dosya var mı?
        file_path = self._directory / path
        if not file_path.is_file():
            return PlainTextResponse("Not found", status_code=404)
        
        # Güvenlik: path directory içinde mi? (path traversal önlemek için)
        try:
            file_path.resolve().relative_to(self._directory.resolve())
        except ValueError:
            return PlainTextResponse("Forbidden", status_code=403)
        
        media_type = self._mime_for(file_path.name)
        headers = {}
        if self._cache_max_age > 0:
            headers["Cache-Control"] = f"public, max-age={self._cache_max_age}"
        # PWA service worker için scope izni
        if file_path.name == "sw.js":
            headers["Service-Worker-Allowed"] = "/"
        
        return FileResponse(
            str(file_path),
            media_type=media_type,
            headers=headers,
        )
