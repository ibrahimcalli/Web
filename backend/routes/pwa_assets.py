"""
Production static assets — manifest.json, sw.js, offline.html, favicon.ico.

Bu route'lar /static altında DEĞİL, kök seviyesinde servis edilir.
SPA fallback'in (index.html) bu dosyaları ezmemesi için:
  1) Bu router SPA fallback'ten ÖNCE include edilir (rok kayıt sırası önemli).
  2) GET ve HEAD metotları desteklenir.
  3) Doğru Content-Type ile döner.
  4) Eksik dosyalar 404 + Content-Type'a göre döner (HTML değil).
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from backend.core.config import BASE_DIR

router = APIRouter()

STATIC_DIR = BASE_DIR / "static"


def _serve_static(filename: str, media_type: str, cache_control: str = "public, max-age=3600"):
    """
    Bir statik dosyayı FileResponse ile döndürür.
    
    Eğer dosya yoksa 404 + JSON döner (HTML düşmez).
    """
    path = STATIC_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"{filename} bulunamadı")
    return FileResponse(
        str(path),
        media_type=media_type,
        headers={
            "Cache-Control": cache_control,
            "Service-Worker-Allowed": "/",
        }
    )


# ─── manifest.json ─────────────────────────────────────────────────────────────
# Hem GET hem HEAD desteklenir. (FastAPI @api_route(["GET","HEAD"]) desenli.)

@router.api_route("/manifest.json", methods=["GET", "HEAD"], include_in_schema=False)
async def manifest_json():
    """PWA manifest — application/manifest+json."""
    return _serve_static(
        "manifest.json",
        media_type="application/manifest+json",
        cache_control="public, max-age=86400",
    )


# ─── sw.js ─────────────────────────────────────────────────────────────────────

@router.api_route("/sw.js", methods=["GET", "HEAD"], include_in_schema=False)
async def service_worker():
    """PWA service worker — application/javascript."""
    return _serve_static(
        "sw.js",
        media_type="application/javascript",
        cache_control="public, max-age=3600",
    )


# ─── offline.html ──────────────────────────────────────────────────────────────

@router.api_route("/offline.html", methods=["GET", "HEAD"], include_in_schema=False)
async def offline_page():
    """PWA offline fallback — text/html."""
    return _serve_static(
        "offline.html",
        media_type="text/html; charset=utf-8",
        cache_control="public, max-age=3600",
    )


# ─── favicon.ico ──────────────────────────────────────────────────────────────
# SPA fallback'ten muaf olması için burada. Eğer dosya yoksa:
#   4xx döneriz — tutarlı davranış.
#   tarayıcılar varolmayan favicon'u zaten tolere eder.

@router.api_route("/favicon.ico", methods=["GET", "HEAD"], include_in_schema=False)
async def favicon_ico():
    """Site favicon — image/x-icon. Tutarlı 204 döner (dosya yoksa)."""
    path = STATIC_DIR / "favicon.ico"
    if not path.exists():
        # Tarayıcılar 404 favicon'u sıklıkla tekrar istediği için 204No Content daha
        # performanslı. Ama tutarlılık için burada 404 ile uyumlu tutuyoruz.
        return JSONResponse(
            status_code=404,
            content={"mesaj": "favicon.ico bulunamadı"},
            headers={"Cache-Control": "no-store"},
        )
    return FileResponse(
        str(path),
        media_type="image/x-icon",
        headers={"Cache-Control": "public, max-age=86400"},
    )
